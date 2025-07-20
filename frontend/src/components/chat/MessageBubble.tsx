"use client"

import { Message } from "@/types/chat"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Card } from "@/components/ui/card"
import { useAuth } from "@/hooks/useAuth"
import { Bot, User } from "lucide-react"
import { cn } from "@/lib/utils"

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
              <AvatarFallback className="bg-red-600 text-white">
                <User className="w-4 h-4" />
              </AvatarFallback>
            </>
          ) : (
            <AvatarFallback className="bg-blue-600 text-white">
              <Bot className="w-4 h-4" />
            </AvatarFallback>
          )}
        </Avatar>

        {/* Message Content */}
        <Card className={cn(
          "p-3 shadow-sm",
          isUser 
            ? "bg-red-600 text-white border-red-600" 
            : "bg-white border-gray-200"
        )}>
          <div className="text-sm whitespace-pre-wrap break-words">
            {message.content}
            {message.isStreaming && (
              <span className="inline-block w-2 h-4 ml-1 bg-current animate-pulse rounded" />
            )}
          </div>
          
          {/* Timestamp */}
          <div className={cn(
            "text-xs mt-2 opacity-70",
            isUser ? "text-red-100" : "text-gray-500"
          )}>
            {message.timestamp.toLocaleTimeString([], { 
              hour: '2-digit', 
              minute: '2-digit' 
            })}
          </div>
        </Card>
      </div>
    </div>
  )
}