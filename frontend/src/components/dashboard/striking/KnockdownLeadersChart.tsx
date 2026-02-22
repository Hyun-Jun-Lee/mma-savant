'use client'

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import type { KnockdownLeader } from '@/types/dashboard'

interface KnockdownLeadersChartProps {
  data: KnockdownLeader[]
}

export function KnockdownLeadersChart({ data }: KnockdownLeadersChartProps) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart
        data={data}
        layout="vertical"
        margin={{ top: 5, right: 30, left: 10, bottom: 0 }}
      >
        <XAxis
          type="number"
          tick={{ fill: '#52525b', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          allowDecimals={false}
        />
        <YAxis
          dataKey="name"
          type="category"
          tick={{ fill: '#a1a1aa', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          width={100}
        />
        <Tooltip
          content={({ active, payload, label }) => {
            if (!active || !payload?.length) return null
            const d = payload[0]?.payload as KnockdownLeader
            return (
              <div className="rounded-lg border border-white/[0.06] bg-zinc-900 px-3 py-2 text-xs shadow-lg">
                <p className="mb-1 font-medium text-zinc-200">{label}</p>
                <p className="text-zinc-400">Knockdowns: {d.total_knockdowns}</p>
                <p className="text-zinc-400">KD/Fight: {d.kd_per_fight.toFixed(2)}</p>
                <p className="text-zinc-400">Fights: {d.total_fights}</p>
              </div>
            )
          }}
        />
        <Bar
          dataKey="total_knockdowns"
          fill="#ef4444"
          radius={[0, 4, 4, 0]}
          barSize={16}
          name="Knockdowns"
        />
      </BarChart>
    </ResponsiveContainer>
  )
}
