'use client'

import { useRef, useCallback } from 'react'
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Label,
} from 'recharts'
import type { FinishMethod } from '@/types/dashboard'
import { FINISH_COLORS } from '@/lib/utils'

const FALLBACK_COLORS = ['#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#ec4899']
const RADIAN = Math.PI / 180
const OR = 78
const IR = 42
const ELBOW_R = OR + 10
const TEXT_R = OR + 28
const MIN_GAP = 32

interface LabelPos {
  edgeX: number; edgeY: number
  elbowX: number; elbowY: number
  textX: number; finalY: number
  anchor: 'start' | 'end'
}

function computePositions(
  data: FinishMethod[], total: number, cx: number, cy: number,
): LabelPos[] {
  let angle = 90
  const items = data.map((d) => {
    const sweep = (d.count / total) * 360
    const mid = angle - sweep / 2
    angle -= sweep
    const cos = Math.cos(-mid * RADIAN)
    const sin = Math.sin(-mid * RADIAN)
    const isRight = cos >= 0
    return {
      edgeX: cx + OR * cos,
      edgeY: cy + OR * sin,
      elbowX: cx + ELBOW_R * cos,
      elbowY: cy + ELBOW_R * sin,
      rawY: cy + ELBOW_R * sin,
      isRight,
    }
  })

  const finalYs = items.map((item) => item.rawY)
  const indexed = items.map((item, i) => ({ ...item, i }))
  const right = indexed.filter((x) => x.isRight).sort((a, b) => a.rawY - b.rawY)
  const left = indexed.filter((x) => !x.isRight).sort((a, b) => a.rawY - b.rawY)

  for (const group of [right, left]) {
    if (group.length === 0) continue
    for (let j = 1; j < group.length; j++) {
      if (finalYs[group[j].i] - finalYs[group[j - 1].i] < MIN_GAP) {
        finalYs[group[j].i] = finalYs[group[j - 1].i] + MIN_GAP
      }
    }
    const rawCog = group.reduce((s, g) => s + g.rawY, 0) / group.length
    const adjCog = group.reduce((s, g) => s + finalYs[g.i], 0) / group.length
    const shift = rawCog - adjCog
    group.forEach((g) => { finalYs[g.i] += shift })
  }

  return items.map((item, i) => ({
    edgeX: item.edgeX,
    edgeY: item.edgeY,
    elbowX: item.elbowX,
    elbowY: item.elbowY,
    textX: item.isRight ? cx + TEXT_R : cx - TEXT_R,
    finalY: finalYs[i],
    anchor: (item.isRight ? 'start' : 'end') as 'start' | 'end',
  }))
}

interface FinishMethodsChartProps {
  data: FinishMethod[]
}

export function FinishMethodsChart({ data }: FinishMethodsChartProps) {
  const total = data.reduce((sum, d) => sum + d.count, 0)
  const chartData = data.map((d) => ({ ...d }))
  const posRef = useRef<LabelPos[] | null>(null)

  /* eslint-disable @typescript-eslint/no-explicit-any */
  const renderLabel = useCallback(
    (props: any) => {
      const { cx, cy, index } = props

      if (index === 0) {
        posRef.current = computePositions(data, total, cx, cy)
      }

      const pos = posRef.current?.[index]
      if (!pos) return null

      const d = data[index]
      const pct = ((d.count / total) * 100).toFixed(1)
      const color =
        FINISH_COLORS[d.method_category] ??
        FALLBACK_COLORS[index % FALLBACK_COLORS.length]
      const pad = pos.anchor === 'start' ? 5 : -5

      return (
        <g>
          <polyline
            points={`${pos.edgeX},${pos.edgeY} ${pos.elbowX},${pos.elbowY} ${pos.textX},${pos.finalY}`}
            fill="none"
            stroke={color}
            strokeWidth={1}
            strokeOpacity={0.4}
          />
          <circle cx={pos.textX} cy={pos.finalY} r={2} fill={color} />
          <text
            x={pos.textX + pad}
            y={pos.finalY - 3}
            textAnchor={pos.anchor}
            fill="#d4d4d8"
            fontSize={11}
            fontWeight={500}
          >
            {d.method_category}
          </text>
          <text
            x={pos.textX + pad}
            y={pos.finalY + 10}
            textAnchor={pos.anchor}
            fill="#71717a"
            fontSize={10}
          >
            {d.count.toLocaleString()} ({pct}%)
          </text>
        </g>
      )
    },
    [data, total],
  )
  /* eslint-enable @typescript-eslint/no-explicit-any */

  return (
    <ResponsiveContainer width="100%" height={280}>
      <PieChart>
        <Pie
          data={chartData as Record<string, unknown>[]}
          dataKey="count"
          nameKey="method_category"
          cx="50%"
          cy="50%"
          innerRadius={IR}
          outerRadius={OR}
          strokeWidth={0}
          animationBegin={400}
          animationDuration={1400}
          animationEasing="ease-out"
          startAngle={90}
          endAngle={-270}
          label={renderLabel}
          labelLine={false}
        >
          {data.map((d, i) => (
            <Cell
              key={i}
              fill={
                FINISH_COLORS[d.method_category] ??
                FALLBACK_COLORS[i % FALLBACK_COLORS.length]
              }
            />
          ))}
          <Label
            value={total.toLocaleString()}
            position="center"
            dy={-4}
            style={{ fill: '#e4e4e7', fontSize: '16px', fontWeight: 600 }}
          />
          <Label
            value="Total"
            position="center"
            dy={12}
            style={{ fill: '#71717a', fontSize: '10px' }}
          />
        </Pie>
      </PieChart>
    </ResponsiveContainer>
  )
}
