"use client"

import { useEffect, useRef, useMemo } from "react"
import { useChatStore } from "@/store/chatStore"
import { Message } from "@/types/chat"
import { MessageBubble } from "./MessageBubble"
import { QuestionAnswerCard } from "./QuestionAnswerCard"
import { TypingIndicator } from "./TypingIndicator"
import { Bot } from "lucide-react"

export function HistoryView() {
  const { messages, isTyping } = useChatStore()
  const bottomRef = useRef<HTMLDivElement>(null)

  // 메시지를 질문-응답 쌍으로 그룹핑
  const questionAnswerPairs = useMemo(() => {
    const pairs: Array<{ userQuestion: Message; assistantResponse: Message }> = []

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
        }
      }
    }

    return pairs // 시간순으로 표시 (최신이 아래)
  }, [messages])

  // 새 메시지가 추가되거나 타이핑 상태가 변경될 때마다 스크롤을 맨 아래로
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isTyping])


  // 메시지가 없을 때만 환영 메시지 표시 (히스토리가 있으면 카드 표시)
  if (messages.length === 0) {
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

  // 메시지가 있으면 카드 형태로 표시 (완성된 쌍이 없어도 표시)

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 sm:px-10">
      <div className="mx-auto max-w-7xl">
        {/* 완성된 질문-응답 쌍이 있으면 카드로 표시 */}
        {questionAnswerPairs.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-fade-in mb-6" style={{ alignItems: 'start' }}>
            {questionAnswerPairs.map((pair) => (
              <QuestionAnswerCard
                key={`${pair.userQuestion.id}-${pair.assistantResponse.id}`}
                userQuestion={pair.userQuestion}
                assistantResponse={pair.assistantResponse}
              />
            ))}
          </div>
        )}

        {/* 진행 중인 메시지들 (쌍이 안 맞는 경우) */}
        {messages.length > questionAnswerPairs.length * 2 && (
          <div className="max-w-4xl mx-auto space-y-4">
            {messages.slice(questionAnswerPairs.length * 2).map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
          </div>
        )}

        {/* 타이핑 인디케이터 */}
        {isTyping && <TypingIndicator isVisible={isTyping} />}

        {/* 스크롤 앵커 */}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}