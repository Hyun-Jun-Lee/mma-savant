"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Message } from "@/types/chat"
import { MessageSquare, ChevronRight } from "lucide-react"
import { formatDistanceToNow } from "date-fns"
import { ko } from "date-fns/locale"

interface QuestionAnswerCardProps {
  userQuestion: Message
  assistantResponse?: Message
  sessionId?: string
  onClick?: () => void
}

export function QuestionAnswerCard({ userQuestion, onClick }: QuestionAnswerCardProps) {
  return (
    <Card
      className="bg-white/[0.03] border-white/[0.06] hover:bg-white/[0.05] hover:border-white/[0.12] transition-all duration-300 ease-out cursor-pointer group rounded-xl"
      onClick={onClick}
    >
      <CardContent className="p-6">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 shrink-0 rounded-full bg-white/[0.06] flex items-center justify-center">
            <MessageSquare className="w-5 h-5 text-zinc-400" />
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