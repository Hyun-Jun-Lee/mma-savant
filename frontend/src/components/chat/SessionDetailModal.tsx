"use client"

import { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { ChartRenderer } from "@/components/visualization/ChartRenderer"
import { Message } from "@/types/chat"
import { Bot, User, X, Loader2 } from "lucide-react"
import { ChatApiService } from "@/services/chatApi"
import { formatDistanceToNow } from "date-fns"
import { ko } from "date-fns/locale"

interface SessionDetailModalProps {
  sessionId: string | null
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
      const response = await ChatApiService.getChatHistory(sessionId, 50, 0)
      const loadedMessages: Message[] = response.messages.map(msg => ({
        id: msg.id,
        content: msg.content,
        role: msg.role as 'user' | 'assistant',
        timestamp: new Date(msg.timestamp),
        // visualization data는 content에서 파싱해야 할 수도 있음
      }))
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
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto bg-zinc-900 border-zinc-700">
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
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 shrink-0 rounded-full bg-blue-600 flex items-center justify-center">
                      <Bot className="w-5 h-5 text-white" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-white font-semibold">MMA Savant</p>
                        <p className="text-zinc-500 text-sm">
                          {formatDistanceToNow(assistantMessage.timestamp, { addSuffix: true, locale: ko })}
                        </p>
                      </div>

                      {/* 시각화 데이터가 있으면 차트 렌더링 */}
                      {assistantMessage.visualizationData && (
                        <div className="mb-4">
                          <ChartRenderer data={assistantMessage.visualizationData} />
                        </div>
                      )}

                      {/* 텍스트 응답 */}
                      {assistantMessage.content && (
                        <div className="prose prose-invert max-w-none">
                          <p className="text-zinc-200 whitespace-pre-wrap">
                            {assistantMessage.content}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}