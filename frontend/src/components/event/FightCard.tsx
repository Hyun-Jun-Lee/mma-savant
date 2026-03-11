'use client'

import { useState, useId } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import type { EventMatch, BasicMatchStat, EventFighterStat, StrikeStats } from '@/types/event'
import { ChevronDown, Medal, AlertTriangle } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { toTitleCase } from '@/lib/utils'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'

/** SVG Repo human silhouette (CC0) – single path, clipped into Head / Body / Leg zones */
const SILHOUETTE_PATH =
  'M104.265,117.959c-0.304,3.58,2.126,22.529,3.38,29.959c0.597,3.52,2.234,9.255,1.645,12.3' +
  'c-0.841,4.244-1.084,9.736-0.621,12.934c0.292,1.942,1.211,10.899-0.104,14.175c-0.688,1.718-1.949,10.522-1.949,10.522' +
  'c-3.285,8.294-1.431,7.886-1.431,7.886c1.017,1.248,2.759,0.098,2.759,0.098c1.327,0.846,2.246-0.201,2.246-0.201' +
  'c1.139,0.943,2.467-0.116,2.467-0.116c1.431,0.743,2.758-0.627,2.758-0.627c0.822,0.414,1.023-0.109,1.023-0.109' +
  'c2.466-0.158-1.376-8.05-1.376-8.05c-0.92-7.088,0.913-11.033,0.913-11.033c6.004-17.805,6.309-22.53,3.909-29.24' +
  'c-0.676-1.937-0.847-2.704-0.536-3.545c0.719-1.941,0.195-9.748,1.072-12.848c1.692-5.979,3.361-21.142,4.231-28.217' +
  'c1.169-9.53-4.141-22.308-4.141-22.308c-1.163-5.2,0.542-23.727,0.542-23.727c2.381,3.705,2.29,10.245,2.29,10.245' +
  'c-0.378,6.859,5.541,17.342,5.541,17.342c2.844,4.332,3.921,8.442,3.921,8.747c0,1.248-0.273,4.269-0.273,4.269l0.109,2.631' +
  'c0.049,0.67,0.426,2.977,0.365,4.092c-0.444,6.862,0.646,5.571,0.646,5.571c0.92,0,1.931-5.522,1.931-5.522' +
  'c0,1.424-0.348,5.687,0.42,7.295c0.919,1.918,1.595-0.329,1.607-0.78c0.243-8.737,0.768-6.448,0.768-6.448' +
  'c0.511,7.088,1.139,8.689,2.265,8.135c0.853-0.407,0.073-8.506,0.073-8.506c1.461,4.811,2.569,5.577,2.569,5.577' +
  'c2.411,1.693,0.92-2.983,0.585-3.909c-1.784-4.92-1.839-6.625-1.839-6.625c2.229,4.421,3.909,4.257,3.909,4.257' +
  'c2.174-0.694-1.9-6.954-4.287-9.953c-1.218-1.528-2.789-3.574-3.245-4.789c-0.743-2.058-1.304-8.674-1.304-8.674' +
  'c-0.225-7.807-2.155-11.198-2.155-11.198c-3.3-5.282-3.921-15.135-3.921-15.135l-0.146-16.635' +
  'c-1.157-11.347-9.518-11.429-9.518-11.429c-8.451-1.258-9.627-3.988-9.627-3.988c-1.79-2.576-0.767-7.514-0.767-7.514' +
  'c1.485-1.208,2.058-4.415,2.058-4.415c2.466-1.891,2.345-4.658,1.206-4.628c-0.914,0.024-0.707-0.733-0.707-0.733' +
  'C115.068,0.636,104.01,0,104.01,0h-1.688c0,0-11.063,0.636-9.523,13.089c0,0,0.207,0.758-0.715,0.733' +
  'c-1.136-0.03-1.242,2.737,1.215,4.628c0,0,0.572,3.206,2.058,4.415c0,0,1.023,4.938-0.767,7.514c0,0-1.172,2.73-9.627,3.988' +
  'c0,0-8.375,0.082-9.514,11.429l-0.158,16.635c0,0-0.609,9.853-3.922,15.135c0,0-1.921,3.392-2.143,11.198' +
  'c0,0-0.563,6.616-1.303,8.674c-0.451,1.209-2.021,3.255-3.249,4.789c-2.408,2.993-6.455,9.24-4.29,9.953' +
  'c0,0,1.689,0.164,3.909-4.257c0,0-0.046,1.693-1.827,6.625c-0.35,0.914-1.839,5.59,0.573,3.909c0,0,1.117-0.767,2.569-5.577' +
  'c0,0-0.779,8.099,0.088,8.506c1.133,0.555,1.751-1.047,2.262-8.135c0,0,0.524-2.289,0.767,6.448' +
  'c0.012,0.451,0.673,2.698,1.596,0.78c0.779-1.608,0.429-5.864,0.429-7.295c0,0,0.999,5.522,1.933,5.522' +
  'c0,0,1.099,1.291,0.648-5.571c-0.073-1.121,0.32-3.422,0.369-4.092l0.106-2.631c0,0-0.274-3.014-0.274-4.269' +
  'c0-0.311,1.078-4.415,3.921-8.747c0,0,5.913-10.488,5.532-17.342c0,0-0.082-6.54,2.299-10.245' +
  'c0,0,1.69,18.526,0.545,23.727c0,0-5.319,12.778-4.146,22.308c0.864,7.094,2.53,22.237,4.226,28.217' +
  'c0.886,3.094,0.362,10.899,1.072,12.848c0.32,0.847,0.152,1.627-0.536,3.545c-2.387,6.71-2.083,11.436,3.921,29.24' +
  'c0,0,1.848,3.945,0.914,11.033c0,0-3.836,7.892-1.379,8.05c0,0,0.192,0.523,1.023,0.109c0,0,1.327,1.37,2.761,0.627' +
  'c0,0,1.328,1.06,2.463,0.116c0,0,0.91,1.047,2.237,0.201c0,0,1.742,1.175,2.777-0.098c0,0,1.839,0.408-1.435-7.886' +
  'c0,0-1.254-8.793-1.945-10.522c-1.318-3.275-0.387-12.251-0.106-14.175c0.453-3.216,0.21-8.695-0.618-12.934' +
  'c-0.606-3.038,1.035-8.774,1.641-12.3c1.245-7.423,3.685-26.373,3.38-29.959l1.008,0.354' +
  'C103.809,118.312,104.265,117.959,104.265,117.959z'

