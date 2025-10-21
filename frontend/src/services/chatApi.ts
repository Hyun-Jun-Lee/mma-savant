/**
 * 채팅 세션 관리 API 서비스
 */
import { api } from '@/lib/api'
import type {
  ChatSessionCreate,
  ChatSessionResponse,
  ChatSessionListResponse,
  ChatMessageCreate,
  ChatMessageResponse,
  ChatHistoryResponse,
  SessionValidationResponse,
} from '@/types/api'

export class ChatApiService {
  /**
   * 새 채팅 세션 생성
   */
  static async createSession(data: ChatSessionCreate): Promise<ChatSessionResponse> {
    const response = await api.post<ChatSessionResponse>('/api/chat/session', data)
    return response.data!
  }

  /**
   * 사용자의 채팅 세션 목록 조회
   */
  static async getSessions(limit = 20, offset = 0): Promise<ChatSessionListResponse> {
    const response = await api.get<ChatSessionListResponse>(
      `/api/chat/sessions?limit=${limit}&offset=${offset}`
    )
    return response.data!
  }

  /**
   * 특정 채팅 세션 조회
   */
  static async getSession(conversationId: number): Promise<ChatSessionResponse> {
    const response = await api.get<ChatSessionResponse>(`/api/chat/session/${conversationId}`)
    return response.data!
  }

  /**
   * 채팅 세션 삭제
   */
  static async deleteSession(conversationId: number): Promise<{ success: boolean; message: string }> {
    const response = await api.delete(`/api/chat/session/${conversationId}`)
    return response.data!
  }

  /**
   * 채팅 세션 제목 업데이트
   */
  static async updateSessionTitle(
    conversationId: number,
    title: string
  ): Promise<ChatSessionResponse> {
    const response = await api.put<ChatSessionResponse>(
      `/api/chat/session/${conversationId}/title`,
      { title }
    )
    return response.data!
  }

  /**
   * 채팅 히스토리 조회
   */
  static async getChatHistory(
    conversationId: number,
    limit = 50,
    offset = 0
  ): Promise<ChatHistoryResponse> {
    const response = await api.get<ChatHistoryResponse>(
      `/api/chat/history?conversation_id=${conversationId}&limit=${limit}&offset=${offset}`
    )
    return response.data!
  }

  /**
   * 채팅 메시지 저장 (백업용)
   */
  static async saveMessage(data: ChatMessageCreate): Promise<ChatMessageResponse> {
    const response = await api.post<ChatMessageResponse>('/api/chat/message', data)
    return response.data!
  }

  /**
   * 세션 접근 권한 확인
   */
  static async validateSessionAccess(conversationId: number): Promise<SessionValidationResponse> {
    const response = await api.get<SessionValidationResponse>(
      `/api/chat/session/${conversationId}/validate`
    )
    return response.data!
  }
}