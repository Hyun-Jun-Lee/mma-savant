/**
 * 환경변수 중앙화 설정
 * Next.js의 NEXT_PUBLIC_* 변수는 빌드 타임에 정적으로 인라인되므로
 * 반드시 process.env.NEXT_PUBLIC_XXX 형태로 직접 접근해야 함
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL

if (!API_BASE_URL) {
  throw new Error('NEXT_PUBLIC_API_URL environment variable is not set')
}

/**
 * 서버사이드 전용 백엔드 URL (auth.ts에서 사용)
 * NEXT_PUBLIC_ 접두사 없으므로 클라이언트에 노출되지 않음
 */
const BACKEND_URL = process.env.BACKEND_URL || API_BASE_URL

export const env = {
  API_BASE_URL,
  BACKEND_URL,
} as const
