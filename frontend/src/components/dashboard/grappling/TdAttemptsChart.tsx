'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
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
import type { TdAttemptsLeaderboard } from '@/types/dashboard'

const TABS = [
  { key: 'min10', label: '10+ Fights' },
  { key: 'min15', label: '15+ Fights' },
  { key: 'min20', label: '20+ Fights' },
] as const

type MinKey = (typeof TABS)[number]['key']

interface TdAttemptsChartProps {
  data: TdAttemptsLeaderboard
}

export function TdAttemptsChart({ data }: TdAttemptsChartProps) {
  const router = useRouter()
  const [activeKey, setActiveKey] = useState<MinKey>('min10')
  const fighters = data[activeKey]

  const FighterTick = ({ x, y, payload }: { x?: number; y?: number; payload?: { value: string } }) => {
    const item = fighters.find((d) => d.name === payload?.value)
    return (
      <g transform={`translate(${x ?? 0},${y ?? 0})`}>
        <text
          x={-4}
          y={0}
          dy={4}
          textAnchor="end"
          fill="#a1a1aa"
          fontSize={11}
          style={{ cursor: 'pointer' }}
          onClick={() => item && router.push(`/fighters/${item.fighter_id}`)}
        >
          {payload?.value}
        </text>
      </g>
    )
  }

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
          data={fighters}
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
            tick={<FighterTick />}
            axisLine={false}
            tickLine={false}
            width={100}
          />
          <Tooltip
            content={({ active, payload, label }) => {
              if (!active || !payload?.length) return null
              const d = payload[0]?.payload as (typeof fighters)[number]
              return (
                <div className="rounded-lg border border-white/[0.06] bg-zinc-900 px-3 py-2 text-xs shadow-lg">
                  <p className="mb-1 font-medium text-zinc-200">{label}</p>
                  <p className="text-zinc-400">TD Attempts/Fight: {d.td_attempts_per_fight.toFixed(2)}</p>
                  <p className="text-zinc-400">TD Landed: {d.total_td_landed}/{d.total_td_attempted}</p>
                  <p className="text-zinc-400">Fights: {d.total_fights}</p>
                </div>
              )
            }}
          />
          <ReferenceLine
            x={data.avg_td_attempts}
            stroke="#71717a"
            strokeDasharray="4 4"
            label={{
              value: `Avg ${data.avg_td_attempts.toFixed(1)}`,
              fill: '#71717a',
              fontSize: 10,
              position: 'insideBottomRight',
              dx: 8,
            }}
          />
          <Bar
            dataKey="td_attempts_per_fight"
            fill="#06b6d4"
            barSize={3}
            radius={[0, 2, 2, 0]}
            name="TD Attempts/Fight"
          />
          <Scatter
            dataKey="td_attempts_per_fight"
            fill="rgba(6,182,212,0.85)"
            name="TD Attempts/Fight"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
