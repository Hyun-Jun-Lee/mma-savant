'use client'

import {
  AreaChart,
  Area,
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
  return (
    <ResponsiveContainer width="100%" height={280}>
      <AreaChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
        <defs>
          {Object.entries(COLORS).map(([key, color]) => (
            <linearGradient key={key} id={`frt-${key}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.3} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          ))}
        </defs>
        <XAxis
          dataKey="year"
          tick={{ fill: '#52525b', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fill: '#52525b', fontSize: 11 }}
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
        <Area type="monotone" dataKey="ko_tko_rate" stroke={COLORS.ko_tko_rate} strokeWidth={2} fill={`url(#frt-ko_tko_rate)`} name="KO/TKO" animationBegin={500} animationDuration={1500} animationEasing="ease-out" />
        <Area type="monotone" dataKey="sub_rate" stroke={COLORS.sub_rate} strokeWidth={2} fill={`url(#frt-sub_rate)`} name="Submission" animationBegin={500} animationDuration={1500} animationEasing="ease-out" />
        <Area type="monotone" dataKey="dec_rate" stroke={COLORS.dec_rate} strokeWidth={2} fill={`url(#frt-dec_rate)`} name="Decision" animationBegin={500} animationDuration={1500} animationEasing="ease-out" />
      </AreaChart>
    </ResponsiveContainer>
  )
}
