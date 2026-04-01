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
import { pivotLongToWide, isSecondsField, formatSeconds } from "./pivotData"

interface BarChartVisualizationProps {
  data: Record<string, string | number>[]
  xAxis?: string
  yAxis?: string
}

export function BarChartVisualization({ data, xAxis, yAxis }: BarChartVisualizationProps) {
  if (!data || data.length === 0) {
    return (
      <div className="p-8 text-center text-zinc-400">
        No data to display.
      </div>
    )
  }

  const sampleRow = data[0]

  const xAxisKey = xAxis || Object.keys(sampleRow).find(key =>
    typeof sampleRow[key] === 'string'
  ) || Object.keys(sampleRow)[0]

  const pivoted = pivotLongToWide(data, xAxisKey, yAxis)
  const chartData = pivoted ? pivoted.data : data
  const effectiveSample = chartData[0]

  const numericFields = Object.keys(effectiveSample).filter(key =>
    typeof effectiveSample[key] === 'number'
  )
  const yAxisKeys = pivoted ? pivoted.seriesKeys : (yAxis ? [yAxis] : numericFields)

  const secondsMode = pivoted
    ? isSecondsField(pivoted.valueColumn)
    : yAxisKeys.some(k => isSecondsField(k))

  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={CHART_MARGIN} barCategoryGap="20%">
          <XAxis dataKey={xAxisKey} tick={AXIS_TICK} {...AXIS_PROPS} />
          <YAxis
            tick={AXIS_TICK}
            {...AXIS_PROPS}
            tickFormatter={secondsMode ? formatSeconds : undefined}
          />
          <Tooltip
            cursor={TOOLTIP_CURSOR}
            {...TOOLTIP_STYLE}
            formatter={secondsMode ? (value: number) => formatSeconds(value) : undefined}
          />
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
        {chartData.length} items • by {yAxisKeys.join(", ")}
      </div>
    </div>
  )
}
