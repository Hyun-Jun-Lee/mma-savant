'use client'

import { motion } from 'framer-motion'
import CountUp from 'react-countup'
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
    <motion.div
      initial={{ opacity: 0, y: 28, filter: 'blur(4px)' }}
      animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
      transition={{ duration: 0.7, ease: [0.23, 1, 0.32, 1] }}
      className="rounded-xl border border-white/[0.06] bg-white/[0.03] p-5 transition-all duration-300 ease-out hover:border-white/[0.12] hover:bg-white/[0.05]"
    >
      <h3 className="mb-4 text-sm font-semibold text-zinc-100">Record</h3>

      {/* W-L-D */}
      <div className="flex items-baseline gap-4">
        <div className="text-center">
          <span className="text-3xl font-bold text-emerald-400">
            <CountUp end={record.wins} duration={1.5} easingFn={(t, b, c, d) => { const p = t / d; return b + c * (1 - Math.pow(1 - p, 3)) }} />
          </span>
          <p className="text-xs text-zinc-500">Wins</p>
        </div>
        <span className="text-xl text-zinc-600">-</span>
        <div className="text-center">
          <span className="text-3xl font-bold text-red-400">
            <CountUp end={record.losses} duration={1.5} easingFn={(t, b, c, d) => { const p = t / d; return b + c * (1 - Math.pow(1 - p, 3)) }} />
          </span>
          <p className="text-xs text-zinc-500">Losses</p>
        </div>
        <span className="text-xl text-zinc-600">-</span>
        <div className="text-center">
          <span className="text-3xl font-bold text-amber-400">
            <CountUp end={record.draws} duration={1.5} easingFn={(t, b, c, d) => { const p = t / d; return b + c * (1 - Math.pow(1 - p, 3)) }} />
          </span>
          <p className="text-xs text-zinc-500">Draws</p>
        </div>
      </div>

      {/* Win Rate Bar */}
      <div className="mt-4">
        <div className="flex items-center justify-between text-xs text-zinc-400">
          <span>Win Rate</span>
          <span className="font-medium text-zinc-200">
            <CountUp end={record.win_rate} duration={1.5} decimals={1} easingFn={(t, b, c, d) => { const p = t / d; return b + c * (1 - Math.pow(1 - p, 3)) }} />%
          </span>
        </div>
        <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-white/[0.06]">
          <motion.div
            className="h-full rounded-full bg-emerald-500"
            initial={{ width: 0 }}
            animate={{ width: `${record.win_rate}%` }}
            transition={{ duration: 0.9, ease: 'easeOut', delay: 0.8 }}
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
    </motion.div>
  )
}
