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
  CHART_COLORS,
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

interface StackedBarVisualizationProps {
  data: Record<string, string | number>[]
  xAxis?: string
  yAxis?: string
}

export function StackedBarVisualization({ data, xAxis, yAxis }: StackedBarVisualizationProps) {
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

  const categoryKey = xAxis || Object.keys(sampleRow).find(key =>
    typeof sampleRow[key] === 'string'
  ) || Object.keys(sampleRow)[0]

  const stackKeys = yAxis ? [yAxis] : numericFields

  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={CHART_MARGIN} barCategoryGap="20%">
          <XAxis dataKey={categoryKey} tick={AXIS_TICK} {...AXIS_PROPS} />
          <YAxis tick={AXIS_TICK} {...AXIS_PROPS} />
          <Tooltip cursor={TOOLTIP_CURSOR} {...TOOLTIP_STYLE} />
          <Legend {...LEGEND_STYLE} />

          {stackKeys.map((key, index) => (
            <Bar
              key={key}
              dataKey={key}
              stackId="stack"
              fill={getSemanticColor(key, index)}
              radius={index === stackKeys.length - 1 ? [...BAR_RADIUS] : [0, 0, 0, 0]}
              {...ANIMATION.bar}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>

      <div className="mt-2 text-xs text-zinc-500 text-center">
        {data.length} items • stacked by {stackKeys.join(", ")}
      </div>
    </div>
  )
}
