'use client'

import { useState } from 'react'
import {
  ComposedChart,
  Bar,
  Scatter,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from 'recharts'
import { PillTabs } from '../PillTabs'
import type { MinFightsLeaderboard, SigStrikesLeader } from '@/types/dashboard'

const TABS = [
  { key: 'min10', label: '10+ Fights' },
  { key: 'min20', label: '20+ Fights' },
  { key: 'min30', label: '30+ Fights' },
] as const

type MinKey = (typeof TABS)[number]['key']

interface SigStrikesChartProps {
  data: MinFightsLeaderboard<SigStrikesLeader>
}

export function SigStrikesChart({ data }: SigStrikesChartProps) {
  const [activeKey, setActiveKey] = useState<MinKey>('min10')
  const fighters = data[activeKey]

  const avg =
    fighters.length > 0
      ? fighters.reduce((sum, d) => sum + d.sig_str_per_fight, 0) / fighters.length
      : 0

  // dot 크기를 경기 수에 비례
  const scatterData = fighters.map((d) => ({
    ...d,
    dotSize: Math.max(30, Math.min(120, d.total_fights * 4)),
  }))

  return (
    <div>
      <div className="mb-3">
        <PillTabs
          tabs={[...TABS]}
          activeKey={activeKey}
          onChange={(k) => setActiveKey(k as MinKey)}
          size="sm"
        />
      </div>
    <ResponsiveContainer width="100%" height={280}>
      <ComposedChart
        data={scatterData}
        layout="vertical"
        margin={{ top: 20, right: 40, left: 10, bottom: 0 }}
      >
        <XAxis
          type="number"
          tick={{ fill: '#52525b', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
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
            const val = payload[0]?.value as number
            return (
              <div className="rounded-lg border border-white/[0.06] bg-zinc-900 px-3 py-2 text-xs shadow-lg">
                <p className="mb-1 font-medium text-zinc-200">{label}</p>
                <p className="text-zinc-400">Sig/Fight: {val?.toFixed(1)}</p>
              </div>
            )
          }}
        />
        <ReferenceLine
          x={avg}
          stroke="#71717a"
          strokeDasharray="4 4"
          label={{
            value: `Avg ${avg.toFixed(1)}`,
            fill: '#71717a',
            fontSize: 10,
            position: 'insideBottomRight',
            dx: 8,
          }}
        />
        {/* Stem (thin bar) */}
        <Bar
          dataKey="sig_str_per_fight"
          fill="#f59e0b"
          barSize={3}
          radius={[0, 2, 2, 0]}
          name="Sig/Fight"
        />
        {/* Dot (scatter at end) */}
        <Scatter
          dataKey="sig_str_per_fight"
          fill="rgba(245,158,11,0.85)"
          name="Sig/Fight"
        />
      </ComposedChart>
    </ResponsiveContainer>
    </div>
  )
}
