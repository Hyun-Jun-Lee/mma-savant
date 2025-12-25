"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { AdminStatsResponse } from "@/types/api"

interface AdminStatsProps {
  stats: AdminStatsResponse | null
  isLoading: boolean
}

export function AdminStats({ stats, isLoading }: AdminStatsProps) {
  const statItems = [
    {
      title: "총 사용자",
      value: stats?.total_users ?? 0,
      icon: "👥",
    },
    {
      title: "활성 사용자",
      value: stats?.active_users ?? 0,
      icon: "✅",
    },
    {
      title: "관리자",
      value: stats?.admin_users ?? 0,
      icon: "🛡️",
    },
    {
      title: "오늘 총 요청",
      value: stats?.total_requests_today ?? 0,
      icon: "📊",
    },
    {
      title: "총 대화 세션",
      value: stats?.total_conversations ?? 0,
      icon: "💬",
    },
  ]

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {[...Array(5)].map((_, i) => (
          <Card key={i} className="animate-pulse bg-zinc-900/50 border-white/10">
            <CardHeader className="pb-2">
              <div className="h-4 bg-white/10 rounded w-20" />
            </CardHeader>
            <CardContent>
              <div className="h-8 bg-white/10 rounded w-16" />
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
      {statItems.map((item) => (
        <Card key={item.title} className="bg-zinc-900/50 border-white/10 backdrop-blur-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-zinc-400 flex items-center gap-2">
              <span>{item.icon}</span>
              {item.title}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-white">{item.value.toLocaleString()}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
