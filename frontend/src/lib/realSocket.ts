/**
 * 실제 WebSocket 서비스 (백엔드 연동)
 */
import { EventEmitter } from 'events'
import { getAuthToken } from './api'
import { env } from '@/config/env'

export interface RealSocketEvents {
  connect: () => void
  disconnect: () => void
  message: (data: { content: string; role: 'assistant'; timestamp: Date; messageId?: string }) => void
  final_result: (data: { content: string; message_id: string; conversation_id: number; timestamp: string }) => void
  typing: (data: { isTyping: boolean }) => void
  error: (error: string) => void
}

class RealSocket extends EventEmitter {
  private socket: WebSocket | null = null
  private connected = false
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private conversationId: number | null = null

  async connect(conversationId?: number) {
    try {
      // 이미 연결된 상태면 중복 연결 방지
      if (this.connected && this.socket?.readyState === WebSocket.OPEN) {
        return
      }

      // 기존 연결이 있으면 먼저 정리
      if (this.socket) {
        this.socket.close()
        this.socket = null
        this.connected = false
      }

      // API 클라이언트를 통해 JWT 토큰 가져오기
      const jwtToken = await getAuthToken()
      if (!jwtToken) {
        throw new Error('No authentication token found')
      }

      this.conversationId = conversationId || null

      // WebSocket URL 구성
      const apiUrl = env.API_BASE_URL
      const wsUrl = apiUrl.replace(/^http/, 'ws')
      const params = new URLSearchParams({
        token: jwtToken
      })

      if (this.conversationId) {
        params.append('conversation_id', this.conversationId.toString())
      }

      const url = `${wsUrl}/ws/chat?${params.toString()}`

      this.socket = new WebSocket(url)

      this.socket.onopen = () => {
        this.connected = true
        this.reconnectAttempts = 0
        this.emit('connect')
      }

      this.socket.onclose = (event) => {
        this.connected = false
        this.emit('disconnect')

        // 특정 에러 코드는 재연결하지 않음
        if (event.code === 4001 || event.code === 4003 || event.code === 1006) {
          return
        }
      }

      this.socket.onerror = (error) => {
        console.error('WebSocket error:', error)
        this.emit('error', 'Connection error')
      }

      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          this.handleMessage(data)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

    } catch (error) {
      console.error('Failed to connect to WebSocket:', error)
      this.emit('error', `Connection failed: ${error}`)
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.close()
      this.socket = null
    }
    this.connected = false
    this.removeAllListeners()
    this.emit('disconnect')
  }

  sendMessage(message: string, conversationId?: number) {
    if (!this.connected || !this.socket) {
      this.emit('error', 'Not connected to server')
      return
    }

    const useConversationId = conversationId || this.conversationId

    const messageData = {
      type: 'message',
      content: message,
      conversation_id: useConversationId
    }

    try {
      this.socket.send(JSON.stringify(messageData))
    } catch (error) {
      console.error('Failed to send message:', error)
      this.emit('error', 'Failed to send message')
    }
  }

  private handleMessage(data: Record<string, unknown>) {
    const messageType = String(data.type || '')

    switch (messageType) {
      case 'connection_established':
        this.conversationId = data.conversation_id as number | null
        this.connected = true
        break

      case 'welcome':
        this.emit('message', {
          content: String(data.content || ''),
          role: 'assistant' as const,
          timestamp: new Date()
        })
        break

      case 'typing':
        this.emit('typing', { isTyping: Boolean(data.is_typing) })
        break

      case 'stream_start':
        this.emit('stream_start', {
          message_id: data.message_id as string,
          timestamp: data.timestamp as string,
        })
        break

      case 'stream_token':
        this.emit('stream_token', {
          message_id: data.message_id as string,
          token: data.token as string,
        })
        break

      case 'stream_visualization':
        this.emit('stream_visualization', {
          message_id: data.message_id as string,
          visualization_type: data.visualization_type as string,
          visualization_data: data.visualization_data as Record<string, unknown>,
          insights: data.insights as string[],
        })
        break

      case 'final_result':
        this.emit('typing', { isTyping: false })
        this.emit('final_result', {
          content: data.content as string,
          message_id: data.message_id as string,
          conversation_id: data.conversation_id as number,
          timestamp: data.timestamp as string,
          visualization_type: data.visualization_type as string | undefined,
          visualization_data: data.visualization_data as Record<string, unknown> | undefined,
          insights: data.insights as string[] | undefined,
        })
        break

      case 'response_end':
        this.emit('typing', { isTyping: false })
        this.emit('response_end', {
          message_id: String(data.message_id || ''),
          conversation_id: data.conversation_id as number,
          timestamp: data.timestamp as string,
        })
        break

      case 'error':
        this.emit('error', String(data.error || 'Unknown error'))
        break

      case 'error_response':
        this.emit('error_response', data)
        break

      case 'pong':
        break

      case 'usage_limit_exceeded':
        this.emit('usage_limit_exceeded', data)
        break

      default:
        console.log('Unknown message type:', messageType)
    }
  }

  isConnected() {
    return this.connected
  }

  ping() {
    if (this.connected && this.socket) {
      this.socket.send(JSON.stringify({ type: 'ping' }))
    }
  }

  getConversationId() {
    return this.conversationId
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
