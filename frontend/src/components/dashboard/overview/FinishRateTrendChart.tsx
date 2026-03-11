'use client'

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import type { FinishRateTrend } from '@/types/dashboard'
import { ChartTooltip } from '../ChartTooltip'

interface FinishRateTrendChartProps {
  data: FinishRateTrend[]
}

const COLORS = {
  ko_tko_rate: '#ef4444',
  sub_rate: '#a855f7',
  dec_rate: '#06b6d4',
}

export function FinishRateTrendChart({ data }: FinishRateTrendChartProps) {
  // 5-year interval ticks
  const years = data.map((d) => d.year)
  const minTick = Math.ceil(Math.min(...years) / 5) * 5
  const maxYear = Math.max(...years)
  const ticks: number[] = []
  for (let y = minTick; y <= maxYear; y += 5) ticks.push(y)

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
        <XAxis
          dataKey="year"
          tick={{ fill: '#52525b', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          ticks={ticks}
        />
        <YAxis
          tick={{ fill: '#a1a1aa', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          tickFormatter={(v) => `${v}%`}
        />
        <Tooltip
          content={({ active, payload, label }) => {
            if (!active || !payload?.length) return null
            const d = payload[0]?.payload as FinishRateTrend
            return (
              <ChartTooltip active={active} label={label}>
                <p className="text-red-400">KO/TKO: {d.ko_tko_rate.toFixed(1)}%</p>
                <p className="text-purple-400">Submission: {d.sub_rate.toFixed(1)}%</p>
                <p className="text-cyan-400">Decision: {d.dec_rate.toFixed(1)}%</p>
              </ChartTooltip>
            )
          }}
        />
        <Legend
          iconType="circle"
          iconSize={8}
          wrapperStyle={{ fontSize: '11px', color: '#a1a1aa' }}
        />
        <Line type="monotone" dataKey="ko_tko_rate" stroke={COLORS.ko_tko_rate} strokeWidth={2} dot={false} name="KO/TKO" animationBegin={500} animationDuration={1500} animationEasing="ease-out" />
        <Line type="monotone" dataKey="sub_rate" stroke={COLORS.sub_rate} strokeWidth={2} dot={false} name="Submission" animationBegin={500} animationDuration={1500} animationEasing="ease-out" />
        <Line type="monotone" dataKey="dec_rate" stroke={COLORS.dec_rate} strokeWidth={2} dot={false} name="Decision" animationBegin={500} animationDuration={1500} animationEasing="ease-out" />
      </LineChart>
    </ResponsiveContainer>
  )
}
