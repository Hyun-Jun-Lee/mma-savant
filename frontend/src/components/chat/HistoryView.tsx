"use client"

import { useEffect, useRef, useMemo } from "react"
import { useChatStore } from "@/store/chatStore"
import { useChatSession } from "@/hooks/useChatSession"
import { Message } from "@/types/chat"
import { QuestionAnswerCard } from "./QuestionAnswerCard"
import { SessionDetailModal } from "./SessionDetailModal"
import { Bot, MessageSquare, Loader2 } from "lucide-react"

export function HistoryView() {
  const { messages, isTyping, currentSession, sessions, modalSessionId, isModalOpen, openModal, closeModal } = useChatStore()
  const bottomRef = useRef<HTMLDivElement>(null)

  // 현재 진행 중인 질문 (응답이 아직 없는 사용자 메시지)
  const currentPendingQuestion = useMemo(() => {
    const userMessages = messages.filter(m => m.role === 'user')
    const assistantMessages = messages.filter(m => m.role === 'assistant')

    // 마지막 사용자 메시지가 있고, 그에 대한 응답이 없으면 진행 중
    if (userMessages.length > assistantMessages.length) {
      return userMessages[userMessages.length - 1]
    }
    return null
  }, [messages])

  // 에러 메시지 확인
  const errorMessage = useMemo(() => {
    return messages.find(m => m.role === 'assistant' && m.content.startsWith('⚠️'))
  }, [messages])

  // 새 메시지가 추가되거나 타이핑 상태가 변경될 때마다 스크롤을 맨 아래로
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isTyping])


  // 현재 메시지도 없고 기존 세션도 없을 때만 환영 메시지 표시
  if (messages.length === 0 && sessions.length === 0) {
    return (
      <div className="flex-1 overflow-y-auto px-4 py-6 sm:px-10">
        <div className="mx-auto max-w-7xl">
          <div className="flex items-center justify-center min-h-[60vh]">
            <div className="p-8 text-center max-w-md">
              <div className="mb-6">
                <div className="w-16 h-16 mx-auto bg-white/10 backdrop-blur-sm rounded-full flex items-center justify-center border border-white/20">
                  <Bot className="w-8 h-8 text-white" />
                </div>
              </div>
              <h3 className="text-xl font-semibold text-white mb-3">
                Start analyzing with MMA Savant
              </h3>
              <p className="text-zinc-400 text-sm leading-relaxed mb-6">
                Ask about fighters, techniques, events, history, and everything MMA.
                Get professional and accurate insights.
              </p>

              {/* 예시 질문들 */}
              <div className="space-y-3">
                <p className="text-xs text-zinc-500 font-medium uppercase tracking-wider">Sample questions:</p>
                <div className="space-y-2 text-sm">
                  <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-lg p-3 text-zinc-300 hover:bg-white/10 transition-colors cursor-pointer">
                    "What are Jon Jones' key techniques?"
                  </div>
                  <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-lg p-3 text-zinc-300 hover:bg-white/10 transition-colors cursor-pointer">
                    "What was UFC 300's main event?"
                  </div>
                  <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-lg p-3 text-zinc-300 hover:bg-white/10 transition-colors cursor-pointer">
                    "Explain Brazilian Jiu-Jitsu basics"
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // 통합된 뷰: 현재 진행 중인 질문 + 기존 세션 카드들을 함께 표시
  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 sm:px-10">
      <div className="mx-auto max-w-7xl">

        {/* 현재 진행 중인 질문 카드 (로딩 또는 에러 상태) */}
        {currentPendingQuestion && (
          <div className="mb-8">
            <div className="bg-blue-500/10 backdrop-blur-sm border border-blue-500/30 rounded-lg p-6 animate-fade-in">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 shrink-0 rounded-full bg-blue-500/20 flex items-center justify-center">
                  <MessageSquare className="w-5 h-5 text-blue-400" />
                </div>
                <div className="flex-1">
                  <p className="text-white font-medium mb-3 line-clamp-3">
                    {currentPendingQuestion.content}
                  </p>

                  {/* 에러 메시지 */}
                  {errorMessage ? (
                    <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                      <p className="text-red-400 text-sm">{errorMessage.content}</p>
                    </div>
                  ) : isTyping ? (
                    /* 로딩 상태 */
                    <div className="flex items-center gap-3">
                      <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />
                      <span className="text-blue-300 text-sm">응답을 생성하고 있습니다...</span>
                    </div>
                  ) : null}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 기존 세션 목록 */}
        {sessions.length > 0 && (
          <div>
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-white">이전 대화</h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 animate-fade-in">
              {sessions.map((session) => (
                <div
                  key={session.id}
                  className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-lg p-4 hover:bg-white/10 transition-colors cursor-pointer"
                  onClick={(e) => {
                    e.preventDefault()
                    e.stopPropagation()
                    openModal(session.id)
                  }}
                >
                  <h3 className="text-white font-medium mb-2 line-clamp-2">
                    {session.title || `채팅 ${session.id}`}
                  </h3>
                  <p className="text-zinc-400 text-sm">
                    {session.last_message_at
                      ? new Date(session.last_message_at).toLocaleDateString('ko-KR', {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })
                      : '시간 정보 없음'
                    }
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 스크롤 앵커 */}
        <div ref={bottomRef} />
      </div>

      {/* 세션 상세 모달 */}
      <SessionDetailModal
        sessionId={modalSessionId}
        isOpen={isModalOpen}
        onClose={closeModal}
        sessionTitle={sessions.find(s => s.id === modalSessionId)?.title}
      />
    </div>
  )
}