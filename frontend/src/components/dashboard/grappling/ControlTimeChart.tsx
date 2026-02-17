'use client'

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import type { ControlTimeByClass } from '@/types/dashboard'

const ABBREVIATIONS: Record<string, string> = {
  Strawweight: 'Straw',
  Flyweight: 'Fly',
  Bantamweight: 'Bantam',
  Featherweight: 'Feather',
  Lightweight: 'Light',
  Welterweight: 'Welter',
  Middleweight: 'Middle',
  'Light Heavyweight': 'LHW',
  Heavyweight: 'Heavy',
  "Women's Strawweight": 'W.Straw',
  "Women's Flyweight": 'W.Fly',
  "Women's Bantamweight": 'W.Bantam',
  "Women's Featherweight": 'W.Feather',
}

interface ControlTimeChartProps {
  data: ControlTimeByClass[]
}

function formatSeconds(sec: number) {
  const m = Math.floor(sec / 60)
  const s = Math.round(sec % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

export function ControlTimeChart({ data }: ControlTimeChartProps) {
  const chartData = data.map((d) => ({
    ...d,
    short: ABBREVIATIONS[d.weight_class] ?? d.weight_class,
  }))

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart
        data={chartData}
        margin={{ top: 5, right: 10, left: -10, bottom: 0 }}
      >
        <XAxis
          dataKey="short"
          tick={{ fill: '#a1a1aa', fontSize: 10 }}
          axisLine={false}
          tickLine={false}
          interval={0}
          angle={-35}
          textAnchor="end"
          height={60}
        />
        <YAxis
          tick={{ fill: '#52525b', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          tickFormatter={formatSeconds}
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
          formatter={(value: number) => [formatSeconds(value), 'Avg Control']}
          labelFormatter={(label) =>
            data.find(
              (d) =>
                (ABBREVIATIONS[d.weight_class] ?? d.weight_class) === label
            )?.weight_class ?? label
          }
        />
        <Bar
          dataKey="avg_control_seconds"
          fill="#06b6d4"
          radius={[4, 4, 0, 0]}
          barSize={20}
          name="Avg Control"
        />
      </BarChart>
    </ResponsiveContainer>
  )
}
