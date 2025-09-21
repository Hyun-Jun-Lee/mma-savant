"use client"

import { Lightbulb, TrendingUp, AlertCircle } from "lucide-react"

interface InsightsSummaryProps {
  insights: string[]
}

export function InsightsSummary({ insights }: InsightsSummaryProps) {
  if (!insights || insights.length === 0) {
    return (
      <div className="p-8 text-center text-zinc-400">
        표시할 인사이트가 없습니다.
      </div>
    )
  }

  // 인사이트 타입에 따른 아이콘 선택
  const getInsightIcon = (insight: string) => {
    const lowerInsight = insight.toLowerCase()
    if (lowerInsight.includes("증가") || lowerInsight.includes("상승") || lowerInsight.includes("높") || lowerInsight.includes("향상")) {
      return <TrendingUp className="w-4 h-4 text-green-400" />
    } else if (lowerInsight.includes("주의") || lowerInsight.includes("위험") || lowerInsight.includes("감소") || lowerInsight.includes("낮")) {
      return <AlertCircle className="w-4 h-4 text-yellow-400" />
    } else {
      return <Lightbulb className="w-4 h-4 text-blue-400" />
    }
  }

  return (
    <div className="space-y-3">
      {insights.map((insight, index) => (
        <div
          key={index}
          className="flex items-start gap-3 p-3 bg-zinc-700/30 rounded-lg border border-zinc-600/30 hover:bg-zinc-700/50 transition-colors"
        >
          <div className="mt-0.5 shrink-0">
            {getInsightIcon(insight)}
          </div>
          <div className="text-zinc-200 text-sm leading-relaxed">
            {insight}
          </div>
        </div>
      ))}

      {/* 인사이트 개수 표시 */}
      <div className="pt-2 text-xs text-zinc-500 text-center border-t border-zinc-700/50">
        총 {insights.length}개의 인사이트
      </div>
    </div>
  )
}