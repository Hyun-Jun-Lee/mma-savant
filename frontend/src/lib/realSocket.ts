/**
 * 실제 WebSocket 서비스 (백엔드 연동)
 */
import { EventEmitter } from 'events'
import { getAuthToken } from './api'

export interface RealSocketEvents {
  connect: () => void
  disconnect: () => void
  message: (data: { content: string; role: 'assistant'; timestamp: Date; messageId?: string }) => void
  message_chunk: (data: { content: string; fullContent: string; role: 'assistant'; timestamp: Date; messageId: string }) => void
  response_complete: (data: { messageId: string; timestamp: Date }) => void
  final_result: (data: { content: string; message_id: string; session_id: string; timestamp: string; tool_results?: any[]; intermediate_steps?: any[] }) => void
  typing: (data: { isTyping: boolean }) => void
  error: (error: string) => void
}

class RealSocket extends EventEmitter {
  private socket: WebSocket | null = null
  private connected = false
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private sessionId: string | null = null

  async connect(sessionId?: string) {
    try {
      // 이미 연결된 상태면 중복 연결 방지
      if (this.connected && this.socket?.readyState === WebSocket.OPEN) {
        console.log('🔌 Already connected, skipping connection attempt')
        return
      }
      
      // 기존 연결이 있으면 먼저 정리
      if (this.socket) {
        console.log('🔌 Closing existing WebSocket connection')
        this.socket.close()
        this.socket = null
        this.connected = false
      }

      // API 클라이언트를 통해 JWT 토큰 가져오기 (캐싱 포함)
      const jwtToken = await getAuthToken()
      if (!jwtToken) {
        throw new Error('No authentication token found')
      }

      this.sessionId = sessionId || null
      
      // WebSocket URL 구성
      const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'
      const params = new URLSearchParams({
        token: jwtToken
      })
      
      if (this.sessionId) {
        params.append('session_id', this.sessionId)
      }

      const url = `${wsUrl}/ws/chat?${params.toString()}`
      
      console.log('🔌 Connecting to WebSocket:', url)
      console.log('🔌 Session ID for connection:', this.sessionId)
      
      this.socket = new WebSocket(url)
      
      this.socket.onopen = () => {
        console.log('🔌 WebSocket connected')
        console.log('🔌 Setting connected state to true')
        this.connected = true
        this.reconnectAttempts = 0
        console.log('🔌 Emitting connect event')
        this.emit('connect')
        console.log('🔌 Connect event emitted, connected state:', this.connected)
      }
      
      this.socket.onclose = (event) => {
        console.log('🔌 WebSocket disconnected:', event.code, event.reason)
        this.connected = false
        this.emit('disconnect')
        
        // 특정 에러 코드는 재연결하지 않음 (토큰 오류, 서버 에러 등)
        if (event.code === 4001 || event.code === 4003 || event.code === 1006) {
          console.log('🚫 Not reconnecting due to authentication or server error')
          return
        }
        
        // 자동 재연결 시도 (디버깅을 위해 일시 비활성화)
        console.log('❌ WebSocket connection closed, NOT reconnecting for debugging')
        console.log('❌ Close event details:', { code: event.code, reason: event.reason })
        
        // 재연결 로직 주석 처리
        // if (this.reconnectAttempts < this.maxReconnectAttempts) {
        //   this.reconnectAttempts++
        //   console.log(`🔄 Reconnecting... Attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`)
        //   setTimeout(() => {
        //     this.connect(this.sessionId || undefined)
        //   }, this.reconnectDelay * this.reconnectAttempts)
        // } else {
        //   console.log('❌ Max reconnect attempts reached, giving up')
        //   this.emit('error', 'Connection lost - please refresh the page')
        // }
      }
      
      this.socket.onerror = (error) => {
        console.error('❌ WebSocket error:', error)
        this.emit('error', 'Connection error')
      }
      
      this.socket.onmessage = (event) => {
        console.log('📡 Raw WebSocket message received:', event.data)
        try {
          const data = JSON.parse(event.data)
          console.log('📡 Parsed WebSocket data:', data)
          this.handleMessage(data)
        } catch (error) {
          console.error('❌ Failed to parse WebSocket message:', error, 'Raw data:', event.data)
        }
      }
      
    } catch (error) {
      console.error('❌ Failed to connect to WebSocket:', error)
      this.emit('error', `Connection failed: ${error}`)
    }
  }

  disconnect() {
    console.log('🔌 Disconnecting WebSocket')
    if (this.socket) {
      this.socket.close()
      this.socket = null
    }
    this.connected = false
    this.currentResponse = ''
    // 모든 이벤트 리스너 제거
    this.removeAllListeners()
    this.emit('disconnect')
    console.log('🔌 WebSocket disconnected manually')
  }

