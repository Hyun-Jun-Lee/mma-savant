"use client"

import { useState, useEffect } from "react"
import { HistoryView } from "./HistoryView"
import { MessageInput } from "./MessageInput"
import { UsageLimitPopup } from "./UsageLimitPopup"
import { useChatStore } from "@/store/chatStore"
import { useAuth } from "@/hooks/useAuth"
import { useSocket } from "@/hooks/useSocket"
import { useChatSession } from "@/hooks/useChatSession"
import { useUser } from "@/hooks/useUser"
import { Button } from "@/components/ui/button"
import { UserProfile } from "@/components/auth/UserProfile"
import { ArrowLeft, MessageSquare, User } from "lucide-react"
import { useRouter } from "next/navigation"

export function ChatContainer() {
  const { addMessage, isLoading, currentSession, sessions } = useChatStore()
  const { user } = useAuth()
  const { isConnected, isTyping, sendMessage } = useSocket()
  const { loadSessions, switchToSession } = useChatSession()
  const { incrementUsage } = useUser()
  const router = useRouter()
  const [error, setError] = useState<string | null>(null)

  // 컴포넌트 마운트 시 세션 목록 로드 (자동 전환 제거 - 새 대화로 시작)
  useEffect(() => {
    const initializeData = async () => {
      try {
        // 기존 세션 목록 로드 (사이드바에서 이전 대화 확인용)
        await loadSessions()
      } catch (error) {
        console.error('Failed to load sessions:', error)
        setError('세션 목록 로드 중 오류가 발생했습니다.')
      }
    }

    if (user) {
      initializeData()
    }
  }, [user, loadSessions])

  const handleSendMessage = async (message: string) => {
    try {
      setError(null)

      if (!isConnected) {
        setError("서버에 연결되지 않았습니다. 잠시 후 다시 시도해주세요.")
        return
      }

      // 사용자 메시지 추가 (기존 세션 카드들은 유지, 새 질문만 추가)
      addMessage({
        content: message,
        role: "user",
      })

      // 실시간 소켓을 통해 메시지 전송 (conversation_id는 WebSocket에서 처리)
      await sendMessage(message)

      // 사용량 증가 (비동기, 실패해도 채팅 기능에 영향 없음)
      incrementUsage()

    } catch (error) {
      console.error("Error sending message:", error)
      setError("메시지 전송 중 오류가 발생했습니다.")
    }
  }


  return (
    <div className="relative flex h-screen w-full flex-col overflow-hidden bg-gradient-to-br from-zinc-900 via-gray-900 to-slate-900">
      {/* 배경 패턴 */}
      <div className="fixed inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-gray-700/20 via-transparent to-transparent pointer-events-none" />
      <div className="fixed inset-0 bg-grid-white/[0.02] bg-[size:50px_50px] pointer-events-none" />

      {/* 상단 헤더 */}
      <header className="flex-shrink-0 border-b border-solid border-white/10 px-4 sm:px-10 py-3 relative z-10">
        <div className="mx-auto flex max-w-7xl items-center justify-between whitespace-nowrap">
          <div className="flex items-center gap-4 text-white">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.push("/")}
              className="text-zinc-400 hover:text-white hover:bg-white/10 border border-white/10 backdrop-blur-sm"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Home
            </Button>

            <div className="flex items-center gap-3">
              <div className="w-6 h-6">
                <MessageSquare className="w-6 h-6 text-white" />
              </div>
              <h2 className="text-white text-lg font-bold leading-tight tracking-[-0.015em]">
                MMA Savant
              </h2>

              {/* 연결 상태 표시 */}
              <div className="flex items-center gap-2 px-3 py-1.5 bg-white/5 backdrop-blur-sm rounded-full border border-white/10">
                {isConnected ? (
                  <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
                ) : (
                  <div className="w-2 h-2 bg-red-500 rounded-full" />
                )}
                <span className={`text-xs font-medium ${isConnected ? 'text-emerald-400' : 'text-red-400'}`}>
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <UserProfile />
          </div>
        </div>
      </header>

      {/* 상단 입력 영역 */}
      <div className="flex-shrink-0 bg-gradient-to-br from-zinc-900 via-gray-900 to-slate-900 backdrop-blur-sm p-4 sm:px-10 border-b border-solid border-white/10 relative z-10">
        <div className="mx-auto flex max-w-7xl items-center gap-3">
          <div className="h-10 w-10 shrink-0 rounded-full bg-white/10 backdrop-blur-sm border border-white/20 flex items-center justify-center">
            <User className="w-5 h-5 text-white" />
          </div>
          <div className="flex-1">
            <MessageInput
              onSendMessage={handleSendMessage}
              disabled={isLoading}
              placeholder="궁금한 MMA 데이터를 질문해보세요..."
            />
          </div>
        </div>
      </div>

      {/* 에러 표시 */}
      {error && (
        <div className="relative z-10 mx-4 mt-4">
          <div className="p-4 bg-red-500/10 backdrop-blur-sm border border-red-500/20 rounded-lg">
            <p className="text-red-400 text-sm font-medium">{error}</p>
          </div>
        </div>
      )}

      {/* 메인 히스토리 뷰 */}
      <main className="flex-1 overflow-y-auto relative z-10">
        <HistoryView />
      </main>

      {/* 사용량 제한 팝업 */}
      <UsageLimitPopup />
    </div>
  )
}