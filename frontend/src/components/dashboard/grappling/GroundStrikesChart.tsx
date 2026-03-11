'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { ChevronDown } from 'lucide-react'
import { toTitleCase } from '@/lib/utils'
import type { GroundStrikesLeader } from '@/types/dashboard'

interface GroundStrikesChartProps {
  data: GroundStrikesLeader[]
}

function DonutRing({ pct, color, size = 52 }: { pct: number; color: string; size?: number }) {
  const r = (size - 6) / 2
  const c = 2 * Math.PI * r
  const filled = (pct / 100) * c

  return (
    <svg width={size} height={size} className="shrink-0">
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#27272a" strokeWidth={5} />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        fill="none"
        stroke={color}
        strokeWidth={5}
        strokeDasharray={`${filled} ${c - filled}`}
        strokeDashoffset={c * 0.25}
        strokeLinecap="round"
        className="transition-all duration-700"
      />
      <text
        x={size / 2}
        y={size / 2}
        textAnchor="middle"
        dominantBaseline="central"
        fill="#e4e4e7"
        fontSize={11}
        fontWeight={600}
      >
        {pct.toFixed(1)}%
      </text>
    </svg>
  )
}

export function GroundStrikesChart({ data }: GroundStrikesChartProps) {
  const router = useRouter()
  const [expanded, setExpanded] = useState(false)

  const sorted = [...data].sort((a, b) => b.accuracy - a.accuracy)
  const visible = expanded ? sorted.slice(0, 10) : sorted.slice(0, 5)

  return (
    <div className="flex flex-col">
      <div className="divide-y divide-white/[0.04]">
        {visible.map((f, i) => (
          <div
            key={f.fighter_id}
            className="group flex items-center gap-3 px-3 py-2.5 transition-colors hover:bg-white/[0.03]"
          >
            {/* Rank */}
            <span className="w-5 shrink-0 text-center text-xs font-semibold text-zinc-500">
              {i + 1}
            </span>

            {/* Donut */}
            <DonutRing pct={f.accuracy} color="#10b981" />

            {/* Name + Stats */}
            <div className="min-w-0 flex-1">
              <button
                onClick={() => router.push(`/fighters/${f.fighter_id}`)}
                className="truncate text-sm font-medium text-zinc-200 transition-colors hover:text-blue-400"
              >
                {toTitleCase(f.name)}
              </button>
              <div className="mt-0.5 flex items-center gap-3 text-[11px]">
                <span>
                  <span className="font-medium text-emerald-400">{f.total_ground_landed}</span>
                  <span className="ml-1 text-zinc-500">landed</span>
                </span>
                <span>
                  <span className="font-medium text-zinc-400">{f.total_ground_attempted}</span>
                  <span className="ml-1 text-zinc-500">attempted</span>
                </span>
              </div>
            </div>

            {/* Percentage badge */}
            <span className="shrink-0 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2 py-0.5 text-[11px] font-medium text-emerald-400">
              {f.accuracy.toFixed(1)}%
            </span>
          </div>
        ))}
      </div>

      {sorted.length > 5 && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-2 flex w-full items-center justify-center gap-1 rounded-lg py-1.5 text-xs text-zinc-500 transition-colors hover:bg-white/[0.04] hover:text-zinc-300"
        >
          <ChevronDown className={`h-3.5 w-3.5 transition-transform ${expanded ? 'rotate-180' : ''}`} />
          {expanded ? 'Show Less' : `Show All ${sorted.length}`}
        </button>
      )}
    </div>
  )
}