  sendMessage(message: string, sessionId?: string) {
    console.log('📤 sendMessage called, connection state:', this.connected)
    console.log('📤 Socket exists:', !!this.socket)
    console.log('📤 Socket readyState:', this.socket?.readyState)
    
    if (!this.connected || !this.socket) {
      console.log('❌ Cannot send message - not connected')
      this.emit('error', 'Not connected to server')
      return
    }

    // 전달받은 세션 ID를 우선 사용, 없으면 기존 세션 ID 사용
    const useSessionId = sessionId || this.sessionId
    console.log('📤 Using session ID for message:', useSessionId)
    
    const messageData = {
      type: 'message',
      content: message,
      session_id: useSessionId
    }

    try {
      this.socket.send(JSON.stringify(messageData))
      console.log('📤 Sent message:', message)
    } catch (error) {
      console.error('❌ Failed to send message:', error)
      this.emit('error', 'Failed to send message')
    }
  }

  private handleMessage(data: any) {
    console.log('📥 Received WebSocket message:', data.type, data)
    console.log('🔍 Type check:', typeof data.type, data.type.length, JSON.stringify(data.type))
    
    if (data.type === 'response_chunk') {
      console.log('🔍 Entering response_chunk case')
    } else if (data.type.includes('response_chunk')) {
      console.log('🔍 Type includes response_chunk but not exact match')
    }
    
    switch (data.type) {
      case 'connection_established':
        console.log('✅ Connection established:', data.message)
        this.sessionId = data.session_id
        // 연결 상태를 명시적으로 업데이트
        this.connected = true
        console.log('🔌 Connection state updated to connected:', this.connected)
        break
        
      case 'welcome':
        // 환영 메시지를 어시스턴트 메시지로 처리
        this.emit('message', {
          content: data.content,
          role: 'assistant' as const,
          timestamp: new Date()
        })
        break
        
      case 'message_received':
        console.log('✅ Message received by server')
        // 서버에서 새로운 세션 ID를 받은 경우 업데이트
        if (data.session_id && data.session_id !== this.sessionId) {
          console.log(`🔄 Session ID updated: ${this.sessionId} -> ${data.session_id}`)
          this.sessionId = data.session_id
        }
        break
        
      case 'typing':
        this.emit('typing', { isTyping: data.is_typing })
        break
        
      case 'response_start':
        console.log('🚀 Response started')
        this.currentResponse = ''
        break
        
      case 'response_chunk':
        console.log('📝 Processing response_chunk:', data.content)
        console.log('📝 Current response length before:', this.currentResponse.length)
        // 스트리밍 응답 처리 - 청크를 누적
        this.currentResponse += data.content
        console.log('📝 Current response length after:', this.currentResponse.length)
        console.log('📝 Emitting message_chunk event with chunk:', data.content)
        // 증분 청크와 전체 내용을 함께 전달
        this.emit('message_chunk', {
          content: data.content, // 현재 청크만
          fullContent: this.currentResponse, // 전체 누적 내용
          role: 'assistant' as const,
          timestamp: new Date(),
          messageId: data.message_id
        })
        break
        
      case 'final_result':
        console.log('🎯 Processing final_result:', data)
        this.emit('typing', { isTyping: false })
        // final_result를 useSocket의 final_result 리스너로 전달
        this.emit('final_result', {
          content: data.content,
          message_id: data.message_id,
          session_id: data.session_id,
          timestamp: data.timestamp,
          visualization_type: data.visualization_type,
          visualization_data: data.visualization_data,
          insights: data.insights,
          tool_results: data.tool_results,
          intermediate_steps: data.intermediate_steps
        })
        this.currentResponse = '' // 초기화
        break

      case 'response_end':
        console.log('✅ Response completed')
        this.emit('typing', { isTyping: false })
        // 스트리밍 완료 - 기존 메시지를 완료 상태로 변경 (중복 메시지 방지)
        this.emit('response_complete', {
          messageId: data.message_id,
          timestamp: new Date()
        })
        this.currentResponse = '' // 초기화
        break

      case 'error':
        console.error('❌ Server error:', data.error)
        this.emit('error', data.error)
        break
        
      case 'pong':
        console.log('🏓 Pong received')
        break
        
      default:
        console.log('❓ Unknown message type:', data.type)
    }
  }

  private currentResponse = ''

  isConnected() {
    return this.connected
  }

  // Ping 전송 (연결 상태 확인)
  ping() {
    if (this.connected && this.socket) {
      this.socket.send(JSON.stringify({ type: 'ping' }))
    }
  }

  // 현재 세션 ID 반환
  getSessionId() {
    return this.sessionId
  }
}

// 싱글톤 인스턴스
let realSocketInstance: RealSocket | null = null

export const getRealSocket = (): RealSocket => {
  if (!realSocketInstance) {
    realSocketInstance = new RealSocket()
  }
  return realSocketInstance
}