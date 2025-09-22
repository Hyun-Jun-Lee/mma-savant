"use client"

import { Bot } from "lucide-react"

interface TypingIndicatorProps {
  isVisible: boolean
}

export function TypingIndicator({ isVisible }: TypingIndicatorProps) {
  if (!isVisible) {
    return null
  }

  return (
    <div className="flex justify-start mb-4 animate-in fade-in duration-200">
      <div className="flex items-center gap-3 max-w-xs">
        {/* Avatar */}
        <div className="w-8 h-8 bg-white/10 backdrop-blur-sm rounded-full flex items-center justify-center border border-white/20 flex-shrink-0">
          <Bot className="w-4 h-4 text-white" />
        </div>

        {/* Typing animation */}
        <div className="flex items-center gap-2">
          <div className="flex gap-1">
            <div className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
            <div className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
            <div className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
          <span className="text-xs text-zinc-400 ml-1">입력 중...</span>
        </div>
      </div>
    </div>
  )
}