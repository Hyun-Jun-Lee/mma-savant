/**
 * 환경변수 중앙화 설정
 * 빌드 시점에 한 번만 검증하고 타입 안전하게 사용
 */

function requireEnv(key: string): string {
  const value = process.env[key]
  if (!value) {
    throw new Error(`${key} environment variable is not set`)
  }
  return value
}

export const env = {
  API_BASE_URL: requireEnv('NEXT_PUBLIC_API_URL'),
} as const
