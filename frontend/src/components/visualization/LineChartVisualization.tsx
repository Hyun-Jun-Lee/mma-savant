"use client"

import {
  LineChart,
  Line,
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
  LEGEND_STYLE,
  CHART_MARGIN,
  getSemanticColor,
} from "@/lib/chartTheme"

interface LineChartVisualizationProps {
  data: Record<string, string | number>[]
  xAxis?: string
  yAxis?: string
}

export function LineChartVisualization({ data, xAxis, yAxis }: LineChartVisualizationProps) {
  if (!data || data.length === 0) {
    return (
      <div className="p-8 text-center text-zinc-400">
        No data to display.
      </div>
    )
  }

  const sampleRow = data[0]
  const numericFields = Object.keys(sampleRow).filter(key =>
    typeof sampleRow[key] === 'number'
  )

  const xAxisKey = xAxis || Object.keys(sampleRow)[0]
  const yAxisKeys = yAxis ? [yAxis] : numericFields

  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={CHART_MARGIN}>
          <XAxis dataKey={xAxisKey} tick={AXIS_TICK} {...AXIS_PROPS} />
          <YAxis tick={AXIS_TICK} {...AXIS_PROPS} />
          <Tooltip cursor={TOOLTIP_CURSOR} {...TOOLTIP_STYLE} />
          {yAxisKeys.length > 1 && <Legend {...LEGEND_STYLE} />}

          {yAxisKeys.map((key, index) => {
            const color = getSemanticColor(key, index)
            return (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                stroke={color}
                strokeWidth={2}
                dot={{ fill: color, strokeWidth: 2, r: 3 }}
                activeDot={{ r: 6, stroke: color, strokeWidth: 2, fill: '#18181b' }}
                {...ANIMATION.line}
              />
            )
          })}
        </LineChart>
      </ResponsiveContainer>

      <div className="mt-2 text-xs text-zinc-500 text-center">
        {data.length} data points • {yAxisKeys.join(", ")} trend
      </div>
    </div>
  )
}
