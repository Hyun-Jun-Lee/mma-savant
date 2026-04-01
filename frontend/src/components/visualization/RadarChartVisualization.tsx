"use client"

import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from "recharts"
import {
  TOOLTIP_STYLE,
  LEGEND_STYLE,
  getSemanticColor,
} from "@/lib/chartTheme"
import { pivotLongToWide, transposeForRadar } from "./pivotData"

interface RadarChartVisualizationProps {
  data: Record<string, string | number>[]
  xAxis?: string
  yAxis?: string
}

export function RadarChartVisualization({ data, xAxis, yAxis }: RadarChartVisualizationProps) {
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

  // 1) 소수 행 x 다수 열 (선수 비교) → 전치 + 정규화
  const transposed = transposeForRadar(data, categoryKey)

  // 2) long format → wide pivot
  const pivoted = !transposed ? pivotLongToWide(data, categoryKey, yAxis) : null

  const chartData = transposed?.data ?? pivoted?.data ?? data
  const angleKey = transposed ? "stat" : categoryKey
  const effectiveSample = chartData[0]

  const numericFields = Object.keys(effectiveSample).filter(key =>
    typeof effectiveSample[key] === 'number' && !key.startsWith("_raw_")
  )
  const valueKeys = transposed
    ? transposed.seriesKeys
    : pivoted
      ? pivoted.seriesKeys
      : (yAxis ? [yAxis] : numericFields)

  const isNormalized = !!transposed

  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="70%" data={chartData}>
          <PolarGrid stroke="rgba(255,255,255,0.1)" />
          <PolarAngleAxis
            dataKey={angleKey}
            tick={{ fill: '#a1a1aa', fontSize: 11 }}
          />
          <PolarRadiusAxis
            tick={{ fill: '#52525b', fontSize: 10 }}
            axisLine={false}
            domain={isNormalized ? [0, 100] : undefined}
          />
          <Tooltip
            {...TOOLTIP_STYLE}
            formatter={(value: number, name: string, props: { payload?: Record<string, string | number> }) => {
              if (isNormalized && props.payload) {
                const raw = props.payload[`_raw_${name}`]
                if (raw !== undefined) {
                  return [`${Number(raw).toLocaleString(undefined, { maximumFractionDigits: 1 })}`, name]
                }
              }
              return [Number(value).toLocaleString(undefined, { maximumFractionDigits: 1 }), name]
            }}
          />
          <Legend {...LEGEND_STYLE} />

          {valueKeys.map((key, index) => {
            const color = getSemanticColor(key, index)
            return (
              <Radar
                key={key}
                name={key}
                dataKey={key}
                stroke={color}
                fill={color}
                fillOpacity={0.25}
                strokeWidth={2}
                animationBegin={300}
                animationDuration={1200}
                animationEasing="ease-out"
              />
            )
          })}
        </RadarChart>
      </ResponsiveContainer>

      <div className="mt-2 text-xs text-zinc-500 text-center">
        {chartData.length} categories • {valueKeys.join(", ")} comparison
      </div>
    </div>
  )
}
