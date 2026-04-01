"use client"

import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from "recharts"
import {
  TOOLTIP_STYLE,
  ANIMATION,
  PIE_DONUT,
  LEGEND_STYLE,
  getSemanticColor,
} from "@/lib/chartTheme"

interface PieChartVisualizationProps {
  data: Record<string, string | number>[]
  xAxis?: string
  yAxis?: string
}

export function PieChartVisualization({ data, xAxis, yAxis }: PieChartVisualizationProps) {
  if (!data || data.length === 0) {
    return (
      <div className="p-8 text-center text-zinc-400">
        No data to display.
      </div>
    )
  }

  const sampleRow = data[0]
  const nameKey = xAxis || Object.keys(sampleRow).find(key =>
    typeof sampleRow[key] === 'string'
  ) || Object.keys(sampleRow)[0]

  const valueKey = yAxis || Object.keys(sampleRow).find(key =>
    typeof sampleRow[key] === 'number'
  ) || Object.keys(sampleRow)[1]

  const pieData = data.map((item) => ({
    name: String(item[nameKey]),
    value: Number(item[valueKey]) || 0,
  }))

  const total = pieData.reduce((sum, item) => sum + item.value, 0)

  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={pieData}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            {...PIE_DONUT}
            {...ANIMATION.pie}
          >
            {pieData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={getSemanticColor(entry.name, index)}
              />
            ))}
          </Pie>

          {/* Donut center total */}
          <text
            x="50%"
            y="48%"
            textAnchor="middle"
            dominantBaseline="middle"
            className="fill-zinc-200 text-xl font-semibold"
          >
            {total.toLocaleString()}
          </text>
          <text
            x="50%"
            y="57%"
            textAnchor="middle"
            dominantBaseline="middle"
            className="fill-zinc-500 text-[10px]"
          >
            Total
          </text>

          <Tooltip
            {...TOOLTIP_STYLE}
            formatter={(value: number, name: string) => [
              `${value.toLocaleString()} (${((value / total) * 100).toFixed(1)}%)`,
              name
            ]}
          />
          <Legend {...LEGEND_STYLE} />
        </PieChart>
      </ResponsiveContainer>

      <div className="mt-2 text-xs text-zinc-500 text-center">
        {pieData.length} items total • Grand total: {total.toLocaleString()}
      </div>
    </div>
  )
}
