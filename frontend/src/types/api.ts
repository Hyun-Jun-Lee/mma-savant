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
  name?: string
  email?: string
  picture?: string  // Backend 필드명과 일치
  username?: string
  total_requests: number
  daily_requests: number
  daily_request_limit: number
  remaining_requests: number
  is_active: boolean
  is_admin: boolean
  created_at: string
  updated_at?: string
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

// Admin API 타입

export interface UserAdminResponse {
  id: number
  email?: string
  name?: string
  picture?: string
  is_admin: boolean
  total_requests: number
  daily_requests: number
  daily_request_limit: number
  last_request_date?: string
  is_active: boolean
  created_at: string
  updated_at?: string
}

export interface UserListResponse {
  users: UserAdminResponse[]
  total_users: number
  page: number
  page_size: number
  total_pages: number
}

export interface UserLimitUpdate {
  daily_request_limit: number
}

export interface UserAdminStatusUpdate {
  is_admin: boolean
}

export interface UserActiveStatusUpdate {
  is_active: boolean
}

export interface AdminStatsResponse {
  total_users: number
  active_users: number
  admin_users: number
  total_requests_today: number
  total_conversations: number
}