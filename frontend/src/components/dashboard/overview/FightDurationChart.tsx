'use client'

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from 'recharts'
import type { OverviewResponse } from '@/types/dashboard'

interface FightDurationChartProps {
  data: OverviewResponse['fight_duration']
}

function formatSeconds(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

export function FightDurationChart({ data }: FightDurationChartProps) {
  const chartData = data.rounds.map((r) => ({
    ...r,
    label: `R${r.result_round}`,
  }))

  const avgLabel = data.avg_time_seconds
    ? `Avg ${formatSeconds(data.avg_time_seconds)}`
    : `Avg R${data.avg_round.toFixed(1)}`

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={chartData} margin={{ top: 20, right: 10, left: -10, bottom: 0 }}>
        <XAxis
          dataKey="label"
          tick={{ fill: '#52525b', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fill: '#52525b', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          cursor={{ fill: 'rgba(255,255,255,0.04)' }}
          contentStyle={{
            backgroundColor: '#18181b',
            border: '1px solid rgba(255,255,255,0.06)',
            borderRadius: '8px',
            fontSize: '12px',
          }}
          itemStyle={{ color: '#e4e4e7' }}
          labelStyle={{ color: '#a1a1aa' }}
          formatter={(value: number, name: string) =>
            name === 'fight_count'
              ? [value, 'Fights']
              : [`${value.toFixed(1)}%`, 'Percentage']
          }
        />
        <Bar
          dataKey="fight_count"
          fill="#f59e0b"
          radius={[4, 4, 0, 0]}
          name="fight_count"
        />
        <ReferenceLine
          x={`R${Math.round(data.avg_round)}`}
          stroke="#71717a"
          strokeDasharray="4 4"
          label={{
            value: avgLabel,
            fill: '#71717a',
            fontSize: 10,
            position: 'top',
          }}
        />
      </BarChart>
    </ResponsiveContainer>
  )
}
