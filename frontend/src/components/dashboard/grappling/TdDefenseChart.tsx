'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { PillTabs } from '../PillTabs'
import type { MinFightsLeaderboard, TdDefenseLeader } from '@/types/dashboard'

const TABS = [
  { key: 'min10', label: '10+ Fights' },
  { key: 'min15', label: '15+ Fights' },
  { key: 'min20', label: '20+ Fights' },
] as const

type MinKey = (typeof TABS)[number]['key']

interface TdDefenseChartProps {
  data: MinFightsLeaderboard<TdDefenseLeader>
}

export function TdDefenseChart({ data }: TdDefenseChartProps) {
  const router = useRouter()
  const [activeKey, setActiveKey] = useState<MinKey>('min10')
  const fighters = data[activeKey]

  const FighterTick = ({ x, y, payload }: any) => {
    const item = fighters.find((d: any) => d.name === payload.value)
    return (
      <g transform={`translate(${x},${y})`}>
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
          {payload.value}
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
        <BarChart
          data={fighters}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 10, bottom: 0 }}
        >
          <XAxis
            type="number"
            domain={[0, 100]}
            tick={{ fill: '#52525b', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v) => `${v}%`}
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
              const d = payload[0]?.payload as TdDefenseLeader
              return (
                <div className="rounded-lg border border-white/[0.06] bg-zinc-900 px-3 py-2 text-xs shadow-lg">
                  <p className="mb-1 font-medium text-zinc-200">{label}</p>
                  <p className="text-zinc-400">Defense Rate: {d.td_defense_rate.toFixed(1)}%</p>
                  <p className="text-zinc-400">Defended: {d.td_defended}/{d.opp_td_attempted}</p>
                  <p className="text-zinc-400">Opp. Landed: {d.opp_td_landed}</p>
                </div>
              )
            }}
          />
          <Bar
            dataKey="td_defense_rate"
            fill="#10b981"
            radius={[0, 4, 4, 0]}
            barSize={16}
            name="TD Defense %"
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
