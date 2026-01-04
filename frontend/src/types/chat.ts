// 시각화 데이터 타입 정의
export interface VisualizationData {
  selected_visualization: "table" | "bar_chart" | "pie_chart" | "line_chart" | "scatter_plot" | "text_summary"
  visualization_data: {
    title: string
    data: Record<string, string | number>[]
    x_axis?: string
    y_axis?: string
  }
  insights: string[]
}

export interface Message {
  id: string
  content: string
  role: "user" | "assistant"
  timestamp: Date
  isStreaming?: boolean
  // 시각화 데이터 필드 추가 (null 허용 - API 응답에서 null이 올 수 있음)
  visualizationData?: VisualizationData | null
}

export interface ChatSession {
  id: number
  user_id: number
  title?: string
  last_message_at?: Date
  created_at: Date
  updated_at: Date
}

// 사용량 제한 정보
export interface UsageLimitInfo {
  exceeded: boolean
  dailyRequests: number
  dailyLimit: number
  remainingRequests: number
  error?: string
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
  // 모달 상태
  modalSessionId: number | null
  isModalOpen: boolean
  // 사용량 제한 상태
  usageLimit: UsageLimitInfo | null
  showUsageLimitPopup: boolean
}

export interface ChatStore extends ChatState {
  addMessage: (message: Omit<Message, "id" | "timestamp">) => Message
  updateMessage: (id: string, content: string, isStreaming?: boolean, visualizationData?: VisualizationData | null) => void
  setCurrentMessage: (message: string) => void
  setLoading: (loading: boolean) => void
  setConnected: (connected: boolean) => void
  setTyping: (typing: boolean) => void
  clearChat: () => void
  
  // 세션 관리 액션들
  setCurrentSession: (session: ChatSession | null) => void
  setSessions: (sessions: ChatSession[]) => void
  addSession: (session: ChatSession) => void
  removeSession: (sessionId: number) => void
  updateSession: (sessionId: number, updates: Partial<ChatSession>) => void
  setSessionsLoading: (loading: boolean) => void
  setHistoryLoading: (loading: boolean) => void
  loadMessagesFromHistory: (messages: Message[]) => void
  // 모달 액션들
  openModal: (sessionId: number) => void
  closeModal: () => void
  // 사용량 제한 액션들
  setUsageLimit: (info: UsageLimitInfo | null) => void
  setShowUsageLimitPopup: (show: boolean) => void
}