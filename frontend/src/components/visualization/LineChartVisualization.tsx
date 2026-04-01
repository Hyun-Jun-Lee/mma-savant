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
import { pivotLongToWide, isSecondsField, formatSeconds } from "./pivotData"

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

  const xAxisKey = xAxis || Object.keys(sampleRow).find(key =>
    typeof sampleRow[key] === 'string'
  ) || Object.keys(sampleRow)[0]

  // Pivot long→wide if multi-series long format detected
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
        <LineChart data={chartData} margin={CHART_MARGIN}>
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
        {chartData.length} data points • {yAxisKeys.join(", ")} trend
      </div>
    </div>
  )
}
