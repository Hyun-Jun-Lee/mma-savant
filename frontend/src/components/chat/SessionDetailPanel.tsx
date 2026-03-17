"use client"

import { useState, useEffect, useRef, useMemo } from "react"
import { useChatStore } from "@/store/chatStore"
import { ChartRenderer } from "@/components/visualization/ChartRenderer"
import { Message } from "@/types/chat"
import { Bot, User, Loader2, ArrowLeft } from "lucide-react"
import { ChatApiService } from "@/services/chatApi"
import { formatDistanceToNow } from "date-fns"
import { ko } from "date-fns/locale"
import { processAssistantResponse } from "@/lib/visualizationParser"
import ReactMarkdown from "react-markdown"

interface SessionDetailPanelProps {
  onBack?: () => void
  showBackButton?: boolean
}

export function SessionDetailPanel({ onBack, showBackButton }: SessionDetailPanelProps) {
  const { messages, isTyping, selectedSessionId, sessions } = useChatStore()
  const [loading, setLoading] = useState(false)
  const [loadedMessages, setLoadedMessages] = useState<Message[]>([])
  const [error, setError] = useState<string | null>(null)
  const fetchIdRef = useRef(0)

  // Mode A: 스트리밍 중인지 판별 (미응답 user 메시지가 있으면 스트리밍 모드)
  const isStreamingMode = useMemo(() => {
    const userMessages = messages.filter(m => m.role === 'user')
    const assistantMessages = messages.filter(m => m.role === 'assistant')
    return userMessages.length > assistantMessages.length || messages.some(m => m.isStreaming)
  }, [messages])

  const currentQuestion = useMemo(() => {
    return messages.find(m => m.role === 'user')
  }, [messages])

  const streamingResponse = useMemo(() => {
    return [...messages].reverse().find(m => m.role === 'assistant')
  }, [messages])

  // Mode B: 선택된 세션 로드
  useEffect(() => {
    if (isStreamingMode || !selectedSessionId) return

    const currentFetchId = ++fetchIdRef.current
    setLoading(true)
    setError(null)

    ChatApiService.getChatHistory(selectedSessionId, 50, 0)
      .then((response) => {
        // stale request guard
        if (currentFetchId !== fetchIdRef.current) return

        const parsed: Message[] = response.messages.map(msg => {
          if (msg.role === 'assistant') {
            const { visualizationData, textContent } = processAssistantResponse(msg.content)
            let finalContent = textContent || ''
            if (finalContent.includes('```json') || finalContent.includes('selected_visualization')) {
              finalContent = ''
            }
            return {
              id: msg.id,
              content: finalContent,
              role: msg.role as 'user' | 'assistant',
              timestamp: new Date(msg.timestamp),
              visualizationData,
            }
          }
          return {
            id: msg.id,
            content: msg.content,
            role: msg.role as 'user' | 'assistant',
            timestamp: new Date(msg.timestamp),
          }
        })
        setLoadedMessages(parsed)
      })
      .catch((err) => {
        if (currentFetchId !== fetchIdRef.current) return
        console.error('Failed to load session details:', err)
        setError('세션 정보를 불러올 수 없습니다.')
      })
      .finally(() => {
        if (currentFetchId !== fetchIdRef.current) return
        setLoading(false)
      })
  }, [selectedSessionId, isStreamingMode])

  const selectedSessionTitle = sessions.find(s => s.id === selectedSessionId)?.title

  // ------ Mode A: 스트리밍 ------
  if (isStreamingMode) {
    return (
      <div className="flex h-full flex-col overflow-y-auto">
        {showBackButton && (
          <div className="flex-shrink-0 border-b border-white/[0.06] px-4 py-3">
            <button onClick={onBack} className="flex items-center gap-2 text-sm text-zinc-400 hover:text-white transition-colors">
              <ArrowLeft className="w-4 h-4" />
              Back
            </button>
          </div>
        )}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="mx-auto max-w-4xl space-y-6">
            {/* 사용자 질문 */}
            {currentQuestion && (
              <div className="bg-white/[0.03] rounded-lg p-6">
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 shrink-0 rounded-full bg-white/[0.06] flex items-center justify-center">
                    <User className="w-5 h-5 text-zinc-400" />
                  </div>
                  <div className="flex-1">
                    <p className="text-white font-semibold mb-2">You</p>
                    <p className="text-zinc-200">{currentQuestion.content}</p>
                  </div>
                </div>
              </div>
            )}

            {/* 스트리밍 응답 */}
            {streamingResponse ? (
              <div className="bg-violet-500/5 rounded-lg p-6 border border-violet-500/10">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 shrink-0 rounded-full bg-violet-500/20 flex items-center justify-center">
                    <Bot className="w-5 h-5 text-violet-400" />
                  </div>
                  <p className="text-white font-semibold">MMA Savant</p>
                </div>

                {streamingResponse.visualizationData && (
                  <div className="mb-4 w-full">
                    <ChartRenderer data={streamingResponse.visualizationData} />
                  </div>
                )}

                {streamingResponse.content && streamingResponse.content.trim().length > 0 && (
                  <div className="prose prose-invert max-w-none text-sm">
                    <ReactMarkdown>{streamingResponse.content}</ReactMarkdown>
                    {streamingResponse.isStreaming && (
                      <span className="inline-block w-2 h-4 ml-1 bg-violet-400 animate-pulse rounded" />
                    )}
                  </div>
                )}

                {!streamingResponse.content && streamingResponse.isStreaming && (
                  <div className="flex items-center gap-3">
                    <Loader2 className="w-4 h-4 text-violet-400 animate-spin" />
                    <span className="text-violet-300 text-sm">응답을 생성하고 있습니다...</span>
                  </div>
                )}
              </div>
            ) : isTyping ? (
              <div className="bg-violet-500/5 rounded-lg p-6 border border-violet-500/10">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 shrink-0 rounded-full bg-violet-500/20 flex items-center justify-center">
                    <Bot className="w-5 h-5 text-violet-400" />
                  </div>
                  <div className="flex items-center gap-3">
                    <Loader2 className="w-4 h-4 text-violet-400 animate-spin" />
                    <span className="text-violet-300 text-sm">응답을 생성하고 있습니다...</span>
                  </div>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      </div>
    )
  }

  // ------ Mode B: 로드된 세션 ------
  if (selectedSessionId) {
    const userMessage = loadedMessages.find(m => m.role === 'user')
    const assistantMessage = loadedMessages.find(m => m.role === 'assistant')

    return (
      <div className="flex h-full flex-col">
        {/* 헤더 */}
        <div className="flex-shrink-0 border-b border-white/[0.06] px-6 py-3 flex items-center gap-3">
          {showBackButton && (
            <button onClick={onBack} className="flex items-center text-zinc-400 hover:text-white transition-colors">
              <ArrowLeft className="w-4 h-4" />
            </button>
          )}
          <h2 className="text-sm font-medium text-white truncate">
            {selectedSessionTitle || `Chat ${selectedSessionId}`}
          </h2>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-violet-400" />
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <p className="text-red-400">{error}</p>
            </div>
          ) : (
            <div className="mx-auto max-w-4xl space-y-6">
              {/* 사용자 질문 */}
              {userMessage && (
                <div className="bg-white/[0.03] rounded-lg p-6">
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 shrink-0 rounded-full bg-white/[0.06] flex items-center justify-center">
                      <User className="w-5 h-5 text-zinc-400" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-white font-semibold">You</p>
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
                <div className="bg-violet-500/5 rounded-lg p-6 border border-violet-500/10">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 shrink-0 rounded-full bg-violet-500/20 flex items-center justify-center">
                      <Bot className="w-5 h-5 text-violet-400" />
                    </div>
                    <div className="flex-1 flex items-center justify-between">
                      <p className="text-white font-semibold">MMA Savant</p>
                      <p className="text-zinc-500 text-sm">
                        {formatDistanceToNow(assistantMessage.timestamp, { addSuffix: true, locale: ko })}
                      </p>
                    </div>
                  </div>

                  {assistantMessage.visualizationData && (
                    <div className="mb-4 w-full">
                      <ChartRenderer data={assistantMessage.visualizationData} />
                    </div>
                  )}

                  {assistantMessage.content && assistantMessage.content.trim().length > 0 && (
                    <div className="prose prose-invert max-w-none">
                      <p className="text-zinc-200 whitespace-pre-wrap">
                        {assistantMessage.content}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    )
  }

  // ------ Mode C: 빈 상태 ------
  return (
    <div className="flex h-full items-center justify-center">
      <div className="p-8 text-center max-w-md">
        <div className="mb-6">
          <div className="w-16 h-16 mx-auto bg-violet-500/20 rounded-full flex items-center justify-center border border-white/[0.06]">
            <Bot className="w-8 h-8 text-violet-400" />
          </div>
        </div>
        <h3 className="text-xl font-semibold text-white mb-3">
          Start analyzing with MMA Savant
        </h3>
        <p className="text-zinc-400 text-sm leading-relaxed mb-6">
          Ask about fighters, techniques, events, history, and everything MMA.
          Get professional and accurate insights.
        </p>

        <div className="space-y-3">
          <p className="text-xs text-zinc-500 font-medium uppercase tracking-wider">Sample questions:</p>
          <div className="space-y-2 text-sm">
            <div className="bg-white/[0.03] border border-white/[0.06] rounded-lg p-3 text-zinc-300 hover:bg-white/[0.05] transition-colors cursor-pointer">
              {`"What are Jon Jones' key techniques?"`}
            </div>
            <div className="bg-white/[0.03] border border-white/[0.06] rounded-lg p-3 text-zinc-300 hover:bg-white/[0.05] transition-colors cursor-pointer">
              {`"What was UFC 300's main event?"`}
            </div>
            <div className="bg-white/[0.03] border border-white/[0.06] rounded-lg p-3 text-zinc-300 hover:bg-white/[0.05] transition-colors cursor-pointer">
              {`"Explain Brazilian Jiu-Jitsu basics"`}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
