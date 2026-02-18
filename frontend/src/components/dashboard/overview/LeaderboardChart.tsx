'use client'

import { useState } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { PillTabs } from '../PillTabs'
import type { OverviewResponse } from '@/types/dashboard'

const TABS = [
  { key: 'wins', label: 'Most Wins' },
  { key: 'winrate_min10', label: 'Win Rate (10+)' },
  { key: 'winrate_min20', label: 'Win Rate (20+)' },
  { key: 'winrate_min30', label: 'Win Rate (30+)' },
] as const

type LeaderboardKey = (typeof TABS)[number]['key']

interface LeaderboardChartProps {
  data: OverviewResponse['leaderboard']
  ufcOnly: boolean
  onUfcOnlyChange: (value: boolean) => void
}

export function LeaderboardChart({ data, ufcOnly, onUfcOnlyChange }: LeaderboardChartProps) {
  const [activeKey, setActiveKey] = useState<LeaderboardKey>('wins')

  const fighters = data[activeKey]
  const isWinRate = activeKey !== 'wins'
  const dataKey = isWinRate ? 'win_rate' : 'wins'

  return (
    <div>
      <div className="mb-3 flex items-center justify-between gap-3">
        <PillTabs
          tabs={[...TABS]}
          activeKey={activeKey}
          onChange={(k) => setActiveKey(k as LeaderboardKey)}
          size="sm"
        />
        <button
          onClick={() => onUfcOnlyChange(!ufcOnly)}
          className="flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium transition-colors bg-white/[0.04] hover:bg-white/[0.08]"
        >
          <span className={ufcOnly ? 'text-zinc-500' : 'text-white'}>All MMA</span>
          <div
            className={`relative h-4 w-7 rounded-full transition-colors ${
              ufcOnly ? 'bg-amber-500' : 'bg-zinc-600'
            }`}
          >
            <div
              className={`absolute top-0.5 h-3 w-3 rounded-full bg-white transition-transform ${
                ufcOnly ? 'translate-x-3.5' : 'translate-x-0.5'
              }`}
            />
          </div>
          <span className={ufcOnly ? 'text-amber-400' : 'text-zinc-500'}>UFC Only</span>
        </button>
      </div>
      <ResponsiveContainer width="100%" height={320}>
        <BarChart
          data={fighters}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 10, bottom: 0 }}
        >
          <XAxis
            type="number"
            tick={{ fill: '#52525b', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            domain={isWinRate ? [0, 100] : undefined}
            tickFormatter={isWinRate ? (v) => `${v}%` : undefined}
          />
          <YAxis
            dataKey="name"
            type="category"
            tick={{ fill: '#a1a1aa', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            width={120}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#18181b',
              border: '1px solid rgba(255,255,255,0.06)',
              borderRadius: '8px',
              fontSize: '12px',
            }}
            itemStyle={{ color: '#e4e4e7' }}
            labelStyle={{ color: '#a1a1aa' }}
            formatter={(value: number) =>
              isWinRate ? `${value.toFixed(1)}%` : value
            }
          />
          <Bar
            dataKey={dataKey}
            fill="#8b5cf6"
            radius={[0, 4, 4, 0]}
            barSize={16}
            name={isWinRate ? 'Win Rate' : 'Wins'}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
