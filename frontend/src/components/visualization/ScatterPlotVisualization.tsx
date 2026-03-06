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
        표시할 데이터가 없습니다.
      </div>
    )
  }

  const sampleRow = data[0]
  const numericFields = Object.keys(sampleRow).filter(key =>
    typeof sampleRow[key] === 'number'
  )

  const xAxisKey = xAxis || numericFields[0] || Object.keys(sampleRow)[0]
  const yAxisKey = yAxis || numericFields[1] || Object.keys(sampleRow)[1]

  // Use 3rd numeric field for bubble size if available
  const zAxisKey = numericFields.find(k => k !== xAxisKey && k !== yAxisKey)

  const scatterData = data.map((item, index) => ({
    x: Number(item[xAxisKey]) || index,
    y: Number(item[yAxisKey]) || 0,
    z: zAxisKey ? Number(item[zAxisKey]) || 50 : 50,
    name: item.name || item[Object.keys(item)[0]] || `Point ${index + 1}`,
    originalData: item
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
          <ZAxis type="number" dataKey="z" range={[40, 200]} />
          <Tooltip
            cursor={TOOLTIP_CURSOR_DASHED}
            {...TOOLTIP_STYLE}
            formatter={(value: number, name: string) => [
              value.toLocaleString(),
              name === "x" ? xAxisKey : name === "y" ? yAxisKey : name
            ]}
            labelFormatter={(label) => `${label}`}
          />
          <Scatter
            name="데이터 포인트"
            data={scatterData}
            fill={getSemanticColor(xAxisKey, 0)}
            fillOpacity={0.7}
            {...ANIMATION.scatter}
          />
        </ScatterChart>
      </ResponsiveContainer>

      <div className="mt-2 text-xs text-zinc-500 text-center">
        {data.length}개 데이터 포인트 • X: {xAxisKey}, Y: {yAxisKey}
      </div>
    </div>
  )
}
