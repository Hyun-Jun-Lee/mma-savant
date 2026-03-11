"use client"

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
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

interface AreaChartVisualizationProps {
  data: Record<string, string | number>[]
  xAxis?: string
  yAxis?: string
}

export function AreaChartVisualization({ data, xAxis, yAxis }: AreaChartVisualizationProps) {
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

  const xAxisKey = xAxis || Object.keys(sampleRow).find(key =>
    typeof sampleRow[key] === 'string'
  ) || Object.keys(sampleRow)[0]

  const yAxisKeys = yAxis ? [yAxis] : numericFields

  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={CHART_MARGIN}>
          <defs>
            {yAxisKeys.map((key, index) => {
              const color = getSemanticColor(key, index)
              return (
                <linearGradient key={`grad-${key}`} id={`area-grad-${index}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={color} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={color} stopOpacity={0} />
                </linearGradient>
              )
            })}
          </defs>

          <XAxis dataKey={xAxisKey} tick={AXIS_TICK} {...AXIS_PROPS} />
          <YAxis tick={AXIS_TICK} {...AXIS_PROPS} />
          <Tooltip cursor={TOOLTIP_CURSOR} {...TOOLTIP_STYLE} />
          {yAxisKeys.length > 1 && <Legend {...LEGEND_STYLE} />}

          {yAxisKeys.map((key, index) => {
            const color = getSemanticColor(key, index)
            return (
              <Area
                key={key}
                type="monotone"
                dataKey={key}
                stroke={color}
                strokeWidth={2}
                fill={`url(#area-grad-${index})`}
                {...ANIMATION.line}
              />
            )
          })}
        </AreaChart>
      </ResponsiveContainer>

      <div className="mt-2 text-xs text-zinc-500 text-center">
        {data.length} data points • {yAxisKeys.join(", ")} trend
      </div>
    </div>
  )
}
