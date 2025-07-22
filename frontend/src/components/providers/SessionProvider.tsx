"use client"

import { SessionProvider as NextAuthSessionProvider } from "next-auth/react"

interface SessionProviderProps {
  children: React.ReactNode
}

export function SessionProvider({ children }: SessionProviderProps) {
  return (
    <NextAuthSessionProvider
      // 세션 폴링 간격을 5분으로 증가 (기본값: 4초)
      refetchInterval={5 * 60}
      // 윈도우 포커스 시에만 세션 업데이트
      refetchOnWindowFocus={true}
      // 브라우저 탭 간 세션 동기화 간격을 1분으로 증가 (기본값: 1초)  
      refetchWhenOffline={false}
    >
      {children}
    </NextAuthSessionProvider>
  )
}