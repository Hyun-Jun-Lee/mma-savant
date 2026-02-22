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
import type { RoundStrikeTrend } from '@/types/dashboard'

interface RoundStrikeTrendChartProps {
  data: RoundStrikeTrend[]
}

const AREAS = [
  { key: 'avg_head', color: '#ef4444', name: 'Head' },
  { key: 'avg_body', color: '#f59e0b', name: 'Body' },
  { key: 'avg_leg', color: '#10b981', name: 'Leg' },
  { key: 'avg_clinch', color: '#06b6d4', name: 'Clinch' },
  { key: 'avg_ground', color: '#8b5cf6', name: 'Ground' },
] as const

export function RoundStrikeTrendChart({ data }: RoundStrikeTrendChartProps) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <AreaChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
        <defs>
          {AREAS.map(({ key, color }) => (
            <linearGradient key={key} id={`rst-${key}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.3} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          ))}
        </defs>
        <XAxis
          dataKey="round"
          tick={{ fill: '#52525b', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          tickFormatter={(v) => `R${v}`}
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
          labelFormatter={(v) => `Round ${v}`}
          formatter={(value: number) => value.toFixed(1)}
        />
        <Legend
          iconType="circle"
          iconSize={8}
          wrapperStyle={{ fontSize: '11px', color: '#a1a1aa' }}
        />
        {AREAS.map(({ key, color, name }) => (
          <Area
            key={key}
            type="monotone"
            dataKey={key}
            stroke={color}
            strokeWidth={2}
            fill={`url(#rst-${key})`}
            name={name}
          />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  )
}
