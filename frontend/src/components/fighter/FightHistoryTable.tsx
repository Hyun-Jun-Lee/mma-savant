'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Link from 'next/link'
import type { FightHistoryItem, PerMatchStats } from '@/types/fighter'
import { ChevronDown, ChevronRight, HelpCircle } from 'lucide-react'
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { Badge } from '@/components/ui/badge'
import { toTitleCase, formatDate } from '@/lib/utils'

interface Props {
  fights: FightHistoryItem[]
}

function formatControlTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

function ResultBadge({ result, method, eventDate }: { result: string; method?: string | null; eventDate?: string | null }) {
  const lower = result.toLowerCase()
  const isNc = lower === 'nc'
  const isCanceled = isNc && method?.toUpperCase() === 'CNC'
  const isPastUnknown = lower === 'unknown' && eventDate && new Date(eventDate) < new Date()
  const variant =
    lower === 'win' ? 'win'
    : lower === 'loss' ? 'loss'
    : isNc ? 'canceled'
    : isPastUnknown ? 'canceled'
    : lower === 'unknown' ? 'draw'
    : 'draw'
  const label = isPastUnknown ? 'Canceled' : isCanceled ? 'Canceled' : lower === 'unknown' ? 'TBD' : isNc ? 'NC' : result
  return (
    <Badge variant={variant} className="text-[10px] font-semibold uppercase">
      {label}
    </Badge>
  )
}

function PerMatchDetail({ stats }: { stats: PerMatchStats }) {
  const { basic, sig_str } = stats

  return (
    <div className="space-y-3 rounded-lg border border-white/[0.06] bg-white/[0.02] p-4 text-xs">
      {basic && (
        <div>
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-zinc-500">
            Basic Stats
          </p>
          <div className="grid grid-cols-2 gap-x-6 gap-y-1.5 sm:grid-cols-3">
            <StatLine label="Sig. Str." value={`${basic.sig_str_landed}/${basic.sig_str_attempted}`} />
            <StatLine label="Total Str." value={`${basic.total_str_landed}/${basic.total_str_attempted}`} />
            <StatLine label="Knockdowns" value={basic.knockdowns} />
            <StatLine label="Takedowns" value={`${basic.td_landed}/${basic.td_attempted}`} />
            <StatLine label="Sub. Att." value={basic.submission_attempts} />
            <StatLine label="Ctrl Time" value={formatControlTime(basic.control_time_seconds)} />
          </div>
        </div>
      )}

      {sig_str && (
        <div>
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-zinc-500">
            Significant Strikes by Target
          </p>
          <div className="grid grid-cols-2 gap-x-6 gap-y-1.5 sm:grid-cols-3">
            <StatLine label="Head" value={`${sig_str.head_landed}/${sig_str.head_attempted}`} />
            <StatLine label="Body" value={`${sig_str.body_landed}/${sig_str.body_attempted}`} />
            <StatLine label="Leg" value={`${sig_str.leg_landed}/${sig_str.leg_attempted}`} />
            <StatLine label="Clinch" value={`${sig_str.clinch_landed}/${sig_str.clinch_attempted}`} />
            <StatLine label="Ground" value={`${sig_str.ground_landed}/${sig_str.ground_attempted}`} />
          </div>
        </div>
      )}

      {!basic && !sig_str && (
        <p className="text-zinc-500">Stats not available</p>
      )}
    </div>
  )
}

function StatLine({
  label,
  value,
}: {
  label: string
  value: string | number
}) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-zinc-500">{label}</span>
      <span className="font-medium text-zinc-200">{value}</span>
    </div>
  )
}

function computeAvgFightTime(fights: FightHistoryItem[]): string | null {
  const durations: number[] = []
  for (const f of fights) {
    if (f.round != null && f.round > 0 && f.time) {
      const parts = f.time.trim().split(':')
      if (parts.length === 2) {
        const mins = parseInt(parts[0], 10)
        const secs = parseInt(parts[1], 10)
        if (!isNaN(mins) && !isNaN(secs)) {
          durations.push((f.round - 1) * 300 + mins * 60 + secs)
        }
      }
    }
  }
  if (durations.length === 0) return null
  const avg = durations.reduce((a, b) => a + b, 0) / durations.length
  const totalRounds = Math.floor(avg / 300) + 1
  const remainder = avg % 300
  const m = Math.floor(remainder / 60)
  const s = Math.round(remainder % 60)
  return `${totalRounds}R ${m}:${s.toString().padStart(2, '0')}`
}

