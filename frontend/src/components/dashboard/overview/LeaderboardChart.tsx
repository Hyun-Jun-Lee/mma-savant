'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { ChevronDown } from 'lucide-react'
import { toTitleCase } from '@/lib/utils'
import { PillTabs, TabContent } from '../PillTabs'
import { ChartCard } from '../ChartCard'
import { WeightClassFilter } from '../WeightClassFilter'
import { Skeleton } from '@/components/ui/skeleton'
import { chartApi } from '@/services/dashboardApi'
import type { OverviewResponse } from '@/types/dashboard'
import { ChartTooltip } from '../ChartTooltip'

const TABS = [
  { key: 'wins', label: 'Most Wins' },
  { key: 'winrate_min10', label: 'Win Rate (10+)' },
  { key: 'winrate_min15', label: 'Win Rate (15+)' },
  { key: 'winrate_min20', label: 'Win Rate (20+)' },
  { key: 'win_streak', label: 'Win Streak' },
] as const

type LeaderboardKey = (typeof TABS)[number]['key']

type Leaderboard = OverviewResponse['leaderboard']

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
  const isWinStreak = activeKey === 'win_streak'
  const isWinRate = !isWinStreak && activeKey !== 'wins'
  const dataKey = isWinStreak ? 'win_streak' : isWinRate ? 'win_rate' : 'wins'

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
              fighter && router.push(`/fighters/${fighter.fighter_id}`)
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
      description="Top fighters by wins and win rate"
      tooltip="총 승수 또는 승률 기준 상위 파이터를 보여줍니다. 최소 경기 수(10/15/20)로 필터링할 수 있습니다."
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
            <ResponsiveContainer width="100%" height={expanded ? 320 : 180}>
              <BarChart
                data={displayFighters}
                layout="vertical"
                margin={{ top: 5, right: 30, left: 10, bottom: 0 }}
              >
                <XAxis
                  type="number"
                  tick={{ fill: '#52525b', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  domain={isWinRate ? [0, 100] : undefined}
                  tickFormatter={isWinRate ? (v) => `${v}%` : isWinStreak ? (v) => `${v}W` : undefined}
                />
                <YAxis
                  dataKey="name"
                  type="category"
                  tick={FighterTick}
                  axisLine={false}
                  tickLine={false}
                  width={120}
                />
                <Tooltip
                  content={({ active, payload, label }) => {
                    if (!active || !payload?.length) return null
                    const val = payload[0]?.value as number
                    return (
                      <ChartTooltip active={active} label={label}>
                        <p className="text-zinc-400">
                          {isWinRate
                            ? `Win Rate: ${val.toFixed(1)}%`
                            : isWinStreak
                              ? `Streak: ${val} wins`
                              : `Wins: ${val}`}
                        </p>
                      </ChartTooltip>
                    )
                  }}
                />
                <Bar
                  dataKey={dataKey}
                  fill="#8b5cf6"
                  radius={[0, 4, 4, 0]}
                  barSize={16}
                  name={isWinStreak ? 'Win Streak' : isWinRate ? 'Win Rate' : 'Wins'}
                />
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
          )}
        </div>
      )}
    </ChartCard>
  )
}
