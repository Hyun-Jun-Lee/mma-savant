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
}

export function LeaderboardChart({ data }: LeaderboardChartProps) {
  const [activeKey, setActiveKey] = useState<LeaderboardKey>('wins')

  const fighters = data[activeKey]
  const isWinRate = activeKey !== 'wins'
  const dataKey = isWinRate ? 'win_rate' : 'wins'

  return (
    <div>
      <div className="mb-3">
        <PillTabs
          tabs={[...TABS]}
          activeKey={activeKey}
          onChange={(k) => setActiveKey(k as LeaderboardKey)}
          size="sm"
        />
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
