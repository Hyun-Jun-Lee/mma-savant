/**
 * API 클라이언트 및 유틸리티 함수
 */
import { getSession } from 'next-auth/react'
import { AuthApiService } from '@/services/authApi'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface ApiResponse<T = unknown> {
  data?: T
  error?: string
  status: number
}

export interface ApiErrorResponse {
  message?: string
  detail?: string
  [key: string]: unknown
}

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public response?: ApiErrorResponse
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

// JWT 토큰 캐시
let cachedToken: string | null = null
let tokenExpiry: number | null = null

/**
 * JWT 토큰 가져오기 (캐싱 포함)
 * 일반 로그인과 OAuth 로그인 모두 지원
 */
export async function getAuthToken(): Promise<string | null> {
  try {
    // 1. 일반 로그인 토큰 확인 (localStorage)
    const localToken = AuthApiService.getToken()
    if (localToken) {
      return localToken
    }

    // 2. OAuth 토큰 캐시 확인
    if (cachedToken && tokenExpiry && Date.now() < tokenExpiry - 60000) {
      return cachedToken
    }

    // 3. OAuth 세션에서 토큰 가져오기
    const session = await getSession()

    if (!session?.user) {
      cachedToken = null
      tokenExpiry = null
      return null
    }

    // 백엔드에서 JWT 토큰 생성 요청
    const response = await fetch(`${API_BASE_URL}/api/auth/google-token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        google_token: session.googleAccessToken || '',
        email: session.user.email || '',
        name: session.user.name || '',
        picture: session.user.image || '',
      }),
    })

    if (response.ok) {
      const tokenData = await response.json()
      cachedToken = tokenData.access_token
      tokenExpiry = Date.now() + (tokenData.expires_in * 1000)
      return cachedToken
    }

    console.error('Failed to get JWT token from backend')
    cachedToken = null
    tokenExpiry = null
    return null

  } catch (error) {
    console.error('Failed to get auth token:', error)
    cachedToken = null
    tokenExpiry = null
    return null
  }
}

/**
 * API 요청 헬퍼
 */
async function apiRequest<T = unknown>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const url = `${API_BASE_URL}${endpoint}`

  // 인증 토큰 가져오기
  const token = await getAuthToken()

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    })

    let data: T | undefined
    let errorData: ApiErrorResponse | undefined
    const contentType = response.headers.get('content-type')

    if (contentType && contentType.includes('application/json')) {
      const jsonData = await response.json()
      if (response.ok) {
        data = jsonData as T
      } else {
        errorData = jsonData as ApiErrorResponse
      }
    }

    if (!response.ok) {
      throw new ApiError(
        errorData?.message || errorData?.detail || `HTTP ${response.status}: ${response.statusText}`,
        response.status,
        errorData
      )
    }

    return {
      data,
      status: response.status,
    }
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }

    const errorMessage = error instanceof Error ? error.message : 'Unknown error'
    throw new ApiError(
      `Network error: ${errorMessage}`,
      0,
      { message: errorMessage }
    )
  }
}

/**
 * API 메서드들
 */
export const api = {
  get: <T = unknown>(endpoint: string, options?: RequestInit) =>
    apiRequest<T>(endpoint, { ...options, method: 'GET' }),

  post: <T = unknown>(endpoint: string, data?: unknown, options?: RequestInit) =>
    apiRequest<T>(endpoint, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    }),

  put: <T = unknown>(endpoint: string, data?: unknown, options?: RequestInit) =>
    apiRequest<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    }),

  delete: <T = unknown>(endpoint: string, options?: RequestInit) =>
    apiRequest<T>(endpoint, { ...options, method: 'DELETE' }),

  patch: <T = unknown>(endpoint: string, data?: unknown, options?: RequestInit) =>
    apiRequest<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    }),
}

/**
 * API 에러 핸들링 유틸리티
 */
export function handleApiError(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return '인증이 필요합니다. 다시 로그인해 주세요.'
    }
    if (error.status === 403) {
      return '접근 권한이 없습니다.'
    }
    if (error.status === 404) {
      return '요청한 리소스를 찾을 수 없습니다.'
    }
    if (error.status >= 500) {
      return '서버 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.'
    }
    return error.message
  }
  
  return '알 수 없는 오류가 발생했습니다.'
}