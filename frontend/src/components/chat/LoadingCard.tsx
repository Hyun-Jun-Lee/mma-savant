"use client"

import { Card, CardContent } from "@/components/ui/card"
import { User, Bot, Loader2 } from "lucide-react"

interface LoadingCardProps {
  userQuestion: string
}

export function LoadingCard({ userQuestion }: LoadingCardProps) {
  return (
    <Card className="bg-zinc-800/50 backdrop-blur-sm border-zinc-700 animate-pulse">
      <CardContent className="p-6">
        {/* 사용자 질문 */}
        <div className="flex items-start gap-3 mb-4">
          <div className="w-8 h-8 shrink-0 rounded-full bg-zinc-700 flex items-center justify-center">
            <User className="w-4 h-4 text-zinc-300" />
          </div>
          <div className="flex-1">
            <p className="text-white text-sm font-bold leading-normal tracking-[0.015em]">사용자</p>
            <p className="text-white text-sm font-normal leading-normal mt-1">{userQuestion}</p>
          </div>
        </div>

        {/* 로딩 중인 어시스턴트 응답 */}
        <div className="border-t border-zinc-700 pt-4">
          <div className="flex items-start gap-3 mb-4">
            <div className="w-8 h-8 shrink-0 rounded-full bg-blue-600 flex items-center justify-center">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <div className="flex-1">
              <p className="text-white text-sm font-bold leading-normal tracking-[0.015em]">MMA Savant</p>
            </div>
          </div>

          <div className="ml-11 space-y-3">
            {/* 로딩 표시 */}
            <div className="flex items-center gap-3 text-blue-400">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-sm">응답을 생성하고 있습니다...</span>
            </div>

            {/* 로딩 애니메이션 바 */}
            <div className="w-full bg-zinc-700/50 rounded-full h-1 overflow-hidden">
              <div className="h-full bg-blue-500/50 rounded-full animate-pulse" style={{ width: '60%' }}></div>
            </div>

            {/* 로딩 중 플레이스홀더 텍스트 */}
            <div className="space-y-2">
              <div className="h-4 bg-zinc-700/30 rounded animate-pulse"></div>
              <div className="h-4 bg-zinc-700/30 rounded animate-pulse w-3/4"></div>
              <div className="h-4 bg-zinc-700/30 rounded animate-pulse w-1/2"></div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}