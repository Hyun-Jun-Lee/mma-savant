'use client'

import { useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { ChevronDown } from 'lucide-react'
import { toTitleCase } from '@/lib/utils'
import { PillTabs, TabContent } from '../PillTabs'
import type { MinFightsLeaderboard, StrikeExchange } from '@/types/dashboard'

const TABS = [
  { key: 'min20', label: '20+ Fights' },
  { key: 'min15', label: '15+ Fights' },
  { key: 'min10', label: '10+ Fights' },
] as const

type MinKey = (typeof TABS)[number]['key']

interface StrikeExchangeChartProps {
  data: MinFightsLeaderboard<StrikeExchange>
}

interface BulletRowProps {
  fighter: StrikeExchange
  maxValue: number
  onNavigate: (id: number) => void
}

function BulletRow({ fighter, maxValue, onNavigate }: BulletRowProps) {
  const { name, fighter_id, sig_landed_per_fight, sig_absorbed_per_fight, differential_per_fight } = fighter
  const pct = (v: number) => `${(v / maxValue) * 100}%`
  const diffSign = differential_per_fight >= 0 ? '+' : ''
  const diffColor = differential_per_fight >= 0 ? '#10b981' : '#ef4444'

  return (
    <div className="group flex items-center gap-2 py-[7px]">
      {/* Fighter name */}
      <div className="w-[100px] shrink-0 overflow-hidden">
        <span
          className="block cursor-pointer truncate text-[11px] leading-tight text-zinc-400 transition-colors group-hover:text-blue-400"
          onClick={() => onNavigate(fighter_id)}
        >
          {toTitleCase(name)}
        </span>
      </div>

      {/* Bullet chart — single row */}
      <div className="relative h-[18px] flex-1">
        {/* Taken background bar */}
        <div
          className="absolute inset-y-0 left-0 rounded-r"
          style={{
            width: pct(sig_absorbed_per_fight),
            backgroundColor: 'rgba(239, 68, 68, 0.15)',
          }}
        />
        {/* Landed foreground bar */}
        <div
          className="absolute inset-y-0 left-0 rounded-r"
          style={{
            width: pct(sig_landed_per_fight),
            backgroundColor: '#f59e0b',
          }}
        />
        {/* Landed value inside bar */}
        <span
          className="absolute inset-y-0 flex items-center text-[9px] font-medium text-zinc-950"
          style={{ left: pct(sig_landed_per_fight), transform: 'translateX(-30px)' }}
        >
          {sig_landed_per_fight.toFixed(1)}
        </span>
        {/* Differential at right end of longer bar */}
        <span
          className="absolute inset-y-0 flex items-center text-[10px] font-semibold"
          style={{
            left: pct(Math.max(sig_landed_per_fight, sig_absorbed_per_fight)),
            transform: 'translateX(6px)',
            color: diffColor,
          }}
        >
          {diffSign}{differential_per_fight.toFixed(1)}
        </span>
        {/* Taken marker line */}
        <div
          className="absolute inset-y-[-2px]"
          style={{
            left: pct(sig_absorbed_per_fight),
            width: '2px',
            backgroundColor: '#ef4444',
          }}
        />
        {/* Taken value next to marker */}
        <span
          className="absolute inset-y-0 flex items-center text-[9px] font-bold"
          style={{
            left: pct(sig_absorbed_per_fight),
            transform: 'translateX(5px)',
            color: '#ef4444',
          }}
        >
          {sig_absorbed_per_fight.toFixed(1)}
        </span>
      </div>

    </div>
  )
}

export function StrikeExchangeChart({ data }: StrikeExchangeChartProps) {
  const router = useRouter()
  const [activeKey, setActiveKey] = useState<MinKey>('min20')
  const [expanded, setExpanded] = useState(false)
  const fighters = data[activeKey]
  const displayFighters = expanded ? fighters : fighters.slice(0, 5)

  const rawMax = Math.max(
    ...displayFighters.map((f) => Math.max(f.sig_landed_per_fight, f.sig_absorbed_per_fight)),
    1,
  )
  const maxValue = rawMax * 1.06

  const handleNavigate = useCallback(
    (id: number) => router.push(`/fighters/${id}`),
    [router],
  )

  return (
    <div>
      <div className="mb-3">
        <PillTabs
          tabs={[...TABS]}
          activeKey={activeKey}
          onChange={(k) => setActiveKey(k as MinKey)}
          size="sm"
        />
      </div>
      <TabContent activeKey={activeKey}>
        {/* X-axis scale */}
        <div className="mb-1 flex items-end pl-[108px] pr-[8px]">
          {[0, Math.round(maxValue * 0.25), Math.round(maxValue * 0.5), Math.round(maxValue * 0.75), Math.round(maxValue)].map((v) => (
            <span
              key={v}
              className="flex-1 text-left text-[10px] text-zinc-600"
            >
              {v}
            </span>
          ))}
        </div>

        {/* Rows */}
        <div>
          {displayFighters.map((f) => (
            <BulletRow
              key={f.fighter_id}
              fighter={f}
              maxValue={maxValue}
              onNavigate={handleNavigate}
            />
          ))}
        </div>

        {/* Legend */}
        <div className="mt-3 flex items-center justify-center gap-4 text-[10px] text-zinc-500">
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: '#f59e0b' }} />
            Landed / Fight
          </span>
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: '#ef4444' }} />
            Taken / Fight (marker)
          </span>
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: '#10b981' }} />
            Differential
          </span>
        </div>

        {fighters.length > 5 && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="mt-2 flex w-full items-center justify-center gap-1 rounded-lg py-1.5 text-xs text-zinc-500 transition-colors hover:bg-white/[0.04] hover:text-zinc-300"
          >
            <ChevronDown className={`h-3.5 w-3.5 transition-transform ${expanded ? 'rotate-180' : ''}`} />
            {expanded ? 'Show Less' : `Show All ${fighters.length}`}
          </button>
        )}
      </TabContent>
    </div>
  )
}