export function FightHistoryTable({ fights }: Props) {
  const [expandedId, setExpandedId] = useState<number | null>(null)

  if (fights.length === 0) {
    return (
      <div className="rounded-xl border border-white/[0.06] bg-white/[0.03] p-5 transition-all duration-300 ease-out hover:border-white/[0.12] hover:bg-white/[0.05]">
        <h3 className="text-sm font-semibold text-zinc-100">Fight History</h3>
        <p className="mt-4 text-center text-sm text-zinc-500">
          No fight records
        </p>
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 28, filter: 'blur(4px)' }}
      animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
      transition={{ duration: 0.7, ease: [0.23, 1, 0.32, 1] }}
      className="rounded-xl border border-white/[0.06] bg-white/[0.03] p-5 transition-all duration-300 ease-out hover:border-white/[0.12] hover:bg-white/[0.05]"
    >
      <div className="mb-4 flex items-center gap-1.5">
        <h3 className="text-sm font-semibold text-zinc-100">
          Fight History
        </h3>
        {/* Recent 5 fights result dots */}
        <div className="ml-auto flex items-center gap-1">
          {fights.slice(0, 5).map((f, i) => {
            const r = f.result.toLowerCase()
            const isNc = r === 'nc'
            const isCanceled = (isNc && f.method?.toUpperCase() === 'CNC') || (r === 'unknown' && f.event_date && new Date(f.event_date) < new Date())
            const color =
              r === 'win'
                ? 'bg-emerald-400'
                : r === 'loss'
                  ? 'bg-red-400'
                  : (isNc || isCanceled)
                    ? 'bg-amber-400'
                    : 'bg-zinc-500'
            const label = r === 'win' ? 'W' : r === 'loss' ? 'L' : isCanceled ? 'CNC' : isNc ? 'NC' : 'D'
            return (
              <Tooltip key={f.match_id}>
                <TooltipTrigger asChild>
                  <span className={`inline-block h-2 w-2 rounded-full ${color}`} />
                </TooltipTrigger>
                <TooltipContent
                  side="top"
                  className="bg-zinc-900 text-zinc-200 border border-white/[0.06] text-[10px] px-1.5 py-0.5"
                >
                  {label} vs {toTitleCase(f.opponent.name)}
                </TooltipContent>
              </Tooltip>
            )
          })}
        </div>
        {(() => {
          const avg = computeAvgFightTime(fights)
          return avg ? (
            <span className="text-xs text-zinc-500">
              Avg. {avg}
            </span>
          ) : null
        })()}
        <Tooltip>
          <TooltipTrigger asChild>
            <HelpCircle className="h-3.5 w-3.5 shrink-0 cursor-help text-zinc-600 hover:text-zinc-400 transition-colors" />
          </TooltipTrigger>
          <TooltipContent
            side="top"
            className="max-w-[240px] bg-zinc-900 text-zinc-200 border border-white/[0.06]"
          >
            행을 클릭하면 경기별 상세 스탯을 확인할 수 있습니다. MAIN 표시는 해당 경기가 메인 이벤트였음을 나타냅니다.
          </TooltipContent>
        </Tooltip>
      </div>

      {/* Desktop table header */}
      <div className="hidden text-[10px] font-semibold uppercase tracking-wider text-zinc-600 sm:grid sm:grid-cols-[2rem_5rem_1fr_1fr_7rem_3.5rem_5.5rem]  sm:gap-2 sm:px-2 sm:pb-2">
        <span />
        <span>Result</span>
        <span>Opponent</span>
        <span>Event</span>
        <span>Method</span>
        <span>Rnd</span>
        <span>Date</span>
      </div>

      <div className="divide-y divide-white/[0.03]">
        {fights.map((fight) => {
          const isExpanded = expandedId === fight.match_id
          const hasStats = fight.stats && (fight.stats.basic || fight.stats.sig_str)

          return (
            <div key={fight.match_id}>
              {/* Row */}
              <button
                type="button"
                className="w-full text-left transition-colors hover:bg-white/[0.03]"
                onClick={() =>
                  setExpandedId(isExpanded ? null : fight.match_id)
                }
              >
                {/* Desktop */}
                <div className="hidden items-center gap-2 px-2 py-2.5 text-xs sm:grid sm:grid-cols-[2rem_5rem_1fr_1fr_7rem_3.5rem_5.5rem]">
                  <span className="text-zinc-600">
                    {hasStats ? (
                      isExpanded ? (
                        <ChevronDown className="h-3.5 w-3.5" />
                      ) : (
                        <ChevronRight className="h-3.5 w-3.5" />
                      )
                    ) : null}
                  </span>
                  <ResultBadge result={fight.result} method={fight.method} eventDate={fight.event_date} />
                  <span className="flex items-center gap-1.5 truncate text-zinc-200">
                    <Link
                      href={`/fighters/${fight.opponent.id}`}
                      className="hover:text-blue-400 hover:underline"
                      onClick={(e) => e.stopPropagation()}
                    >
                      {toTitleCase(fight.opponent.name)}
                    </Link>
                    {fight.is_main_event && (
                      <span className="rounded px-1 py-0.5 text-[9px] font-semibold uppercase text-amber-400 bg-amber-400/10">Main</span>
                    )}
                  </span>
                  <span className="truncate text-zinc-400">
                    {fight.event_id ? (
                      <Link
                        href={`/events/${fight.event_id}`}
                        className="hover:text-blue-400 hover:underline transition-colors"
                        onClick={(e) => e.stopPropagation()}
                      >
                        {fight.event_name ?? '-'}
                      </Link>
                    ) : (
                      fight.event_name ?? '-'
                    )}
                  </span>
                  <span className="text-zinc-400">
                    {fight.method ?? '-'}
                  </span>
                  <span className="text-zinc-400">
                    R{fight.round ?? '-'}{' '}
                    {fight.time ?? ''}
                  </span>
                  <span className="text-zinc-500">
                    {fight.event_date ? formatDate(fight.event_date) : '-'}
                  </span>
                </div>

                {/* Mobile */}
                <div className="flex flex-col gap-1 px-1 py-2.5 sm:hidden">
                  <div className="flex items-center gap-2">
                    <span className="text-zinc-600">
                      {hasStats ? (
                        isExpanded ? (
                          <ChevronDown className="h-3.5 w-3.5" />
                        ) : (
                          <ChevronRight className="h-3.5 w-3.5" />
                        )
                      ) : null}
                    </span>
                    <ResultBadge result={fight.result} method={fight.method} eventDate={fight.event_date} />
                    <span className="text-xs text-zinc-200">
                      vs{' '}
                      <Link
                        href={`/fighters/${fight.opponent.id}`}
                        className="hover:text-blue-400 hover:underline"
                        onClick={(e) => e.stopPropagation()}
                      >
                        {toTitleCase(fight.opponent.name)}
                      </Link>
                    </span>
                    {fight.is_main_event && (
                      <span className="rounded px-1 py-0.5 text-[9px] font-semibold uppercase text-amber-400 bg-amber-400/10">Main</span>
                    )}
                  </div>
                  <div className="ml-6 flex flex-wrap gap-x-3 text-[10px] text-zinc-500">
                    <span>{fight.method ?? '-'}</span>
                    <span>R{fight.round ?? '-'} {fight.time ?? ''}</span>
                    <span>{fight.event_date ? formatDate(fight.event_date) : '-'}</span>
                  </div>
                </div>
              </button>

              {/* Expanded stats */}
              <AnimatePresence>
                {isExpanded && fight.stats && (
                  <motion.div
                    key="expanded-stats"
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.25, ease: 'easeOut' }}
                    className="overflow-hidden"
                  >
                    <div className="px-2 pb-3 pt-1 sm:pl-10">
                      <PerMatchDetail stats={fight.stats} />
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          )
        })}
      </div>
    </motion.div>
  )
}