interface Props {
  match: EventMatch
  eventDate?: string | null
}

function formatControlTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

function getMethodBadgeVariant(method: string | null): 'ko' | 'submission' | 'decision' | 'draw' | 'canceled' {
  if (!method) return 'canceled'
  const m = method.toLowerCase()
  if (m.includes('ko') || m.includes('tko')) return 'ko'
  if (m.includes('sub')) return 'submission'
  if (m.includes('dec')) return 'decision'
  return 'canceled'
}

function isNcOrCanceled(result: string | null, method: string | null, eventDate?: string | null): 'canceled' | 'nc' | false {
  if (method?.toUpperCase() === 'CNC') return 'canceled'
  if (result?.toLowerCase() === 'nc') return 'nc'
  if (!result && !method && eventDate && new Date(eventDate) < new Date()) return 'canceled'
  return false
}

function getResultStyle(result: string | null): string {
  if (!result) return 'text-zinc-100'
  const r = result.toLowerCase()
  if (r === 'win') return 'text-zinc-100 font-semibold'
  if (r === 'loss') return 'text-zinc-500'
  if (r === 'nc') return 'text-zinc-500'
  return 'text-zinc-100'
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

const COMPARISON_STATS = [
  { label: 'SIG. STRIKES', format: (s: BasicMatchStat) => `${s.sig_str_attempted > 0 ? Math.round((s.sig_str_landed / s.sig_str_attempted) * 100) : 0}%(${s.sig_str_landed}/${s.sig_str_attempted})`, value: (s: BasicMatchStat) => s.sig_str_attempted > 0 ? s.sig_str_landed / s.sig_str_attempted : 0 },
  { label: 'TOTAL STRIKES', format: (s: BasicMatchStat) => `${s.total_str_attempted > 0 ? Math.round((s.total_str_landed / s.total_str_attempted) * 100) : 0}%(${s.total_str_landed}/${s.total_str_attempted})`, value: (s: BasicMatchStat) => s.total_str_attempted > 0 ? s.total_str_landed / s.total_str_attempted : 0 },
  { label: 'KNOCKDOWNS', format: (s: BasicMatchStat) => `${s.knockdowns}`, value: (s: BasicMatchStat) => s.knockdowns },
  { label: 'TAKEDOWNS', format: (s: BasicMatchStat) => `${s.td_landed}/${s.td_attempted}`, value: (s: BasicMatchStat) => s.td_landed },
  { label: 'SUB. ATTEMPTS', format: (s: BasicMatchStat) => `${s.submission_attempts}`, value: (s: BasicMatchStat) => s.submission_attempts },
  { label: 'CTRL TIME', format: (s: BasicMatchStat) => formatControlTime(s.control_time_seconds), value: (s: BasicMatchStat) => s.control_time_seconds },
]

function resultColor(result: string | null): { bar: string; hex: string; text: string } {
  if (result?.toLowerCase() === 'win') return { bar: 'bg-emerald-500/80', hex: '#10b981cc', text: 'text-emerald-400/80' }
  if (result?.toLowerCase() === 'loss') return { bar: 'bg-red-500/40', hex: '#ef444466', text: 'text-red-400/40' }
  if (result?.toLowerCase() === 'nc') return { bar: 'bg-amber-500/40', hex: '#f59e0b66', text: 'text-amber-400/40' }
  return { bar: 'bg-zinc-500/80', hex: '#71717acc', text: 'text-zinc-400/80' }
}

function StatBars({ leftStats, rightStats, leftResult, rightResult }: { leftStats: BasicMatchStat; rightStats: BasicMatchStat; leftResult?: string | null; rightResult?: string | null }) {
  const lColor = resultColor(leftResult ?? null)
  const rColor = resultColor(rightResult ?? null)

  return (
    <div className="space-y-3">
      {COMPARISON_STATS.map((row) => {
        const lv = row.value(leftStats)
        const rv = row.value(rightStats)
        const maxVal = Math.max(lv, rv, 1)
        const lPct = (lv / maxVal) * 100
        const rPct = (rv / maxVal) * 100
        const lHigher = lv > rv
        const rHigher = rv > lv

        return (
          <div key={row.label}>
            <p className="mb-1 text-center text-[10px] uppercase tracking-wider text-zinc-500">
              {row.label}
            </p>
            <div className="flex items-center gap-2">
              <span className={`w-16 shrink-0 text-right text-xs ${lHigher ? `font-semibold ${lColor.text}` : 'text-zinc-500'}`}>
                {row.format(leftStats)}
              </span>
              <div className="flex flex-1 gap-0.5">
                <div className="relative h-[18px] flex-1 overflow-hidden rounded-l bg-white/[0.06]">
                  <div
                    className={`absolute right-0 top-0 h-full rounded-l-sm transition-all duration-700 ease-out ${lHigher ? lColor.bar : 'bg-zinc-600/50'}`}
                    style={{ width: `${lPct}%` }}
                  />
                </div>
                <div className="relative h-[18px] flex-1 overflow-hidden rounded-r bg-white/[0.06]">
                  <div
                    className={`absolute left-0 top-0 h-full rounded-r-sm transition-all duration-700 ease-out ${rHigher ? rColor.bar : 'bg-zinc-600/50'}`}
                    style={{ width: `${rPct}%` }}
                  />
                </div>
              </div>
              <span className={`w-16 shrink-0 text-left text-xs ${rHigher ? `font-semibold ${rColor.text}` : 'text-zinc-500'}`}>
                {row.format(rightStats)}
              </span>
            </div>
          </div>
        )
      })}
    </div>
  )
}

function resultBadgeVariant(result: string | null): 'win' | 'loss' | 'draw' {
  if (result?.toLowerCase() === 'win') return 'win'
  if (result?.toLowerCase() === 'loss') return 'loss'
  return 'draw'
}

const PHYSICAL_STATS = [
  {
    label: 'HEIGHT',
    getValue: (f: EventFighterStat) => f.height_cm,
    format: (v: number) => `${v}`,
    unit: 'cm',
  },
  {
    label: 'REACH',
    getValue: (f: EventFighterStat) => f.reach_cm,
    format: (v: number) => `${v}`,
    unit: 'cm',
  },
]

function PhysicalComparison({ left, right }: { left: EventFighterStat; right: EventFighterStat }) {
  const hasAnyPhysical = PHYSICAL_STATS.some((s) => s.getValue(left) || s.getValue(right))
  const hasStance = left.stance || right.stance
  if (!hasAnyPhysical && !hasStance) return null

  const lColor = resultColor(left.result)
  const rColor = resultColor(right.result)

  return (
    <div className="grid grid-cols-3 gap-x-2">
      {PHYSICAL_STATS.map((row) => {
        const lv = row.getValue(left)
        const rv = row.getValue(right)
        if (!lv && !rv) return null
        const lHigher = lv != null && rv != null && lv > rv
        const rHigher = lv != null && rv != null && rv > lv

        return (
          <div key={row.label} className="flex flex-col items-center gap-1">
            <p className="text-[10px] uppercase tracking-wider text-zinc-500">
              {row.label}
            </p>
            <div className="flex items-baseline gap-1.5">
              <span className={`text-lg font-bold ${lHigher ? lColor.text : 'text-zinc-300'}`}>
                {lv != null ? row.format(lv) : '—'}
              </span>
              <span className="text-[10px] text-zinc-600">vs</span>
              <span className={`text-lg font-bold ${rHigher ? rColor.text : 'text-zinc-300'}`}>
                {rv != null ? row.format(rv) : '—'}
              </span>
            </div>
            <p className="text-[10px] text-zinc-600">{row.unit}</p>
          </div>
        )
      })}
      {hasStance && (
        <div className="flex flex-col items-center gap-1">
          <p className="text-[10px] uppercase tracking-wider text-zinc-500">
            STANCE
          </p>
          <div className="flex items-baseline gap-1.5">
            <span className="text-sm font-bold text-zinc-300">
              {left.stance ?? '—'}
            </span>
            <span className="text-[10px] text-zinc-600">vs</span>
            <span className="text-sm font-bold text-zinc-300">
              {right.stance ?? '—'}
            </span>
          </div>
        </div>
      )}
    </div>
  )
}

function BodySilhouette({ stats, side }: { stats: StrikeStats; side: 'left' | 'right' }) {
  const clipId = useId()
  const headLanded = stats.head_strikes_landed
  const bodyLanded = stats.body_strikes_landed
  const legLanded = stats.leg_strikes_landed
  const total = headLanded + bodyLanded + legLanded

  const headPct = total > 0 ? Math.round((headLanded / total) * 100) : 0
  const bodyPct = total > 0 ? Math.round((bodyLanded / total) * 100) : 0
  const legPct = total > 0 ? 100 - headPct - bodyPct : 0

  const zones = [
    { pct: headPct, count: headLanded, color: '#ef4444', top: '8%' },
    { pct: bodyPct, count: bodyLanded, color: '#f59e0b', top: '38%' },
    { pct: legPct, count: legLanded, color: '#06b6d4', top: '76%' },
  ]

  return (
    <div className={`flex items-start ${side === 'right' ? 'flex-row-reverse' : ''}`}>
      {/* Labels */}
      <div className="relative h-[160px] w-12 shrink-0">
        {zones.map((z) => (
          <div
            key={z.color}
            className={`absolute w-full -translate-y-1/2 ${side === 'left' ? 'text-right' : 'text-left'}`}
            style={{ top: z.top }}
          >
            <p className="text-sm font-bold" style={{ color: z.color }}>{z.pct}%</p>
            <p className="text-[9px] text-zinc-500">({z.count})</p>
          </div>
        ))}
      </div>

      {/* Silhouette */}
      <svg viewBox="0 0 206.326 206.326" className="h-[160px] w-auto shrink-0">
        <defs>
          <clipPath id={clipId}>
            <path d={SILHOUETTE_PATH} />
          </clipPath>
        </defs>

        <rect x="0" y="0" width="206.326" height="30"
          clipPath={`url(#${clipId})`}
          fill={headPct > 0 ? '#ef4444' : '#3f3f46'}
          opacity={headPct > 0 ? 0.85 : 0.3}
        />
        <rect x="0" y="30" width="206.326" height="100"
          clipPath={`url(#${clipId})`}
          fill={bodyPct > 0 ? '#f59e0b' : '#3f3f46'}
          opacity={bodyPct > 0 ? 0.85 : 0.3}
        />
        <rect x="0" y="130" width="206.326" height="76.326"
          clipPath={`url(#${clipId})`}
          fill={legPct > 0 ? '#06b6d4' : '#3f3f46'}
          opacity={legPct > 0 ? 0.85 : 0.3}
        />

        <line x1="0" y1="30" x2="206.326" y2="30"
          stroke="rgba(0,0,0,0.4)" strokeWidth="1"
          clipPath={`url(#${clipId})`}
        />
        <line x1="0" y1="130" x2="206.326" y2="130"
          stroke="rgba(0,0,0,0.4)" strokeWidth="1"
          clipPath={`url(#${clipId})`}
        />
      </svg>
    </div>
  )
}

function StrikeTargetComparison({ left, right }: { left: EventFighterStat; right: EventFighterStat }) {
  const ls = left.strike_stats
  const rs = right.strike_stats
  if (!ls || !rs) return null

  const lColor = resultColor(left.result)
  const rColor = resultColor(right.result)
  const lTotal = ls.head_strikes_landed + ls.body_strikes_landed + ls.leg_strikes_landed
  const rTotal = rs.head_strikes_landed + rs.body_strikes_landed + rs.leg_strikes_landed
  const diff = lTotal - rTotal

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-center gap-3">
        <p className="text-[10px] uppercase tracking-wider text-zinc-500">Target Distribution</p>
        <div className="flex items-center gap-2 text-[9px] text-zinc-500">
          <span className="flex items-center gap-1"><span className="inline-block h-1.5 w-1.5 rounded-full bg-[#ef4444]" />Head</span>
          <span className="flex items-center gap-1"><span className="inline-block h-1.5 w-1.5 rounded-full bg-[#f59e0b]" />Body</span>
          <span className="flex items-center gap-1"><span className="inline-block h-1.5 w-1.5 rounded-full bg-[#06b6d4]" />Leg</span>
        </div>
      </div>

      <div className="flex items-start justify-center gap-4">
        <BodySilhouette stats={ls} side="left" />
        <BodySilhouette stats={rs} side="right" />
      </div>

      {/* Total summary */}
      <div className="flex items-stretch gap-2">
        <div className="flex-1 text-center">
          <p className={`text-xl font-bold ${lColor.text}`}>{lTotal}</p>
          <p className="text-[10px] text-zinc-500">Total Landed</p>
        </div>
        <div className="flex flex-col items-center justify-center border-x border-white/[0.06] px-4">
          <p className={`text-sm font-bold ${diff > 0 ? lColor.text : diff < 0 ? rColor.text : 'text-zinc-400'}`}>
            {toTitleCase(diff > 0 ? left.name : diff < 0 ? right.name : '')} {diff !== 0 ? `+${Math.abs(diff)}` : 'Even'}
          </p>
          <p className="text-[10px] text-zinc-500">Difference</p>
        </div>
        <div className="flex-1 text-center">
          <p className={`text-xl font-bold ${rColor.text}`}>{rTotal}</p>
          <p className="text-[10px] text-zinc-500">Total Landed</p>
        </div>
      </div>
    </div>
  )
}

