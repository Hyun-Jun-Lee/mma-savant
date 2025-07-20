/**
 * 사용자 관리 API 서비스
 */
import { api } from '@/lib/api'
import type {
  UserProfileResponse,
  UserProfileUpdate,
  UsageResponse,
  AuthCheckResponse,
} from '@/types/api'

export class UserApiService {
  /**
   * 현재 사용자 프로필 조회
   */
  static async getCurrentUserProfile(): Promise<UserProfileResponse> {
    const response = await api.get<UserProfileResponse>('/api/user/profile')
    return response.data!
  }

  /**
   * 사용자 프로필 업데이트
   */
  static async updateProfile(data: UserProfileUpdate): Promise<UserProfileResponse> {
    const response = await api.put<UserProfileResponse>('/api/user/profile', data)
    return response.data!
  }

  /**
   * 특정 사용자 프로필 조회 (ID 기반)
   */
  static async getUserProfile(userId: number): Promise<UserProfileResponse> {
    const response = await api.get<UserProfileResponse>(`/api/user/profile/${userId}`)
    return response.data!
  }

  /**
   * 사용자 사용량 증가
   */
  static async incrementUsage(): Promise<UsageResponse> {
    const response = await api.post<UsageResponse>('/api/user/increment-usage')
    return response.data!
  }

  /**
   * 인증 상태 확인
   */
  static async checkAuth(): Promise<AuthCheckResponse> {
    const response = await api.get<AuthCheckResponse>('/api/user/check-auth')
    return response.data!
  }

  /**
   * 현재 사용자 정보 조회 (간단한 별칭)
   */
  static async getMe(): Promise<UserProfileResponse> {
    const response = await api.get<UserProfileResponse>('/api/user/me')
    return response.data!
  }
}