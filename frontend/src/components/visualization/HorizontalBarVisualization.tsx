"use client"

import {
  BarChart,
  Bar,
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
  getSemanticColor,
} from "@/lib/chartTheme"
import { pivotLongToWide, isSecondsField, formatSeconds } from "./pivotData"

interface HorizontalBarVisualizationProps {
  data: Record<string, string | number>[]
  xAxis?: string
  yAxis?: string
}

export function HorizontalBarVisualization({ data, xAxis, yAxis }: HorizontalBarVisualizationProps) {
  if (!data || data.length === 0) {
    return (
      <div className="p-8 text-center text-zinc-400">
        No data to display.
      </div>
    )
  }

  const sampleRow = data[0]

  // 수평 바 차트: Y축=카테고리(이름), X축=값(숫자)
  const categoryKey = yAxis || Object.keys(sampleRow).find(key =>
    typeof sampleRow[key] === 'string'
  ) || Object.keys(sampleRow)[0]

  const pivoted = pivotLongToWide(data, categoryKey, xAxis)
  const chartData = pivoted ? pivoted.data : data
  const effectiveSample = chartData[0]

  const numericFields = Object.keys(effectiveSample).filter(key =>
    typeof effectiveSample[key] === 'number'
  )
  const valueKeys = pivoted ? pivoted.seriesKeys : (xAxis ? [xAxis] : numericFields)

  const secondsMode = pivoted
    ? isSecondsField(pivoted.valueColumn)
    : valueKeys.some(k => isSecondsField(k))

  const chartHeight = Math.max(320, chartData.length * 36)

  return (
    <div className="w-full" style={{ height: chartHeight }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} layout="vertical" margin={{ top: 10, right: 30, left: 10, bottom: 5 }} barCategoryGap="20%">
          <XAxis
            type="number"
            tick={AXIS_TICK}
            {...AXIS_PROPS}
            tickFormatter={secondsMode ? formatSeconds : undefined}
          />
          <YAxis
            type="category"
            dataKey={categoryKey}
            tick={{ ...AXIS_TICK, fontSize: 11 }}
            width={120}
            {...AXIS_PROPS}
          />
          <Tooltip
            cursor={TOOLTIP_CURSOR}
            {...TOOLTIP_STYLE}
            formatter={secondsMode ? (value: number) => formatSeconds(value) : undefined}
          />
          {valueKeys.length > 1 && <Legend {...LEGEND_STYLE} />}

          {valueKeys.map((key, index) => (
            <Bar
              key={key}
              dataKey={key}
              fill={getSemanticColor(key, index)}
              radius={[0, 4, 4, 0]}
              {...ANIMATION.bar}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>

      <div className="mt-2 text-xs text-zinc-500 text-center">
        {chartData.length} items ranked by {valueKeys.join(", ")}
      </div>
    </div>
  )
}
