'use client'

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import type { EventTimeline } from '@/types/dashboard'
import { ChartTooltip } from '../ChartTooltip'

interface EventsTimelineChartProps {
  data: EventTimeline[]
}

export function EventsTimelineChart({ data }: EventsTimelineChartProps) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <AreaChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
        <defs>
          <linearGradient id="evtGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#06b6d4" stopOpacity={0.3} />
            <stop offset="100%" stopColor="#06b6d4" stopOpacity={0} />
          </linearGradient>
        </defs>
        <XAxis
          dataKey="year"
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
          content={({ active, payload, label }) => {
            if (!active || !payload?.length) return null
            const count = payload[0]?.value as number
            return (
              <ChartTooltip active={active} label={label}>
                <p className="text-zinc-400">Events: {count}</p>
              </ChartTooltip>
            )
          }}
        />
        <Area
          type="monotone"
          dataKey="event_count"
          stroke="#06b6d4"
          strokeWidth={2}
          fill="url(#evtGrad)"
          name="Events"
          animationBegin={600}
          animationDuration={1800}
          animationEasing="ease-out"
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}
