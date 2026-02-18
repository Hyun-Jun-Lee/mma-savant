'use client'

import { useState } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  LabelList,
} from 'recharts'
import { PillTabs } from '../PillTabs'
import type { MinFightsLeaderboard, StrikingAccuracyFighter } from '@/types/dashboard'

const TABS = [
  { key: 'min10', label: '10+ Fights' },
  { key: 'min20', label: '20+ Fights' },
  { key: 'min30', label: '30+ Fights' },
] as const

type MinKey = (typeof TABS)[number]['key']

interface StrikingAccuracyChartProps {
  data: MinFightsLeaderboard<StrikingAccuracyFighter>
}

function getColor(accuracy: number) {
  if (accuracy >= 62) return '#8b5cf6'
  if (accuracy >= 55) return '#7c3aed'
  return '#6d28d9'
}

export function StrikingAccuracyChart({ data }: StrikingAccuracyChartProps) {
  const [activeKey, setActiveKey] = useState<MinKey>('min10')
  const fighters = data[activeKey]
  const chartData = fighters.map((d) => ({ ...d, accLabel: `${d.accuracy}%` }))

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
        margin={{ top: 5, right: 50, left: 10, bottom: 0 }}
        barGap={-16}
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
          cursor={{ fill: 'rgba(255,255,255,0.04)' }}
          contentStyle={{
            backgroundColor: '#18181b',
            border: '1px solid rgba(255,255,255,0.06)',
            borderRadius: '8px',
            fontSize: '12px',
          }}
          itemStyle={{ color: '#e4e4e7' }}
          labelStyle={{ color: '#a1a1aa' }}
        />
        {/* Attempted (background bar) */}
        <Bar
          dataKey="total_sig_attempted"
          fill="#8b5cf6"
          fillOpacity={0.15}
          barSize={16}
          radius={[0, 3, 3, 0]}
          name="Attempted"
        />
        {/* Landed (foreground bar) */}
        <Bar
          dataKey="total_sig_landed"
          barSize={16}
          radius={[0, 3, 3, 0]}
          name="Landed"
        >
          <LabelList
            dataKey="accLabel"
            position="right"
            style={{ fill: '#a1a1aa', fontSize: 10 }}
          />
          {chartData.map((d, i) => (
            <Cell key={i} fill={getColor(d.accuracy)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
    </div>
  )
}
