import { create } from 'zustand'
import { ChatStore, Message } from '@/types/chat'

export const useChatStore = create<ChatStore>((set, get) => ({
  messages: [],
  isLoading: false,
  isConnected: false,
  isTyping: false,
  currentMessage: "",
  // 세션 관리 상태 초기값
  currentSession: null,
  sessions: [],
  sessionsLoading: false,
  historyLoading: false,
  // 선택된 세션 초기값
  selectedSessionId: null,
  // 사용량 제한 상태 초기값
  usageLimit: null,
  showUsageLimitPopup: false,
  // 에러 팝업 상태 초기값
  errorInfo: null,
  showErrorPopup: false,

  addMessage: (message) => {
    const newMessage: Message = {
      ...message,
      id: crypto.randomUUID(),
      timestamp: new Date(),
    }
    
    console.log('🏪 Adding message to store:', newMessage.id, 'role:', newMessage.role, 'isStreaming:', newMessage.isStreaming)
    
    set((state) => ({
      messages: [...state.messages, newMessage],
    }))
    
    return newMessage
  },

  updateMessage: (id, content, isStreaming, visualizationData) => {
    console.log('🏪 Updating message in store:', id, 'content length:', content.length, 'isStreaming:', isStreaming, 'hasVisualization:', !!visualizationData)

    set((state) => {
      const messageFound = state.messages.find(msg => msg.id === id)
      if (!messageFound) {
        console.log('❌ Message not found in store:', id)
      } else {
        console.log('✅ Message found in store, updating:', id)
      }

      return {
        messages: state.messages.map((msg) =>
          msg.id === id ? {
            ...msg,
            content,
            isStreaming: isStreaming ?? false,
            visualizationData: visualizationData !== undefined ? visualizationData : msg.visualizationData
          } : msg
        ),
      }
    })
  },

  setCurrentMessage: (currentMessage) => set({ currentMessage }),
  
  setLoading: (isLoading) => set({ isLoading }),
  
  setConnected: (isConnected) => set({ isConnected }),
  
  setTyping: (isTyping) => set({ isTyping }),

  clearChat: () => set({ 
    messages: [], 
    currentMessage: "", 
    isLoading: false 
  }),

  // 세션 관리 액션들
  setCurrentSession: (session) => set({ currentSession: session }),
  
  setSessions: (sessions) => {
    const convertedSessions = sessions.map(session => ({
      ...session,
      last_message_at: session.last_message_at ? new Date(session.last_message_at) : undefined,
      created_at: new Date(session.created_at),
      updated_at: new Date(session.updated_at),
    }))
    set({ sessions: convertedSessions })
  },
  
  addSession: (session) => {
    const convertedSession = {
      ...session,
      last_message_at: session.last_message_at ? new Date(session.last_message_at) : undefined,
      created_at: new Date(session.created_at),
      updated_at: new Date(session.updated_at),
    }
    console.log('🏪 Adding session to store:', convertedSession.id, 'title:', convertedSession.title)
    set((state) => {
      console.log('🏪 Previous sessions count:', state.sessions.length)
      const newSessions = [convertedSession, ...state.sessions]
      console.log('🏪 New sessions count:', newSessions.length)
      return { sessions: newSessions }
    })
  },
  
  removeSession: (sessionId) => set((state) => ({
    sessions: state.sessions.filter(s => s.id !== sessionId),
    currentSession: state.currentSession?.id === sessionId ? null : state.currentSession,
    selectedSessionId: state.selectedSessionId === sessionId ? null : state.selectedSessionId
  })),
  
  updateSession: (sessionId, updates) => set((state) => ({
    sessions: state.sessions.map(session =>
      session.id === sessionId ? { ...session, ...updates } : session
    ),
    currentSession: state.currentSession?.id === sessionId
      ? { ...state.currentSession, ...updates }
      : state.currentSession
  })),
  
  setSessionsLoading: (loading) => set({ sessionsLoading: loading }),
  
  setHistoryLoading: (loading) => set({ historyLoading: loading }),
  
  loadMessagesFromHistory: (messages) => {
    const convertedMessages = messages.map(msg => ({
      ...msg,
      timestamp: new Date(msg.timestamp)
    }))
    set({ messages: convertedMessages })
  },

  // 세션 선택 액션들
  selectSession: (sessionId) => {
    const session = get().sessions.find(s => s.id === sessionId)
    set({ selectedSessionId: sessionId, currentSession: session ?? null })
  },
  deselectSession: () => set({ selectedSessionId: null }),
  startNewChat: () => set({
    currentSession: null,
    selectedSessionId: null,
    messages: [],
    currentMessage: "",
    isLoading: false,
    isTyping: false,
  }),

  // 사용량 제한 액션들
  setUsageLimit: (info) => set({ usageLimit: info }),
  setShowUsageLimitPopup: (show) => set({ showUsageLimitPopup: show }),

  // 에러 팝업 액션들
  setErrorInfo: (info) => set({ errorInfo: info }),
  setShowErrorPopup: (show) => set({ showErrorPopup: show }),
}))