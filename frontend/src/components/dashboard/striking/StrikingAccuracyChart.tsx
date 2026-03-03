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
  Cell,
  LabelList,
} from 'recharts'
import { ChevronDown } from 'lucide-react'
import { PillTabs, TabContent } from '../PillTabs'
import { toTitleCase } from '@/lib/utils'
import type { MinFightsLeaderboard, StrikingAccuracyFighter } from '@/types/dashboard'
import { ChartTooltip } from '../ChartTooltip'

const TABS = [
  { key: 'min10', label: '10+ Fights' },
  { key: 'min15', label: '15+ Fights' },
  { key: 'min20', label: '20+ Fights' },
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

  const chartData = displayFighters.map((d) => ({ ...d, accLabel: `${d.accuracy}%` }))

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
          tick={<FighterTick />}
          axisLine={false}
          tickLine={false}
          width={100}
        />
        <Tooltip
          cursor={{ fill: 'rgba(255,255,255,0.04)' }}
          content={({ active, payload, label }) => {
            if (!active || !payload?.length) return null
            const d = payload[0]?.payload as StrikingAccuracyFighter & { accLabel: string }
            return (
              <ChartTooltip active={active} label={label}>
                <p className="text-zinc-400">Landed: {d.total_sig_landed}</p>
                <p className="text-zinc-400">Attempted: {d.total_sig_attempted}</p>
                <p className="text-zinc-400">Accuracy: {d.accuracy}%</p>
              </ChartTooltip>
            )
          }}
        />
        {/* Attempted (background bar) */}
        <Bar
          dataKey="total_sig_attempted"
          fill="#8b5cf6"
          fillOpacity={0.15}
          barSize={16}
          radius={[0, 3, 3, 0]}
          name="Attempted"
          animationBegin={200}
          animationDuration={900}
          animationEasing="ease-out"
        />
        {/* Landed (foreground bar) */}
        <Bar
          dataKey="total_sig_landed"
          barSize={16}
          radius={[0, 3, 3, 0]}
          name="Landed"
          animationBegin={500}
          animationDuration={900}
          animationEasing="ease-out"
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
