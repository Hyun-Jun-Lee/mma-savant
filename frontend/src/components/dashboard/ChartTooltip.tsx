import type { ReactNode } from 'react'

interface ChartTooltipProps {
  active?: boolean
  label?: string | number
  children?: ReactNode
}

export function ChartTooltip({ active, label, children }: ChartTooltipProps) {
  if (!active) return null
  return (
    <div className="rounded-lg border border-white/[0.06] bg-zinc-900 px-3 py-2 text-xs shadow-lg">
      {label !== undefined && <p className="mb-1 font-medium text-zinc-200">{label}</p>}
      {children}
    </div>
  )
}
