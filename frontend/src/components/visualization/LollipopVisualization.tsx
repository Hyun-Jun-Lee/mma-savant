"use client"

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Cell,
} from "recharts"
import {
  CHART_COLORS,
  AXIS_TICK,
  AXIS_PROPS,
  TOOLTIP_STYLE,
  TOOLTIP_CURSOR,
  ANIMATION,
  CHART_MARGIN,
  getSemanticColor,
} from "@/lib/chartTheme"
import { isSecondsField, formatSeconds } from "./pivotData"
import { defaultFormatter, defaultTickFormatter } from "@/lib/chartTheme"

interface LollipopVisualizationProps {
  data: Record<string, string | number>[]
  xAxis?: string
  yAxis?: string
}

export function LollipopVisualization({ data, xAxis, yAxis }: LollipopVisualizationProps) {
  if (!data || data.length === 0) {
    return (
      <div className="p-8 text-center text-zinc-400">
        No data to display.
      </div>
    )
  }

  const sampleRow = data[0]
  const categoryKey = xAxis || Object.keys(sampleRow).find(key =>
    typeof sampleRow[key] === 'string'
  ) || Object.keys(sampleRow)[0]

  const numericFields = Object.keys(sampleRow).filter(key =>
    typeof sampleRow[key] === 'number'
  )
  const valueKey = yAxis || numericFields[0] || Object.keys(sampleRow)[1]

  const secondsMode = isSecondsField(valueKey)
  const avg = data.reduce((sum, item) => sum + Number(item[valueKey] || 0), 0) / data.length

  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={CHART_MARGIN}>
          <XAxis dataKey={categoryKey} tick={AXIS_TICK} {...AXIS_PROPS} />
          <YAxis
            tick={AXIS_TICK}
            {...AXIS_PROPS}
            tickFormatter={secondsMode ? formatSeconds : defaultTickFormatter}
          />
          <Tooltip
            cursor={TOOLTIP_CURSOR}
            {...TOOLTIP_STYLE}
            formatter={secondsMode ? (value: number) => formatSeconds(value) : defaultFormatter}
          />

          <ReferenceLine
            y={avg}
            stroke="#71717a"
            strokeDasharray="4 4"
            label={{
              value: secondsMode ? `Avg: ${formatSeconds(avg)}` : `Avg: ${avg.toFixed(1)}`,
              position: 'insideTopRight',
              fill: '#a1a1aa',
              fontSize: 11,
            }}
          />

          <Bar
            dataKey={valueKey}
            barSize={6}
            radius={[4, 4, 4, 4]}
            {...ANIMATION.bar}
          >
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={Number(entry[valueKey]) >= avg
                  ? CHART_COLORS[0]
                  : '#52525b'
                }
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <div className="mt-2 flex items-center justify-center gap-4 text-xs text-zinc-500">
        <span>{data.length} items</span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-0.5 w-4 border-t border-dashed border-zinc-500" />
          Avg: {secondsMode ? formatSeconds(avg) : avg.toFixed(1)}
        </span>
      </div>
    </div>
  )
}
