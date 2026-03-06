'use client'

import { useState } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import type { EventMatch, BasicMatchStat } from '@/types/event'
import { ChevronDown, Medal } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { toTitleCase } from '@/lib/utils'

interface Props {
  match: EventMatch
}

function formatControlTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

function getMethodBadgeVariant(method: string | null): 'ko' | 'submission' | 'decision' | 'draw' {
  if (!method) return 'draw'
  const m = method.toLowerCase()
  if (m.includes('ko') || m.includes('tko')) return 'ko'
  if (m.includes('sub')) return 'submission'
  if (m.includes('dec')) return 'decision'
  return 'draw'
}

function getResultStyle(result: string | null): string {
  if (!result) return 'text-zinc-400'
  const r = result.toLowerCase()
  if (r === 'win') return 'text-emerald-400 font-semibold'
  if (r === 'loss') return 'text-red-400'
  return 'text-zinc-400'
}

function StatLine({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-zinc-500">{label}</span>
      <span className="font-medium text-zinc-200">{value}</span>
    </div>
  )
}

function FighterStats({ stats }: { stats: BasicMatchStat }) {
  return (
    <div className="grid grid-cols-2 gap-x-6 gap-y-1.5 sm:grid-cols-3">
      <StatLine label="Sig. Str." value={`${stats.sig_str_landed}/${stats.sig_str_attempted}`} />
      <StatLine label="Total Str." value={`${stats.total_str_landed}/${stats.total_str_attempted}`} />
      <StatLine label="Knockdowns" value={stats.knockdowns} />
      <StatLine label="Takedowns" value={`${stats.td_landed}/${stats.td_attempted}`} />
      <StatLine label="Sub. Att." value={stats.submission_attempts} />
      <StatLine label="Ctrl Time" value={formatControlTime(stats.control_time_seconds)} />
    </div>
  )
}

export function FightCard({ match }: Props) {
  const [expanded, setExpanded] = useState(false)
  const [roundExpanded, setRoundExpanded] = useState(false)

  const hasStats = match.fighters.some((f) => f.stats)

  return (
    <div className={`rounded-xl border transition-all duration-300 ease-out ${
      match.is_main_event
        ? 'border-amber-500/20 bg-amber-500/[0.04] hover:border-amber-500/30 hover:bg-amber-500/[0.06]'
        : 'border-white/[0.06] bg-white/[0.03] hover:border-white/[0.12] hover:bg-white/[0.05]'
    }`}>
      {/* Main row */}
      <button
        type="button"
        className="w-full text-left"
        onClick={() => hasStats && setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3 p-4 sm:p-5">
          {/* Expand indicator */}
          <span className="shrink-0 text-zinc-600">
            {hasStats ? (
              <ChevronDown
                className={`h-4 w-4 transition-transform ${expanded ? 'rotate-180' : ''}`}
              />
            ) : (
              <span className="inline-block h-4 w-4" />
            )}
          </span>

          {/* Fight content */}
          <div className="min-w-0 flex-1">
            {/* Top row: weight class + method info */}
            <div className="flex flex-wrap items-center gap-2 text-xs">
              {match.weight_class && (
                <span className="font-medium text-zinc-400">
                  {toTitleCase(match.weight_class)}
                </span>
              )}
              {match.method && (
                <Badge variant={getMethodBadgeVariant(match.method)} className="text-[10px]">
                  {match.method}
                </Badge>
              )}
              {match.result_round != null && match.result_round > 0 && (
                <span className="text-zinc-500">
                  R{match.result_round} {match.time ?? ''}
                </span>
              )}
            </div>

            {/* Fighters row */}
            <div className="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm">
              {match.fighters.map((fighter, idx) => (
                <span key={fighter.fighter_id} className="flex items-center gap-x-2">
                  {idx > 0 && <span className="text-zinc-600">vs</span>}
                  {fighter.result?.toLowerCase() === 'win' && (
                    <Medal className="h-3.5 w-3.5 shrink-0 text-amber-400" />
                  )}
                  <Link
                    href={`/fighters/${fighter.fighter_id}`}
                    className={`transition-colors hover:text-blue-400 hover:underline ${getResultStyle(fighter.result)}`}
                    onClick={(e) => e.stopPropagation()}
                  >
                    {toTitleCase(fighter.name)}
                  </Link>
                  {fighter.ranking != null && (
                    <span className="text-[10px] font-medium text-zinc-500">
                      #{fighter.ranking}
                    </span>
                  )}
                </span>
              ))}
            </div>
          </div>
        </div>
      </button>

      {/* Expanded stats */}
      <AnimatePresence>
        {expanded && hasStats && (
          <motion.div
            key="fight-stats"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.25, ease: 'easeOut' }}
            className="overflow-hidden"
          >
            <div className="border-t border-white/[0.06] px-4 pb-4 pt-3 sm:px-5">
              <div className="space-y-4">
                {match.fighters.map((fighter) => {
                  if (!fighter.stats) return null
                  return (
                    <div key={fighter.fighter_id}>
                      <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-zinc-500">
                        <span className={fighter.result?.toLowerCase() === 'win' ? 'text-zinc-300' : ''}>
                          {toTitleCase(fighter.name)}
                        </span>
                        {fighter.result && (
                          <span className="ml-2">
                            ({fighter.result})
                          </span>
                        )}
                      </p>
                      <div className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-3 text-xs">
                        <FighterStats stats={fighter.stats} />
                      </div>
                    </div>
                  )
                })}

                {/* Round-by-round toggle */}
                {match.fighters.some((f) => f.round_stats && f.round_stats.length > 1) && (
                  <>
                    <button
                      type="button"
                      className="flex items-center gap-1 text-[11px] text-zinc-500 transition-colors hover:text-zinc-300"
                      onClick={() => setRoundExpanded(!roundExpanded)}
                    >
                      <ChevronDown className={`h-3 w-3 transition-transform ${roundExpanded ? 'rotate-180' : ''}`} />
                      {roundExpanded ? 'Hide round details' : 'Show round details'}
                    </button>

                    <AnimatePresence>
                      {roundExpanded && (
                        <motion.div
                          key="round-stats"
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          exit={{ opacity: 0, height: 0 }}
                          transition={{ duration: 0.25, ease: 'easeOut' }}
                          className="overflow-hidden"
                        >
                          <div className="space-y-4">
                            {match.fighters.map((fighter) => {
                              if (!fighter.round_stats || fighter.round_stats.length <= 1) return null
                              return (
                                <div key={`round-${fighter.fighter_id}`}>
                                  <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-zinc-500">
                                    <span className={fighter.result?.toLowerCase() === 'win' ? 'text-zinc-300' : ''}>
                                      {toTitleCase(fighter.name)}
                                    </span>
                                    {' — Round Details'}
                                  </p>
                                  <div className="space-y-2">
                                    {fighter.round_stats.map((rs) => (
                                      <div key={rs.round} className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-3 text-xs">
                                        <p className="mb-1.5 text-[10px] font-semibold text-zinc-400">Round {rs.round}</p>
                                        <FighterStats stats={rs} />
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )
                            })}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
