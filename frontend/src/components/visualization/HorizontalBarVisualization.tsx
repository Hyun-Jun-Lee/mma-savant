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
  const numericFields = Object.keys(sampleRow).filter(key =>
    typeof sampleRow[key] === 'number'
  )

  const categoryKey = xAxis || Object.keys(sampleRow).find(key =>
    typeof sampleRow[key] === 'string'
  ) || Object.keys(sampleRow)[0]

  const valueKeys = yAxis ? [yAxis] : numericFields

  const chartHeight = Math.max(320, data.length * 36)

  return (
    <div className="w-full" style={{ height: chartHeight }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 10, right: 30, left: 10, bottom: 5 }} barCategoryGap="20%">
          <XAxis type="number" tick={AXIS_TICK} {...AXIS_PROPS} />
          <YAxis
            type="category"
            dataKey={categoryKey}
            tick={{ ...AXIS_TICK, fontSize: 11 }}
            width={120}
            {...AXIS_PROPS}
          />
          <Tooltip cursor={TOOLTIP_CURSOR} {...TOOLTIP_STYLE} />
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
        {data.length} items ranked by {valueKeys.join(", ")}
      </div>
    </div>
  )
}
