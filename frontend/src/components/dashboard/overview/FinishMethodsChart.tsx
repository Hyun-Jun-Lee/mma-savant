'use client'

import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from 'recharts'
import type { FinishMethod } from '@/types/dashboard'
import { FINISH_COLORS } from '@/lib/utils'

const FALLBACK_COLORS = ['#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#ec4899']

interface FinishMethodsChartProps {
  data: FinishMethod[]
}

export function FinishMethodsChart({ data }: FinishMethodsChartProps) {
  const total = data.reduce((sum, d) => sum + d.count, 0)
  const chartData = data.map((d) => ({ ...d }))

  return (
    <ResponsiveContainer width="100%" height={280}>
      <PieChart>
        <Pie
          data={chartData as Record<string, unknown>[]}
          dataKey="count"
          nameKey="method_category"
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={100}
          strokeWidth={0}
          animationBegin={400}
          animationDuration={1400}
          animationEasing="ease-out"
          startAngle={90}
          endAngle={-270}
        >
          {data.map((d, i) => (
            <Cell key={i} fill={FINISH_COLORS[d.method_category] ?? FALLBACK_COLORS[i % FALLBACK_COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            backgroundColor: '#18181b',
            border: '1px solid rgba(255,255,255,0.06)',
            borderRadius: '8px',
            fontSize: '12px',
          }}
          itemStyle={{ color: '#e4e4e7' }}
          labelStyle={{ color: '#a1a1aa' }}
          formatter={(value: number, name: string) => [
            `${value} (${((value / total) * 100).toFixed(1)}%)`,
            name,
          ]}
        />
        <Legend
          verticalAlign="bottom"
          iconType="circle"
          iconSize={8}
          wrapperStyle={{ fontSize: '11px', color: '#a1a1aa' }}
        />
      </PieChart>
    </ResponsiveContainer>
  )
}
