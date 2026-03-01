'use client'

import { useRouter } from 'next/navigation'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  LabelList,
} from 'recharts'
import type { KoTkoLeader } from '@/types/dashboard'

interface KoTkoLeadersChartProps {
  data: KoTkoLeader[]
}

export function KoTkoLeadersChart({ data }: KoTkoLeadersChartProps) {
  const router = useRouter()

  const FighterTick = ({ x, y, payload }: any) => {
    const item = data.find((d) => d.name === payload.value)
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
          onClick={() => item && router.push(`/fighters/${item.fighter_id}`)}
        >
          {payload.value}
        </text>
      </g>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
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
          cursor={false}
          contentStyle={{
            backgroundColor: '#18181b',
            border: '1px solid rgba(255,255,255,0.06)',
            borderRadius: '8px',
            fontSize: '12px',
          }}
          itemStyle={{ color: '#e4e4e7' }}
          labelStyle={{ color: '#a1a1aa' }}
        />
        <Bar
          dataKey="ko_tko_finishes"
          fill="#ef4444"
          radius={[0, 4, 4, 0]}
          barSize={16}
          name="KO/TKO"
        >
          <LabelList
            dataKey="ko_tko_finishes"
            position="right"
            style={{ fill: '#a1a1aa', fontSize: 11 }}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
