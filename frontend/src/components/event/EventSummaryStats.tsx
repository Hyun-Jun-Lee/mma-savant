'use client'

import type { EventSummary } from '@/types/event'

interface Props {
  summary: EventSummary
}

interface StatItemProps {
  label: string
  value: number
  color: string
}

function StatItem({ label, value, color }: StatItemProps) {
  return (
    <div className="rounded-xl border border-white/[0.06] bg-white/[0.03] p-4 transition-all duration-300 ease-out hover:border-white/[0.12] hover:bg-white/[0.05]">
      <p className="text-xs text-zinc-500">{label}</p>
      <p className={`mt-1 text-2xl font-bold tracking-tight ${color}`}>
        {value}
      </p>
    </div>
  )
}

export function EventSummaryStats({ summary }: Props) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
      <StatItem label="KO/TKO" value={summary.ko_tko_count} color="text-red-400" />
      <StatItem label="Submission" value={summary.submission_count} color="text-purple-400" />
      <StatItem label="Decision" value={summary.decision_count} color="text-cyan-400" />
      <StatItem label="Other" value={summary.other_count} color="text-zinc-400" />
    </div>
  )
}
