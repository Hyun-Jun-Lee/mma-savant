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
import { ChartTooltip } from '../ChartTooltip'

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
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null
            const d = payload[0]?.payload as { label: string; fight_count: number; pct: number; result_round: number }
            return (
              <ChartTooltip active={active} label={`Round ${d.result_round}`}>
                <p className="text-zinc-400">Fights: {d.fight_count}</p>
                {d.pct !== undefined && <p className="text-zinc-400">Percentage: {d.pct.toFixed(1)}%</p>}
              </ChartTooltip>
            )
          }}
        />
        <Bar
          dataKey="fight_count"
          fill="#f59e0b"
          radius={[4, 4, 0, 0]}
          name="fight_count"
          animationBegin={600}
          animationDuration={1000}
          animationEasing="ease-out"
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
