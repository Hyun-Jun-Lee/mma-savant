/**
 * 채팅 세션 관리 커스텀 훅
 */
"use client"

import { useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { useChatStore } from '@/store/chatStore'
import { ChatApiService } from '@/services/chatApi'
import { ApiError } from '@/lib/api'
import { ChatSession, Message, VisualizationData } from '@/types/chat'
import { processAssistantResponse } from '@/lib/visualizationParser'
import { ChatSessionResponse } from '@/types/api'

export function useChatSession() {
  const router = useRouter()
  const {
    currentSession,
    sessions,
    sessionsLoading,
    historyLoading,
    setCurrentSession,
    setSessions,
    addSession,
    removeSession,
    updateSession,
    setSessionsLoading,
    setHistoryLoading,
    loadMessagesFromHistory,
    clearChat,
  } = useChatStore()

  /**
   * API 응답을 ChatSession으로 변환
   */
  const convertApiResponseToSession = useCallback((response: ChatSessionResponse): ChatSession => ({
    id: response.id,
    user_id: response.user_id,
    title: response.title,
    last_message_at: response.last_message_at ? new Date(response.last_message_at) : undefined,
    created_at: new Date(response.created_at),
    updated_at: new Date(response.updated_at),
  }), [])

  /**
   * 새 채팅 세션 생성
   */
  const createSession = useCallback(async (title?: string): Promise<ChatSession | null> => {
    try {
      const response = await ChatApiService.createSession({ title })
      const session = convertApiResponseToSession(response)
      addSession(session)
      setCurrentSession(session)
      clearChat() // 새 세션 시작 시 기존 메시지 클리어
      return session
    } catch (error) {
      console.error('Failed to create session:', error)
      const isAuthError = error instanceof ApiError && error.status === 401
      if (isAuthError) {
        router.push('/')
      }
      return null
    }
  }, [addSession, setCurrentSession, clearChat, convertApiResponseToSession, router])

  /**
   * 세션 목록 불러오기
   */
  const loadSessions = useCallback(async (limit = 20, offset = 0) => {
    setSessionsLoading(true)
    try {
      const response = await ChatApiService.getSessions(limit, offset)
      const convertedSessions = response.sessions.map(convertApiResponseToSession)
      setSessions(convertedSessions)
    } catch (error) {
      console.error('Failed to load sessions:', error)
      // 인증 오류(401)만 홈으로 리다이렉트, 그 외는 조용히 실패
      const isAuthError = error instanceof ApiError && error.status === 401
      if (isAuthError) {
        router.push('/')
      }
    } finally {
      setSessionsLoading(false)
    }
  }, [setSessions, setSessionsLoading, convertApiResponseToSession, router])

  /**
   * 특정 세션으로 전환
   */
  const switchToSession = useCallback(async (conversationId: number): Promise<boolean> => {
    try {
      const response = await ChatApiService.getSession(conversationId)
      const session = convertApiResponseToSession(response)
      setCurrentSession(session)

      // 채팅 히스토리 로드
      await loadChatHistory(conversationId)
      return true
    } catch (error) {
      console.error('Failed to switch session:', error)
      const isAuthError = error instanceof ApiError && error.status === 401
      if (isAuthError) {
        router.push('/')
      }
      return false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [setCurrentSession, convertApiResponseToSession, router])

  /**
   * 채팅 히스토리 불러오기
   */
  const loadChatHistory = useCallback(async (conversationId: number, limit = 50, offset = 0) => {
    setHistoryLoading(true)
    try {
      const response = await ChatApiService.getChatHistory(conversationId, limit, offset)
      const validVizTypes = ['table', 'bar_chart', 'pie_chart', 'line_chart', 'area_chart', 'radar_chart', 'scatter_plot', 'horizontal_bar', 'stacked_bar', 'ring_list', 'lollipop_chart'] as const

      const messages: Message[] = response.messages.map(msg => {
        if (msg.role === 'assistant') {
          // 1) visualization 필드 우선 (차트 메타데이터)
          const viz = msg.visualization?.[0]
          if (viz?.visualization_type && viz?.visualization_data) {
            const vizData: VisualizationData | null = validVizTypes.includes(viz.visualization_type as typeof validVizTypes[number])
              ? {
                  selected_visualization: viz.visualization_type as VisualizationData['selected_visualization'],
                  visualization_data: {
                    title: String((viz.visualization_data as Record<string, unknown>).title || "분석 결과"),
                    data: ((viz.visualization_data as Record<string, unknown>).data || viz.visualization_data) as Record<string, string | number>[],
                    x_axis: (viz.visualization_data as Record<string, unknown>).x_axis as string | undefined,
                    y_axis: (viz.visualization_data as Record<string, unknown>).y_axis as string | undefined,
                  },
                  insights: viz.insights || [],
                }
              : null
            return {
              id: msg.id,
              content: msg.content,
              role: msg.role as 'user' | 'assistant',
              timestamp: new Date(msg.timestamp),
              visualizationData: vizData,
            }
          }
          // 2) fallback: content에서 시각화 파싱 (레거시)
          const { visualizationData, textContent } = processAssistantResponse(msg.content)
          let finalContent = textContent || ''
          if (finalContent.includes('```json') || finalContent.includes('selected_visualization')) {
            finalContent = ''
          }
          return {
            id: msg.id,
            content: finalContent,
            role: msg.role as 'user' | 'assistant',
            timestamp: new Date(msg.timestamp),
            visualizationData,
          }
        }
        return {
          id: msg.id,
          content: msg.content,
          role: msg.role as 'user' | 'assistant',
          timestamp: new Date(msg.timestamp),
        }
      })
      loadMessagesFromHistory(messages)
    } catch (error) {
      console.error('Failed to load chat history:', error)
      const isAuthError = error instanceof ApiError && error.status === 401
      if (isAuthError) {
        router.push('/')
      }
    } finally {
      setHistoryLoading(false)
    }
  }, [setHistoryLoading, loadMessagesFromHistory, router])

  /**
   * 세션 삭제
   */
  const deleteSession = useCallback(async (conversationId: number): Promise<boolean> => {
    try {
      await ChatApiService.deleteSession(conversationId)
      removeSession(conversationId)

      // 현재 세션이 삭제된 경우 세션 클리어 (자동 생성하지 않음)
      if (currentSession?.id === conversationId) {
        setCurrentSession(null)
        clearChat()
      }
      return true
    } catch (error) {
      console.error('Failed to delete session:', error)
      const isAuthError = error instanceof ApiError && error.status === 401
      if (isAuthError) {
        router.push('/')
      }
      return false
    }
  }, [removeSession, currentSession, setCurrentSession, clearChat, router])

  /**
   * 세션 제목 업데이트
   */
  const updateSessionTitle = useCallback(async (conversationId: number, title: string): Promise<boolean> => {
    try {
      const response = await ChatApiService.updateSessionTitle(conversationId, title)
      const updatedSession = convertApiResponseToSession(response)

      updateSession(conversationId, { title: updatedSession.title })
      return true
    } catch (error) {
      console.error('Failed to update session title:', error)
      const isAuthError = error instanceof ApiError && error.status === 401
      if (isAuthError) {
        router.push('/')
      }
      return false
    }
  }, [updateSession, convertApiResponseToSession, router])

  /**
   * 세션 접근 권한 확인
   */
  const validateSessionAccess = useCallback(async (conversationId: number): Promise<boolean> => {
    try {
      const response = await ChatApiService.validateSessionAccess(conversationId)
      return response.has_access
    } catch (error) {
      console.error('Failed to validate session access:', error)
      return false
    }
  }, [])

  return {
    // 상태
    currentSession,
    sessions,
    sessionsLoading,
    historyLoading,
    
    // 액션
    createSession,
    loadSessions,
    switchToSession,
    loadChatHistory,
    deleteSession,
    updateSessionTitle,
    validateSessionAccess,
  }
}