'use client'

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import type { TdByWeightClass } from '@/types/dashboard'

interface TdByWeightClassChartProps {
  data: TdByWeightClass[]
}

export function TdByWeightClassChart({ data }: TdByWeightClassChartProps) {
  const filtered = data.filter((d) => d.weight_class.toLowerCase() !== 'open weight')

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={filtered} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
        <XAxis
          dataKey="weight_class"
          tick={{ fill: '#52525b', fontSize: 10 }}
          axisLine={false}
          tickLine={false}
          angle={-30}
          textAnchor="end"
          height={50}
        />
        <YAxis
          tick={{ fill: '#52525b', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
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
          formatter={(value: number) => value.toFixed(2)}
        />
        <Legend
          iconType="circle"
          iconSize={8}
          wrapperStyle={{ fontSize: '11px', color: '#a1a1aa' }}
        />
        <Bar dataKey="avg_td_attempts_per_fight" fill="#06b6d4" radius={[4, 4, 0, 0]} barSize={14} name="Attempts" />
        <Bar dataKey="avg_td_landed_per_fight" fill="#10b981" radius={[4, 4, 0, 0]} barSize={14} name="Landed" />
      </BarChart>
    </ResponsiveContainer>
  )
}
