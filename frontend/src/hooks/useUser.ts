/**
 * 사용자 관리 커스텀 훅
 */
"use client"

import { useCallback, useState } from 'react'
import { UserApiService } from '@/services/userApi'
import { handleApiError, ApiError } from '@/lib/api'
import { UserProfileResponse, UserProfileUpdate, UsageResponse } from '@/types/api'

export function useUser() {
  const [userProfile, setUserProfile] = useState<UserProfileResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isUpdating, setIsUpdating] = useState(false)

  /**
   * 현재 사용자 프로필 로드
   */
  const loadUserProfile = useCallback(async (): Promise<UserProfileResponse | null> => {
    setIsLoading(true)
    try {
      const profile = await UserApiService.getCurrentUserProfile()
      setUserProfile(profile)
      return profile
    } catch (error) {
      console.error('Failed to load user profile:', error)
      // 인증 오류가 아닌 경우에만 알림 표시
      const isAuthError = error instanceof ApiError && error.status === 401
      if (!isAuthError) {
        alert(`프로필 로드 실패: ${handleApiError(error)}`)
      }
      return null
    } finally {
      setIsLoading(false)
    }
  }, [])

  /**
   * 사용자 프로필 업데이트
   */
  const updateUserProfile = useCallback(async (updates: UserProfileUpdate): Promise<boolean> => {
    setIsUpdating(true)
    try {
      const updatedProfile = await UserApiService.updateProfile(updates)
      setUserProfile(updatedProfile)
      return true
    } catch (error) {
      console.error('Failed to update user profile:', error)
      alert(`프로필 업데이트 실패: ${handleApiError(error)}`)
      return false
    } finally {
      setIsUpdating(false)
    }
  }, [])

  /**
   * 사용자 사용량 증가
   */
  const incrementUsage = useCallback(async (): Promise<UsageResponse | null> => {
    try {
      const response = await UserApiService.incrementUsage()
      
      // 사용량 정보가 있으면 로컬 프로필도 업데이트
      if (response.usage && userProfile) {
        setUserProfile(prev => prev ? {
          ...prev,
          total_requests: response.usage!.total_requests,
          daily_requests: response.usage!.daily_requests,
          remaining_requests: response.usage!.remaining_requests,
        } : null)
      }
      
      return response
    } catch (error) {
      console.error('Failed to increment usage:', error)
      // 사용량 업데이트 실패는 조용히 처리 (채팅 기능에 영향 없음)
      return null
    }
  }, [userProfile])

  /**
   * 인증 상태 확인
   */
  const checkAuth = useCallback(async (): Promise<boolean> => {
    try {
      const response = await UserApiService.checkAuth()
      return response.authenticated && response.token_valid
    } catch (error) {
      console.error('Auth check failed:', error)
      return false
    }
  }, [])

  /**
   * 특정 사용자 프로필 조회 (관리자용)
   */
  const getUserById = useCallback(async (userId: number): Promise<UserProfileResponse | null> => {
    try {
      const profile = await UserApiService.getUserProfile(userId)
      return profile
    } catch (error) {
      console.error('Failed to get user by ID:', error)
      alert(`사용자 조회 실패: ${handleApiError(error)}`)
      return null
    }
  }, [])

  return {
    // 상태
    userProfile,
    isLoading,
    isUpdating,
    
    // 액션
    loadUserProfile,
    updateUserProfile,
    incrementUsage,
    checkAuth,
    getUserById,
  }
}