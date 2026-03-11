'use client'

import { useMemo } from 'react'
import { useRouter } from 'next/navigation'
import { toTitleCase } from '@/lib/utils'
import type { TdSubCorrelation, TdSubCorrelationFighter } from '@/types/dashboard'

interface TdSubCorrelationChartProps {
  data: TdSubCorrelation
}

const QUADRANT_CONFIG = [
  { key: 'high_td_high_sub', title: 'TD\u2191 SUB\u2191', titleColor: 'text-emerald-400' },
  { key: 'high_td_low_sub', title: 'TD\u2191 SUB\u2193', titleColor: 'text-blue-400' },
  { key: 'low_td_high_sub', title: 'TD\u2193 SUB\u2191', titleColor: 'text-purple-400' },
  { key: 'low_td_low_sub', title: 'TD\u2193 SUB\u2193', titleColor: 'text-zinc-500' },
] as const

function HeatCell({
  value,
  maxVal,
  color,
  label,
}: {
  value: number
  maxVal: number
  color: 'emerald' | 'purple'
  label: string
}) {
  const intensity = maxVal > 0 ? value / maxVal : 0
  const bgMap = {
    emerald: `rgba(16, 185, 129, ${0.3 + intensity * 0.4})`,
    purple: `rgba(168, 85, 247, ${0.3 + intensity * 0.4})`,
  }

  return (
    <div
      className="flex h-10 w-12 flex-col items-center justify-center rounded-md"
      style={{ backgroundColor: bgMap[color] }}
    >
      <span className="text-xs font-semibold text-zinc-100">{value}</span>
      <span className="text-[8px] uppercase text-zinc-400">{label}</span>
    </div>
  )
}

export function TdSubCorrelationChart({ data }: TdSubCorrelationChartProps) {
  const router = useRouter()
  const { quadrants } = data

  const { maxTd, maxSub } = useMemo(() => {
    let mTd = 0
    let mSub = 0
    for (const key of Object.keys(quadrants)) {
      for (const f of quadrants[key]?.fighters ?? []) {
        if (f.total_td_landed > mTd) mTd = f.total_td_landed
        if (f.sub_finishes > mSub) mSub = f.sub_finishes
      }
    }
    return { maxTd: mTd, maxSub: mSub }
  }, [quadrants])

  return (
    <div className="grid grid-cols-2 gap-3">
      {QUADRANT_CONFIG.map((cfg) => {
        const q = quadrants[cfg.key]
        const fighters = q?.fighters ?? []
        const count = q?.count ?? 0

        return (
          <div
            key={cfg.key}
            className="rounded-lg border border-white/[0.06] bg-white/[0.02] px-4 py-3"
          >
            <div className="mb-2">
              <span className={`text-xs font-bold ${cfg.titleColor}`}>{cfg.title}</span>
            </div>
            <div className="space-y-2">
              {fighters.map((f: TdSubCorrelationFighter) => (
                <div key={f.fighter_id} className="flex items-center justify-between gap-2">
                  <button
                    onClick={() => router.push(`/fighters/${f.fighter_id}`)}
                    className="min-w-0 truncate text-xs text-zinc-300 transition-colors hover:text-blue-400"
                  >
                    {toTitleCase(f.name)}
                  </button>
                  <div className="flex shrink-0 items-center gap-1">
                    <HeatCell value={f.total_td_landed} maxVal={maxTd} color="emerald" label="TD" />
                    <HeatCell value={f.sub_finishes} maxVal={maxSub} color="purple" label="SUB" />
                  </div>
                </div>
              ))}
              {fighters.length === 0 && (
                <p className="text-[11px] text-zinc-600">No fighters</p>
              )}
            </div>
            {count > 0 && (
              <p className="mt-2 text-right text-[10px] text-zinc-600">
                {count} fighters
              </p>
            )}
          </div>
        )
      })}
    </div>
  )
}
