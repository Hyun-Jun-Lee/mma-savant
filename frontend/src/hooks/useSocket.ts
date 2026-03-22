"use client"

import { useEffect, useRef, useState, useCallback } from 'react'
import { getRealSocket } from '@/lib/realSocket'
import { useChatStore } from '@/store/chatStore'
import { VisualizationData } from '@/types/chat'
import { ChatApiService } from '@/services/chatApi'
import { ErrorResponse, logErrorDetails } from '@/types/error'

export function useSocket() {
  const [isConnected, setIsConnected] = useState(false)
  const [isTyping, setIsTyping] = useState(false)
  const socketRef = useRef(getRealSocket())
  const { addMessage, setConnected, setTyping, currentSession, setCurrentSession, setSessions, setUsageLimit, setShowUsageLimitPopup, setErrorInfo, setShowErrorPopup, clearChat } = useChatStore()

  // 세션 목록 새로고침 함수
  const refreshSessions = useCallback(async () => {
    try {
      const response = await ChatApiService.getSessions(20, 0)
      const convertedSessions = response.sessions.map(session => ({
        id: session.id,
        user_id: session.user_id,
        title: session.title,
        last_message_at: session.last_message_at ? new Date(session.last_message_at) : undefined,
        created_at: new Date(session.created_at),
        updated_at: new Date(session.updated_at),
      }))
      setSessions(convertedSessions)
    } catch (error) {
      console.error('Failed to refresh sessions:', error)
    }
  }, [setSessions])

  useEffect(() => {
    const socket = socketRef.current

    // 연결 이벤트 처리
    socket.on('connect', () => {
      setIsConnected(true)
      setConnected(true)
    })

    socket.on('disconnect', () => {
      setIsConnected(false)
      setConnected(false)
    })

    // 일반 메시지 수신 (환영 메시지 등)
    socket.on('message', (data: { content: string; role: 'assistant'; timestamp: Date; messageId?: string }) => {
      addMessage({
        content: data.content,
        role: data.role
      })
    })

    // final_result 처리 (StateGraph 완성된 결과)
    socket.on('final_result', (data: {
      content?: string;
      message_id: string;
      conversation_id: number;
      timestamp: string;
      visualization_type?: string;
      visualization_data?: Record<string, unknown>;
      insights?: string[];
    }) => {
      console.log('🎯 Received final_result:', data.message_id)

      // 타이핑 상태 해제
      setIsTyping(false)
      setTyping(false)

      // 멀티턴: conversation_id를 currentSession에 반영
      if (data.conversation_id) {
        const prev = useChatStore.getState().currentSession
        if (!prev || prev.id !== data.conversation_id) {
          setCurrentSession({
            id: data.conversation_id,
            user_id: prev?.user_id ?? 0,
            title: prev?.title ?? `채팅 ${new Date().toLocaleString()}`,
            created_at: prev?.created_at ?? new Date(),
            updated_at: new Date(),
            last_message_at: new Date(data.timestamp),
          })
        }
      }

      // 시각화 데이터 구성
      let visualizationData: VisualizationData | null = null
      const validVisualizationTypes = ['table', 'bar_chart', 'pie_chart', 'line_chart', 'area_chart', 'radar_chart', 'scatter_plot', 'text_summary', 'horizontal_bar', 'stacked_bar', 'ring_list', 'lollipop_chart'] as const
      if (
        data.visualization_type &&
        data.visualization_data &&
        data.visualization_type !== 'text_summary' &&
        validVisualizationTypes.includes(data.visualization_type as typeof validVisualizationTypes[number])
      ) {
        visualizationData = {
          selected_visualization: data.visualization_type as VisualizationData['selected_visualization'],
          visualization_data: {
            title: String(data.visualization_data.title || "분석 결과"),
            data: (data.visualization_data.data || data.visualization_data) as Record<string, string | number>[],
            x_axis: data.visualization_data.x_axis as string | undefined,
            y_axis: data.visualization_data.y_axis as string | undefined
          },
          insights: data.insights || []
        }
      }

      // 텍스트 content 처리
      const textContent = data.content ?? ""

      // 완성된 메시지 추가
      addMessage({
        content: textContent,
        role: 'assistant' as const,
        isStreaming: false,
        visualizationData: visualizationData
      })

      // 세션 목록만 백그라운드 갱신 (멀티턴: 채팅 유지)
      refreshSessions()
    })

    // response_end: 타이핑 상태 정리 (final_result에서 이미 처리되나 안전장치)
    socket.on('response_end', () => {
      setIsTyping(false)
      setTyping(false)
    })

    // 타이핑 상태 처리
    socket.on('typing', (data: { isTyping: boolean }) => {
      setIsTyping(data.isTyping)
      setTyping(data.isTyping)
    })

    // 에러 처리
    socket.on('error', (error: string) => {
      console.error('Socket error:', error)
      setErrorInfo({ errorClass: 'UnexpectedException', message: '오류가 발생했습니다. 잠시 후 다시 시도해주세요.' })
      setShowErrorPopup(true)
      setIsTyping(false)
      setTyping(false)
    })

    // 백엔드 에러 응답 처리
    socket.on('error_response', (errorData: ErrorResponse) => {
      logErrorDetails(errorData)

      setErrorInfo({ errorClass: errorData.error_class, message: '오류가 발생했습니다. 잠시 후 다시 시도해주세요.' })
      setShowErrorPopup(true)

      clearChat()
      setIsTyping(false)
      setTyping(false)
    })

    // 일일 사용량 제한 초과 처리
    socket.on('usage_limit_exceeded', (data: {
      error: string;
      daily_requests: number;
      daily_limit: number;
      remaining_requests: number;
      timestamp: string;
    }) => {
      setUsageLimit({
        exceeded: true,
        dailyRequests: data.daily_requests,
        dailyLimit: data.daily_limit,
        remainingRequests: data.remaining_requests,
        error: data.error
      })
      setShowUsageLimitPopup(true)
      setIsTyping(false)
      setTyping(false)
    })

    // 연결되지 않은 경우에만 연결 시도
    if (!socket.isConnected()) {
      socket.connect()
    }

    return () => {
      socket.disconnect()
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const sendMessage = async (message: string) => {
    const actuallyConnected = socketRef.current && socketRef.current.isConnected()

    if (!actuallyConnected) {
      let attempts = 0
      const maxAttempts = 50
      while ((!socketRef.current || !socketRef.current.isConnected()) && attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 100))
        attempts++
      }
      if (!socketRef.current || !socketRef.current.isConnected()) {
        return
      }
    }

    socketRef.current.sendMessage(message, currentSession?.id)
  }

  return {
    isConnected,
    isTyping,
    sendMessage,
  }
}
