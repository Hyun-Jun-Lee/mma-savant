"use client"

import { useAuth } from "@/hooks/useAuth"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import { UserApiService } from "@/services/userApi"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

interface AdminGuardProps {
  children: React.ReactNode
}

export function AdminGuard({ children }: AdminGuardProps) {
  const { isAuthenticated, isLoading: authLoading } = useAuth()
  const router = useRouter()
  const [isAdmin, setIsAdmin] = useState<boolean | null>(null)
  const [isCheckingAdmin, setIsCheckingAdmin] = useState(true)

  useEffect(() => {
    async function checkAdminStatus() {
      if (!isAuthenticated) {
        setIsCheckingAdmin(false)
        return
      }

      try {
        const profile = await UserApiService.getCurrentUserProfile()
        setIsAdmin(profile.is_admin ?? false)
      } catch (error) {
        console.error("Failed to check admin status:", error)
        setIsAdmin(false)
      } finally {
        setIsCheckingAdmin(false)
      }
    }

    if (!authLoading) {
      checkAdminStatus()
    }
  }, [isAuthenticated, authLoading])

  // 인증 로딩 중
  if (authLoading || isCheckingAdmin) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-red-600"></div>
      </div>
    )
  }

  // 미인증 상태
  if (!isAuthenticated) {
    router.push("/auth/signin")
    return null
  }

  // 관리자 아님
  if (!isAdmin) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 to-red-100 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl font-bold text-red-600">
              Access Denied
            </CardTitle>
            <CardDescription>
              관리자 권한이 필요합니다.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-center">
            <button
              onClick={() => router.push("/chat")}
              className="text-red-600 hover:underline"
            >
              채팅 페이지로 돌아가기
            </button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return <>{children}</>
}
