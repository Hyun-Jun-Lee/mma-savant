import { create } from 'zustand'
import { ChatStore, Message, ChatSession } from '@/types/chat'

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

  addMessage: (message) => {
    const newMessage: Message = {
      ...message,
      id: crypto.randomUUID(),
      timestamp: new Date(),
    }
    
    set((state) => ({
      messages: [...state.messages, newMessage],
    }))
  },

  updateMessage: (id, content) => {
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === id ? { ...msg, content, isStreaming: false } : msg
      ),
    }))
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
    set((state) => ({
      sessions: [convertedSession, ...state.sessions]
    }))
  },
  
  removeSession: (sessionId) => set((state) => ({
    sessions: state.sessions.filter(s => s.session_id !== sessionId),
    currentSession: state.currentSession?.session_id === sessionId ? null : state.currentSession
  })),
  
  updateSession: (sessionId, updates) => set((state) => ({
    sessions: state.sessions.map(session =>
      session.session_id === sessionId ? { ...session, ...updates } : session
    ),
    currentSession: state.currentSession?.session_id === sessionId
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
}))