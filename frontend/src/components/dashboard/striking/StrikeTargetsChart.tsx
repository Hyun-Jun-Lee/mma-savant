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

interface StrikeTargetsChartProps {
  data: StrikeTarget[]
}

export function StrikeTargetsChart({ data }: StrikeTargetsChartProps) {
  const total = data.reduce((sum, d) => sum + d.landed, 0)

  return (
    <ResponsiveContainer width="100%" height={280}>
      <RadarChart data={data} cx="50%" cy="50%" outerRadius="75%">
        <PolarGrid stroke="rgba(255,255,255,0.06)" />
        <PolarAngleAxis
          dataKey="target"
          tick={{ fill: '#a1a1aa', fontSize: 11 }}
        />
        <PolarRadiusAxis tick={false} axisLine={false} />
        <Radar
          dataKey="landed"
          stroke="#8b5cf6"
          fill="#8b5cf6"
          fillOpacity={0.25}
          strokeWidth={2}
          name="Landed"
        />
        <Tooltip
          contentStyle={{
            backgroundColor: '#18181b',
            border: '1px solid rgba(255,255,255,0.06)',
            borderRadius: '8px',
            fontSize: '12px',
          }}
          itemStyle={{ color: '#e4e4e7' }}
          labelStyle={{ color: '#a1a1aa' }}
          formatter={(value: number) => {
            const pct = total > 0 ? ((value / total) * 100).toFixed(1) : '0.0'
            return [`${value.toLocaleString()} (${pct}%)`, 'Landed']
          }}
        />
      </RadarChart>
    </ResponsiveContainer>
  )
}
