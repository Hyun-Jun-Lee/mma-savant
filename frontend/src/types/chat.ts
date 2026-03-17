// 시각화 데이터 타입 정의
export interface VisualizationData {
  selected_visualization: "table" | "bar_chart" | "pie_chart" | "line_chart" | "area_chart" | "radar_chart" | "scatter_plot" | "text_summary" | "horizontal_bar" | "stacked_bar" | "ring_list" | "lollipop_chart"
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

// 에러 정보
export interface ErrorInfo {
  errorClass: string
  message: string
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
  // 선택된 세션 상태
  selectedSessionId: number | null
  // 사용량 제한 상태
  usageLimit: UsageLimitInfo | null
  showUsageLimitPopup: boolean
  // 에러 팝업 상태
  errorInfo: ErrorInfo | null
  showErrorPopup: boolean
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
  // 세션 선택 액션들
  selectSession: (sessionId: number) => void
  deselectSession: () => void
  startNewChat: () => void
  // 사용량 제한 액션들
  setUsageLimit: (info: UsageLimitInfo | null) => void
  setShowUsageLimitPopup: (show: boolean) => void
  // 에러 팝업 액션들
  setErrorInfo: (info: ErrorInfo | null) => void
  setShowErrorPopup: (show: boolean) => void
}