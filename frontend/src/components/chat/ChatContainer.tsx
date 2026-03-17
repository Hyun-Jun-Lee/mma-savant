"use client"

import { useState, useEffect, useCallback } from "react"
import { SessionListPanel } from "./SessionListPanel"
import { SessionDetailPanel } from "./SessionDetailPanel"
import { MessageInput } from "./MessageInput"
import { UsageLimitPopup } from "./UsageLimitPopup"
import { ErrorPopup } from "./ErrorPopup"
import { useChatStore } from "@/store/chatStore"
import { useAuth } from "@/hooks/useAuth"
import { useSocket } from "@/hooks/useSocket"
import { useChatSession } from "@/hooks/useChatSession"
import { useUser } from "@/hooks/useUser"
import { User } from "lucide-react"
import { cn } from "@/lib/utils"

export function ChatContainer() {
  const { addMessage, isLoading } = useChatStore()
  const { user } = useAuth()
  const { isConnected, sendMessage } = useSocket()
  const { loadSessions } = useChatSession()
  const { incrementUsage } = useUser()
  const [error, setError] = useState<string | null>(null)
  const [showMobileDetail, setShowMobileDetail] = useState(false)
  const isLoggedIn = !!user

  // WebSocket 연결 완료 후 세션 목록 1회 로드
  useEffect(() => {
    if (isLoggedIn && isConnected) {
      loadSessions().catch((error) => {
        console.error('Failed to load sessions:', error)
        setError('세션 목록 로드 중 오류가 발생했습니다.')
      })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isLoggedIn, isConnected])

  const handleSendMessage = async (message: string) => {
    try {
      setError(null)

      if (!isConnected) {
        setError("서버에 연결되지 않았습니다. 잠시 후 다시 시도해주세요.")
        return
      }

      // 사용자 메시지 추가
      addMessage({
        content: message,
        role: "user",
      })

      // 모바일에서 스트리밍 화면 바로 보여주기
      setShowMobileDetail(true)

      // 실시간 소켓을 통해 메시지 전송
      await sendMessage(message)

      // 사용량 증가
      incrementUsage()

    } catch (error) {
      console.error("Error sending message:", error)
      setError("메시지 전송 중 오류가 발생했습니다.")
    }
  }

  const handleSessionSelect = useCallback(() => {
    setShowMobileDetail(true)
  }, [])

  const handleMobileBack = useCallback(() => {
    setShowMobileDetail(false)
  }, [])

  return (
    <div className="relative flex h-[calc(100vh-3.5rem)] w-full flex-col overflow-hidden bg-[#050507]">

      {/* 상단 입력 영역 */}
      <div className="flex-shrink-0 backdrop-blur-sm p-4 sm:px-10 border-b border-white/[0.06] relative z-10">
        <div className="mx-auto flex max-w-7xl items-center gap-3">
          <div className="h-10 w-10 shrink-0 rounded-full bg-white/[0.06] border border-white/[0.06] flex items-center justify-center">
            <User className="w-5 h-5 text-white" />
          </div>
          <div className="flex-1">
            <MessageInput
              onSendMessage={handleSendMessage}
              disabled={isLoading}
              placeholder="궁금한 MMA 데이터를 질문해보세요..."
            />
          </div>
          {/* 연결 상태 */}
          <div className="flex shrink-0 items-center gap-1.5 rounded-full border border-white/[0.06] bg-white/[0.03] px-2.5 py-1">
            <div className={`h-1.5 w-1.5 rounded-full ${isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`} />
            <span className={`text-[11px] font-medium ${isConnected ? 'text-emerald-400' : 'text-red-400'}`}>
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
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

      {/* 마스터-디테일 레이아웃 */}
      <div className="flex flex-1 overflow-hidden relative z-10">
        {/* 좌측: 세션 목록 */}
        <div
          className={cn(
            "h-full border-r border-white/[0.06] flex-shrink-0",
            "w-full md:w-80",
            showMobileDetail ? "hidden md:block" : "block"
          )}
        >
          <SessionListPanel onSessionSelect={handleSessionSelect} />
        </div>

        {/* 우측: 세션 상세 */}
        <div
          className={cn(
            "h-full flex-1 min-w-0",
            showMobileDetail ? "block" : "hidden md:block"
          )}
        >
          <SessionDetailPanel
            onBack={handleMobileBack}
            showBackButton={showMobileDetail}
          />
        </div>
      </div>

      {/* 사용량 제한 팝업 */}
      <UsageLimitPopup />
      {/* 에러 팝업 */}
      <ErrorPopup />
    </div>
  )
}
