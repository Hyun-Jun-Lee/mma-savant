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
  const numericFields = Object.keys(sampleRow).filter(key =>
    typeof sampleRow[key] === 'number'
  )

  // Category field for angle axis
  const categoryKey = xAxis || Object.keys(sampleRow).find(key =>
    typeof sampleRow[key] === 'string'
  ) || Object.keys(sampleRow)[0]

  // Numeric series for radar lines
  const valueKeys = yAxis ? [yAxis] : numericFields

  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="70%" data={data}>
          <PolarGrid stroke="rgba(255,255,255,0.1)" />
          <PolarAngleAxis
            dataKey={categoryKey}
            tick={{ fill: '#a1a1aa', fontSize: 11 }}
          />
          <PolarRadiusAxis
            tick={{ fill: '#52525b', fontSize: 10 }}
            axisLine={false}
          />
          <Tooltip {...TOOLTIP_STYLE} />
          {valueKeys.length > 1 && <Legend {...LEGEND_STYLE} />}

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
        {data.length} categories • {valueKeys.join(", ")} comparison
      </div>
    </div>
  )
}
