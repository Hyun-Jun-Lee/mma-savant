"use client"

import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ZAxis
} from "recharts"

interface ScatterPlotVisualizationProps {
  data: Record<string, string | number>[]
  xAxis?: string
  yAxis?: string
}

export function ScatterPlotVisualization({ data, xAxis, yAxis }: ScatterPlotVisualizationProps) {
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

  // x축과 y축 결정
  const xAxisKey = xAxis || numericFields[0] || Object.keys(sampleRow)[0]
  const yAxisKey = yAxis || numericFields[1] || Object.keys(sampleRow)[1]

  // 산점도용 데이터 변환
  const scatterData = data.map((item, index) => ({
    x: Number(item[xAxisKey]) || index,
    y: Number(item[yAxisKey]) || 0,
    z: 50, // 점 크기 (고정값)
    name: item.name || item[Object.keys(item)[0]] || `Point ${index + 1}`,
    originalData: item
  }))

  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart
          margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            type="number"
            dataKey="x"
            name={xAxisKey}
            stroke="#9ca3af"
            fontSize={12}
          />
          <YAxis
            type="number"
            dataKey="y"
            name={yAxisKey}
            stroke="#9ca3af"
            fontSize={12}
          />
          <ZAxis type="number" dataKey="z" range={[50, 200]} />
          <Tooltip
            cursor={{ strokeDasharray: "3 3" }}
            contentStyle={{
              backgroundColor: "#374151",
              border: "1px solid #6b7280",
              borderRadius: "8px",
              color: "#f9fafb"
            }}
            formatter={(value: number, name: string) => [
              value.toLocaleString(),
              name === "x" ? xAxisKey : name === "y" ? yAxisKey : name
            ]}
            labelFormatter={(label) => `${label}`}
          />
          <Scatter
            name="데이터 포인트"
            data={scatterData}
            fill="#8884d8"
          />
        </ScatterChart>
      </ResponsiveContainer>

      {/* 데이터 요약 */}
      <div className="mt-2 text-xs text-zinc-500 text-center">
        {data.length}개 데이터 포인트 • X: {xAxisKey}, Y: {yAxisKey}
      </div>
    </div>
  )
}