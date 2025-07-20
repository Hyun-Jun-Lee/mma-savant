"use client"

import { useEffect, useRef } from "react"
import { MessageBubble } from "./MessageBubble"
import { TypingIndicator } from "./TypingIndicator"
import { useChatStore } from "@/store/chatStore"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Card } from "@/components/ui/card"
import { Bot } from "lucide-react"

export function MessageList() {
  const { messages, isTyping } = useChatStore()
  const bottomRef = useRef<HTMLDivElement>(null)
  const scrollAreaRef = useRef<HTMLDivElement>(null)

  // 새 메시지가 추가되거나 타이핑 상태가 변경될 때마다 스크롤을 맨 아래로
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isTyping])

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <Card className="p-8 text-center max-w-md">
          <div className="mb-4">
            <Bot className="w-16 h-16 mx-auto text-blue-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-800 mb-2">
            MMA Savant와 대화를 시작하세요
          </h3>
          <p className="text-gray-600 text-sm leading-relaxed">
            파이터, 기술, 이벤트, 역사 등 MMA에 관한 모든 것을 물어보세요. 
            전문적이고 정확한 답변을 드리겠습니다.
          </p>
          
          {/* 예시 질문들 */}
          <div className="mt-6 space-y-2">
            <p className="text-xs text-gray-500 font-medium">예시 질문:</p>
            <div className="space-y-1 text-xs text-gray-600">
              <div className="bg-gray-50 rounded p-2">
                "존 존스의 주요 기술은 무엇인가요?"
              </div>
              <div className="bg-gray-50 rounded p-2">
                "UFC 300의 메인 이벤트는 무엇이었나요?"
              </div>
              <div className="bg-gray-50 rounded p-2">
                "브라질리안 주짓수의 기본 기술을 설명해주세요"
              </div>
            </div>
          </div>
        </Card>
      </div>
    )
  }

  return (
    <ScrollArea className="flex-1" ref={scrollAreaRef}>
      <div className="p-4 max-w-4xl mx-auto">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        <TypingIndicator isVisible={isTyping} />
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  )
}