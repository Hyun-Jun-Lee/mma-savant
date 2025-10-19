"use client"

import { useState, useRef, useEffect } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { ChartRenderer } from "@/components/visualization/ChartRenderer"
import { Message } from "@/types/chat"
import { User, ChevronDown, ChevronUp, Bot } from "lucide-react"
import { formatDistanceToNow } from "date-fns"
import { ko } from "date-fns/locale"
import { cn } from "@/lib/utils"

interface QuestionAnswerCardProps {
  userQuestion: Message
  assistantResponse: Message
}

export function QuestionAnswerCard({ userQuestion, assistantResponse }: QuestionAnswerCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [contentHeight, setContentHeight] = useState(0)
  const contentRef = useRef<HTMLDivElement>(null)
  const cardId = `${userQuestion.id.slice(0, 8)}-${assistantResponse.id.slice(0, 8)}`

  useEffect(() => {
    if (contentRef.current) {
      setContentHeight(contentRef.current.scrollHeight)
    }
  }, [assistantResponse.content, assistantResponse.visualizationData])

  const toggleExpanded = (e: React.MouseEvent) => {
    e.stopPropagation()
    console.log(`🔄 Toggling card ${cardId}: ${isExpanded} -> ${!isExpanded}`)
    setIsExpanded(!isExpanded)
  }

  return (
    <Card className="bg-zinc-800/50 backdrop-blur-sm border-zinc-700 hover:bg-zinc-800/70 hover:border-zinc-600 transition-all duration-300 cursor-pointer group min-h-[120px]" style={{ willChange: 'height, transform' }}>
      <CardContent className="p-6">
        {/* 사용자 질문 - 항상 표시 */}
        <div className="flex items-start gap-3" onClick={toggleExpanded}>
          <div className="w-8 h-8 shrink-0 rounded-full bg-zinc-700 flex items-center justify-center">
            <User className="w-4 h-4 text-zinc-300" />
          </div>
          <div className="flex-1">
            <div className="flex items-center justify-between">
              <p className="text-white text-sm font-bold leading-normal tracking-[0.015em]">사용자</p>
              <div className="flex items-center gap-2">
                <p className="text-zinc-500 text-xs">
                  {formatDistanceToNow(userQuestion.timestamp, { addSuffix: true, locale: ko })}
                </p>
                {isExpanded ? (
                  <ChevronUp className="w-4 h-4 text-zinc-400 group-hover:text-zinc-300 transition-colors" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-zinc-400 group-hover:text-zinc-300 transition-colors" />
                )}
              </div>
            </div>
            <p className="text-white text-sm font-normal leading-normal mt-1">{userQuestion.content}</p>
          </div>
        </div>

        {/* 어시스턴트 응답 - 펼쳤을 때만 표시 */}
        <div
          className="overflow-hidden transition-all duration-300 ease-in-out"
          style={{
            height: isExpanded ? `${contentHeight}px` : '0px',
            opacity: isExpanded ? 1 : 0,
            marginTop: isExpanded ? '1rem' : '0px'
          }}
        >
          <div ref={contentRef} className="border-t border-zinc-700 pt-4">
            {/* 어시스턴트 헤더 */}
            <div className="flex items-start gap-3 mb-4">
              <div className="w-8 h-8 shrink-0 rounded-full bg-blue-600 flex items-center justify-center">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div className="flex-1">
                <p className="text-white text-sm font-bold leading-normal tracking-[0.015em]">MMA Savant</p>
              </div>
            </div>

            {/* 어시스턴트 응답 내용 */}
            <div className="space-y-3 ml-11">
              {/* 시각화 데이터 */}
              {assistantResponse.visualizationData && (
                <div className="w-full">
                  <ChartRenderer data={assistantResponse.visualizationData} />
                </div>
              )}

              {/* 텍스트 응답 (시각화가 있을 때는 추가 설명만, 없을 때는 전체 내용) */}
              {assistantResponse.content && assistantResponse.content.trim().length > 0 && (
                <div className="prose prose-invert prose-sm max-w-none">
                  <p className="text-zinc-300 text-sm leading-relaxed whitespace-pre-wrap">
                    {assistantResponse.content}
                  </p>
                </div>
              )}

              {/* 시각화만 있고 텍스트가 없는 경우 기본 설명 */}
              {assistantResponse.visualizationData && (!assistantResponse.content || assistantResponse.content.trim().length === 0) && (
                <div className="text-zinc-400 text-sm italic">
                  데이터 시각화가 완료되었습니다.
                </div>
              )}

              {/* 스트리밍 상태 표시 */}
              {assistantResponse.isStreaming && (
                <div className="flex items-center gap-2 text-zinc-500">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                  <span className="text-xs">응답 생성 중...</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}