'use client'

import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  Label,
} from 'recharts'
import type { GrapplingResponse } from '@/types/dashboard'

interface SubmissionEfficiencyChartProps {
  data: GrapplingResponse['submission_efficiency']
}

export function SubmissionEfficiencyChart({
  data,
}: SubmissionEfficiencyChartProps) {
  const { fighters, avg_efficiency_ratio } = data

  const scatterData = fighters.map((f) => ({
    x: f.total_sub_attempts,
    y: f.sub_finishes,
    name: f.name,
  }))

  const maxAttempts = Math.max(...fighters.map((f) => f.total_sub_attempts), 1)

  return (
    <ResponsiveContainer width="100%" height={280}>
      <ScatterChart margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
        <XAxis
          dataKey="x"
          type="number"
          name="Attempts"
          tick={{ fill: '#52525b', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          label={{
            value: 'Attempts',
            position: 'bottom',
            fill: '#a1a1aa',
            fontSize: 11,
            offset: -5,
          }}
        />
        <YAxis
          dataKey="y"
          type="number"
          name="Finishes"
          tick={{ fill: '#52525b', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          label={{
            value: 'Finishes',
            angle: -90,
            position: 'insideLeft',
            fill: '#a1a1aa',
            fontSize: 11,
          }}
        />
        {/* Average efficiency reference line */}
        <ReferenceLine
          segment={[
            { x: 0, y: 0 },
            { x: maxAttempts, y: maxAttempts * avg_efficiency_ratio },
          ]}
          stroke="#71717a"
          strokeDasharray="4 4"
        >
          <Label
            value={`Avg ${(avg_efficiency_ratio * 100).toFixed(0)}%`}
            fill="#71717a"
            fontSize={10}
            position="end"
          />
        </ReferenceLine>
        <Tooltip
          contentStyle={{
            backgroundColor: '#18181b',
            border: '1px solid rgba(255,255,255,0.06)',
            borderRadius: '8px',
            fontSize: '12px',
          }}
          itemStyle={{ color: '#e4e4e7' }}
          labelStyle={{ color: '#a1a1aa' }}
          labelFormatter={(_, payload) =>
            payload?.[0]?.payload?.name ?? ''
          }
        />
        <Scatter data={scatterData} fill="#8b5cf6" fillOpacity={0.7} />
      </ScatterChart>
    </ResponsiveContainer>
  )
}
