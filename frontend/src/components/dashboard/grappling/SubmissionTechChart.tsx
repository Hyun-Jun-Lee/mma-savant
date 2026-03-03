'use client'

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import type { SubmissionTechnique } from '@/types/dashboard'
import { ChartTooltip } from '../ChartTooltip'

interface SubmissionTechChartProps {
  data: SubmissionTechnique[]
}

export function SubmissionTechChart({ data }: SubmissionTechChartProps) {
  const total = data.reduce((sum, d) => sum + d.count, 0)

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart
        data={data}
        layout="vertical"
        margin={{ top: 5, right: 10, left: 10, bottom: 0 }}
      >
        <XAxis
          type="number"
          tick={{ fill: '#52525b', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          dataKey="technique"
          type="category"
          tick={{ fill: '#a1a1aa', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          width={120}
        />
        <Tooltip
          cursor={{ fill: 'rgba(255,255,255,0.04)' }}
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null
            const d = payload[0]?.payload as SubmissionTechnique
            const pct = total > 0 ? ((d.count / total) * 100).toFixed(1) : '0.0'
            return (
              <ChartTooltip active={active} label={d.technique}>
                <p className="text-zinc-400">Count: {d.count}</p>
                <p className="text-zinc-400">Share: {pct}%</p>
              </ChartTooltip>
            )
          }}
        />
        <Bar
          dataKey="count"
          fill="#a855f7"
          radius={[0, 4, 4, 0]}
          barSize={16}
          name="Count"
          animationBegin={500}
          animationDuration={1200}
          animationEasing="ease-out"
        />
      </BarChart>
    </ResponsiveContainer>
  )
}
