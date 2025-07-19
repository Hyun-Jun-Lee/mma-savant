"use client"

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { GoogleLoginButton } from "@/components/auth/GoogleLoginButton";
import { UserProfile } from "@/components/auth/UserProfile";
import { useAuth } from "@/hooks/useAuth";
import { useRouter } from "next/navigation";

export default function Home() {
  const { isAuthenticated, isLoading, user } = useAuth()
  const router = useRouter()

  const handleStartChat = () => {
    if (isAuthenticated) {
      router.push("/chat")
    } else {
      // 로그인이 필요하다는 알림을 보여주거나 로그인 페이지로 이동
      router.push("/auth/signin")
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 to-red-100">
      {/* 헤더 */}
      <div className="absolute top-4 right-4">
        {isAuthenticated ? (
          <UserProfile />
        ) : (
          !isLoading && (
            <GoogleLoginButton size="sm">
              Sign in
            </GoogleLoginButton>
          )
        )}
      </div>

      {/* 메인 콘텐츠 */}
      <div className="flex items-center justify-center min-h-screen p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <CardTitle className="text-3xl font-bold text-red-600">
              🥊 MMA Savant
            </CardTitle>
            <CardDescription className="text-lg">
              Your Personal MMA Expert Chat Assistant
            </CardDescription>
            {isAuthenticated && user && (
              <p className="text-sm text-green-600 font-medium">
                Welcome back, {user.name || user.email}!
              </p>
            )}
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap gap-2 justify-center">
              <Badge variant="secondary">Fighters</Badge>
              <Badge variant="secondary">Techniques</Badge>
              <Badge variant="secondary">Events</Badge>
              <Badge variant="secondary">History</Badge>
            </div>
            
            <div className="space-y-2">
              <Button 
                className="w-full bg-red-600 hover:bg-red-700" 
                size="lg"
                onClick={handleStartChat}
              >
                {isAuthenticated ? "Continue Chat" : "Start Chat"}
              </Button>
              
              {!isAuthenticated && !isLoading && (
                <GoogleLoginButton className="w-full" size="lg">
                  Sign in with Google
                </GoogleLoginButton>
              )}
            </div>
            
            <div className="text-center text-sm text-gray-600">
              <p>Get expert insights on MMA fighters, techniques, and fight analysis</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
