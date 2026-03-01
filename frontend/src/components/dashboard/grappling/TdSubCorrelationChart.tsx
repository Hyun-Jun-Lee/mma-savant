'use client'

import { useRouter } from 'next/navigation'
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  Tooltip,
  LabelList,
  ReferenceLine,
  ResponsiveContainer,
} from 'recharts'
import type { TdSubCorrelation } from '@/types/dashboard'

interface TdSubCorrelationChartProps {
  data: TdSubCorrelation
}

const QUADRANT_LABELS = [
  { label: 'TD↑ SUB↑', className: 'top-1 right-2' },
  { label: 'TD↓ SUB↑', className: 'top-1 left-12' },
  { label: 'TD↑ SUB↓', className: 'bottom-14 right-2' },
  { label: 'TD↓ SUB↓', className: 'bottom-14 left-12' },
] as const

export function TdSubCorrelationChart({ data }: TdSubCorrelationChartProps) {
  const router = useRouter()
  const { fighters, avg_td, avg_sub } = data

  const scatterData = fighters.map((f) => ({
    x: f.total_td_landed,
    y: f.sub_finishes,
    name: f.name,
    fights: f.total_fights,
    fighter_id: f.fighter_id,
  }))

  // 사분면별 대표 선수 (중심에서 가장 먼 선수) 인덱스 계산
  const labelIndices = new Set<number>()
  const quadrants = [
    { highTd: true, highSub: true },
    { highTd: false, highSub: true },
    { highTd: true, highSub: false },
    { highTd: false, highSub: false },
  ]
  for (const q of quadrants) {
    let bestIdx = -1
    let bestDist = -1
    scatterData.forEach((f, i) => {
      const inQuadrant =
        (f.x >= avg_td) === q.highTd && (f.y >= avg_sub) === q.highSub
      if (!inQuadrant) return
      const dist = Math.hypot(f.x - avg_td, f.y - avg_sub)
      if (dist > bestDist) {
        bestDist = dist
        bestIdx = i
      }
    })
    if (bestIdx >= 0) labelIndices.add(bestIdx)
  }

  return (
    <div className="relative">
      {QUADRANT_LABELS.map(({ label, className }) => (
        <span
          key={label}
          className={`absolute text-[10px] font-medium text-zinc-400 pointer-events-none ${className}`}
        >
          {label}
        </span>
      ))}
      <ResponsiveContainer width="100%" height={400}>
        <ScatterChart margin={{ top: 24, right: 20, left: 10, bottom: 20 }}>
          <XAxis
            dataKey="x"
            type="number"
            name="TD Landed"
            tick={{ fill: '#52525b', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            label={{
              value: 'TD Landed',
              position: 'insideBottom',
              fill: '#a1a1aa',
              fontSize: 11,
              offset: -10,
            }}
          />
          <YAxis
            dataKey="y"
            type="number"
            name="Sub Finishes"
            tick={{ fill: '#52525b', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            width={40}
            label={{
              value: 'Sub Finishes',
              angle: -90,
              position: 'insideLeft',
              fill: '#a1a1aa',
              fontSize: 11,
              offset: 5,
            }}
          />
          <ReferenceLine
            x={avg_td}
            stroke="#3f3f46"
            strokeDasharray="4 4"
          />
          <ReferenceLine
            y={avg_sub}
            stroke="#3f3f46"
            strokeDasharray="4 4"
          />
          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload?.length) return null
              const d = payload[0]?.payload as (typeof scatterData)[number]
              if (!d) return null
              return (
                <div className="rounded-lg border border-white/[0.06] bg-zinc-900 px-3 py-2 text-xs shadow-lg">
                  <p className="mb-1 font-medium text-zinc-200">{d.name}</p>
                  <p className="text-zinc-400">TD Landed: {d.x}</p>
                  <p className="text-zinc-400">Sub Finishes: {d.y}</p>
                  <p className="text-zinc-400">Fights: {d.fights}</p>
                </div>
              )
            }}
          />
          <Scatter
            data={scatterData}
            fill="#8b5cf6"
            fillOpacity={0.6}
            cursor="pointer"
            onClick={(point: any) => {
              if (point?.fighter_id) router.push(`/fighters/${point.fighter_id}`)
            }}
          >
            <LabelList
              dataKey="name"
              position="top"
              fill="#a1a1aa"
              fontSize={10}
              content={({ index, x, y, value }) =>
                labelIndices.has(index!) ? (
                  <text x={x as number} y={(y as number) - 8} textAnchor="middle" fill="#e4e4e7" fontSize={10}>
                    {value}
                  </text>
                ) : null
              }
            />
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  )
}
