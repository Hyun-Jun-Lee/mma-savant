/**
 * 환경변수 중앙화 설정
 * Next.js의 NEXT_PUBLIC_* 변수는 빌드 타임에 정적으로 인라인되므로
 * 반드시 process.env.NEXT_PUBLIC_XXX 형태로 직접 접근해야 함
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL

if (!API_BASE_URL) {
  throw new Error('NEXT_PUBLIC_API_URL environment variable is not set')
}

export const env = {
  API_BASE_URL,
} as const
