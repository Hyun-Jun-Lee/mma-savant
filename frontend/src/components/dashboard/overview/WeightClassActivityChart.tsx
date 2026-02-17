'use client'

import {
  ComposedChart,
  Bar,
  Scatter,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import type { WeightClassActivity } from '@/types/dashboard'

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

interface WeightClassActivityChartProps {
  data: WeightClassActivity[]
}

export function WeightClassActivityChart({
  data,
}: WeightClassActivityChartProps) {
  const chartData = data.map((d) => ({
    ...d,
    short: ABBREVIATIONS[d.weight_class] ?? d.weight_class,
    finish_count: d.ko_tko_count + d.sub_count,
  }))

  return (
    <ResponsiveContainer width="100%" height={280}>
      <ComposedChart
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
        />
        <Bar
          dataKey="total_fights"
          fill="#8b5cf6"
          radius={[4, 4, 0, 0]}
          barSize={20}
          name="Total Fights"
        />
        <Scatter dataKey="finish_count" fill="#ef4444" name="Finishes" />
        <Tooltip
          cursor={{ fill: 'rgba(255,255,255,0.04)' }}
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null
            const d = payload[0]?.payload as WeightClassActivity & {
              finish_count: number
            }
            if (!d) return null
            return (
              <div className="rounded-lg border border-white/[0.06] bg-zinc-900 px-3 py-2 text-xs shadow-lg">
                <p className="mb-1 text-zinc-400">{d.weight_class}</p>
                <p className="text-zinc-200">
                  Total Fights: {d.total_fights}
                </p>
                <p className="text-zinc-200">
                  Finishes: {d.finish_count} ({d.finish_rate.toFixed(1)}%)
                </p>
                <p className="pl-3 text-zinc-400">
                  KO/TKO: {d.ko_tko_count}
                </p>
                <p className="pl-3 text-zinc-400">SUB: {d.sub_count}</p>
              </div>
            )
          }}
        />
      </ComposedChart>
    </ResponsiveContainer>
  )
}
