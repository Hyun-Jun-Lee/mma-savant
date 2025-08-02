/**
 * 채팅 세션 관리 커스텀 훅
 */
"use client"

import { useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { useChatStore } from '@/store/chatStore'
import { ChatApiService } from '@/services/chatApi'
import { handleApiError } from '@/lib/api'
import { ChatSession, Message } from '@/types/chat'
import { ChatSessionResponse, ChatHistoryResponse } from '@/types/api'

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
    session_id: response.session_id,
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
      alert(`세션 생성 실패: ${handleApiError(error)}`)
      router.push('/')
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
      alert(`세션 목록 로드 실패: ${handleApiError(error)}`)
      router.push('/')
    } finally {
      setSessionsLoading(false)
    }
  }, [setSessions, setSessionsLoading, convertApiResponseToSession, router])

  /**
   * 특정 세션으로 전환
   */
  const switchToSession = useCallback(async (sessionId: string): Promise<boolean> => {
    try {
      const response = await ChatApiService.getSession(sessionId)
      const session = convertApiResponseToSession(response)
      setCurrentSession(session)
      
      // 채팅 히스토리 로드
      await loadChatHistory(sessionId)
      return true
    } catch (error) {
      console.error('Failed to switch session:', error)
      alert(`세션 전환 실패: ${handleApiError(error)}`)
      router.push('/')
      return false
    }
  }, [setCurrentSession, convertApiResponseToSession, router])

  /**
   * 채팅 히스토리 불러오기
   */
  const loadChatHistory = useCallback(async (sessionId: string, limit = 50, offset = 0) => {
    setHistoryLoading(true)
    try {
      const response = await ChatApiService.getChatHistory(sessionId, limit, offset)
      const messages: Message[] = response.messages.map(msg => ({
        id: msg.id,
        content: msg.content,
        role: msg.role,
        timestamp: new Date(msg.timestamp),
      }))
      loadMessagesFromHistory(messages)
    } catch (error) {
      console.error('Failed to load chat history:', error)
      alert(`채팅 히스토리 로드 실패: ${handleApiError(error)}`)
      router.push('/')
    } finally {
      setHistoryLoading(false)
    }
  }, [setHistoryLoading, loadMessagesFromHistory, router])

  /**
   * 세션 삭제
   */
  const deleteSession = useCallback(async (sessionId: string): Promise<boolean> => {
    try {
      await ChatApiService.deleteSession(sessionId)
      removeSession(sessionId)
      
      // 현재 세션이 삭제된 경우 세션 클리어 (자동 생성하지 않음)
      if (currentSession?.session_id === sessionId) {
        setCurrentSession(null)
        clearChat()
      }
      return true
    } catch (error) {
      console.error('Failed to delete session:', error)
      alert(`세션 삭제 실패: ${handleApiError(error)}`)
      router.push('/')
      return false
    }
  }, [removeSession, currentSession, setCurrentSession, clearChat, router])

  /**
   * 세션 제목 업데이트
   */
  const updateSessionTitle = useCallback(async (sessionId: string, title: string): Promise<boolean> => {
    try {
      const response = await ChatApiService.updateSessionTitle(sessionId, title)
      const updatedSession = convertApiResponseToSession(response)
      
      updateSession(sessionId, { title: updatedSession.title })
      return true
    } catch (error) {
      console.error('Failed to update session title:', error)
      alert(`제목 수정 실패: ${handleApiError(error)}`)
      router.push('/')
      return false
    }
  }, [updateSession, convertApiResponseToSession, router])

  /**
   * 세션 접근 권한 확인
   */
  const validateSessionAccess = useCallback(async (sessionId: string): Promise<boolean> => {
    try {
      const response = await ChatApiService.validateSessionAccess(sessionId)
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