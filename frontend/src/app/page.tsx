"use client"

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { UserProfile } from "@/components/auth/UserProfile";
import { useAuth } from "@/hooks/useAuth";
import { useRouter } from "next/navigation";
import { MessageSquare, Shield, TrendingUp, Users } from "lucide-react";

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
    <div className="min-h-screen bg-gradient-to-br from-zinc-900 via-gray-900 to-slate-900">
      {/* 배경 패턴 */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-gray-700/20 via-transparent to-transparent" />
      <div className="absolute inset-0 bg-grid-white/[0.02] bg-[size:50px_50px]" />
      
      {/* 헤더 */}
      <nav className="absolute top-0 left-0 right-0 z-50 p-6">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center">
              <span className="text-zinc-900 font-bold text-sm">MS</span>
            </div>
            <span className="text-white font-semibold text-xl">MMA Savant</span>
          </div>
          
          <div className="flex items-center space-x-4">
            {isAuthenticated ? (
              <UserProfile />
            ) : (
              !isLoading && (
                <Button
                  size="sm"
                  className="bg-white/10 backdrop-blur-sm border border-white/20 text-white hover:bg-white/20"
                  onClick={() => router.push("/auth/signin")}
                >
                  Sign in
                </Button>
              )
            )}
          </div>
        </div>
      </nav>

      {/* 메인 콘텐츠 */}
      <div className="relative flex items-center justify-center min-h-screen p-6">
        <div className="text-center space-y-12 max-w-4xl mx-auto">
          {/* 헤로 섹션 */}
          <div className="space-y-6">
            <div className="inline-flex items-center px-4 py-2 bg-white/5 backdrop-blur-sm rounded-full border border-white/10">
              <Shield className="w-4 h-4 mr-2 text-zinc-400" />
              <span className="text-zinc-400 text-sm font-medium">Professional MMA Analysis</span>
            </div>
            
            <h1 className="text-5xl md:text-7xl font-bold text-white tracking-tight">
              <span className="bg-gradient-to-r from-white to-zinc-400 bg-clip-text text-transparent">
                MMA Savant
              </span>
            </h1>
            
            <p className="text-xl md:text-2xl text-zinc-400 max-w-2xl mx-auto leading-relaxed">
              Your AI-powered expert for comprehensive MMA analysis, fighter insights, and strategic intelligence
            </p>

            {isAuthenticated && user && (
              <div className="inline-flex items-center px-6 py-3 bg-emerald-500/10 backdrop-blur-sm rounded-full border border-emerald-500/20">
                <div className="w-2 h-2 bg-emerald-500 rounded-full mr-3 animate-pulse" />
                <span className="text-emerald-400 font-medium">
                  Welcome back, {user.name || user.email}
                </span>
              </div>
            )}
          </div>

          {/* 기능 카드들 */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-12">
            {[
              { icon: Users, title: "Fighters", desc: "Complete profiles & stats" },
              { icon: TrendingUp, title: "Analytics", desc: "Performance insights" },
              { icon: MessageSquare, title: "Techniques", desc: "Fighting methods" },
              { icon: Shield, title: "Events", desc: "Historical data" },
            ].map((item, index) => (
              <Card key={index} className="bg-white/5 backdrop-blur-sm border-white/10 hover:bg-white/10 transition-all duration-300">
                <CardContent className="p-6 text-center">
                  <item.icon className="w-8 h-8 mx-auto mb-3 text-zinc-300" />
                  <h3 className="font-semibold text-white mb-1">{item.title}</h3>
                  <p className="text-sm text-zinc-400">{item.desc}</p>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* CTA 버튼들 */}
          <div className="space-y-4 max-w-md mx-auto">
            <Button
              className="w-full h-14 bg-white text-zinc-900 hover:bg-zinc-100 font-semibold text-lg shadow-xl"
              size="lg"
              onClick={handleStartChat}
            >
              <MessageSquare className="w-5 h-5 mr-3" />
              {isAuthenticated ? "Continue Analysis" : "Start Analysis"}
            </Button>

            {!isAuthenticated && !isLoading && (
              <Button
                className="w-full h-12 bg-red-600 hover:bg-red-700 text-white font-medium"
                size="lg"
                onClick={() => router.push("/auth/signin")}
              >
                로그인
              </Button>
            )}

            <p className="text-zinc-500 text-sm">
              Advanced AI analysis • Real-time insights • Professional grade data
            </p>
          </div>
        </div>
      </div>

      {/* 하단 그라디언트 */}
      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent" />
    </div>
  );
}
