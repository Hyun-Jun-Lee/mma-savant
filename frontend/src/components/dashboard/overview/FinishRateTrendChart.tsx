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

interface FinishRateTrendChartProps {
  data: FinishRateTrend[]
}

const COLORS = {
  ko_tko_rate: '#ef4444',
  sub_rate: '#8b5cf6',
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
          contentStyle={{
            backgroundColor: '#18181b',
            border: '1px solid rgba(255,255,255,0.06)',
            borderRadius: '8px',
            fontSize: '12px',
          }}
          itemStyle={{ color: '#e4e4e7' }}
          labelStyle={{ color: '#a1a1aa' }}
          formatter={(value: number) => `${value.toFixed(1)}%`}
        />
        <Legend
          iconType="circle"
          iconSize={8}
          wrapperStyle={{ fontSize: '11px', color: '#a1a1aa' }}
        />
        <Area type="monotone" dataKey="ko_tko_rate" stroke={COLORS.ko_tko_rate} strokeWidth={2} fill={`url(#frt-ko_tko_rate)`} name="KO/TKO" />
        <Area type="monotone" dataKey="sub_rate" stroke={COLORS.sub_rate} strokeWidth={2} fill={`url(#frt-sub_rate)`} name="Submission" />
        <Area type="monotone" dataKey="dec_rate" stroke={COLORS.dec_rate} strokeWidth={2} fill={`url(#frt-dec_rate)`} name="Decision" />
      </AreaChart>
    </ResponsiveContainer>
  )
}
