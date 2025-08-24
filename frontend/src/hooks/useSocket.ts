"use client"

import { useEffect, useRef, useState, useCallback } from 'react'
import { getRealSocket } from '@/lib/realSocket'
import { useChatStore } from '@/store/chatStore'

export function useSocket() {
  const [isConnected, setIsConnected] = useState(false)
  const [isTyping, setIsTyping] = useState(false)
  const socketRef = useRef(getRealSocket())
  const { addMessage, updateMessage, setConnected, setTyping, currentSession, setCurrentSession } = useChatStore()
  const currentStreamingMessage = useRef<{ id: string; content: string; storeId?: string } | null>(null)

  // Zustand 스토어 함수들은 이미 안정적이므로 직접 사용

  useEffect(() => {
    const socket = socketRef.current
    
    console.log('🎣 Setting up useSocket event listeners')

    // 연결 이벤트 처리
    socket.on('connect', () => {
      console.log('🔌 Connected to WebSocket server')
      setIsConnected(true)
      setConnected(true)
    })

    socket.on('disconnect', () => {
      console.log('🔌 Disconnected from WebSocket server')
      setIsConnected(false)
      setConnected(false)
    })

    // 메시지 수신 처리 (환영 메시지 등 일반 메시지용)
    socket.on('message', (data: { content: string; role: 'assistant'; timestamp: Date; messageId?: string }) => {
      console.log('💪 Received message:', data)
      addMessage({
        content: data.content,
        role: data.role
      })
    })

    // 스트리밍 메시지 청크 처리
    socket.on('message_chunk', (data: { 
      content: string; 
      fullContent: string;
      messageId: string;
      role: 'assistant';
      timestamp: Date;
    }) => {
      console.log('📝 Received message_chunk:', data)
      console.log('📝 Current streaming message:', currentStreamingMessage.current?.id)
      
      if (!currentStreamingMessage.current || currentStreamingMessage.current.id !== data.messageId) {
        // 새로운 스트리밍 메시지 시작 - 즉시 타이핑 상태 해제
        console.log('🆕 Starting new streaming message:', data.messageId)
        console.log('⚡ Immediately stopping typing indicator')
        setIsTyping(false)
        setTyping(false)
        
        // 새 메시지 추가
        const newMessage = {
          content: data.fullContent, // 첫 청크는 fullContent를 사용
          role: 'assistant' as const,
          isStreaming: true
        }
        
        const addedMessage = addMessage(newMessage)
        
        // 현재 스트리밍 메시지 정보 저장 (store ID 직접 사용)
        currentStreamingMessage.current = { 
          id: data.messageId, 
          content: data.fullContent,
          storeId: addedMessage.id // addMessage에서 반환된 실제 ID 사용
        }
        
        console.log('📝 New streaming message stored with store ID:', addedMessage.id)
      } else {
        // 기존 메시지 업데이트 - fullContent로 전체 내용 업데이트
        console.log('🔄 Updating streaming message:', data.messageId, 'new length:', data.fullContent.length)
        currentStreamingMessage.current.content = data.fullContent
        
        // store ID를 사용하여 직접 메시지 업데이트
        const storeId = currentStreamingMessage.current.storeId
        if (storeId) {
          console.log('📝 Updating message in store by store ID:', storeId)
          
          // 메시지가 실제로 존재하는지 먼저 확인
          const messages = useChatStore.getState().messages
          const targetMessage = messages.find(msg => msg.id === storeId)
          
          if (targetMessage) {
            console.log('✅ Target message found, updating:', storeId)
            updateMessage(storeId, data.fullContent, true)
          } else {
            console.log('❌ Target message not found in store:', storeId)
            // fallback으로 마지막 스트리밍 메시지 찾기
            const lastAssistantMessage = [...messages].reverse().find(msg => msg.role === 'assistant' && msg.isStreaming)
            if (lastAssistantMessage) {
              console.log('📝 Using fallback message:', lastAssistantMessage.id)
              updateMessage(lastAssistantMessage.id, data.fullContent, true)
              currentStreamingMessage.current.storeId = lastAssistantMessage.id
            } else {
              console.log('❌ No streaming assistant message found in store at all')
            }
          }
        } else {
          console.log('❌ No storeId available, using fallback')
          // fallback: 마지막 스트리밍 메시지 찾기
          const messages = useChatStore.getState().messages
          const lastAssistantMessage = [...messages].reverse().find(msg => msg.role === 'assistant' && msg.isStreaming)
          if (lastAssistantMessage) {
            console.log('📝 Updating message in store (fallback):', lastAssistantMessage.id)
            updateMessage(lastAssistantMessage.id, data.fullContent, true)
            // store ID 저장
            currentStreamingMessage.current.storeId = lastAssistantMessage.id
          } else {
            console.log('❌ No streaming assistant message found in store')
          }
        }
      }
    })

    // 스트리밍 완료 처리  
    socket.on('response_complete', (data: { messageId: string; timestamp: Date }) => {
      console.log('✅ Response complete:', data.messageId)
      // 스트리밍 메시지를 완료 상태로 변경
      if (currentStreamingMessage.current && currentStreamingMessage.current.id === data.messageId) {
        console.log('📝 Finalizing streaming message:', data.messageId)
        
        const finalContent = currentStreamingMessage.current.content
        
        if (currentStreamingMessage.current.storeId) {
          // store ID를 사용하여 직접 완료 처리
          console.log('📝 Setting streaming message as completed by store ID:', currentStreamingMessage.current.storeId)
          updateMessage(currentStreamingMessage.current.storeId, finalContent, false)
        } else {
          // fallback: 마지막 스트리밍 메시지 찾기
          const messages = useChatStore.getState().messages
          const lastAssistantMessage = [...messages].reverse().find(msg => msg.role === 'assistant' && msg.isStreaming)
          if (lastAssistantMessage) {
            console.log('📝 Setting streaming message as completed (fallback):', lastAssistantMessage.id)
            updateMessage(lastAssistantMessage.id, finalContent, false)
          }
        }
        
        currentStreamingMessage.current = null
      }
    })

    // 타이핑 상태 처리
    socket.on('typing', (data: { isTyping: boolean }) => {
      setIsTyping(data.isTyping)
      setTyping(data.isTyping)
    })

    // 메시지 수신 확인 처리 (새 세션 생성 시 세션 정보 업데이트)
    socket.on('message_received', (data: { 
      type: string;
      message_id: string;
      session_id: string;
      timestamp: string;
    }) => {
      console.log('📩 Message received confirmation:', data)
      
      // 현재 세션이 없거나 다른 세션이면 업데이트
      if (!currentSession || currentSession.session_id !== data.session_id) {
        console.log('🔄 Updating current session from WebSocket:', data.session_id)
        
        // 새 세션 정보 생성 (기본 정보만)
        const newSession = {
          id: Date.now(), // 임시 ID
          session_id: data.session_id,
          user_id: 0, // 임시 user_id
          title: `채팅 ${new Date().toLocaleString()}`,
          created_at: new Date(),
          updated_at: new Date(),
          last_message_at: new Date(data.timestamp)
        }
        
        // ChatStore의 현재 세션 업데이트
        setCurrentSession(newSession)
        console.log('✅ Current session updated:', newSession)
      }
    })

    // 에러 처리
    socket.on('error', (error: string) => {
      console.error('Socket error:', error)
    })

    // 초기 연결만 수행 (세션 ID 없이)
    console.log('🔌 Setting up socket event listeners')
    console.log('🔌 Socket current state:', socket.isConnected())
    
    // 연결되지 않은 경우에만 연결 시도
    if (!socket.isConnected()) {
      console.log('🔌 Initial connection without session')
      socket.connect() // 세션 ID 없이 초기 연결
    } else {
      console.log('🔌 Socket already connected, skipping initial connect call')
    }

    // 클린업
    return () => {
      console.log('🎣 Cleaning up useSocket event listeners')
      // 소켓 연결 해제
      socket.disconnect()
    }
  }, [addMessage, updateMessage, setConnected, setTyping, setCurrentSession]) // currentSession 의존성 제거하여 재연결 방지

  const sendMessage = async (message: string) => {
    console.log('🚀 sendMessage called, React isConnected:', isConnected)
    console.log('🚀 sendMessage called, Socket isConnected:', socketRef.current.isConnected())
    console.log('🚀 sendMessage called, Socket exists:', !!socketRef.current)
    
    // 실제 소켓 상태를 기준으로 판단
    const actuallyConnected = socketRef.current && socketRef.current.isConnected()
    
    // 연결되지 않은 경우 잠시 대기 후 재시도
    if (!actuallyConnected) {
      console.log('⏳ Socket not actually connected, waiting for connection...')
      
      // 최대 5초 동안 연결을 기다림
      let attempts = 0
      const maxAttempts = 50 // 5초 (100ms * 50)
      
      while ((!socketRef.current || !socketRef.current.isConnected()) && attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 100))
        attempts++
        console.log(`⏳ Waiting for connection... attempt ${attempts}/${maxAttempts}, socket exists: ${!!socketRef.current}, socket connected: ${socketRef.current?.isConnected()}`)
      }
      
      if (!socketRef.current || !socketRef.current.isConnected()) {
        console.log('❌ Connection timeout after waiting')
        return
      }
      
      console.log('✅ Connection established, sending message')
    }
    
    // 현재 세션 ID로 메시지 전송 (동적으로 세션 ID 설정)
    console.log('📤 Sending message with session:', currentSession?.session_id)
    socketRef.current.sendMessage(message, currentSession?.session_id)
  }

  return {
    isConnected,
    isTyping,
    sendMessage,
  }
}