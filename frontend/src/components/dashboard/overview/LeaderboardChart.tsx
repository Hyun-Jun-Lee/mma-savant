'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
  LabelList,
  ResponsiveContainer,
} from 'recharts'
import { ChevronDown } from 'lucide-react'
import { toTitleCase, FINISH_COLORS } from '@/lib/utils'
import { PillTabs, TabContent } from '../PillTabs'
import { ChartCard } from '../ChartCard'
import { WeightClassFilter } from '../WeightClassFilter'
import { Skeleton } from '@/components/ui/skeleton'
import { chartApi } from '@/services/dashboardApi'
import type { OverviewResponse } from '@/types/dashboard'
import { ChartTooltip } from '../ChartTooltip'

const TABS = [
  { key: 'wins', label: 'Most Wins' },
  { key: 'win_streak', label: 'Win Streak' },
  { key: 'lose_streak', label: 'Lose Streak' },
] as const

type LeaderboardKey = (typeof TABS)[number]['key']

type Leaderboard = OverviewResponse['leaderboard']

const STACK_COLORS = {
  ko_tko: FINISH_COLORS.ko_tko ?? '#ef4444',
  submission: FINISH_COLORS.submission ?? '#a855f7',
  decision: FINISH_COLORS.decision ?? '#06b6d4',
}

interface LeaderboardChartProps {
  initialData: Leaderboard | undefined
  parentLoading: boolean
  error: string | null
  onRetry: () => void
  index?: number
}

export function LeaderboardChart({
  initialData,
  parentLoading,
  error,
  onRetry,
  index,
}: LeaderboardChartProps) {
  const router = useRouter()
  const [activeKey, setActiveKey] = useState<LeaderboardKey>('wins')
  const [weightClassId, setWeightClassId] = useState<number | undefined>()
  const [ufcOnly, setUfcOnly] = useState(true)
  const [localData, setLocalData] = useState<Leaderboard | undefined>()
  const [loading, setLoading] = useState(false)

  // Fetch when weightClassId or ufcOnly changes from initial state
  useEffect(() => {
    // Both at initial values -> use tab initial data
    if (weightClassId === undefined && ufcOnly === true) {
      setLocalData(undefined)
      return
    }

    let cancelled = false
    setLoading(true)
    chartApi
      .getLeaderboard(weightClassId, ufcOnly)
      .then((result) => {
        if (!cancelled) setLocalData(result)
      })
      .catch(console.error)
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [weightClassId, ufcOnly])

  const [expanded, setExpanded] = useState(false)

  const displayData = localData ?? initialData

  const fighters = displayData?.[activeKey]
  const displayFighters = expanded ? fighters : fighters?.slice(0, 5)
  const isStreakTab = activeKey === 'win_streak' || activeKey === 'lose_streak'

  /* eslint-disable @typescript-eslint/no-explicit-any */
  const FighterTick = useCallback(
    (props: any) => {
      const { x, y, payload } = props
      const fighter = displayFighters?.find((f: any) => f.name === payload.value)
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
            onClick={() =>
              fighter && router.push(`/fighters/${(fighter as any).fighter_id}`)
            }
            onMouseEnter={(e) => {
              e.currentTarget.setAttribute('fill', '#60a5fa')
            }}
            onMouseLeave={(e) => {
              e.currentTarget.setAttribute('fill', '#a1a1aa')
            }}
          >
            {toTitleCase(payload.value)}
          </text>
        </g>
      )
    },
    [displayFighters, router]
  )
  /* eslint-enable @typescript-eslint/no-explicit-any */

  return (
    <ChartCard
      title="Leaderboard"
      description="Top fighters by wins and win streak"
      tooltip="Shows top fighters by total wins (stacked by finish method: KO/TKO, Submission, Decision) or win streak."
      headerRight={
        <WeightClassFilter value={weightClassId} onChange={setWeightClassId} />
      }
      loading={!initialData && parentLoading}
      error={error}
      onRetry={onRetry}
      index={index}
    >
      {loading ? (
        <Skeleton className="h-[360px] bg-white/[0.06]" />
      ) : (
        <div>
          <div className="mb-3 flex items-center justify-between gap-3">
            <PillTabs
              tabs={[...TABS]}
              activeKey={activeKey}
              onChange={(k) => setActiveKey(k as LeaderboardKey)}
              size="sm"
            />
            <button
              onClick={() => setUfcOnly(!ufcOnly)}
              className="flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium transition-colors bg-white/[0.04] hover:bg-white/[0.08]"
            >
              <span className={ufcOnly ? 'text-zinc-500' : 'text-white'}>
                All MMA
              </span>
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
              <span className={ufcOnly ? 'text-amber-400' : 'text-zinc-500'}>
                UFC Only
              </span>
            </button>
          </div>
          {fighters && (
            <TabContent activeKey={activeKey}>
              {isStreakTab ? (
                <StreakChart
                  data={displayFighters}
                  FighterTick={FighterTick}
                  expanded={expanded}
                  dataKey={activeKey === 'win_streak' ? 'win_streak' : 'lose_streak'}
                  color={activeKey === 'win_streak' ? '#8b5cf6' : '#ef4444'}
                  suffix={activeKey === 'win_streak' ? 'W' : 'L'}
                />
              ) : (
                <WinsStackedChart
                  data={displayFighters}
                  FighterTick={FighterTick}
                  expanded={expanded}
                />
              )}
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
          )}
        </div>
      )}
    </ChartCard>
  )
}

