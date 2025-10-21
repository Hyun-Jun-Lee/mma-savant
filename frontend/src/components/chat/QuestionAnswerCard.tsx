"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Message } from "@/types/chat"
import { User, MessageSquare, ChevronRight } from "lucide-react"
import { formatDistanceToNow } from "date-fns"
import { ko } from "date-fns/locale"

interface QuestionAnswerCardProps {
  userQuestion: Message
  sessionId: string
  onClick: () => void
}

export function QuestionAnswerCard({ userQuestion, sessionId, onClick }: QuestionAnswerCardProps) {
  return (
    <Card
      className="bg-zinc-800/50 backdrop-blur-sm border-zinc-700 hover:bg-zinc-800/70 hover:border-zinc-600 transition-all duration-300 cursor-pointer group"
      onClick={onClick}
    >
      <CardContent className="p-6">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 shrink-0 rounded-full bg-zinc-700 flex items-center justify-center">
            <MessageSquare className="w-5 h-5 text-zinc-300" />
          </div>
          <div className="flex-1">
            <div className="flex items-center justify-between mb-2">
              <p className="text-zinc-500 text-xs">
                {formatDistanceToNow(userQuestion.timestamp, { addSuffix: true, locale: ko })}
              </p>
              <ChevronRight className="w-4 h-4 text-zinc-400 group-hover:text-zinc-300 transition-colors" />
            </div>
            <p className="text-white text-sm font-medium leading-normal line-clamp-2">
              {userQuestion.content}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}