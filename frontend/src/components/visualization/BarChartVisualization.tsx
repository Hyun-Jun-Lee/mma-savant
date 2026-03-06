"use client"

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend
} from "recharts"
import {
  AXIS_TICK,
  AXIS_PROPS,
  TOOLTIP_STYLE,
  TOOLTIP_CURSOR,
  ANIMATION,
  BAR_RADIUS,
  LEGEND_STYLE,
  CHART_MARGIN,
  getSemanticColor,
} from "@/lib/chartTheme"

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

  const sampleRow = data[0]
  const numericFields = Object.keys(sampleRow).filter(key =>
    typeof sampleRow[key] === 'number'
  )

  const xAxisKey = xAxis || Object.keys(sampleRow).find(key =>
    typeof sampleRow[key] === 'string'
  ) || Object.keys(sampleRow)[0]

  const yAxisKeys = yAxis ? [yAxis] : numericFields

  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={CHART_MARGIN}>
          <XAxis dataKey={xAxisKey} tick={AXIS_TICK} {...AXIS_PROPS} />
          <YAxis tick={AXIS_TICK} {...AXIS_PROPS} />
          <Tooltip cursor={TOOLTIP_CURSOR} {...TOOLTIP_STYLE} />
          {yAxisKeys.length > 1 && <Legend {...LEGEND_STYLE} />}

          {yAxisKeys.map((key, index) => (
            <Bar
              key={key}
              dataKey={key}
              fill={getSemanticColor(key, index)}
              radius={[...BAR_RADIUS]}
              {...ANIMATION.bar}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>

      <div className="mt-2 text-xs text-zinc-500 text-center">
        {data.length}개 항목 • {yAxisKeys.join(", ")} 기준
      </div>
    </div>
  )
}
