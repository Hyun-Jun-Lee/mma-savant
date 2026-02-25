'use client'

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'
import type { NationalityDistribution } from '@/types/dashboard'

interface NationalityBarChartProps {
  data: NationalityDistribution[]
}

const BAR_COLOR = '#a855f7'
const BAR_COLOR_OTHERS = '#52525b'

export function NationalityTreemapChart({ data }: NationalityBarChartProps) {
  const top15 = data.slice(0, 15)
  const othersCount = data
    .slice(15)
    .reduce((sum, d) => sum + d.fighter_count, 0)

  const chartData = [
    ...(othersCount > 0
      ? [{ name: 'Others', value: othersCount, isOthers: true }]
      : []),
    ...top15
      .map((d) => ({
        name: d.nationality,
        value: d.fighter_count,
        isOthers: false,
      }))
      .reverse(),
  ]

  const barHeight = chartData.length * 28 + 20

  return (
    <ResponsiveContainer width="100%" height={barHeight}>
      <BarChart
        layout="vertical"
        data={chartData}
        margin={{ top: 4, right: 30, bottom: 4, left: 4 }}
      >
        <XAxis
          type="number"
          tick={{ fontSize: 11, fill: '#a1a1aa' }}
          tickLine={false}
          axisLine={{ stroke: '#27272a' }}
        />
        <YAxis
          type="category"
          dataKey="name"
          tick={{ fontSize: 11, fill: '#d4d4d8' }}
          tickLine={false}
          axisLine={false}
          width={80}
        />
        <Tooltip
          cursor={{ fill: 'rgba(255,255,255,0.04)' }}
          content={({ payload }) => {
            if (!payload?.[0]) return null
            const item = payload[0].payload
            return (
              <div className="rounded-lg border border-white/10 bg-zinc-900 px-3 py-2 text-xs shadow-xl">
                <p className="font-semibold text-zinc-100">{item.name}</p>
                <p className="text-zinc-400">
                  {item.value} fighter{item.value > 1 ? 's' : ''}
                </p>
              </div>
            )
          }}
        />
        <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={18}>
          {chartData.map((entry, index) => (
            <Cell
              key={index}
              fill={entry.isOthers ? BAR_COLOR_OTHERS : BAR_COLOR}
              className="transition-opacity hover:opacity-80"
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
