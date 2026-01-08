/**
 * 인증 API 서비스
 * 회원가입, 로그인 등 인증 관련 API 호출
 */
import { env } from '@/config/env'

const API_BASE_URL = env.API_BASE_URL

export interface SignupRequest {
  username: string
  email?: string
  password: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface AuthResponse {
  success: boolean
  message: string
  access_token?: string
  token_type?: string
  expires_in?: number
  user?: {
    id: number
    username: string
    email?: string
  }
}

export interface AuthError {
  detail: string
}

// 토큰 저장 키
const TOKEN_KEY = 'auth_token'
const TOKEN_EXPIRY_KEY = 'auth_token_expiry'
const USER_KEY = 'auth_user'

export const AuthApiService = {
  /**
   * 회원가입
   */
  async signup(data: SignupRequest): Promise<AuthResponse> {
    const response = await fetch(`${API_BASE_URL}/api/auth/signup`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })

    const result = await response.json()

    if (!response.ok) {
      throw new Error(result.detail || '회원가입에 실패했습니다.')
    }

    // 토큰 저장
    if (result.access_token) {
      this.saveToken(result.access_token, result.expires_in || 86400)
      if (result.user) {
        this.saveUser(result.user)
      }
    }

    return result
  },

  /**
   * 로그인
   */
  async login(data: LoginRequest): Promise<AuthResponse> {
    const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })

    const result = await response.json()

    if (!response.ok) {
      throw new Error(result.detail || '로그인에 실패했습니다.')
    }

    // 토큰 저장
    if (result.access_token) {
      this.saveToken(result.access_token, result.expires_in || 86400)
      if (result.user) {
        this.saveUser(result.user)
      }
    }

    return result
  },

  /**
   * 로그아웃
   */
  logout(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(TOKEN_EXPIRY_KEY)
      localStorage.removeItem(USER_KEY)
    }
  },

  /**
   * 토큰 저장
   */
  saveToken(token: string, expiresIn: number): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem(TOKEN_KEY, token)
      const expiry = Date.now() + expiresIn * 1000
      localStorage.setItem(TOKEN_EXPIRY_KEY, expiry.toString())
    }
  },

  /**
   * 사용자 정보 저장
   */
  saveUser(user: { id: number; username: string; email?: string }): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem(USER_KEY, JSON.stringify(user))
    }
  },

  /**
   * 저장된 토큰 가져오기
   */
  getToken(): string | null {
    if (typeof window === 'undefined') return null

    const token = localStorage.getItem(TOKEN_KEY)
    const expiry = localStorage.getItem(TOKEN_EXPIRY_KEY)

    if (!token || !expiry) return null

    // 만료 확인
    if (Date.now() > parseInt(expiry)) {
      this.logout()
      return null
    }

    return token
  },

  /**
   * 저장된 사용자 정보 가져오기
   */
  getUser(): { id: number; username: string; email?: string } | null {
    if (typeof window === 'undefined') return null

    const userStr = localStorage.getItem(USER_KEY)
    if (!userStr) return null

    try {
      return JSON.parse(userStr)
    } catch {
      return null
    }
  },

  /**
   * 로그인 상태 확인
   */
  isAuthenticated(): boolean {
    return this.getToken() !== null
  },
}
