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
  const { currentMessage, setCurrentMessage, isLoading } = useChatStore()
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSend = () => {
    const trimmedMessage = currentMessage.trim()
    if (!trimmedMessage || isLoading || disabled) return

    // 메시지 전송
    onSendMessage?.(trimmedMessage)
    setCurrentMessage("")
    
    // 텍스트 영역 높이 리셋
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
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

  const isDisabled = disabled || isLoading
  const canSend = currentMessage.trim().length > 0 && !isDisabled

  return (
    <div className="border-t border-white/10 bg-black/20 backdrop-blur-sm p-4">
      <div className="flex gap-3 items-end max-w-4xl mx-auto">
        <div className="flex-1 relative">
          <Textarea
            ref={textareaRef}
            value={currentMessage}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={isDisabled}
            className={cn(
              "min-h-[44px] max-h-[120px] resize-none pr-12",
              "bg-white/5 backdrop-blur-sm border-white/10 text-white placeholder-zinc-400",
              "focus:ring-2 focus:ring-white/30 focus:border-white/30",
              "hover:bg-white/10 hover:border-white/20 transition-colors",
              isDisabled && "opacity-50 cursor-not-allowed"
            )}
            style={{ height: "auto" }}
          />
          
          {/* 글자수 표시 */}
          <div className="absolute bottom-2 right-2 text-xs text-zinc-500">
            {currentMessage.length}/1000
          </div>
        </div>
        
        <Button
          onClick={handleSend}
          disabled={!canSend}
          size="lg"
          className={cn(
            "bg-white text-zinc-900 hover:bg-zinc-100 font-medium transition-colors",
            "border border-white/20 shadow-lg",
            !canSend && "opacity-50 cursor-not-allowed"
          )}
        >
          {isLoading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Send className="w-4 h-4" />
          )}
        </Button>
      </div>
      
      {/* 도움말 텍스트 */}
      <div className="text-xs text-zinc-400 mt-3 text-center max-w-4xl mx-auto">
        MMA Savant는 파이터, 기술, 이벤트, 역사에 대한 전문 지식을 제공합니다.
      </div>
    </div>
  )
}