'use client'

import { Trophy, Target, Swords, Shield, Flame, Crosshair, HandMetal, Zap } from 'lucide-react'
import type { CategoryLeader } from '@/types/dashboard'

const CATEGORY_ICONS: Record<string, typeof Trophy> = {
  wins: Trophy,
  ko_tko: Flame,
  submissions: HandMetal,
  sig_strikes: Crosshair,
  takedowns: Target,
  td_accuracy: Zap,
  strike_accuracy: Swords,
  td_defense: Shield,
}

const CATEGORY_COLORS: Record<string, string> = {
  wins: 'text-amber-400',
  ko_tko: 'text-red-400',
  submissions: 'text-purple-400',
  sig_strikes: 'text-orange-400',
  takedowns: 'text-cyan-400',
  td_accuracy: 'text-emerald-400',
  strike_accuracy: 'text-blue-400',
  td_defense: 'text-teal-400',
}

interface CategoryLeadersCardProps {
  data: CategoryLeader[]
}

export function CategoryLeadersCard({ data }: CategoryLeadersCardProps) {
  if (!data.length) return null

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {data.map((leader) => {
        const Icon = CATEGORY_ICONS[leader.category] || Trophy
        const colorClass = CATEGORY_COLORS[leader.category] || 'text-zinc-400'

        return (
          <div
            key={leader.category}
            className="rounded-xl border border-white/[0.06] bg-white/[0.03] p-4 transition-all hover:border-white/[0.12] hover:bg-white/[0.05]"
          >
            <div className="mb-2 flex items-center gap-2">
              <Icon className={`h-4 w-4 ${colorClass}`} />
              <span className="text-xs font-medium text-zinc-500">
                {leader.label}
              </span>
            </div>
            <p className="truncate text-sm font-semibold text-zinc-100">
              {leader.name}
            </p>
            <p className={`mt-0.5 text-lg font-bold ${colorClass}`}>
              {typeof leader.value === 'number' && leader.value % 1 !== 0
                ? leader.value.toFixed(1)
                : leader.value}
              <span className="ml-1 text-xs font-normal text-zinc-500">
                {leader.unit}
              </span>
            </p>
          </div>
        )
      })}
    </div>
  )
}
