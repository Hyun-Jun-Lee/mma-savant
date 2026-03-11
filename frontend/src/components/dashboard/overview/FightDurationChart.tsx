'use client'

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  LabelList,
  ReferenceLine,
  ResponsiveContainer,
} from 'recharts'
import type { OverviewResponse } from '@/types/dashboard'
import { ChartTooltip } from '../ChartTooltip'
import { FINISH_COLORS } from '@/lib/utils'

interface FightDurationChartProps {
  data: OverviewResponse['fight_duration']
}

function formatSeconds(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

const STACK_COLORS = {
  ko_tko: FINISH_COLORS.ko_tko ?? '#ef4444',
  submission: FINISH_COLORS.submission ?? '#a855f7',
  decision_other: FINISH_COLORS.decision ?? '#06b6d4',
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
      <BarChart data={chartData} margin={{ top: 24, right: 10, left: -10, bottom: 0 }}>
        <XAxis
          dataKey="label"
          tick={{ fill: '#52525b', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fill: '#a1a1aa', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          cursor={{ fill: 'rgba(255,255,255,0.04)' }}
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null
            const d = payload[0]?.payload as {
              label: string; result_round: number; fight_count: number
              ko_tko: number; submission: number; decision_other: number
            }
            return (
              <ChartTooltip active={active} label={`Round ${d.result_round}`}>
                <p style={{ color: STACK_COLORS.ko_tko }}>KO/TKO: {d.ko_tko}</p>
                <p style={{ color: STACK_COLORS.submission }}>Submission: {d.submission}</p>
                <p style={{ color: STACK_COLORS.decision_other }}>Decision/Other: {d.decision_other}</p>
              </ChartTooltip>
            )
          }}
        />
        <Legend
          verticalAlign="top"
          iconType="circle"
          iconSize={8}
          wrapperStyle={{ fontSize: '11px', color: '#a1a1aa', paddingBottom: '16px' }}
        />
        <Bar
          dataKey="ko_tko"
          name="KO/TKO"
          stackId="a"
          fill={STACK_COLORS.ko_tko}
          animationBegin={600}
          animationDuration={1000}
          animationEasing="ease-out"
        />
        <Bar
          dataKey="submission"
          name="Submission"
          stackId="a"
          fill={STACK_COLORS.submission}
          animationBegin={600}
          animationDuration={1000}
          animationEasing="ease-out"
        />
        <Bar
          dataKey="decision_other"
          name="Decision/Other"
          stackId="a"
          fill={STACK_COLORS.decision_other}
          radius={[4, 4, 0, 0]}
          animationBegin={600}
          animationDuration={1000}
          animationEasing="ease-out"
        >
          <LabelList
            dataKey="fight_count"
            position="top"
            fill="#a1a1aa"
            fontSize={10}
          />
        </Bar>
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
