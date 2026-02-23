'use client'

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

export function TdSubCorrelationChart({ data }: TdSubCorrelationChartProps) {
  const { fighters, avg_td, avg_sub } = data

  const scatterData = fighters.map((f) => ({
    x: f.total_td_landed,
    y: f.sub_finishes,
    name: f.name,
    fights: f.total_fights,
  }))

  return (
    <ResponsiveContainer width="100%" height={280}>
      <ScatterChart margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
        <XAxis
          dataKey="x"
          type="number"
          name="TD Landed"
          tick={{ fill: '#52525b', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          label={{
            value: 'TD Landed',
            position: 'bottom',
            fill: '#a1a1aa',
            fontSize: 11,
            offset: -5,
          }}
        />
        <YAxis
          dataKey="y"
          type="number"
          name="Sub Finishes"
          tick={{ fill: '#52525b', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          label={{
            value: 'Sub Finishes',
            angle: -90,
            position: 'insideLeft',
            fill: '#a1a1aa',
            fontSize: 11,
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
        <Scatter data={scatterData} fill="#8b5cf6" fillOpacity={0.6}>
          <LabelList
            dataKey="name"
            position="top"
            fill="#a1a1aa"
            fontSize={10}
            content={({ index, x, y, value }) =>
              index === 0 ? (
                <text x={x as number} y={(y as number) - 8} textAnchor="middle" fill="#e4e4e7" fontSize={10}>
                  {value}
                </text>
              ) : null
            }
          />
        </Scatter>
      </ScatterChart>
    </ResponsiveContainer>
  )
}
