'use client'

import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'
import type { GroundStrikesLeader } from '@/types/dashboard'

interface GroundStrikesChartProps {
  data: GroundStrikesLeader[]
}

export function GroundStrikesChart({ data }: GroundStrikesChartProps) {
  const scatterData = data.map((d) => ({
    x: d.total_ground_attempted,
    y: d.total_ground_landed,
    z: d.accuracy,
    name: d.name,
  }))

  const maxVal = Math.max(
    ...data.map((d) => Math.max(d.total_ground_attempted, d.total_ground_landed)),
    1
  )

  return (
    <ResponsiveContainer width="100%" height={280}>
      <ScatterChart margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
        <XAxis
          dataKey="x"
          type="number"
          name="Attempted"
          tick={{ fill: '#52525b', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          label={{
            value: 'Attempted',
            position: 'bottom',
            fill: '#a1a1aa',
            fontSize: 11,
            offset: -5,
          }}
        />
        <YAxis
          dataKey="y"
          type="number"
          name="Landed"
          tick={{ fill: '#52525b', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          label={{
            value: 'Landed',
            angle: -90,
            position: 'insideLeft',
            fill: '#a1a1aa',
            fontSize: 11,
          }}
        />
        <ZAxis dataKey="z" range={[40, 200]} name="Accuracy" />
        {/* 100% reference line */}
        <ReferenceLine
          segment={[
            { x: 0, y: 0 },
            { x: maxVal, y: maxVal },
          ]}
          stroke="#3f3f46"
          strokeDasharray="4 4"
        />
        {/* 70% reference line */}
        <ReferenceLine
          segment={[
            { x: 0, y: 0 },
            { x: maxVal, y: maxVal * 0.7 },
          ]}
          stroke="#27272a"
          strokeDasharray="4 4"
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
          formatter={(value: number, name: string) => {
            if (name === 'Accuracy') return [`${value.toFixed(1)}%`, name]
            return [value, name]
          }}
          labelFormatter={(_, payload) =>
            payload?.[0]?.payload?.name ?? ''
          }
        />
        <Scatter data={scatterData} fill="#10b981" fillOpacity={0.6} />
      </ScatterChart>
    </ResponsiveContainer>
  )
}
