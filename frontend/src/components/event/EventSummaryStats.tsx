'use client'

import { motion } from 'framer-motion'
import CountUp from 'react-countup'
import type { EventSummary } from '@/types/event'

interface Props {
  summary: EventSummary
}

interface StatItemProps {
  label: string
  value: number
  color: string
  index?: number
}

function StatItem({ label, value, color, index }: StatItemProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 28, filter: 'blur(4px)' }}
      animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
      transition={{ duration: 0.7, ease: [0.23, 1, 0.32, 1], delay: (index ?? 0) * 0.1 }}
      className="rounded-xl border border-white/[0.06] bg-white/[0.03] p-4 transition-all duration-300 ease-out hover:border-white/[0.12] hover:bg-white/[0.05]"
    >
      <p className="text-xs text-zinc-500">{label}</p>
      <p className={`mt-1 text-2xl font-bold tracking-tight ${color}`}>
        <CountUp
          end={value}
          duration={1.5}
          easingFn={(t, b, c, d) => {
            const p = t / d
            return b + c * (1 - Math.pow(1 - p, 3))
          }}
        />
      </p>
    </motion.div>
  )
}

export function EventSummaryStats({ summary }: Props) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
      <StatItem label="KO/TKO" value={summary.ko_tko_count} color="text-red-400" index={0} />
      <StatItem label="Submission" value={summary.submission_count} color="text-purple-400" index={1} />
      <StatItem label="Decision" value={summary.decision_count} color="text-cyan-400" index={2} />
      <StatItem label="Other" value={summary.other_count} color="text-zinc-400" index={3} />
    </div>
  )
}
