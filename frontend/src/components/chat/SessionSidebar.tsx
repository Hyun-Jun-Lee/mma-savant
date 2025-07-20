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
        className="flex-1 bg-black bg-opacity-50"
        onClick={onClose}
      />
      
      {/* 사이드바 */}
      <Card className="w-80 h-full rounded-none border-l shadow-lg">
        <div className="flex flex-col h-full">
          {/* 헤더 */}
          <div className="p-4 border-b">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">채팅 히스토리</h2>
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                className="text-gray-500"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
            
            <Button
              onClick={handleCreateSession}
              className="w-full mt-3 bg-red-600 hover:bg-red-700"
              size="sm"
            >
              <Plus className="w-4 h-4 mr-2" />
              새 채팅 시작
            </Button>
          </div>

          {/* 세션 목록 */}
          <ScrollArea className="flex-1 p-2">
            {sessionsLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="text-gray-500">로딩 중...</div>
              </div>
            ) : sessions.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 text-gray-500">
                <MessageSquare className="w-8 h-8 mb-2 opacity-50" />
                <p className="text-sm">채팅 히스토리가 없습니다</p>
              </div>
            ) : (
              <div className="space-y-1">
                {sessions.map((session) => (
                  <Card
                    key={session.session_id}
                    className={`p-3 cursor-pointer transition-colors hover:bg-gray-50 ${
                      currentSession?.session_id === session.session_id
                        ? 'bg-red-50 border-red-200'
                        : 'border-gray-200'
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
                              className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded"
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
                              className="p-1 h-6 w-6"
                              onClick={(e) => handleSaveTitle(session.session_id, e)}
                            >
                              <Check className="w-3 h-3 text-green-600" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="p-1 h-6 w-6"
                              onClick={handleCancelEdit}
                            >
                              <X className="w-3 h-3 text-red-600" />
                            </Button>
                          </div>
                        ) : (
                          <>
                            <h3 className="font-medium text-sm truncate">
                              {session.title || `채팅 ${session.id}`}
                            </h3>
                            <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
                              <Clock className="w-3 h-3" />
                              <span>
                                {session.last_message_at 
                                  ? formatDate(session.last_message_at)
                                  : formatDate(session.updated_at)
                                }
                              </span>
                              <span>•</span>
                              <span>{session.message_count}개 메시지</span>
                            </div>
                          </>
                        )}
                      </div>

                      {editingSessionId !== session.session_id && (
                        <div className="flex items-center gap-1 ml-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="p-1 h-6 w-6 opacity-0 group-hover:opacity-100"
                            onClick={(e) => handleEditTitle(session, e)}
                          >
                            <Edit3 className="w-3 h-3" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="p-1 h-6 w-6 opacity-0 group-hover:opacity-100 text-red-600"
                            onClick={(e) => handleDeleteSession(session.session_id, e)}
                          >
                            <Trash2 className="w-3 h-3" />
                          </Button>
                        </div>
                      )}
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </ScrollArea>

          {/* 푸터 정보 */}
          <div className="p-4 border-t text-xs text-gray-500">
            총 {sessions.length}개의 채팅 세션
          </div>
        </div>
      </Card>
    </div>
  )
}