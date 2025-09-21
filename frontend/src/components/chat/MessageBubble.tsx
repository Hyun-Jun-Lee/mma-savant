"use client"

import { Message } from "@/types/chat"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Card } from "@/components/ui/card"
import { useAuth } from "@/hooks/useAuth"
import { Bot, User } from "lucide-react"
import { cn } from "@/lib/utils"
import ReactMarkdown from "react-markdown"
import { ChartRenderer } from "@/components/visualization/ChartRenderer"

interface MessageBubbleProps {
  message: Message
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const { user } = useAuth()
  const isUser = message.role === "user"
  const isAssistant = message.role === "assistant"

  return (
    <div className={cn(
      "flex w-full mb-4 animate-in slide-in-from-bottom-2",
      isUser ? "justify-end" : "justify-start"
    )}>
      <div className={cn(
        "flex max-w-[80%] gap-3",
        isUser ? "flex-row-reverse" : "flex-row"
      )}>
        {/* Avatar */}
        <Avatar className="w-8 h-8 shrink-0">
          {isUser ? (
            <>
              <AvatarImage src={user?.image || ""} alt={user?.name || ""} />
              <AvatarFallback className="bg-zinc-600 text-white">
                <User className="w-4 h-4" />
              </AvatarFallback>
            </>
          ) : (
            <AvatarFallback className="bg-white/10 text-white backdrop-blur-sm border border-white/20">
              <Bot className="w-4 h-4" />
            </AvatarFallback>
          )}
        </Avatar>

        {/* Message Content */}
        {isUser ? (
          <Card className="p-3 shadow-sm bg-zinc-700 text-white border-zinc-600">
            <div className="text-sm break-words prose prose-invert prose-sm max-w-none">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
            
            {/* Timestamp */}
            <div className="text-xs mt-2 opacity-70 text-zinc-300">
              {message.timestamp.toLocaleTimeString([], { 
                hour: '2-digit', 
                minute: '2-digit' 
              })}
            </div>
          </Card>
        ) : (
          <div className="max-w-none">
            {/* 시각화 데이터가 있으면 차트 렌더링, 없으면 텍스트 */}
            {message.visualizationData ? (
              <div className="space-y-3">
                <ChartRenderer data={message.visualizationData} />
                {/* 스트리밍 인디케이터 */}
                {message.isStreaming && (
                  <div className="text-center">
                    <span className="inline-block w-2 h-4 bg-blue-400 animate-pulse rounded" />
                  </div>
                )}
              </div>
            ) : (
              <div className="text-sm break-words text-white prose prose-invert prose-sm max-w-none">
                <ReactMarkdown>{message.content}</ReactMarkdown>
                {message.isStreaming && (
                  <span className="inline-block w-2 h-4 ml-1 bg-current animate-pulse rounded" />
                )}
              </div>
            )}

            {/* Timestamp */}
            <div className="text-xs mt-2 opacity-70 text-zinc-400">
              {message.timestamp.toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit'
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}