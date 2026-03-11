'use client'

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  LabelList,
} from 'recharts'
import type { WeightClassActivity } from '@/types/dashboard'
import { ChartTooltip } from '../ChartTooltip'

interface WeightClassActivityChartProps {
  data: WeightClassActivity[]
}

const EXCLUDED_CLASSES = new Set(['open weight', 'catch weight'])

export function WeightClassActivityChart({
  data,
}: WeightClassActivityChartProps) {
  const chartData = data
    .filter((d) => !EXCLUDED_CLASSES.has(d.weight_class.toLowerCase()))
    .sort((a, b) => b.total_fights - a.total_fights)

  const chartHeight = Math.max(280, chartData.length * 26)

  return (
    <ResponsiveContainer width="100%" height={chartHeight}>
      <BarChart
        data={chartData}
        layout="vertical"
        margin={{ top: 5, right: 45, left: 0, bottom: 0 }}
      >
        <XAxis
          type="number"
          tick={{ fill: '#52525b', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          type="category"
          dataKey="weight_class"
          tick={{ fill: '#a1a1aa', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          width={120}
        />
        <Tooltip
          cursor={{ fill: 'rgba(255,255,255,0.04)' }}
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null
            const d = payload[0]?.payload as WeightClassActivity
            if (!d) return null
            return (
              <ChartTooltip active={active} label={d.weight_class}>
                <p className="text-zinc-400">
                  Total Fights: {d.total_fights}
                </p>
              </ChartTooltip>
            )
          }}
        />
        <Bar
          dataKey="total_fights"
          fill="#8b5cf6"
          radius={[0, 4, 4, 0]}
          barSize={16}
          name="Total Fights"
          animationBegin={500}
          animationDuration={1200}
          animationEasing="ease-out"
        >
          <LabelList
            dataKey="total_fights"
            position="right"
            fill="#a1a1aa"
            fontSize={11}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
