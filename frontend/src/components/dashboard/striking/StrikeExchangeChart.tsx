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
import { ChevronDown } from 'lucide-react'
import { toTitleCase } from '@/lib/utils'
import { PillTabs, TabContent } from '../PillTabs'
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
  const [expanded, setExpanded] = useState(false)
  const fighters = data[activeKey]
  const displayFighters = expanded ? fighters : fighters.slice(0, 5)

  const FighterTick = ({ x, y, payload }: { x?: number; y?: number; payload?: { value: string } }) => {
    const item = displayFighters.find((d) => d.name === payload?.value)
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
          onMouseEnter={(e) => { e.currentTarget.setAttribute('fill', '#60a5fa') }}
          onMouseLeave={(e) => { e.currentTarget.setAttribute('fill', '#a1a1aa') }}
        >
          {toTitleCase(payload?.value ?? '')}
        </text>
      </g>
    )
  }

  const chartData = displayFighters.map((f) => ({
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
      <TabContent activeKey={activeKey}>
      <ResponsiveContainer width="100%" height={expanded ? 320 : 180}>
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
          <Bar dataKey="differential" barSize={16} radius={[0, 4, 4, 0]} name="Differential" animationBegin={500} animationDuration={1200} animationEasing="ease-out">
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
      {fighters.length > 5 && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-2 flex w-full items-center justify-center gap-1 rounded-lg py-1.5 text-xs text-zinc-500 transition-colors hover:bg-white/[0.04] hover:text-zinc-300"
        >
          <ChevronDown className={`h-3.5 w-3.5 transition-transform ${expanded ? 'rotate-180' : ''}`} />
          {expanded ? 'Show Less' : `Show All ${fighters.length}`}
        </button>
      )}
      </TabContent>
    </div>
  )
}
