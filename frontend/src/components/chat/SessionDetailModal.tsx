"use client"

import { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { ChartRenderer } from "@/components/visualization/ChartRenderer"
import { Message } from "@/types/chat"
import { Bot, User, X, Loader2 } from "lucide-react"
import { ChatApiService } from "@/services/chatApi"
import { formatDistanceToNow } from "date-fns"
import { ko } from "date-fns/locale"
import { processAssistantResponse } from "@/lib/visualizationParser"

interface SessionDetailModalProps {
  sessionId: number | null
  isOpen: boolean
  onClose: () => void
  sessionTitle?: string
}

export function SessionDetailModal({ sessionId, isOpen, onClose, sessionTitle }: SessionDetailModalProps) {
  const [loading, setLoading] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (isOpen && sessionId) {
      loadSessionDetails()
    }
  }, [isOpen, sessionId])

  const loadSessionDetails = async () => {
    if (!sessionId) return

    setLoading(true)
    setError(null)

    try {
      // 세션의 히스토리 로드
      const response = await ChatApiService.getChatHistory(sessionId as number, 50, 0)
      const loadedMessages: Message[] = response.messages.map(msg => {
        // assistant 메시지인 경우 시각화 데이터 파싱
        if (msg.role === 'assistant') {
          console.log('🔍 Processing assistant message:', msg.content.substring(0, 200))
          const { visualizationData, textContent } = processAssistantResponse(msg.content)
          console.log('📊 Parsed visualization:', !!visualizationData)
          console.log('📝 Text content after parsing:', textContent?.substring(0, 200))

          // textContent가 비어있거나 여전히 JSON이 포함되어 있다면 빈 문자열로
          let finalContent = textContent || ''
          if (finalContent.includes('```json') || finalContent.includes('selected_visualization')) {
            console.log('⚠️ JSON still present in content, removing entirely')
            finalContent = ''
          }

          return {
            id: msg.id,
            content: finalContent,
            role: msg.role as 'user' | 'assistant',
            timestamp: new Date(msg.timestamp),
            visualizationData: visualizationData // 파싱된 시각화 데이터
          }
        }

        // user 메시지는 그대로
        return {
          id: msg.id,
          content: msg.content,
          role: msg.role as 'user' | 'assistant',
          timestamp: new Date(msg.timestamp),
        }
      })
      setMessages(loadedMessages)
    } catch (err) {
      console.error('Failed to load session details:', err)
      setError('세션 정보를 불러올 수 없습니다.')
    } finally {
      setLoading(false)
    }
  }

  const userMessage = messages.find(m => m.role === 'user')
  const assistantMessage = messages.find(m => m.role === 'assistant')

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="w-fit max-w-[90vw] max-h-[85vh] overflow-y-auto bg-zinc-900 border-zinc-700">
        <DialogHeader>
          <DialogTitle className="text-white flex items-center justify-between">
            <span>{sessionTitle || '대화 상세'}</span>
            <button
              onClick={onClose}
              className="p-1 rounded-md hover:bg-zinc-800 transition-colors"
            >
              <X className="w-5 h-5 text-zinc-400" />
            </button>
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6 mt-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <p className="text-red-400">{error}</p>
            </div>
          ) : (
            <>
              {/* 사용자 질문 */}
              {userMessage && (
                <div className="bg-zinc-800/50 rounded-lg p-6">
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 shrink-0 rounded-full bg-zinc-700 flex items-center justify-center">
                      <User className="w-5 h-5 text-zinc-300" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-white font-semibold">사용자</p>
                        <p className="text-zinc-500 text-sm">
                          {formatDistanceToNow(userMessage.timestamp, { addSuffix: true, locale: ko })}
                        </p>
                      </div>
                      <p className="text-zinc-200">{userMessage.content}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* AI 응답 */}
              {assistantMessage && (
                <div className="bg-blue-900/20 rounded-lg p-6 border border-blue-800/30">
                  {/* 헤더: 아바타 + 이름 + 시간 */}
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 shrink-0 rounded-full bg-blue-600 flex items-center justify-center">
                      <Bot className="w-5 h-5 text-white" />
                    </div>
                    <div className="flex-1 flex items-center justify-between">
                      <p className="text-white font-semibold">MMA Savant</p>
                      <p className="text-zinc-500 text-sm">
                        {formatDistanceToNow(assistantMessage.timestamp, { addSuffix: true, locale: ko })}
                      </p>
                    </div>
                  </div>

                  {/* 시각화 데이터가 있으면 차트 렌더링 - 전체 너비 사용 */}
                  {assistantMessage.visualizationData && (
                    <div className="mb-4 w-full">
                      <ChartRenderer data={assistantMessage.visualizationData} />
                    </div>
                  )}

                  {/* 텍스트 응답 - 시각화가 없거나 추가 텍스트가 있을 때만 표시 */}
                  {assistantMessage.content && assistantMessage.content.trim().length > 0 && (
                    <div className="prose prose-invert max-w-none">
                      <p className="text-zinc-200 whitespace-pre-wrap">
                        {assistantMessage.content}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}