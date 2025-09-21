"use client"

import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend
} from "recharts"

interface PieChartVisualizationProps {
  data: Record<string, string | number>[]
  xAxis?: string
  yAxis?: string
}

export function PieChartVisualization({ data, xAxis, yAxis }: PieChartVisualizationProps) {
  if (!data || data.length === 0) {
    return (
      <div className="p-8 text-center text-zinc-400">
        표시할 데이터가 없습니다.
      </div>
    )
  }

  // 파이 차트용 데이터 변환
  const sampleRow = data[0]
  const nameKey = xAxis || Object.keys(sampleRow).find(key =>
    typeof sampleRow[key] === 'string'
  ) || Object.keys(sampleRow)[0]

  const valueKey = yAxis || Object.keys(sampleRow).find(key =>
    typeof sampleRow[key] === 'number'
  ) || Object.keys(sampleRow)[1]

  // 파이 차트용 색상 팔레트
  const colors = [
    "#8884d8", "#82ca9d", "#ffc658", "#ff7c7c", "#8dd1e1",
    "#d084d0", "#87ceeb", "#dda0dd", "#98fb98", "#f0e68c",
    "#ffb347", "#deb887", "#ff6347", "#40e0d0", "#ee82ee"
  ]

  // 데이터 정규화 (name, value 형태로 변환)
  const pieData = data.map((item, index) => ({
    name: String(item[nameKey]),
    value: Number(item[valueKey]) || 0,
    originalData: item
  }))

  // 총합 계산
  const total = pieData.reduce((sum, item) => sum + item.value, 0)

  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={pieData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={(entry) => {
              const percent = ((entry.value / total) * 100).toFixed(1)
              return `${entry.name}: ${percent}%`
            }}
            outerRadius={100}
            fill="#8884d8"
            dataKey="value"
          >
            {pieData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={colors[index % colors.length]}
              />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: "#374151",
              border: "1px solid #6b7280",
              borderRadius: "8px",
              color: "#f9fafb"
            }}
            formatter={(value: number) => [
              `${value.toLocaleString()} (${((value / total) * 100).toFixed(1)}%)`,
              valueKey
            ]}
          />
          <Legend />
        </PieChart>
      </ResponsiveContainer>

      {/* 데이터 요약 */}
      <div className="mt-2 text-xs text-zinc-500 text-center">
        총 {pieData.length}개 항목 • 전체: {total.toLocaleString()}
      </div>
    </div>
  )
}