/* eslint-disable @typescript-eslint/no-explicit-any */

function WinsStackedChart({
  data,
  FighterTick,
  expanded,
}: {
  data: any[] | undefined
  FighterTick: any
  expanded: boolean
}) {
  if (!data?.length) return null

  const chartData = data.map((f: any) => ({
    ...f,
    name: f.name,
    ko_tko_wins: f.ko_tko_wins ?? 0,
    sub_wins: f.sub_wins ?? 0,
    dec_wins: f.dec_wins ?? 0,
  }))

  const opacityFor = (i: number) => Math.max(0.2, 1 - i * 0.13)

  return (
    <>
      <div className="flex items-center gap-4 pb-1 text-[11px] text-zinc-400">
        {[
          { label: 'KO/TKO', color: STACK_COLORS.ko_tko },
          { label: 'Submission', color: STACK_COLORS.submission },
          { label: 'Decision', color: STACK_COLORS.decision },
        ].map((item) => (
          <span key={item.label} className="flex items-center gap-1.5">
            <span className="inline-block h-2 w-2 rounded-full" style={{ background: item.color }} />
            {item.label}
          </span>
        ))}
      </div>
      <ResponsiveContainer width="100%" height={expanded ? Math.max(320, chartData.length * 34) : 180}>
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 5, right: 40, left: 10, bottom: 0 }}
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
            tick={FighterTick}
            axisLine={false}
            tickLine={false}
            width={120}
            interval={0}
          />
          <Tooltip
            cursor={{ fill: 'rgba(255,255,255,0.04)' }}
            content={({ active, payload }) => {
              if (!active || !payload?.length) return null
              const d = payload[0]?.payload as any
              return (
                <ChartTooltip active={active} label={toTitleCase(d.name)}>
                  <p style={{ color: STACK_COLORS.ko_tko }}>KO/TKO: {d.ko_tko_wins}</p>
                  <p style={{ color: STACK_COLORS.submission }}>Submission: {d.sub_wins}</p>
                  <p style={{ color: STACK_COLORS.decision }}>Decision: {d.dec_wins}</p>
                </ChartTooltip>
              )
            }}
          />
          <Bar dataKey="ko_tko_wins" stackId="a" fill={STACK_COLORS.ko_tko} barSize={16}>
            {chartData.map((_: any, i: number) => (
              <Cell key={i} fillOpacity={opacityFor(i)} />
            ))}
          </Bar>
          <Bar dataKey="sub_wins" stackId="a" fill={STACK_COLORS.submission} barSize={16}>
            {chartData.map((_: any, i: number) => (
              <Cell key={i} fillOpacity={opacityFor(i)} />
            ))}
          </Bar>
          <Bar dataKey="dec_wins" stackId="a" fill={STACK_COLORS.decision} radius={[0, 4, 4, 0]} barSize={16}>
            {chartData.map((_: any, i: number) => (
              <Cell key={i} fillOpacity={opacityFor(i)} />
            ))}
            <LabelList
              dataKey="wins"
              position="right"
              fill="#a1a1aa"
              fontSize={10}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </>
  )
}

function StreakChart({
  data,
  FighterTick,
  expanded,
  dataKey,
  color,
  suffix,
}: {
  data: any[] | undefined
  FighterTick: any
  expanded: boolean
  dataKey: string
  color: string
  suffix: string
}) {
  if (!data?.length) return null

  const opacityFor = (i: number) => Math.max(0.2, 1 - i * 0.13)
  const label = suffix === 'W' ? 'wins' : 'losses'

  return (
    <ResponsiveContainer width="100%" height={expanded ? Math.max(320, data.length * 34) : 180}>
      <BarChart
        data={data}
        layout="vertical"
        margin={{ top: 5, right: 40, left: 10, bottom: 0 }}
      >
        <XAxis
          type="number"
          tick={{ fill: '#52525b', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          tickFormatter={(v) => `${v}${suffix}`}
        />
        <YAxis
          dataKey="name"
          type="category"
          tick={FighterTick}
          axisLine={false}
          tickLine={false}
          width={120}
          interval={0}
        />
        <Tooltip
          cursor={{ fill: 'rgba(255,255,255,0.04)' }}
          content={({ active, payload, label: tooltipLabel }) => {
            if (!active || !payload?.length) return null
            const val = payload[0]?.value as number
            return (
              <ChartTooltip active={active} label={tooltipLabel}>
                <p className="text-zinc-400">Streak: {val} {label}</p>
              </ChartTooltip>
            )
          }}
        />
        <Bar
          dataKey={dataKey}
          fill={color}
          radius={[0, 4, 4, 0]}
          barSize={16}
        >
          {data.map((_: any, i: number) => (
            <Cell key={i} fillOpacity={opacityFor(i)} />
          ))}
          <LabelList
            dataKey={dataKey}
            position="right"
            fill="#a1a1aa"
            fontSize={10}
            formatter={(v: unknown) => `${v}${suffix}`}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

/* eslint-enable @typescript-eslint/no-explicit-any */
