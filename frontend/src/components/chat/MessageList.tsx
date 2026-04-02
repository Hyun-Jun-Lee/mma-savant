"use client"

import { useEffect, useRef } from "react"
import { MessageBubble } from "./MessageBubble"
import { TypingIndicator } from "./TypingIndicator"
import { useChatStore } from "@/store/chatStore"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Bot } from "lucide-react"

export function MessageList() {
  const { messages, isTyping } = useChatStore()
  const bottomRef = useRef<HTMLDivElement>(null)
  const scrollAreaRef = useRef<HTMLDivElement>(null)

  // 메시지 변경사항 로그
  useEffect(() => {
    console.log('🧩 MessageList: messages updated', {
      count: messages.length,
      messages: messages.map(m => ({ id: m.id, role: m.role, isStreaming: m.isStreaming, contentLength: m.content.length })),
      isTyping
    })
  }, [messages, isTyping])

  // 새 메시지가 추가되거나 타이핑 상태가 변경될 때마다 스크롤을 맨 아래로
  useEffect(() => {
    requestAnimationFrame(() => {
      const viewport = bottomRef.current?.closest('[data-slot="scroll-area-viewport"]') as HTMLElement | null
      if (viewport) {
        viewport.scrollTop = viewport.scrollHeight
      }
    })
  }, [messages, isTyping])

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="p-8 text-center max-w-md">
          <div className="mb-6">
            <div className="w-16 h-16 mx-auto bg-violet-500/20 rounded-full flex items-center justify-center border border-white/[0.06]">
              <Bot className="w-8 h-8 text-violet-400" />
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
              <div className="bg-white/[0.03] border border-white/[0.06] rounded-lg p-3 text-zinc-300 hover:bg-white/[0.05] transition-colors cursor-pointer">
                {`"What are Jon Jones' key techniques?"`}
              </div>
              <div className="bg-white/[0.03] border border-white/[0.06] rounded-lg p-3 text-zinc-300 hover:bg-white/[0.05] transition-colors cursor-pointer">
                {`"What was UFC 300's main event?"`}
              </div>
              <div className="bg-white/[0.03] border border-white/[0.06] rounded-lg p-3 text-zinc-300 hover:bg-white/[0.05] transition-colors cursor-pointer">
                {`"Explain Brazilian Jiu-Jitsu basics"`}
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <ScrollArea className="flex-1" ref={scrollAreaRef}>
      <div className="p-4 max-w-4xl mx-auto min-h-full">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        <TypingIndicator isVisible={isTyping} />
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  )
}