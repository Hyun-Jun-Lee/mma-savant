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
  LabelList,
  Cell,
} from 'recharts'
import { ChevronDown } from 'lucide-react'
import { toTitleCase } from '@/lib/utils'
import type { KoTkoLeader } from '@/types/dashboard'
import { ChartTooltip } from '../ChartTooltip'

interface KoTkoLeadersChartProps {
  data: KoTkoLeader[]
}

export function KoTkoLeadersChart({ data }: KoTkoLeadersChartProps) {
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
    <ResponsiveContainer width="100%" height={expanded ? Math.max(320, displayData.length * 34) : 180}>
      <BarChart
        data={displayData}
        layout="vertical"
        margin={{ top: 5, right: 40, left: 10, bottom: 0 }}
      >
        <XAxis
          type="number"
          tick={{ fill: '#52525b', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          dataKey="name"
          type="category"
          tick={<FighterTick />}
          axisLine={false}
          tickLine={false}
          width={100}
          interval={0}
        />
        <Tooltip
          cursor={false}
          content={({ active, payload, label }) => {
            if (!active || !payload?.length) return null
            const d = payload[0]?.payload as KoTkoLeader
            return (
              <ChartTooltip active={active} label={label}>
                <p className="text-zinc-400">KO/TKO Finishes: {d.ko_tko_finishes}</p>
              </ChartTooltip>
            )
          }}
        />
        <Bar
          dataKey="ko_tko_finishes"
          fill="#ef4444"
          radius={[0, 4, 4, 0]}
          barSize={16}
          name="KO/TKO"
          animationBegin={500}
          animationDuration={1200}
          animationEasing="ease-out"
        >
          <LabelList
            dataKey="ko_tko_finishes"
            position="right"
            style={{ fill: '#a1a1aa', fontSize: 11 }}
          />
          {displayData.map((_, i) => (
            <Cell
              key={i}
              fill="#ef4444"
              fillOpacity={Math.max(0.2, 1 - i * 0.13)}
            />
          ))}
        </Bar>
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