function ComparisonView({ match }: { match: EventMatch }) {
  const [roundExpanded, setRoundExpanded] = useState(false)
  const [left, right] = match.fighters

  const rounds = left.round_stats && right.round_stats
    ? [...new Set([...left.round_stats.map((r) => r.round), ...right.round_stats.map((r) => r.round)])].sort((a, b) => a - b)
    : []
  const hasRounds = rounds.length > 1

  return (
    <div className="space-y-3">
      {/* Fighter header */}
      <div className="flex justify-center gap-8">
        <div className="flex items-center gap-2">
          {left.result && (
            <Badge variant={resultBadgeVariant(left.result)} className="text-[10px]">
              {left.result.toUpperCase()}
            </Badge>
          )}
          <span className="text-sm font-semibold text-zinc-200">{toTitleCase(left.name)}</span>
          {left.ranking != null && (
            <span className="text-[10px] text-zinc-500">#{left.ranking}</span>
          )}
        </div>
        <span className="shrink-0 px-8 text-xs text-zinc-600">VS</span>
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-zinc-200">{toTitleCase(right.name)}</span>
          {right.ranking != null && (
            <span className="text-[10px] text-zinc-500">#{right.ranking}</span>
          )}
          {right.result && (
            <Badge variant={resultBadgeVariant(right.result)} className="text-[10px]">
              {right.result.toUpperCase()}
            </Badge>
          )}
        </div>
      </div>

      {/* Physical comparison */}
      <PhysicalComparison left={left} right={right} />
      <div className="border-t border-white/[0.06]" />

      {/* Aggregate stat bars */}
      <StatBars leftStats={left.stats!} rightStats={right.stats!} leftResult={left.result} rightResult={right.result} />
      <div className="border-t border-white/[0.06]" />

      {/* Strike target comparison + Total Landed */}
      <StrikeTargetComparison left={left} right={right} />
      {left.strike_stats && right.strike_stats && (
        <div className="border-t border-white/[0.06]" />
      )}

      {/* Round-by-Round charts */}
      {hasRounds && (() => {
        const leftName = toTitleCase(left.name)
        const rightName = toTitleCase(right.name)
        const lc = resultColor(left.result)
        const rc = resultColor(right.result)
        const sigData = rounds.map((r) => ({
          round: `R${r}`,
          [leftName]: left.round_stats?.find((s) => s.round === r)?.sig_str_landed ?? 0,
          [rightName]: right.round_stats?.find((s) => s.round === r)?.sig_str_landed ?? 0,
        }))
        const ctrlData = rounds.map((r) => ({
          round: `R${r}`,
          [leftName]: left.round_stats?.find((s) => s.round === r)?.control_time_seconds ?? 0,
          [rightName]: right.round_stats?.find((s) => s.round === r)?.control_time_seconds ?? 0,
        }))
        const isTitleFight = rounds.length >= 5
        const tooltipStyle = {
          contentStyle: { backgroundColor: '#18181b', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 8, fontSize: 12 },
          itemStyle: { color: '#d4d4d8' },
          labelStyle: { color: '#a1a1aa', fontSize: 11 },
        }

        return (
          <div className={`grid gap-3 ${isTitleFight ? 'grid-cols-1' : 'grid-cols-1 sm:grid-cols-2'}`}>
            {/* Sig. Strikes line chart */}
            <div className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-4">
              <p className="text-xs font-semibold text-zinc-200">Round-by-Round Sig. Strikes</p>
              <p className="mb-3 text-[10px] text-zinc-500">Sig. strikes landed per round</p>
              <ResponsiveContainer width="100%" height={180}>
                <LineChart data={sigData} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
                  <CartesianGrid stroke="rgba(255,255,255,0.04)" vertical={false} />
                  <XAxis dataKey="round" tick={{ fill: '#71717a', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: '#a1a1aa', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip {...tooltipStyle} />
                  <Legend iconType="circle" iconSize={6} wrapperStyle={{ fontSize: 11, color: '#a1a1aa' }} />
                  <Line type="monotone" dataKey={leftName} stroke={lc.hex} strokeWidth={2} dot={{ r: 3, fill: lc.hex, strokeWidth: 0 }} activeDot={{ r: 4, strokeWidth: 0 }} />
                  <Line type="monotone" dataKey={rightName} stroke={rc.hex} strokeWidth={2} dot={{ r: 3, fill: rc.hex, strokeWidth: 0 }} activeDot={{ r: 4, strokeWidth: 0 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Control Time line chart */}
            <div className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-4">
              <p className="text-xs font-semibold text-zinc-200">Round-by-Round Control Time</p>
              <p className="mb-3 text-[10px] text-zinc-500">Control time per round (seconds)</p>
              <ResponsiveContainer width="100%" height={180}>
                <LineChart data={ctrlData} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
                  <CartesianGrid stroke="rgba(255,255,255,0.04)" vertical={false} />
                  <XAxis dataKey="round" tick={{ fill: '#71717a', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: '#a1a1aa', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(v: number) => `${Math.floor(v / 60)}:${(v % 60).toString().padStart(2, '0')}`} />
                  <Tooltip
                    {...tooltipStyle}
                    formatter={(value: number) => [`${Math.floor(value / 60)}:${(value % 60).toString().padStart(2, '0')}`, undefined]}
                  />
                  <Legend iconType="circle" iconSize={6} wrapperStyle={{ fontSize: 11, color: '#a1a1aa' }} />
                  <Line type="monotone" dataKey={leftName} stroke={lc.hex} strokeWidth={2} dot={{ r: 3, fill: lc.hex, strokeWidth: 0 }} activeDot={{ r: 4, strokeWidth: 0 }} />
                  <Line type="monotone" dataKey={rightName} stroke={rc.hex} strokeWidth={2} dot={{ r: 3, fill: rc.hex, strokeWidth: 0 }} activeDot={{ r: 4, strokeWidth: 0 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )
      })()}

      {/* Round-by-round toggle */}
      {hasRounds && (
        <>
          <button
            type="button"
            className="flex w-full items-center justify-center gap-1 rounded-lg py-1.5 text-[11px] text-zinc-500 transition-colors hover:bg-white/[0.04] hover:text-zinc-300"
            onClick={() => setRoundExpanded(!roundExpanded)}
          >
            <ChevronDown className={`h-3 w-3 transition-transform ${roundExpanded ? 'rotate-180' : ''}`} />
            {roundExpanded ? 'Hide round details' : `Show round details (${rounds.length}R)`}
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
                <div className="space-y-3">
                  {rounds.map((roundNum) => {
                    const lrs = left.round_stats?.find((r) => r.round === roundNum)
                    const rrs = right.round_stats?.find((r) => r.round === roundNum)
                    if (!lrs || !rrs) return null
                    return (
                      <div key={roundNum} className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-3">
                        <p className="mb-2 text-center text-[10px] font-semibold uppercase tracking-wider text-zinc-400">
                          Round {roundNum}
                        </p>
                        <StatBars leftStats={lrs} rightStats={rrs} leftResult={left.result} rightResult={right.result} />
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
  )
}

export function FightCard({ match, eventDate }: Props) {
  const [expanded, setExpanded] = useState(false)

  const hasStats = match.fighters.some((f) => f.stats)
  const ncStatus = isNcOrCanceled(match.fighters[0]?.result ?? null, match.method, eventDate)

  return (
    <div className="rounded-xl border border-white/[0.06] bg-white/[0.03] transition-all duration-300 ease-out hover:border-white/[0.12] hover:bg-white/[0.05]">
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
              {match.is_main_event && (
                <Badge variant="champion" className="text-[10px]">MAIN</Badge>
              )}
              {match.weight_class && (
                <span className="font-medium text-zinc-400">
                  {toTitleCase(match.weight_class)}
                </span>
              )}
              {ncStatus === 'canceled' ? (
                <Badge variant="canceled" className="text-[10px]">
                  <AlertTriangle className="h-2.5 w-2.5" />
                  Canceled
                </Badge>
              ) : ncStatus === 'nc' ? (
                <Badge variant="canceled" className="text-[10px]">
                  NC — {match.method ?? 'No Contest'}
                </Badge>
              ) : match.method ? (
                <Badge variant={getMethodBadgeVariant(match.method)} className="text-[10px]">
                  {match.method}
                </Badge>
              ) : null}
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
                    className={`transition-colors hover:text-blue-400 hover:underline ${ncStatus ? 'text-zinc-500' : getResultStyle(fighter.result)}`}
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
            <div className="border-t border-white/[0.06] px-8 pb-4 pt-3 sm:px-10">
              {/* Comparison view (2 fighters with stats) or fallback */}
              {match.fighters.length === 2 && match.fighters[0].stats && match.fighters[1].stats ? (
                <ComparisonView match={match} />
              ) : (
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
                            <span className="ml-2">({fighter.result})</span>
                          )}
                        </p>
                        <div className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-3 text-xs">
                          <FighterStats stats={fighter.stats} />
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
