"use client"

import { useEffect, useRef, useState } from 'react'
import { getRealSocket } from '@/lib/realSocket'
import { useChatStore } from '@/store/chatStore'

export function useSocket() {
  const [isConnected, setIsConnected] = useState(false)
  const [isTyping, setIsTyping] = useState(false)
  const socketRef = useRef(getRealSocket())
  const { addMessage, setConnected, setTyping, currentSession } = useChatStore()

  useEffect(() => {
    const socket = socketRef.current

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

    // 메시지 수신 처리
    socket.on('message', (data: { content: string; role: 'assistant'; timestamp: Date }) => {
      addMessage({
        content: data.content,
        role: data.role,
      })
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

    // 연결 시작 - 현재 세션 ID와 함께
    socket.connect(currentSession?.session_id)

    // 클린업
    return () => {
      socket.disconnect()
    }
  }, [addMessage, setConnected, setTyping, currentSession?.session_id])

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