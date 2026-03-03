'use client'

import type { FighterRecord } from '@/types/fighter'
import { Badge } from '@/components/ui/badge'

interface Props {
  record: FighterRecord
}

export function RecordCard({ record }: Props) {
  const total = record.wins + record.losses + record.draws

  if (total === 0) {
    return (
      <div className="rounded-xl border border-white/[0.06] bg-white/[0.03] p-5 transition-all duration-300 ease-out hover:border-white/[0.12] hover:bg-white/[0.05]">
        <h3 className="text-sm font-semibold text-zinc-100">Record</h3>
        <p className="mt-4 text-center text-sm text-zinc-500">
          No fights recorded
        </p>
      </div>
    )
  }

  const { type, count } = record.current_streak

  return (
    <div className="rounded-xl border border-white/[0.06] bg-white/[0.03] p-5 transition-all duration-300 ease-out hover:border-white/[0.12] hover:bg-white/[0.05]">
      <h3 className="mb-4 text-sm font-semibold text-zinc-100">Record</h3>

      {/* W-L-D */}
      <div className="flex items-baseline gap-4">
        <div className="text-center">
          <span className="text-3xl font-bold text-emerald-400">
            {record.wins}
          </span>
          <p className="text-xs text-zinc-500">Wins</p>
        </div>
        <span className="text-xl text-zinc-600">-</span>
        <div className="text-center">
          <span className="text-3xl font-bold text-red-400">
            {record.losses}
          </span>
          <p className="text-xs text-zinc-500">Losses</p>
        </div>
        <span className="text-xl text-zinc-600">-</span>
        <div className="text-center">
          <span className="text-3xl font-bold text-zinc-400">
            {record.draws}
          </span>
          <p className="text-xs text-zinc-500">Draws</p>
        </div>
      </div>

      {/* Win Rate Bar */}
      <div className="mt-4">
        <div className="flex items-center justify-between text-xs text-zinc-400">
          <span>Win Rate</span>
          <span className="font-medium text-zinc-200">
            {record.win_rate}%
          </span>
        </div>
        <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-white/[0.06]">
          <div
            className="h-full rounded-full bg-emerald-500 transition-all duration-500"
            style={{ width: `${record.win_rate}%` }}
          />
        </div>
      </div>

      {/* Streak */}
      {type !== 'none' && count > 0 && (
        <div className="mt-3">
          <Badge variant={type === 'win' ? 'win' : 'loss'}>
            {count} {type === 'win' ? 'Win' : 'Loss'} Streak
          </Badge>
        </div>
      )}
    </div>
  )
}
