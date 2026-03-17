"use client"

import { useRef, useEffect } from "react"
import { useChatStore } from "@/store/chatStore"
import { ChartRenderer } from "@/components/visualization/ChartRenderer"
import { MessageInput } from "./MessageInput"
import { Bot, User, Loader2, ArrowLeft } from "lucide-react"
import { formatDistanceToNow } from "date-fns"
import { ko } from "date-fns/locale"
import ReactMarkdown from "react-markdown"

interface SessionDetailPanelProps {
  onBack?: () => void
  showBackButton?: boolean
  onSendMessage: (message: string) => void
  isConnected: boolean
  error: string | null
}

export function SessionDetailPanel({ onBack, showBackButton, onSendMessage, isConnected, error }: SessionDetailPanelProps) {
  const { messages, isTyping, isLoading, selectedSessionId, sessions, historyLoading } = useChatStore()
  const scrollRef = useRef<HTMLDivElement>(null)

  // 메시지 변경 시 하단으로 스크롤
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  const selectedSessionTitle = sessions.find(s => s.id === selectedSessionId)?.title

  // 대화 내용이 있으면 스레드 표시 (스트리밍 중이든 히스토리 로드든 동일)
  if (messages.length > 0 || historyLoading) {
    const lastMessage = messages[messages.length - 1]
    const showTypingIndicator = isTyping && (!lastMessage || lastMessage.role === 'user')

    return (
      <div className="flex h-full flex-col bg-zinc-950/80">
        {/* 헤더 */}
        {(showBackButton || selectedSessionId) && (
          <div className="flex-shrink-0 border-b border-white/[0.06] px-6 py-3 flex items-center gap-3">
            {showBackButton && (
              <button onClick={onBack} className="flex items-center text-zinc-400 hover:text-white transition-colors">
                <ArrowLeft className="w-4 h-4" />
              </button>
            )}
            {selectedSessionId && (
              <h2 className="text-sm font-medium text-white truncate">
                {selectedSessionTitle || `Chat ${selectedSessionId}`}
              </h2>
            )}
          </div>
        )}

        <div ref={scrollRef} className="flex-1 overflow-y-auto p-6">
          {historyLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-violet-400" />
            </div>
          ) : (
            <div className="mx-auto max-w-4xl space-y-6">
              {messages.map((msg) => (
                msg.role === 'user' ? (
                  <div key={msg.id} className="flex justify-start">
                    <div className="max-w-[80%] bg-white/[0.03] rounded-lg p-5">
                      <div className="flex items-start gap-3">
                        <div className="w-8 h-8 shrink-0 rounded-full bg-white/[0.06] flex items-center justify-center">
                          <User className="w-4 h-4 text-zinc-400" />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-1.5">
                            <p className="text-sm text-white font-semibold">You</p>
                            <p className="text-zinc-500 text-xs">
                              {formatDistanceToNow(msg.timestamp, { addSuffix: true, locale: ko })}
                            </p>
                          </div>
                          <p className="text-zinc-200 text-sm break-keep">{msg.content}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div key={msg.id} className="flex justify-end">
                    <div className="max-w-[85%] bg-violet-500/5 rounded-lg p-5 border border-violet-500/10">
                      {msg.visualizationData && (
                        <div className="mb-4 w-full">
                          <ChartRenderer data={msg.visualizationData} />
                        </div>
                      )}

                      {msg.content && msg.content.trim().length > 0 && (
                        <div className="prose prose-invert max-w-none text-sm break-keep">
                          <ReactMarkdown>{msg.content}</ReactMarkdown>
                          {msg.isStreaming && (
                            <span className="inline-block w-2 h-4 ml-1 bg-violet-400 animate-pulse rounded" />
                          )}
                        </div>
                      )}

                      {!msg.content && msg.isStreaming && (
                        <div className="flex items-center gap-3">
                          <Loader2 className="w-4 h-4 text-violet-400 animate-spin" />
                          <span className="text-violet-300 text-sm">응답을 생성하고 있습니다...</span>
                        </div>
                      )}
                    </div>
                  </div>
                )
              ))}

              {/* 타이핑 인디케이터 (아직 assistant 메시지가 없을 때) */}
              {showTypingIndicator && (
                <div className="flex justify-end">
                  <div className="max-w-[85%] bg-violet-500/5 rounded-lg p-5 border border-violet-500/10">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 shrink-0 rounded-full bg-violet-500/20 flex items-center justify-center">
                        <Bot className="w-4 h-4 text-violet-400" />
                      </div>
                      <div className="flex items-center gap-3">
                        <Loader2 className="w-4 h-4 text-violet-400 animate-spin" />
                        <span className="text-violet-300 text-sm">응답을 생성하고 있습니다...</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* 에러 표시 */}
        {error && (
          <div className="flex-shrink-0 mx-4 mb-2">
            <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
              <p className="text-red-400 text-sm font-medium">{error}</p>
            </div>
          </div>
        )}

        {/* 하단 입력 영역 */}
        <div className="flex-shrink-0 border-t border-white/[0.06] p-4">
          <div className="mx-auto max-w-4xl flex items-center gap-3">
            <div className="flex-1">
              <MessageInput
                onSendMessage={onSendMessage}
                disabled={isLoading}
                placeholder="궁금한 MMA 데이터를 질문해보세요..."
              />
            </div>
            <div className="flex shrink-0 items-center gap-1.5 rounded-full border border-white/[0.06] bg-white/[0.03] px-2.5 py-1">
              <div className={`h-1.5 w-1.5 rounded-full ${isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`} />
              <span className={`text-[11px] font-medium ${isConnected ? 'text-emerald-400' : 'text-red-400'}`}>
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // 빈 상태 (Welcome screen)
  return (
    <div className="flex h-full flex-col bg-zinc-950/80">
      <div className="flex flex-1 items-center justify-center">
        <div className="p-8 text-center max-w-md">
          <div className="mb-6">
            <div className="w-16 h-16 mx-auto bg-violet-500/20 rounded-full flex items-center justify-center border border-white/[0.06]">
              <Bot className="w-8 h-8 text-violet-400" />
            </div>
          </div>
          <h3 className="text-xl font-semibold text-white mb-3">
            Start analyzing with MMA Savant
          </h3>
          <p className="text-zinc-400 text-sm leading-relaxed">
            Ask about fighters, techniques, events, history, and everything MMA.
            Get professional and accurate insights.
          </p>
        </div>
      </div>

      {/* 하단 입력 영역 */}
      <div className="flex-shrink-0 border-t border-white/[0.06] p-4">
        <div className="mx-auto max-w-4xl flex items-center gap-3">
          <div className="flex-1">
            <MessageInput
              onSendMessage={onSendMessage}
              disabled={isLoading}
              placeholder="궁금한 MMA 데이터를 질문해보세요..."
            />
          </div>
          <div className="flex shrink-0 items-center gap-1.5 rounded-full border border-white/[0.06] bg-white/[0.03] px-2.5 py-1">
            <div className={`h-1.5 w-1.5 rounded-full ${isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`} />
            <span className={`text-[11px] font-medium ${isConnected ? 'text-emerald-400' : 'text-red-400'}`}>
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
