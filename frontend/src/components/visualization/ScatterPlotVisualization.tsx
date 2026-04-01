"use client"

import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ZAxis
} from "recharts"
import {
  AXIS_TICK,
  AXIS_PROPS,
  TOOLTIP_STYLE,
  TOOLTIP_CURSOR_DASHED,
  ANIMATION,
  CHART_MARGIN,
  getSemanticColor,
} from "@/lib/chartTheme"

interface ScatterPlotVisualizationProps {
  data: Record<string, string | number>[]
  xAxis?: string
  yAxis?: string
}

export function ScatterPlotVisualization({ data, xAxis, yAxis }: ScatterPlotVisualizationProps) {
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

  const xAxisKey = xAxis || numericFields[0] || Object.keys(sampleRow)[0]
  const yAxisKey = yAxis || numericFields[1] || Object.keys(sampleRow)[1]

  // 이름 컬럼: xAxis/yAxis에 해당하지 않는 문자열 필드
  const nameKey = Object.keys(sampleRow).find(key =>
    typeof sampleRow[key] === 'string' && key !== xAxisKey && key !== yAxisKey
  ) || Object.keys(sampleRow)[0]

  const scatterData = data.map((item, index) => ({
    x: Number(item[xAxisKey]) || index,
    y: Number(item[yAxisKey]) || 0,
    name: String(item[nameKey] || `Point ${index + 1}`),
  }))

  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={CHART_MARGIN}>
          <XAxis
            type="number"
            dataKey="x"
            name={xAxisKey}
            tick={AXIS_TICK}
            {...AXIS_PROPS}
          />
          <YAxis
            type="number"
            dataKey="y"
            name={yAxisKey}
            tick={AXIS_TICK}
            {...AXIS_PROPS}
          />
          <Tooltip
            cursor={TOOLTIP_CURSOR_DASHED}
            content={({ payload }) => {
              if (!payload || payload.length === 0) return null
              const point = payload[0]?.payload
              if (!point) return null
              return (
                <div style={TOOLTIP_STYLE.contentStyle} className="px-3 py-2">
                  <p className="text-zinc-300 font-medium mb-1 capitalize">{point.name}</p>
                  <p className="text-zinc-400 text-xs">{xAxisKey}: <span className="text-zinc-200">{Number(point.x).toLocaleString(undefined, { maximumFractionDigits: 1 })}</span></p>
                  <p className="text-zinc-400 text-xs">{yAxisKey}: <span className="text-zinc-200">{Number(point.y).toLocaleString(undefined, { maximumFractionDigits: 1 })}</span></p>
                </div>
              )
            }}
          />
          <Scatter
            name="Data Points"
            data={scatterData}
            fill={getSemanticColor(xAxisKey, 0)}
            fillOpacity={0.7}
            {...ANIMATION.scatter}
          />
        </ScatterChart>
      </ResponsiveContainer>

      <div className="mt-2 text-xs text-zinc-500 text-center">
        {data.length} data points • X: {xAxisKey}, Y: {yAxisKey}
      </div>
    </div>
  )
}
