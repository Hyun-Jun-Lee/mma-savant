"use client"

import { useState, useMemo } from "react"
import { ChevronDown } from "lucide-react"
import { CHART_COLORS } from "@/lib/chartTheme"

interface RingListVisualizationProps {
  data: Record<string, string | number>[]
  xAxis?: string
  yAxis?: string
}

function DonutRing({ pct, color, size = 48 }: { pct: number; color: string; size?: number }) {
  const r = (size - 6) / 2
  const c = 2 * Math.PI * r
  const clamped = Math.min(Math.max(pct, 0), 100)
  const filled = (clamped / 100) * c

  return (
    <svg width={size} height={size} className="shrink-0">
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#27272a" strokeWidth={5} />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        fill="none"
        stroke={color}
        strokeWidth={5}
        strokeDasharray={`${filled} ${c - filled}`}
        strokeDashoffset={c * 0.25}
        strokeLinecap="round"
        className="transition-all duration-700"
      />
      <text
        x={size / 2}
        y={size / 2}
        textAnchor="middle"
        dominantBaseline="central"
        fill="#e4e4e7"
        fontSize={11}
        fontWeight={600}
      >
        {clamped.toFixed(0)}%
      </text>
    </svg>
  )
}

export function RingListVisualization({ data, xAxis, yAxis }: RingListVisualizationProps) {
  const [expanded, setExpanded] = useState(false)

  const { sorted, nameKey, valueKey, hasPercentage } = useMemo(() => {
    if (!data || data.length === 0) return { sorted: [], nameKey: '', valueKey: '', hasPercentage: false }

    const sampleRow = data[0]
    const nKey = xAxis || Object.keys(sampleRow).find(key =>
      typeof sampleRow[key] === 'string'
    ) || Object.keys(sampleRow)[0]

    const numericFields = Object.keys(sampleRow).filter(key =>
      typeof sampleRow[key] === 'number'
    )
    const vKey = yAxis || numericFields[0] || Object.keys(sampleRow)[1]

    const isPct = numericFields.some(k =>
      /rate|pct|percent|ratio|accuracy|efficiency|avg/i.test(k)
    )

    const items = [...data].sort((a, b) => Number(b[vKey]) - Number(a[vKey]))

    return { sorted: items, nameKey: nKey, valueKey: vKey, hasPercentage: isPct }
  }, [data, xAxis, yAxis])

  if (sorted.length === 0) {
    return (
      <div className="p-8 text-center text-zinc-400">
        No data to display.
      </div>
    )
  }

  const visible = expanded ? sorted.slice(0, 10) : sorted.slice(0, 5)
  const otherNumericKeys = Object.keys(sorted[0]).filter(
    k => typeof sorted[0][k] === 'number' && k !== valueKey
  )

  return (
    <div className="flex flex-col">
      <div className="divide-y divide-white/[0.04]">
        {visible.map((item, i) => {
          const val = Number(item[valueKey])
          const displayPct = hasPercentage ? val : 0

          return (
            <div
              key={i}
              className="group flex items-center gap-3 px-3 py-2.5 transition-colors hover:bg-white/[0.03]"
            >
              <span className="w-5 shrink-0 text-center text-xs font-semibold text-zinc-500">
                {i + 1}
              </span>

              {hasPercentage && (
                <DonutRing pct={displayPct} color={CHART_COLORS[i % CHART_COLORS.length]} />
              )}

              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-zinc-200">
                  {String(item[nameKey])}
                </p>
                {otherNumericKeys.length > 0 && (
                  <div className="mt-0.5 flex items-center gap-3 text-[11px]">
                    {otherNumericKeys.slice(0, 3).map(k => (
                      <span key={k}>
                        <span className="font-medium text-zinc-400">{Number(item[k]).toLocaleString()}</span>
                        <span className="ml-1 text-zinc-500">{k}</span>
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <span className="shrink-0 rounded-full border border-white/[0.08] bg-white/[0.04] px-2 py-0.5 text-[11px] font-medium text-zinc-300">
                {hasPercentage ? `${val.toFixed(1)}%` : val.toLocaleString()}
              </span>
            </div>
          )
        })}
      </div>

      {sorted.length > 5 && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-2 flex w-full items-center justify-center gap-1 rounded-lg py-1.5 text-xs text-zinc-500 transition-colors hover:bg-white/[0.04] hover:text-zinc-300"
        >
          <ChevronDown className={`h-3.5 w-3.5 transition-transform ${expanded ? 'rotate-180' : ''}`} />
          {expanded ? 'Show Less' : `Show All ${sorted.length}`}
        </button>
      )}

      <div className="mt-2 text-xs text-zinc-500 text-center">
        {sorted.length} items ranked by {valueKey}
      </div>
    </div>
  )
}
