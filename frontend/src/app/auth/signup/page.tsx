"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { GoogleLoginButton } from "@/components/auth/GoogleLoginButton"
import { SignupForm } from "@/components/auth/SignupForm"
import { Button } from "@/components/ui/button"
import { ArrowLeft } from "lucide-react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/hooks/useAuth"
import { useEffect } from "react"

type AuthTab = "general" | "oauth"

export default function SignUpPage() {
  const router = useRouter()
  const { isAuthenticated, isLoading } = useAuth()
  const [activeTab, setActiveTab] = useState<AuthTab>("general")

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

  const handleSignupSuccess = () => {
    router.push("/chat")
  }

  const handleLoginClick = () => {
    router.push("/auth/signin")
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
                Create your account
              </CardDescription>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Auth Tab Selector */}
          <div className="flex rounded-lg bg-white/5 p-1">
            <button
              onClick={() => setActiveTab("general")}
              className={`flex-1 py-2 px-4 text-sm font-medium rounded-md transition-all ${
                activeTab === "general"
                  ? "bg-white/10 text-white"
                  : "text-zinc-400 hover:text-white"
              }`}
            >
              일반 회원가입
            </button>
            <button
              onClick={() => setActiveTab("oauth")}
              className={`flex-1 py-2 px-4 text-sm font-medium rounded-md transition-all ${
                activeTab === "oauth"
                  ? "bg-white/10 text-white"
                  : "text-zinc-400 hover:text-white"
              }`}
            >
              소셜 로그인
            </button>
          </div>

          {/* Tab Content */}
          {activeTab === "general" ? (
            <SignupForm
              onSuccess={handleSignupSuccess}
              onLoginClick={handleLoginClick}
            />
          ) : (
            <div className="space-y-4">
              <GoogleLoginButton
                className="w-full bg-white text-zinc-900 hover:bg-zinc-100 font-medium border border-white/20 shadow-lg"
                size="lg"
              >
                Continue with Google
              </GoogleLoginButton>

              <p className="text-center text-sm text-zinc-400">
                이미 계정이 있으신가요?{" "}
                <button
                  onClick={handleLoginClick}
                  className="text-red-500 hover:text-red-400 underline"
                >
                  로그인
                </button>
              </p>
            </div>
          )}

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
            <p>By signing up, you agree to our Terms of Service and Privacy Policy.</p>
            <p>Get expert insights on MMA fighters, techniques, and fight analysis.</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
