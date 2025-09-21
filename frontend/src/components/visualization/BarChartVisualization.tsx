"use client"

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from "recharts"

interface BarChartVisualizationProps {
  data: Record<string, string | number>[]
  xAxis?: string
  yAxis?: string
}

export function BarChartVisualization({ data, xAxis, yAxis }: BarChartVisualizationProps) {
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
  const xAxisKey = xAxis || Object.keys(sampleRow).find(key =>
    typeof sampleRow[key] === 'string'
  ) || Object.keys(sampleRow)[0]

  const yAxisKeys = yAxis ? [yAxis] : numericFields

  // 색상 팔레트 (차트별 다른 색상)
  const colors = [
    "#8884d8", "#82ca9d", "#ffc658", "#ff7c7c", "#8dd1e1",
    "#d084d0", "#87ceeb", "#dda0dd", "#98fb98", "#f0e68c"
  ]

  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey={xAxisKey}
            stroke="#9ca3af"
            fontSize={12}
          />
          <YAxis
            stroke="#9ca3af"
            fontSize={12}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#374151",
              border: "1px solid #6b7280",
              borderRadius: "8px",
              color: "#f9fafb"
            }}
          />
          {yAxisKeys.length > 1 && <Legend />}

          {yAxisKeys.map((key, index) => (
            <Bar
              key={key}
              dataKey={key}
              fill={colors[index % colors.length]}
              radius={[2, 2, 0, 0]}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>

      {/* 데이터 요약 */}
      <div className="mt-2 text-xs text-zinc-500 text-center">
        {data.length}개 항목 • {yAxisKeys.join(", ")} 기준
      </div>
    </div>
  )
}