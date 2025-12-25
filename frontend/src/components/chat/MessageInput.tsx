"use client"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { useChatStore } from "@/store/chatStore"
import { Send, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

interface MessageInputProps {
  onSendMessage?: (message: string) => void
  disabled?: boolean
  placeholder?: string
}

export function MessageInput({
  onSendMessage,
  disabled = false,
  placeholder = "MMA에 대해 무엇이든 물어보세요... (Shift+Enter로 줄바꿈)"
}: MessageInputProps) {
  const { currentMessage, setCurrentMessage, isLoading, usageLimit } = useChatStore()
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSend = () => {
    const trimmedMessage = currentMessage.trim()
    if (!trimmedMessage || isLoading || disabled) return

    onSendMessage?.(trimmedMessage)
    setCurrentMessage("")

    // 텍스트 영역 높이 리셋
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    // 한글 IME 조합 중일 때는 Enter 무시 (입력 분할 방지)
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value
    setCurrentMessage(value)
    
    // 자동 높이 조절
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`
    }
  }

  useEffect(() => {
    // 컴포넌트 마운트 시 포커스
    textareaRef.current?.focus()
  }, [])

  // 사용량 제한 초과 시 입력 비활성화
  const isUsageLimitExceeded = usageLimit?.exceeded ?? false
  const isDisabled = disabled || isLoading || isUsageLimitExceeded
  const canSend = currentMessage.trim().length > 0 && !isDisabled

  // 사용량 초과 시 placeholder 변경
  const displayPlaceholder = isUsageLimitExceeded
    ? "일일 사용량을 초과했습니다. 내일 다시 이용해 주세요."
    : placeholder

  return (
    <div className="flex h-12 flex-1 flex-col min-w-40">
      <div className="flex h-full w-full flex-1 items-stretch rounded-lg">
        <input
          ref={textareaRef as any}
          value={currentMessage}
          onChange={(e) => setCurrentMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={displayPlaceholder}
          disabled={isDisabled}
          className={cn(
            "h-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg rounded-r-none border-none",
            "bg-zinc-800 px-4 pr-2 text-base font-normal leading-normal text-white placeholder:text-zinc-400",
            "focus:border-none focus:outline-0 focus:ring-0",
            isDisabled && "opacity-50 cursor-not-allowed"
          )}
        />
        <div className="flex items-center justify-center rounded-r-lg border-l-0 bg-zinc-800 !pr-2 pr-4">
          <div className="flex items-center justify-end gap-4">
            <div className="flex items-center gap-1">
              <button
                onClick={handleSend}
                disabled={!canSend}
                className={cn(
                  "flex items-center justify-center p-1.5 text-zinc-400 hover:text-white transition-colors",
                  !canSend && "opacity-50 cursor-not-allowed"
                )}
              >
                {isLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}