'use client'

import { motion } from 'framer-motion'
import type { CareerStats } from '@/types/fighter'

interface Props {
  stats: CareerStats | null
  submissionWins?: number
}

function StatRow({
  label,
  landed,
  attempted,
  delay = 0,
  color = 'bg-amber-500',
}: {
  label: string
  landed: number
  attempted: number
  delay?: number
  color?: string
}) {
  const pct = attempted > 0 ? Math.round((landed / attempted) * 100) : 0
  return (
    <div>
      <div className="flex items-center justify-between text-xs">
        <span className="text-zinc-400">{label}</span>
        <span className="text-zinc-200">
          {landed}/{attempted} ({pct}%)
        </span>
      </div>
      <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-white/[0.06]">
        <motion.div
          className={`h-full rounded-full ${color}`}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.9, ease: 'easeOut', delay: 0.7 + delay }}
        />
      </div>
    </div>
  )
}

function formatControlTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

export function CareerStatsCard({ stats, submissionWins = 0 }: Props) {
  if (!stats) {
    return (
      <div className="rounded-xl border border-white/[0.06] bg-white/[0.03] p-5 transition-all duration-300 ease-out hover:border-white/[0.12] hover:bg-white/[0.05]">
        <h3 className="text-sm font-semibold text-zinc-100">Career Stats</h3>
        <p className="mt-4 text-center text-sm text-zinc-500">
          No stats available
        </p>
      </div>
    )
  }

  const { striking, grappling } = stats

  // Head/Body/Leg proportional bar
  const totalTargetLanded =
    striking.head_landed + striking.body_landed + striking.leg_landed
  const headPct =
    totalTargetLanded > 0
      ? Math.round((striking.head_landed / totalTargetLanded) * 100)
      : 0
  const bodyPct =
    totalTargetLanded > 0
      ? Math.round((striking.body_landed / totalTargetLanded) * 100)
      : 0
  const legPct = totalTargetLanded > 0 ? 100 - headPct - bodyPct : 0

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      {/* Striking */}
      <motion.div
        initial={{ opacity: 0, y: 28, filter: 'blur(4px)' }}
        animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
        transition={{ duration: 0.7, ease: [0.23, 1, 0.32, 1], delay: 0 }}
        className="rounded-xl border border-white/[0.06] bg-white/[0.03] p-5 transition-all duration-300 ease-out hover:border-white/[0.12] hover:bg-white/[0.05]"
      >
        <h3 className="mb-4 text-sm font-semibold text-zinc-100">
          Striking
        </h3>

        <div className="space-y-3">
          <StatRow
            label="Sig. Strikes"
            landed={striking.sig_str_landed}
            attempted={striking.sig_str_attempted}
            delay={0}
            color="bg-amber-500"
          />

          <div className="flex items-center justify-between text-xs">
            <span className="text-zinc-400">Knockdowns</span>
            <span className="font-medium text-zinc-200">
              {striking.knockdowns}
              <span className="text-zinc-500"> / Absorbed </span>
              {striking.opp_knockdowns}
            </span>
          </div>

          {/* Target Distribution */}
          {totalTargetLanded > 0 && (
            <div>
              <p className="mb-1 text-xs text-zinc-400">Target Distribution</p>
              <div className="flex h-3 w-full overflow-hidden rounded-full">
                <motion.div
                  className="bg-red-500"
                  initial={{ width: 0 }}
                  animate={{ width: `${headPct}%` }}
                  transition={{ duration: 0.9, ease: 'easeOut', delay: 0.9 }}
                  title={`Head: ${headPct}%`}
                />
                <motion.div
                  className="bg-amber-500"
                  initial={{ width: 0 }}
                  animate={{ width: `${bodyPct}%` }}
                  transition={{ duration: 0.9, ease: 'easeOut', delay: 1.0 }}
                  title={`Body: ${bodyPct}%`}
                />
                <motion.div
                  className="bg-cyan-500"
                  initial={{ width: 0 }}
                  animate={{ width: `${legPct}%` }}
                  transition={{ duration: 0.9, ease: 'easeOut', delay: 1.1 }}
                  title={`Leg: ${legPct}%`}
                />
              </div>
              <div className="mt-1 flex gap-3 text-[10px] text-zinc-500">
                <span className="flex items-center gap-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-red-500" />
                  Head {headPct}%
                </span>
                <span className="flex items-center gap-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
                  Body {bodyPct}%
                </span>
                <span className="flex items-center gap-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-cyan-500" />
                  Leg {legPct}%
                </span>
              </div>
            </div>
          )}
        </div>
      </motion.div>

      {/* Grappling */}
      <motion.div
        initial={{ opacity: 0, y: 28, filter: 'blur(4px)' }}
        animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
        transition={{ duration: 0.7, ease: [0.23, 1, 0.32, 1], delay: 0.1 }}
        className="rounded-xl border border-white/[0.06] bg-white/[0.03] p-5 transition-all duration-300 ease-out hover:border-white/[0.12] hover:bg-white/[0.05]"
      >
        <h3 className="mb-4 text-sm font-semibold text-zinc-100">
          Grappling
        </h3>

        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs">
            <span className="text-zinc-400">TD Offense</span>
            <span className="font-medium text-zinc-200">
              {grappling.td_landed}/{grappling.td_attempted}{' '}
              {grappling.td_attempted > 0 && (
                <span className="text-zinc-500">
                  ({Math.round((grappling.td_landed / grappling.td_attempted) * 100)}%)
                </span>
              )}
            </span>
          </div>

          <div className="flex items-center justify-between text-xs">
            <span className="text-zinc-400">TD Defense</span>
            <span className="font-medium text-zinc-200">
              {grappling.opp_td_attempted > 0
                ? `${grappling.opp_td_attempted - grappling.opp_td_landed}/${grappling.opp_td_attempted} (${Math.round((1 - grappling.opp_td_landed / grappling.opp_td_attempted) * 100)}%)`
                : '0/0'}
            </span>
          </div>

          <div className="flex items-center justify-between text-xs">
            <span className="text-zinc-400">Control Time (Avg/Total)</span>
            <span className="font-medium text-zinc-200">
              {formatControlTime(grappling.avg_control_time_seconds)}{' '}
              <span className="text-zinc-500">/ {formatControlTime(grappling.control_time_seconds)}</span>
            </span>
          </div>

          <div className="flex items-center justify-between text-xs">
            <span className="text-zinc-400">Submissions</span>
            <span className="font-medium text-zinc-200">
              {submissionWins}/{grappling.submission_attempts}{' '}
              {grappling.submission_attempts > 0 && (
                <span className="text-zinc-500">
                  ({Math.round((submissionWins / grappling.submission_attempts) * 100)}%)
                </span>
              )}
            </span>
          </div>

          {grappling.top_submission && (
            <div className="flex items-center justify-between text-xs">
              <span className="text-zinc-400">Best Submission</span>
              <span className="font-medium text-zinc-200">
                {grappling.top_submission}
              </span>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  )
}
