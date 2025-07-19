"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { GoogleLoginButton } from "@/components/auth/GoogleLoginButton"
import { Button } from "@/components/ui/button"
import { ArrowLeft } from "lucide-react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/hooks/useAuth"
import { useEffect } from "react"

export default function SignInPage() {
  const router = useRouter()
  const { isAuthenticated, isLoading } = useAuth()

  // 이미 로그인된 경우 채팅 페이지로 리다이렉트
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.push("/chat")
    }
  }, [isAuthenticated, isLoading, router])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-red-600"></div>
      </div>
    )
  }

  if (isAuthenticated) {
    return null // 리다이렉트 중
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 to-red-100 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center space-y-4">
          <div>
            <CardTitle className="text-3xl font-bold text-red-600">
              🥊 MMA Savant
            </CardTitle>
            <CardDescription className="text-lg mt-2">
              Sign in to your account
            </CardDescription>
          </div>
        </CardHeader>
        
        <CardContent className="space-y-6">
          <div className="space-y-4">
            <GoogleLoginButton className="w-full" size="lg">
              Continue with Google
            </GoogleLoginButton>
          </div>
          
          <div className="text-center">
            <Button 
              variant="ghost" 
              onClick={() => router.push("/")}
              className="text-sm text-gray-600 hover:text-gray-800"
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Home
            </Button>
          </div>
          
          <div className="text-center text-xs text-gray-500 space-y-2">
            <p>By signing in, you agree to our Terms of Service and Privacy Policy.</p>
            <p>Get expert insights on MMA fighters, techniques, and fight analysis.</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}