'use client'

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import type { SigStrikesByWeightClass } from '@/types/dashboard'
import { abbreviateWeightClass } from '@/lib/utils'

interface SigStrikesByWcChartProps {
  data: SigStrikesByWeightClass[]
}

const EXCLUDED_CLASSES = new Set(['open weight', 'catch weight'])

export function SigStrikesByWcChart({ data }: SigStrikesByWcChartProps) {
  const filtered = data
    .filter((d) => !EXCLUDED_CLASSES.has(d.weight_class.toLowerCase()))
    .map((d) => ({ ...d, short: abbreviateWeightClass(d.weight_class) }))

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={filtered} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
        <XAxis
          dataKey="short"
          tick={{ fill: '#a1a1aa', fontSize: 10 }}
          axisLine={false}
          tickLine={false}
          interval={0}
          angle={-35}
          textAnchor="end"
          height={60}
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
          formatter={(value: number) => value.toFixed(1)}
        />
        <Bar
          dataKey="avg_sig_str_per_fight"
          fill="#f59e0b"
          radius={[4, 4, 0, 0]}
          barSize={20}
          name="Avg Sig. Strikes/Fight"
          animationBegin={500}
          animationDuration={1200}
          animationEasing="ease-out"
        />
      </BarChart>
    </ResponsiveContainer>
  )
}
