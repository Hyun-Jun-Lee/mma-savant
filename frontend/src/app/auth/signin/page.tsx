"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { GoogleLoginButton } from "@/components/auth/GoogleLoginButton"
import { LoginForm } from "@/components/auth/LoginForm"
import { Button } from "@/components/ui/button"
import { ArrowLeft } from "lucide-react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/hooks/useAuth"
import { useEffect } from "react"

export default function SignInPage() {
  const router = useRouter()
  const { isAuthenticated, isLoading } = useAuth()

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.push("/chat")
    }
  }, [isAuthenticated, isLoading, router])

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-zinc-900 via-gray-900 to-slate-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white/30"></div>
      </div>
    )
  }

  if (isAuthenticated) {
    return null
  }

  const handleLoginSuccess = () => {
    router.push("/chat")
  }

  const handleSignupClick = () => {
    router.push("/auth/signup")
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-900 via-gray-900 to-slate-900 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-gray-700/20 via-transparent to-transparent" />
      <div className="absolute inset-0 bg-grid-white/[0.02] bg-[size:50px_50px]" />

      <Card className="relative w-full max-w-md bg-white/5 backdrop-blur-sm border-white/10">
        <CardHeader className="text-center space-y-6 pb-4">
          <div className="space-y-4">
            <div className="w-16 h-16 mx-auto bg-white rounded-xl flex items-center justify-center shadow-lg">
              <span className="text-zinc-900 font-bold text-xl">MS</span>
            </div>
            <div>
              <CardTitle className="text-3xl font-bold text-white">
                MMA Savant
              </CardTitle>
              <CardDescription className="text-lg mt-2 text-zinc-400">
                Sign in to your account
              </CardDescription>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* 일반 로그인 폼 */}
          <LoginForm
            onSuccess={handleLoginSuccess}
            onSignupClick={handleSignupClick}
          />

          {/* 구분선 */}
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-white/10" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-zinc-900 px-2 text-zinc-500">또는</span>
            </div>
          </div>

          {/* Google 로그인 버튼 */}
          <GoogleLoginButton
            className="w-full bg-white text-zinc-900 hover:bg-zinc-100 font-medium border border-white/20 shadow-lg"
            size="lg"
          >
            Continue with Google
          </GoogleLoginButton>

          <div className="text-center">
            <Button
              variant="ghost"
              onClick={() => router.push("/")}
              className="text-sm text-zinc-400 hover:text-white hover:bg-white/10 transition-colors"
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Home
            </Button>
          </div>

          <div className="text-center text-xs text-zinc-500 space-y-2">
            <p>By signing in, you agree to our Terms of Service and Privacy Policy.</p>
            <p>Get expert insights on MMA fighters, techniques, and fight analysis.</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
