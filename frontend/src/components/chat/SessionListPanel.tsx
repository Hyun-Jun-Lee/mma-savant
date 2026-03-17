"use client"

import { useMemo, useState } from "react"
import { useChatStore } from "@/store/chatStore"
import { useChatSession } from "@/hooks/useChatSession"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog"
import { MessageSquare, Loader2, Trash2, Clock, AlertTriangle } from "lucide-react"
import { formatDistanceToNow } from "date-fns"
import { ko } from "date-fns/locale"
import { cn } from "@/lib/utils"

interface SessionListPanelProps {
  onSessionSelect?: (id: number) => void
}

export function SessionListPanel({ onSessionSelect }: SessionListPanelProps) {
  const { messages, isTyping, sessions, sessionsLoading, selectedSessionId, selectSession } = useChatStore()
  const { deleteSession } = useChatSession()
  const [deleteTarget, setDeleteTarget] = useState<{ id: number; title: string } | null>(null)

  // 현재 진행 중인 질문 (응답이 아직 없는 사용자 메시지)
  const currentPendingQuestion = useMemo(() => {
    const userMessages = messages.filter(m => m.role === 'user')
    const assistantMessages = messages.filter(m => m.role === 'assistant')
    if (userMessages.length > assistantMessages.length) {
      return userMessages[userMessages.length - 1]
    }
    return null
  }, [messages])

  const handleSelectSession = (sessionId: number) => {
    selectSession(sessionId)
    onSessionSelect?.(sessionId)
  }

  const handleDeleteClick = (sessionId: number, sessionTitle: string, e: React.MouseEvent) => {
    e.stopPropagation()
    setDeleteTarget({ id: sessionId, title: sessionTitle })
  }

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return
    await deleteSession(deleteTarget.id)
    setDeleteTarget(null)
  }

  const formatDate = (date: Date) => {
    try {
      return formatDistanceToNow(date, { addSuffix: true, locale: ko })
    } catch {
      return "알 수 없음"
    }
  }

  return (
    <div className="flex h-full flex-col">
      {/* 헤더 */}
      <div className="flex-shrink-0 border-b border-white/[0.06] px-4 py-3">
        <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider">History</h2>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-3 space-y-1.5">
          {/* 현재 진행 중인 질문 */}
          {currentPendingQuestion && (
            <div className="rounded-lg border border-violet-500/20 bg-violet-500/5 p-3 animate-fade-in">
              <div className="flex items-start gap-2.5">
                <div className="mt-0.5 w-5 h-5 shrink-0 rounded-full bg-violet-500/20 flex items-center justify-center">
                  {isTyping ? (
                    <Loader2 className="w-3 h-3 text-violet-400 animate-spin" />
                  ) : (
                    <MessageSquare className="w-3 h-3 text-violet-400" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white font-medium line-clamp-1">
                    {currentPendingQuestion.content}
                  </p>
                  <p className="text-xs text-violet-300 mt-1">
                    {isTyping ? '응답 생성 중...' : '처리 중...'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* 세션 목록 */}
          {sessionsLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-5 h-5 animate-spin text-zinc-500" />
            </div>
          ) : sessions.length === 0 && !currentPendingQuestion ? (
            <div className="flex flex-col items-center justify-center py-8 text-zinc-500">
              <MessageSquare className="w-6 h-6 mb-2 opacity-50" />
              <p className="text-xs">No history</p>
            </div>
          ) : (
            sessions.map((session) => (
              <div
                key={session.id}
                className={cn(
                  "group rounded-lg border p-3 cursor-pointer transition-all duration-200",
                  selectedSessionId === session.id
                    ? "bg-white/10 border-white/[0.12]"
                    : "bg-white/[0.03] border-white/[0.06] hover:bg-white/[0.05] hover:border-white/[0.1]"
                )}
                onClick={() => handleSelectSession(session.id)}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-medium text-white line-clamp-1">
                      {session.title || `Chat ${session.id}`}
                    </h3>
                    <div className="flex items-center gap-1.5 mt-1 text-xs text-zinc-500">
                      <Clock className="w-3 h-3" />
                      <span>
                        {session.last_message_at
                          ? formatDate(new Date(session.last_message_at))
                          : formatDate(new Date(session.updated_at))
                        }
                      </span>
                    </div>
                  </div>
                  <button
                    className="p-1 rounded opacity-0 group-hover:opacity-100 transition-opacity text-zinc-500 hover:text-red-400 hover:bg-red-500/10"
                    onClick={(e) => handleDeleteClick(session.id, session.title || `Chat ${session.id}`, e)}
                    title="Delete session"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </ScrollArea>

      {/* 푸터 */}
      <div className="flex-shrink-0 border-t border-white/[0.06] px-4 py-2">
        <p className="text-[11px] text-zinc-500 text-center">
          {sessions.length} sessions
        </p>
      </div>

      {/* 삭제 확인 다이얼로그 */}
      <Dialog open={!!deleteTarget} onOpenChange={() => setDeleteTarget(null)}>
        <DialogContent className="max-w-sm bg-[#0a0a0f] border-white/[0.08]" showCloseButton={false}>
          <DialogHeader>
            <div className="mx-auto mb-2 w-12 h-12 rounded-full bg-red-500/10 flex items-center justify-center">
              <AlertTriangle className="w-6 h-6 text-red-400" />
            </div>
            <DialogTitle className="text-white text-center">세션을 삭제할까요?</DialogTitle>
            <DialogDescription className="text-zinc-400 text-center">
              <span className="font-medium text-zinc-300">{deleteTarget?.title}</span>
              {" "}세션이 영구적으로 삭제됩니다. 이 작업은 되돌릴 수 없습니다.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="mt-2 flex gap-3 sm:flex-row">
            <button
              onClick={() => setDeleteTarget(null)}
              className="flex-1 rounded-lg border border-white/[0.08] bg-white/[0.03] px-4 py-2.5 text-sm font-medium text-zinc-300 hover:bg-white/[0.06] transition-colors"
            >
              취소
            </button>
            <button
              onClick={handleDeleteConfirm}
              className="flex-1 rounded-lg bg-red-500/20 border border-red-500/30 px-4 py-2.5 text-sm font-medium text-red-400 hover:bg-red-500/30 transition-colors"
            >
              삭제
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
