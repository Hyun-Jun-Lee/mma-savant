/**
 * API 응답 타입 정의
 */

export interface ChatSessionCreate {
  title?: string
}

export interface ChatSessionResponse {
  id: number
  user_id: number
  title?: string
  message_count: number
  last_message_at?: string
  created_at: string
  updated_at: string
}

export interface ChatSessionListResponse {
  sessions: ChatSessionResponse[]
  total_sessions: number
}

export interface ChatMessageCreate {
  content: string
  role: 'user' | 'assistant'
  conversation_id: number
}

export interface ChatMessageResponse {
  id: string
  content: string
  role: 'user' | 'assistant'
  timestamp: string
  conversation_id: number
}

export interface ChatHistoryResponse {
  conversation_id: number
  messages: ChatMessageResponse[]
  total_messages: number
  has_more: boolean
}

export interface UserProfileResponse {
  id: number
  name: string
  email: string
  avatar_url?: string
  total_requests: number
  daily_requests: number
  remaining_requests: number
  created_at: string
  updated_at: string
}

export interface UserProfileUpdate {
  name?: string
  avatar_url?: string
}

export interface UsageResponse {
  success: boolean
  message: string
  usage?: {
    total_requests: number
    daily_requests: number
    remaining_requests: number
  }
}

export interface AuthCheckResponse {
  authenticated: boolean
  user_id: number
  email: string
  name: string
  token_valid: boolean
}

export interface SessionValidationResponse {
  conversation_id: number
  has_access: boolean
  user_id: number
}