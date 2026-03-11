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
import type { ControlTimeByClass } from '@/types/dashboard'
import { abbreviateWeightClass, WEIGHT_CLASS_ABBR } from '@/lib/utils'

interface ControlTimeChartProps {
  data: ControlTimeByClass[]
}

function formatSeconds(sec: number) {
  const m = Math.floor(sec / 60)
  const s = Math.round(sec % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

const EXCLUDED_CLASSES = new Set(['open weight', 'catch weight'])

export function ControlTimeChart({ data }: ControlTimeChartProps) {
  const chartData = data
    .filter((d) => !EXCLUDED_CLASSES.has(d.weight_class.toLowerCase()))
    .map((d) => ({
      ...d,
      short: abbreviateWeightClass(d.weight_class),
      label: formatSeconds(d.avg_control_seconds),
    }))

  return (
    <ResponsiveContainer width="100%" height={Math.max(280, chartData.length * 30)}>
      <BarChart
        data={chartData}
        layout="vertical"
        margin={{ top: 5, right: 50, left: 10, bottom: 0 }}
      >
        <XAxis
          type="number"
          tick={{ fill: '#52525b', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          tickFormatter={formatSeconds}
        />
        <YAxis
          dataKey="short"
          type="category"
          tick={{ fill: '#a1a1aa', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          width={55}
          interval={0}
        />
        <Tooltip
          cursor={{ fill: 'rgba(255,255,255,0.04)' }}
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null
            const d = payload[0]?.payload as ControlTimeByClass & { short: string }
            return (
              <div className="rounded-lg border border-white/[0.06] bg-zinc-900 px-3 py-2 text-xs shadow-lg">
                <p className="mb-1 font-medium text-zinc-200">{d.weight_class}</p>
                <p className="text-zinc-400">Avg Control: {formatSeconds(d.avg_control_seconds)}</p>
              </div>
            )
          }}
        />
        <Bar
          dataKey="avg_control_seconds"
          fill="#06b6d4"
          radius={[0, 4, 4, 0]}
          barSize={16}
          name="Avg Control"
          animationBegin={500}
          animationDuration={1200}
          animationEasing="ease-out"
        >
          <LabelList
            dataKey="label"
            position="right"
            style={{ fill: '#a1a1aa', fontSize: 10 }}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
