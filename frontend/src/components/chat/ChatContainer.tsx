"use client"

import { useState, useEffect, useCallback } from "react"
import { SessionListPanel } from "./SessionListPanel"
import { SessionDetailPanel } from "./SessionDetailPanel"
import { UsageLimitPopup } from "./UsageLimitPopup"
import { ErrorPopup } from "./ErrorPopup"
import { useChatStore } from "@/store/chatStore"
import { useAuth } from "@/hooks/useAuth"
import { useSocket } from "@/hooks/useSocket"
import { useChatSession } from "@/hooks/useChatSession"
import { useUser } from "@/hooks/useUser"
import { PanelLeft } from "lucide-react"
import { cn } from "@/lib/utils"

export function ChatContainer() {
  const { addMessage, deselectSession, clearChat } = useChatStore()
  const { user } = useAuth()
  const { isConnected, sendMessage } = useSocket()
  const { loadSessions, switchToSession } = useChatSession()
  const { incrementUsage } = useUser()
  const [error, setError] = useState<string | null>(null)
  const [showMobileDetail, setShowMobileDetail] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
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

  const handleSessionSelect = useCallback(async (sessionId: number) => {
    setShowMobileDetail(true)
    await switchToSession(sessionId)
  }, [switchToSession])

  const handleMobileBack = useCallback(() => {
    setShowMobileDetail(false)
    deselectSession()
    clearChat()
  }, [deselectSession, clearChat])

  const toggleSidebar = useCallback(() => {
    setSidebarCollapsed(prev => !prev)
  }, [])

  return (
    <div className="relative flex h-[calc(100vh-3.5rem)] w-full flex-col overflow-hidden bg-[#050507]">
      {/* 마스터-디테일 레이아웃 */}
      <div className="flex flex-1 overflow-hidden relative z-10">
        {/* 좌측: 세션 목록 (접기/펼치기 가능) */}
        <div
          className={cn(
            "h-full flex-shrink-0 transition-all duration-300 ease-in-out overflow-hidden",
            sidebarCollapsed
              ? "w-0 border-r-0"
              : "w-full md:w-80 border-r border-zinc-700/50",
            showMobileDetail ? "hidden md:block" : "block"
          )}
        >
          <div className="h-full w-full md:w-80">
            <SessionListPanel
              onSessionSelect={handleSessionSelect}
              onCollapse={toggleSidebar}
            />
          </div>
        </div>

        {/* 우측: 세션 상세 */}
        <div
          className={cn(
            "h-full flex-1 min-w-0",
            showMobileDetail ? "block" : "hidden md:block"
          )}
        >
          {/* 사이드바 펼치기 버튼 (접혀있을 때만 표시) */}
          {sidebarCollapsed && (
            <button
              onClick={toggleSidebar}
              className="absolute left-2 top-2 z-20 hidden md:flex items-center justify-center w-8 h-8 rounded-md border border-white/[0.08] bg-zinc-900/90 text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors"
              title="사이드바 열기"
            >
              <PanelLeft className="w-4 h-4" />
            </button>
          )}
          <SessionDetailPanel
            onBack={handleMobileBack}
            showBackButton={showMobileDetail}
            onSendMessage={handleSendMessage}
            isConnected={isConnected}
            error={error}
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
