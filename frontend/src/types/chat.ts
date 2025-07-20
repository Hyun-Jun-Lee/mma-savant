export interface Message {
  id: string
  content: string
  role: "user" | "assistant"
  timestamp: Date
  isStreaming?: boolean
}

export interface ChatSession {
  id: number
  user_id: number
  session_id: string
  title?: string
  message_count: number
  last_message_at?: Date
  created_at: Date
  updated_at: Date
}

export interface ChatState {
  messages: Message[]
  isLoading: boolean
  isConnected: boolean
  isTyping: boolean
  currentMessage: string
  // 세션 관리 상태 추가
  currentSession: ChatSession | null
  sessions: ChatSession[]
  sessionsLoading: boolean
  historyLoading: boolean
}

export interface ChatStore extends ChatState {
  addMessage: (message: Omit<Message, "id" | "timestamp">) => void
  updateMessage: (id: string, content: string) => void
  setCurrentMessage: (message: string) => void
  setLoading: (loading: boolean) => void
  setConnected: (connected: boolean) => void
  setTyping: (typing: boolean) => void
  clearChat: () => void
  
  // 세션 관리 액션들
  setCurrentSession: (session: ChatSession | null) => void
  setSessions: (sessions: ChatSession[]) => void
  addSession: (session: ChatSession) => void
  removeSession: (sessionId: string) => void
  updateSession: (sessionId: string, updates: Partial<ChatSession>) => void
  setSessionsLoading: (loading: boolean) => void
  setHistoryLoading: (loading: boolean) => void
  loadMessagesFromHistory: (messages: Message[]) => void
}