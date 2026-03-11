'use client'

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  LabelList,
} from 'recharts'
import type { SigStrikesByWeightClass } from '@/types/dashboard'
import { ChartTooltip } from '../ChartTooltip'

interface SigStrikesByWcChartProps {
  data: SigStrikesByWeightClass[]
}

const EXCLUDED_CLASSES = new Set(['open weight', 'catch weight'])

export function SigStrikesByWcChart({ data }: SigStrikesByWcChartProps) {
  const filtered = data
    .filter((d) => !EXCLUDED_CLASSES.has(d.weight_class.toLowerCase()))

  return (
    <ResponsiveContainer width="100%" height={Math.max(280, filtered.length * 34)}>
      <BarChart
        data={filtered}
        layout="vertical"
        margin={{ top: 5, right: 50, left: 10, bottom: 0 }}
      >
        <XAxis
          type="number"
          tick={{ fill: '#52525b', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          dataKey="weight_class"
          type="category"
          tick={{ fill: '#a1a1aa', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          width={110}
          interval={0}
        />
        <Tooltip
          cursor={{ fill: 'rgba(255,255,255,0.04)' }}
          content={({ active, payload, label }) => {
            if (!active || !payload?.length) return null
            const d = payload[0]?.payload as SigStrikesByWeightClass
            return (
              <ChartTooltip active={active} label={label}>
                <p className="text-zinc-400">Avg Sig. Strikes/Fight: {d.avg_sig_str_per_fight.toFixed(1)}</p>
                <p className="text-zinc-400">Total Fights: {d.total_fights}</p>
              </ChartTooltip>
            )
          }}
        />
        <Bar
          dataKey="avg_sig_str_per_fight"
          fill="#f59e0b"
          radius={[0, 4, 4, 0]}
          barSize={18}
          name="Avg Sig. Strikes/Fight"
          animationBegin={500}
          animationDuration={1200}
          animationEasing="ease-out"
        >
          <LabelList
            dataKey="avg_sig_str_per_fight"
            position="right"
            style={{ fill: '#a1a1aa', fontSize: 11 }}
            formatter={(v: unknown) => Number(v).toFixed(1)}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
