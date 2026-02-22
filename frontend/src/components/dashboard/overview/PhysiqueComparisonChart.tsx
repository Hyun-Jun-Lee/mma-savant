'use client'

import { useState } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ReferenceLine,
} from 'recharts'
import { PillTabs } from '../PillTabs'
import type { PhysiqueComparison } from '@/types/dashboard'

interface PhysiqueComparisonChartProps {
  data: PhysiqueComparison[]
}

const TABS = [
  { key: 'height', label: 'Height' },
  { key: 'reach', label: 'Reach' },
  { key: 'advantage', label: 'Reach Adv.' },
] as const

type TabKey = (typeof TABS)[number]['key']

const METRIC_CONFIG = {
  height: { key: 'avg_height_cm', color: '#06b6d4', label: 'Avg Height (cm)', unit: 'cm' },
  reach: { key: 'avg_reach_cm', color: '#f59e0b', label: 'Avg Reach (cm)', unit: 'cm' },
  advantage: { key: 'avg_reach_advantage', color: '#10b981', label: 'Reach Advantage (cm)', unit: 'cm' },
} as const

export function PhysiqueComparisonChart({ data }: PhysiqueComparisonChartProps) {
  const [activeTab, setActiveTab] = useState<TabKey>('height')
  const config = METRIC_CONFIG[activeTab]

  const avg = data.length > 0
    ? data.reduce((sum, d) => sum + (d[config.key as keyof PhysiqueComparison] as number), 0) / data.length
    : 0

  return (
    <div>
      <div className="mb-3">
        <PillTabs
          tabs={[...TABS]}
          activeKey={activeTab}
          onChange={(k) => setActiveTab(k as TabKey)}
          size="sm"
        />
      </div>
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
            tickFormatter={(v) => `${v}`}
          />
          <YAxis
            dataKey="weight_class"
            type="category"
            tick={{ fill: '#a1a1aa', fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            width={110}
          />
          <Tooltip
            content={({ active, payload, label }) => {
              if (!active || !payload?.length) return null
              const d = payload[0]?.payload as PhysiqueComparison
              return (
                <div className="rounded-lg border border-white/[0.06] bg-zinc-900 px-3 py-2 text-xs shadow-lg">
                  <p className="mb-1 font-medium text-zinc-200">{label}</p>
                  <p className="text-zinc-400">Height: {d.avg_height_cm} cm</p>
                  <p className="text-zinc-400">Reach: {d.avg_reach_cm} cm</p>
                  <p className="text-zinc-400">Reach Adv: {d.avg_reach_advantage > 0 ? '+' : ''}{d.avg_reach_advantage} cm</p>
                  <p className="text-zinc-400">Fighters: {d.fighter_count}</p>
                </div>
              )
            }}
          />
          <Legend
            iconType="circle"
            iconSize={8}
            wrapperStyle={{ fontSize: '11px', color: '#a1a1aa' }}
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
          <Bar
            dataKey={config.key}
            fill={config.color}
            radius={[0, 4, 4, 0]}
            barSize={14}
            name={config.label}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
