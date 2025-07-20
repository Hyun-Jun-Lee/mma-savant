"use client"

import { AuthGuard } from "@/components/auth/AuthGuard"
import { ChatContainer } from "@/components/chat/ChatContainer"

export default function ChatPage() {
  return (
    <AuthGuard>
      <div className="h-screen bg-gray-50">
        <ChatContainer />
      </div>
    </AuthGuard>
  )
}