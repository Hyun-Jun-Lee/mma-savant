"use client"

import { AuthGuard } from "@/components/auth/AuthGuard"
import { ChatContainer } from "@/components/chat/ChatContainer"

export default function ChatPage() {
  return (
    <AuthGuard>
      <ChatContainer />
    </AuthGuard>
  )
}