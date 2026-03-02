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
  ReferenceLine,
  Cell,
} from 'recharts'
import { PillTabs } from '../PillTabs'
import type { MinFightsLeaderboard, StrikeExchange } from '@/types/dashboard'

const TABS = [
  { key: 'min10', label: '10+ Fights' },
  { key: 'min15', label: '15+ Fights' },
  { key: 'min20', label: '20+ Fights' },
] as const

type MinKey = (typeof TABS)[number]['key']

interface StrikeExchangeChartProps {
  data: MinFightsLeaderboard<StrikeExchange>
}

export function StrikeExchangeChart({ data }: StrikeExchangeChartProps) {
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

  const chartData = fighters.map((f) => ({
    name: f.name,
    fighter_id: f.fighter_id,
    differential: f.differential_per_fight,
    landed: f.sig_landed_per_fight,
    absorbed: f.sig_absorbed_per_fight,
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
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 10, bottom: 0 }}
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
              const d = payload[0]?.payload as (typeof chartData)[number]
              return (
                <div className="rounded-lg border border-white/[0.06] bg-zinc-900 px-3 py-2 text-xs shadow-lg">
                  <p className="mb-1 font-medium text-zinc-200">{label}</p>
                  <p className="text-zinc-400">Landed/Fight: {d.landed.toFixed(1)}</p>
                  <p className="text-zinc-400">Absorbed/Fight: {d.absorbed.toFixed(1)}</p>
                  <p className="text-zinc-400">Differential: {d.differential > 0 ? '+' : ''}{d.differential.toFixed(1)}</p>
                </div>
              )
            }}
          />
          <ReferenceLine x={0} stroke="#3f3f46" />
          <Bar dataKey="differential" barSize={16} radius={[0, 4, 4, 0]} name="Differential">
            {chartData.map((entry, i) => (
              <Cell
                key={i}
                fill={entry.differential >= 0 ? '#10b981' : '#ef4444'}
                fillOpacity={0.8}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
