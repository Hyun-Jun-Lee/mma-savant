/**
 * 관리자 API 서비스
 */
import { api } from '@/lib/api'
import type {
  UserAdminResponse,
  UserListResponse,
  UserLimitUpdate,
  UserAdminStatusUpdate,
  UserActiveStatusUpdate,
  AdminStatsResponse,
} from '@/types/api'

export class AdminApiService {
  /**
   * 전체 사용자 목록 조회 (페이지네이션, 검색)
   */
  static async getAllUsers(
    page: number = 1,
    pageSize: number = 20,
    search?: string
  ): Promise<UserListResponse> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    })
    if (search) {
      params.append('search', search)
    }
    const response = await api.get<UserListResponse>(`/api/admin/users?${params}`)
    return response.data!
  }

  /**
   * 특정 사용자 상세 정보 조회
   */
  static async getUserDetail(userId: number): Promise<UserAdminResponse> {
    const response = await api.get<UserAdminResponse>(`/api/admin/users/${userId}`)
    return response.data!
  }

  /**
   * 사용자 일일 요청 제한 수정
   */
  static async updateUserLimit(
    userId: number,
    data: UserLimitUpdate
  ): Promise<UserAdminResponse> {
    const response = await api.patch<UserAdminResponse>(
      `/api/admin/users/${userId}/limit`,
      data
    )
    return response.data!
  }

  /**
   * 사용자 관리자 권한 변경
   */
  static async updateUserAdminStatus(
    userId: number,
    data: UserAdminStatusUpdate
  ): Promise<UserAdminResponse> {
    const response = await api.patch<UserAdminResponse>(
      `/api/admin/users/${userId}/admin`,
      data
    )
    return response.data!
  }

  /**
   * 사용자 활성화 상태 변경
   */
  static async updateUserActiveStatus(
    userId: number,
    data: UserActiveStatusUpdate
  ): Promise<UserAdminResponse> {
    const response = await api.patch<UserAdminResponse>(
      `/api/admin/users/${userId}/active`,
      data
    )
    return response.data!
  }

  /**
   * 관리자 대시보드 통계 조회
   */
  static async getAdminStats(): Promise<AdminStatsResponse> {
    const response = await api.get<AdminStatsResponse>('/api/admin/stats')
    return response.data!
  }
}
