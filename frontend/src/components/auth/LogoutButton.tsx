"use client"

import { signOut, useSession } from "next-auth/react"
import { Button } from "@/components/ui/button"
import { useState } from "react"
import { LogOut } from "lucide-react"
import { AuthApiService } from "@/services/authApi"
import { useAuthStore } from "@/store/authStore"
import { useRouter } from "next/navigation"

interface LogoutButtonProps {
  className?: string
  variant?: "default" | "outline" | "secondary" | "ghost" | "link" | "destructive"
  size?: "default" | "sm" | "lg" | "icon"
  children?: React.ReactNode
  showIcon?: boolean
}

export function LogoutButton({
  className,
  variant = "ghost",
  size = "default",
  children = "Sign out",
  showIcon = true
}: LogoutButtonProps) {
  const [isLoading, setIsLoading] = useState(false)
  const { status } = useSession()
  const { logout: storeLogout } = useAuthStore()
  const router = useRouter()

  const handleSignOut = async () => {
    try {
      setIsLoading(true)

      // 일반 로그인 토큰 삭제
      AuthApiService.logout()

      // Zustand 스토어 초기화
      storeLogout()

      // OAuth 세션이 있으면 next-auth 로그아웃도 수행
      if (status === "authenticated") {
        await signOut({
          callbackUrl: "/",
          redirect: true
        })
      } else {
        // 일반 로그인만 했던 경우 직접 리다이렉트
        router.push("/")
      }
    } catch (error) {
      console.error("Sign out error:", error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Button
      onClick={handleSignOut}
      disabled={isLoading}
      variant={variant}
      size={size}
      className={className}
    >
      {showIcon && <LogOut className="mr-2 h-4 w-4" />}
      {isLoading ? "Signing out..." : children}
    </Button>
  )
}
