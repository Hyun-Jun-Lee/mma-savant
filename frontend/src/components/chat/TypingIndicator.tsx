"use client"

import { Card } from "@/components/ui/card"
import { Bot } from "lucide-react"

interface TypingIndicatorProps {
  isVisible: boolean
}

export function TypingIndicator({ isVisible }: TypingIndicatorProps) {
  if (!isVisible) return null

  return (
    <div className="flex justify-start mb-4">
      <Card className="p-3 bg-gray-100 border-gray-200 max-w-xs">
        <div className="flex items-center gap-2">
          <Bot className="w-4 h-4 text-blue-600 flex-shrink-0" />
          <div className="flex gap-1">
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
          <span className="text-xs text-gray-500 ml-1">입력 중...</span>
        </div>
      </Card>
    </div>
  )
}