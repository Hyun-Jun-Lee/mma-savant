"use client"

import { useEffect, useMemo } from "react"
import { QuestionAnswerCard } from "./QuestionAnswerCard"
import { LoadingCard } from "./LoadingCard"
import { useChatStore } from "@/store/chatStore"
import { Message } from "@/types/chat"
import { Bot } from "lucide-react"

export function DashboardGrid() {
  const { messages, isTyping } = useChatStore()

  // 메시지를 질문-응답 쌍으로 그룹핑 + 로딩 상태 관리
  const { questionAnswerPairs, pendingQuestion } = useMemo(() => {
    const pairs: Array<{ userQuestion: Message; assistantResponse: Message }> = []
    let pendingUserQuestion: Message | null = null

    for (let i = 0; i < messages.length; i++) {
      const currentMessage = messages[i]

      // 사용자 메시지를 찾으면
      if (currentMessage.role === 'user') {
        // 다음 어시스턴트 메시지를 찾기
        const nextAssistantMessage = messages.find((msg, index) =>
          index > i && msg.role === 'assistant'
        )

        // 쌍이 완성된 경우에만 추가
        if (nextAssistantMessage) {
          pairs.push({
            userQuestion: currentMessage,
            assistantResponse: nextAssistantMessage
          })
        } else {
          // 어시스턴트 응답이 없는 경우 (로딩 중)
          pendingUserQuestion = currentMessage
        }
      }
    }

    return {
      questionAnswerPairs: pairs.reverse(), // 최신 카드가 앞에 오도록
      pendingQuestion: pendingUserQuestion
    }
  }, [messages])

  // 메시지 변경사항 로그
  useEffect(() => {
    console.log('🧩 DashboardGrid: messages updated', {
      totalMessages: messages.length,
      pairs: questionAnswerPairs.length,
      pendingQuestion: !!pendingQuestion,
      isTyping,
      messages: messages.map(m => ({ id: m.id, role: m.role, contentLength: m.content.length }))
    })
  }, [messages, questionAnswerPairs, pendingQuestion, isTyping])

  if (questionAnswerPairs.length === 0 && !pendingQuestion) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
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
    )
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-8 sm:px-10">
      <div className="mx-auto max-w-7xl">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-fade-in">
          {/* 로딩 중인 질문 (최상단에 표시) */}
          {pendingQuestion && (
            <LoadingCard
              key={`loading-${pendingQuestion.id}`}
              userQuestion={pendingQuestion.content}
            />
          )}

          {/* 완성된 질문-응답 쌍들 */}
          {questionAnswerPairs.map((pair, index) => (
            <QuestionAnswerCard
              key={`${pair.userQuestion.id}-${pair.assistantResponse.id}`}
              userQuestion={pair.userQuestion}
              assistantResponse={pair.assistantResponse}
            />
          ))}
        </div>
      </div>
    </div>
  )
}