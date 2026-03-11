'use client'

import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from 'recharts'
import type { StrikeTarget } from '@/types/dashboard'
import { ChartTooltip } from '../ChartTooltip'

interface StrikeTargetsChartProps {
  data: StrikeTarget[]
}

export function StrikeTargetsChart({ data }: StrikeTargetsChartProps) {
  const total = data.reduce((sum, d) => sum + d.landed, 0)

  const CustomTick = ({ x, y, payload, textAnchor }: {
    x?: number; y?: number; payload?: { value: string }; textAnchor?: string
  }) => {
    const target = payload?.value ?? ''
    const item = data.find((d) => d.target === target)
    const landed = item?.landed ?? 0
    const pct = total > 0 ? ((landed / total) * 100).toFixed(1) : '0.0'

    return (
      <g transform={`translate(${x ?? 0},${y ?? 0})`}>
        <text
          x={0}
          y={0}
          dy={-6}
          textAnchor={textAnchor ?? 'middle'}
          fill="#a1a1aa"
          fontSize={11}
        >
          {target}
        </text>
        <text
          x={0}
          y={0}
          dy={8}
          textAnchor={textAnchor ?? 'middle'}
          fill="#8b5cf6"
          fontSize={10}
          fontWeight={500}
        >
          {landed.toLocaleString()} ({pct}%)
        </text>
      </g>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={390}>
      <RadarChart data={data} cx="50%" cy="50%" outerRadius="80%">
        <PolarGrid stroke="rgba(255,255,255,0.06)" />
        <PolarAngleAxis
          dataKey="target"
          tick={<CustomTick />}
        />
        <PolarRadiusAxis tick={false} axisLine={false} />
        <Radar
          dataKey="landed"
          stroke="#8b5cf6"
          fill="#8b5cf6"
          fillOpacity={0.25}
          strokeWidth={2}
          name="Landed"
          animationBegin={500}
          animationDuration={1200}
          animationEasing="ease-out"
        />
        <Tooltip
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null
            const d = payload[0]?.payload as { target: string; landed: number }
            const pct = total > 0 ? ((d.landed / total) * 100).toFixed(1) : '0.0'
            return (
              <ChartTooltip active={active} label={d.target}>
                <p className="text-zinc-400">Landed: {d.landed.toLocaleString()}</p>
                <p className="text-zinc-400">Share: {pct}%</p>
              </ChartTooltip>
            )
          }}
        />
      </RadarChart>
    </ResponsiveContainer>
  )
}
