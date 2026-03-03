'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { ChevronDown } from 'lucide-react'
import { toTitleCase } from '@/lib/utils'
import type { KnockdownLeader } from '@/types/dashboard'

interface KnockdownLeadersChartProps {
  data: KnockdownLeader[]
}

export function KnockdownLeadersChart({ data }: KnockdownLeadersChartProps) {
  const router = useRouter()
  const [expanded, setExpanded] = useState(false)
  const displayData = expanded ? data : data.slice(0, 5)

  const FighterTick = ({ x, y, payload }: { x?: number; y?: number; payload?: { value: string } }) => {
    const item = displayData.find((d) => d.name === payload?.value)
    return (
      <g transform={`translate(${x ?? 0},${y ?? 0})`}>
        <text
          x={-4}
          y={0}
          dy={4}
          textAnchor="end"
          fill="#a1a1aa"
          fontSize={11}
          style={{ cursor: 'pointer' }}
          onClick={() => item && router.push(`/fighters/${item.fighter_id}`)}
          onMouseEnter={(e) => { e.currentTarget.setAttribute('fill', '#60a5fa') }}
          onMouseLeave={(e) => { e.currentTarget.setAttribute('fill', '#a1a1aa') }}
        >
          {toTitleCase(payload?.value ?? '')}
        </text>
      </g>
    )
  }

  return (
    <>
    <ResponsiveContainer width="100%" height={expanded ? 320 : 180}>
      <BarChart
        data={displayData}
        layout="vertical"
        margin={{ top: 5, right: 30, left: 10, bottom: 0 }}
      >
        <XAxis
          type="number"
          tick={{ fill: '#52525b', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          allowDecimals={false}
        />
        <YAxis
          dataKey="name"
          type="category"
          tick={<FighterTick />}
          axisLine={false}
          tickLine={false}
          width={100}
        />
        <Tooltip
          content={({ active, payload, label }) => {
            if (!active || !payload?.length) return null
            const d = payload[0]?.payload as KnockdownLeader
            return (
              <div className="rounded-lg border border-white/[0.06] bg-zinc-900 px-3 py-2 text-xs shadow-lg">
                <p className="mb-1 font-medium text-zinc-200">{label}</p>
                <p className="text-zinc-400">Knockdowns: {d.total_knockdowns}</p>
                <p className="text-zinc-400">KD/Fight: {d.kd_per_fight.toFixed(2)}</p>
                <p className="text-zinc-400">Fights: {d.total_fights}</p>
              </div>
            )
          }}
        />
        <Bar
          dataKey="total_knockdowns"
          fill="#ef4444"
          radius={[0, 4, 4, 0]}
          barSize={16}
          name="Knockdowns"
          animationBegin={500}
          animationDuration={1200}
          animationEasing="ease-out"
        />
      </BarChart>
    </ResponsiveContainer>
    {data.length > 5 && (
      <button
        onClick={() => setExpanded(!expanded)}
        className="mt-2 flex w-full items-center justify-center gap-1 rounded-lg py-1.5 text-xs text-zinc-500 transition-colors hover:bg-white/[0.04] hover:text-zinc-300"
      >
        <ChevronDown className={`h-3.5 w-3.5 transition-transform ${expanded ? 'rotate-180' : ''}`} />
        {expanded ? 'Show Less' : `Show All ${data.length}`}
      </button>
    )}
    </>
  )
}
