"use client"

import { useEffect, useRef, useState, useCallback } from 'react'
import { getRealSocket } from '@/lib/realSocket'
import { useChatStore } from '@/store/chatStore'

export function useSocket() {
  const [isConnected, setIsConnected] = useState(false)
  const [isTyping, setIsTyping] = useState(false)
  const socketRef = useRef(getRealSocket())
  const { addMessage, updateMessage, setConnected, setTyping, currentSession } = useChatStore()
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
        // 새로운 스트리밍 메시지 시작
        console.log('🆕 Starting new streaming message:', data.messageId)
        
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

    // 에러 처리
    socket.on('error', (error: string) => {
      console.error('Socket error:', error)
    })

    // 연결 시작 - 현재 세션 ID와 함께 (한 번만)
    console.log('🔌 Attempting to connect socket with session:', currentSession?.session_id)
    socket.connect(currentSession?.session_id)

    // 클린업
    return () => {
      console.log('🎣 Cleaning up useSocket event listeners')
      // 소켓 연결 해제
      socket.disconnect()
    }
  }, [currentSession?.session_id, addMessage, updateMessage, setConnected, setTyping]) // 필요한 의존성 추가

  const sendMessage = (message: string) => {
    if (isConnected) {
      socketRef.current.sendMessage(message)
    }
  }

  return {
    isConnected,
    isTyping,
    sendMessage,
  }
}