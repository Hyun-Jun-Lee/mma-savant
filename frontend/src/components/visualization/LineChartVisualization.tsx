"use client"

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from "recharts"

interface LineChartVisualizationProps {
  data: Record<string, string | number>[]
  xAxis?: string
  yAxis?: string
}

export function LineChartVisualization({ data, xAxis, yAxis }: LineChartVisualizationProps) {
  if (!data || data.length === 0) {
    return (
      <div className="p-8 text-center text-zinc-400">
        표시할 데이터가 없습니다.
      </div>
    )
  }

  // 숫자형 데이터 필드 찾기
  const sampleRow = data[0]
  const numericFields = Object.keys(sampleRow).filter(key =>
    typeof sampleRow[key] === 'number'
  )

  // x축과 y축이 지정되지 않은 경우 추론
  const xAxisKey = xAxis || Object.keys(sampleRow)[0]
  const yAxisKeys = yAxis ? [yAxis] : numericFields

  // 대시보드 시맨틱 컬러 기반 팔레트
  const colors = [
    "#8b5cf6", "#10b981", "#f59e0b", "#ef4444", "#06b6d4",
    "#a855f7", "#f97316", "#14b8a6", "#60a5fa", "#71717a"
  ]

  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={data}
          margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
          <XAxis
            dataKey={xAxisKey}
            tick={{ fill: '#52525b', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: '#52525b', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#18181b",
              border: "1px solid rgba(255,255,255,0.06)",
              borderRadius: "8px",
              fontSize: "12px",
            }}
            itemStyle={{ color: '#e4e4e7' }}
            labelStyle={{ color: '#a1a1aa' }}
          />
          {yAxisKeys.length > 1 && <Legend />}

          {yAxisKeys.map((key, index) => (
            <Line
              key={key}
              type="monotone"
              dataKey={key}
              stroke={colors[index % colors.length]}
              strokeWidth={2}
              dot={{ fill: colors[index % colors.length], strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6, stroke: colors[index % colors.length], strokeWidth: 2 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>

      {/* 데이터 요약 */}
      <div className="mt-2 text-xs text-zinc-500 text-center">
        {data.length}개 데이터 포인트 • {yAxisKeys.join(", ")} 추이
      </div>
    </div>
  )
}