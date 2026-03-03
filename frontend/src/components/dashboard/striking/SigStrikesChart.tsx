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
import { ChevronDown } from 'lucide-react'
import { toTitleCase } from '@/lib/utils'
import { PillTabs, TabContent } from '../PillTabs'
import type { MinFightsLeaderboard, SigStrikesLeader } from '@/types/dashboard'

const TABS = [
  { key: 'min10', label: '10+ Fights' },
  { key: 'min15', label: '15+ Fights' },
  { key: 'min20', label: '20+ Fights' },
] as const

type MinKey = (typeof TABS)[number]['key']

interface SigStrikesChartProps {
  data: MinFightsLeaderboard<SigStrikesLeader>
}

export function SigStrikesChart({ data }: SigStrikesChartProps) {
  const router = useRouter()
  const [activeKey, setActiveKey] = useState<MinKey>('min10')
  const [expanded, setExpanded] = useState(false)
  const fighters = data[activeKey]
  const displayFighters = expanded ? fighters : fighters.slice(0, 5)

  const avg =
    displayFighters.length > 0
      ? displayFighters.reduce((sum, d) => sum + d.sig_str_per_fight, 0) / displayFighters.length
      : 0

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

  // dot 크기를 경기 수에 비례
  const scatterData = displayFighters.map((d) => ({
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
    <TabContent activeKey={activeKey}>
    <ResponsiveContainer width="100%" height={expanded ? 320 : 180}>
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
          tick={<FighterTick />}
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
          animationBegin={400}
          animationDuration={1000}
          animationEasing="ease-out"
        />
        {/* Dot (scatter at end) */}
        <Scatter
          dataKey="sig_str_per_fight"
          fill="rgba(245,158,11,0.85)"
          name="Sig/Fight"
          animationBegin={700}
          animationDuration={800}
          animationEasing="ease-out"
        />
      </ComposedChart>
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
