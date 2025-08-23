/**
 * 채팅 세션 관리 사이드바 컴포넌트
 */
"use client"

import { useState } from "react"
import { useChatStore } from "@/store/chatStore"
import { useChatSession } from "@/hooks/useChatSession"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { 
  MessageSquare, 
  Plus, 
  Trash2, 
  Edit3, 
  Check, 
  X,
  Clock,
  MoreVertical
} from "lucide-react"
import { ChatSession } from "@/types/chat"
import { formatDistanceToNow } from "date-fns"
import { ko } from "date-fns/locale"

interface SessionSidebarProps {
  isOpen: boolean
  onClose: () => void
}

export function SessionSidebar({ isOpen, onClose }: SessionSidebarProps) {
  const { 
    currentSession, 
    sessions, 
    sessionsLoading 
  } = useChatStore()
  
  const { 
    createSession, 
    switchToSession, 
    deleteSession, 
    updateSessionTitle 
  } = useChatSession()

  const [editingSessionId, setEditingSessionId] = useState<string | null>(null)
  const [editTitle, setEditTitle] = useState("")

  const handleCreateSession = async () => {
    const session = await createSession()
    if (session) {
      onClose()
    }
  }

  const handleSelectSession = async (sessionId: string) => {
    const success = await switchToSession(sessionId)
    if (success) {
      onClose()
    }
  }

  const handleDeleteSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    
    if (confirm('이 세션을 삭제하시겠습니까?')) {
      await deleteSession(sessionId)
    }
  }

  const handleEditTitle = (session: ChatSession, e: React.MouseEvent) => {
    e.stopPropagation()
    setEditingSessionId(session.session_id)
    setEditTitle(session.title || `채팅 ${session.id}`)
  }

  const handleSaveTitle = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    
    if (editTitle.trim()) {
      const success = await updateSessionTitle(sessionId, editTitle.trim())
      if (success) {
        setEditingSessionId(null)
        setEditTitle("")
      }
    }
  }

  const handleCancelEdit = (e: React.MouseEvent) => {
    e.stopPropagation()
    setEditingSessionId(null)
    setEditTitle("")
  }

  const formatDate = (date: Date) => {
    try {
      return formatDistanceToNow(date, { 
        addSuffix: true, 
        locale: ko 
      })
    } catch {
      return "알 수 없음"
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex">
      {/* 배경 오버레이 */}
      <div 
        className="flex-1 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* 사이드바 */}
      <div className="w-80 h-full bg-zinc-900/95 backdrop-blur-sm border-l border-white/10 shadow-2xl">
        <div className="flex flex-col h-full">
          {/* 헤더 */}
          <div className="p-4 border-b border-white/10">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white">Chat History</h2>
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                className="text-zinc-400 hover:text-white hover:bg-white/10"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
            
            <Button
              onClick={handleCreateSession}
              className="w-full bg-white text-zinc-900 hover:bg-zinc-100 font-medium"
              size="sm"
            >
              <Plus className="w-4 h-4 mr-2" />
              New Chat
            </Button>
          </div>

          {/* 세션 목록 */}
          <ScrollArea className="flex-1 p-3">
            {sessionsLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="text-zinc-400">Loading...</div>
              </div>
            ) : sessions.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 text-zinc-400">
                <MessageSquare className="w-8 h-8 mb-2 opacity-50" />
                <p className="text-sm">No chat history</p>
              </div>
            ) : (
              <div className="space-y-2">
                {sessions.map((session) => (
                  <div
                    key={session.session_id}
                    className={`group p-3 rounded-lg cursor-pointer transition-all duration-200 border ${
                      currentSession?.session_id === session.session_id
                        ? 'bg-white/10 border-white/20 shadow-lg'
                        : 'bg-white/5 border-white/10 hover:bg-white/10 hover:border-white/20'
                    }`}
                    onClick={() => handleSelectSession(session.session_id)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        {editingSessionId === session.session_id ? (
                          <div className="flex items-center gap-1">
                            <input
                              type="text"
                              value={editTitle}
                              onChange={(e) => setEditTitle(e.target.value)}
                              className="flex-1 px-3 py-1.5 text-sm bg-white/10 border border-white/20 rounded-md text-white placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-white/30 focus:border-white/30"
                              onClick={(e) => e.stopPropagation()}
                              autoFocus
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                  handleSaveTitle(session.session_id, e as any)
                                } else if (e.key === 'Escape') {
                                  handleCancelEdit(e as any)
                                }
                              }}
                            />
                            <Button
                              variant="ghost"
                              size="sm"
                              className="p-1 h-7 w-7 hover:bg-emerald-500/20"
                              onClick={(e) => handleSaveTitle(session.session_id, e)}
                            >
                              <Check className="w-3 h-3 text-emerald-400" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="p-1 h-7 w-7 hover:bg-red-500/20"
                              onClick={handleCancelEdit}
                            >
                              <X className="w-3 h-3 text-red-400" />
                            </Button>
                          </div>
                        ) : (
                          <>
                            <h3 className="font-medium text-sm truncate text-white">
                              {session.title || `Chat ${session.id}`}
                            </h3>
                            <div className="flex items-center gap-2 mt-1 text-xs text-zinc-400">
                              <Clock className="w-3 h-3" />
                              <span>
                                {session.last_message_at 
                                  ? formatDate(session.last_message_at)
                                  : formatDate(session.updated_at)
                                }
                              </span>
                            </div>
                          </>
                        )}
                      </div>

                      {editingSessionId !== session.session_id && (
                        <div className="flex items-center gap-1 ml-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="p-1 h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-white/20 text-zinc-400 hover:text-white"
                            onClick={(e) => handleEditTitle(session, e)}
                            title="Edit title"
                          >
                            <Edit3 className="w-3 h-3" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="p-1 h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity text-red-400 hover:text-red-300 hover:bg-red-500/20"
                            onClick={(e) => handleDeleteSession(session.session_id, e)}
                            title="Delete session"
                          >
                            <Trash2 className="w-3 h-3" />
                          </Button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>

          {/* 푸터 정보 */}
          <div className="p-4 border-t border-white/10">
            <p className="text-xs text-zinc-400 text-center">
              {sessions.length} chat sessions
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}