'use client'

import {
  ComposedChart,
  Bar,
  Scatter,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from 'recharts'
import type { SigStrikesLeader } from '@/types/dashboard'

interface SigStrikesChartProps {
  data: SigStrikesLeader[]
}

export function SigStrikesChart({ data }: SigStrikesChartProps) {
  const avg =
    data.length > 0
      ? data.reduce((sum, d) => sum + d.sig_str_per_fight, 0) / data.length
      : 0

  // dot 크기를 경기 수에 비례
  const scatterData = data.map((d) => ({
    ...d,
    dotSize: Math.max(30, Math.min(120, d.total_fights * 4)),
  }))

  return (
    <ResponsiveContainer width="100%" height={280}>
      <ComposedChart
        data={scatterData}
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
          tick={{ fill: '#a1a1aa', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          width={100}
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
          formatter={(value: number, name: string) => {
            if (name === 'Sig/Fight') return [value.toFixed(1), name]
            return [value, name]
          }}
        />
        <ReferenceLine
          x={avg}
          stroke="#71717a"
          strokeDasharray="4 4"
          label={{
            value: `Avg ${avg.toFixed(1)}`,
            fill: '#71717a',
            fontSize: 10,
            position: 'top',
          }}
        />
        {/* Stem (thin bar) */}
        <Bar
          dataKey="sig_str_per_fight"
          fill="#f59e0b"
          barSize={3}
          radius={[0, 2, 2, 0]}
          name="Sig/Fight"
        />
        {/* Dot (scatter at end) */}
        <Scatter
          dataKey="sig_str_per_fight"
          fill="rgba(245,158,11,0.85)"
          name="Sig/Fight"
        />
      </ComposedChart>
    </ResponsiveContainer>
  )
}
