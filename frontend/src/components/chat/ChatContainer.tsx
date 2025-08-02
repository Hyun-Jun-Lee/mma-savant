"use client"

import { useState, useEffect } from "react"
import { MessageList } from "./MessageList"
import { MessageInput } from "./MessageInput"
import { SessionSidebar } from "./SessionSidebar"
import { useChatStore } from "@/store/chatStore"
import { useAuth } from "@/hooks/useAuth"
import { useSocket } from "@/hooks/useSocket"
import { useChatSession } from "@/hooks/useChatSession"
import { useUser } from "@/hooks/useUser"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { UserProfile } from "@/components/auth/UserProfile"
import { ArrowLeft, MessageSquare, Trash2, Wifi, WifiOff, Plus, History } from "lucide-react"
import { useRouter } from "next/navigation"

export function ChatContainer() {
  const { addMessage, clearChat, isLoading, currentSession } = useChatStore()
  const { user } = useAuth()
  const { isConnected, isTyping, sendMessage } = useSocket()
  const { createSession, loadSessions } = useChatSession()
  const { incrementUsage } = useUser()
  const router = useRouter()
  const [error, setError] = useState<string | null>(null)
  const [showSessionSidebar, setShowSessionSidebar] = useState(false)

  // 컴포넌트 마운트 시 세션 목록만 로드 (자동 세션 생성 제거)
  useEffect(() => {
    const initializeData = async () => {
      try {
        // 기존 세션 목록만 로드
        await loadSessions()
      } catch (error) {
        console.error('Failed to load sessions:', error)
        setError('세션 목록 로드 중 오류가 발생했습니다.')
      }
    }

    if (user) {
      initializeData()
    }
  }, [user, loadSessions]) // createSession과 currentSession 의존성 제거

  const handleSendMessage = async (message: string) => {
    try {
      setError(null)

      if (!isConnected) {
        setError("서버에 연결되지 않았습니다. 잠시 후 다시 시도해주세요.")
        return
      }

      // 현재 세션이 없으면 새 세션 생성 (첫 메시지 전송 시에만)
      let sessionToUse = currentSession
      if (!sessionToUse) {
        console.log("첫 메시지 전송 - 새 세션 생성")
        sessionToUse = await createSession()
        if (!sessionToUse) {
          setError("세션 생성에 실패했습니다.")
          return
        }
      }

      // 사용자 메시지 추가
      addMessage({
        content: message,
        role: "user",
      })

      // 실시간 소켓을 통해 메시지 전송
      sendMessage(message)

      // 사용량 증가 (비동기, 실패해도 채팅 기능에 영향 없음)
      incrementUsage()

    } catch (error) {
      console.error("Error sending message:", error)
      setError("메시지 전송 중 오류가 발생했습니다.")
    }
  }

  const handleNewChat = async () => {
    try {
      await createSession()
      setError(null)
    } catch (error) {
      setError("새 채팅 생성에 실패했습니다.")
    }
  }

  const handleClearChat = () => {
    clearChat()
    setError(null)
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* 헤더 */}
      <Card className="border-b rounded-none shadow-sm">
        <div className="flex items-center justify-between p-4">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.push("/")}
              className="text-gray-600 hover:text-gray-800"
            >
              <ArrowLeft className="w-4 h-4 mr-1" />
              홈으로
            </Button>
            
            <div className="flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-red-600" />
              <div className="flex flex-col">
                <h1 className="text-lg font-semibold text-gray-800">
                  MMA Savant
                </h1>
                {currentSession?.title && (
                  <span className="text-xs text-gray-500 truncate max-w-[200px]">
                    {currentSession.title}
                  </span>
                )}
              </div>
              
              {/* 연결 상태 표시 */}
              <div className="flex items-center gap-1 ml-2">
                {isConnected ? (
                  <Wifi className="w-4 h-4 text-green-600" />
                ) : (
                  <WifiOff className="w-4 h-4 text-red-600" />
                )}
                <span className={`text-xs ${isConnected ? 'text-green-600' : 'text-red-600'}`}>
                  {isConnected ? '연결됨' : '연결 끊김'}
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowSessionSidebar(true)}
              className="text-gray-600 hover:text-gray-800"
            >
              <History className="w-4 h-4 mr-1" />
              히스토리
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={handleNewChat}
              className="text-gray-600 hover:text-gray-800"
            >
              <Plus className="w-4 h-4 mr-1" />
              새 채팅
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={handleClearChat}
              className="text-gray-600 hover:text-gray-800"
            >
              <Trash2 className="w-4 h-4 mr-1" />
              대화 초기화
            </Button>
            
            <UserProfile />
          </div>
        </div>
      </Card>

      {/* 에러 표시 */}
      {error && (
        <Card className="m-4 p-3 bg-red-50 border-red-200">
          <p className="text-red-600 text-sm">{error}</p>
        </Card>
      )}

      {/* 메시지 목록 */}
      <MessageList />

      {/* 메시지 입력 */}
      <MessageInput 
        onSendMessage={handleSendMessage}
        disabled={isLoading}
      />

      {/* 세션 사이드바 */}
      <SessionSidebar 
        isOpen={showSessionSidebar}
        onClose={() => setShowSessionSidebar(false)}
      />
    </div>
  )
}