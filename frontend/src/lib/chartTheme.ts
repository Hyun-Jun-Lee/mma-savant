/**
 * Shared Recharts theme constants.
 * Extracted from dashboard chart styles for visual consistency across Chat AI and Dashboard.
 */

import { FINISH_COLORS, CHART_COLORS as SEMANTIC_COLORS } from './utils'

export const CHART_COLORS = [
  '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#06b6d4',
  '#a855f7', '#f97316', '#14b8a6', '#60a5fa', '#71717a',
] as const

export const AXIS_TICK = { fill: '#52525b', fontSize: 11 } as const

export const AXIS_PROPS = { axisLine: false, tickLine: false } as const

export const TOOLTIP_STYLE = {
  contentStyle: {
    backgroundColor: '#18181b',
    border: '1px solid rgba(255,255,255,0.06)',
    borderRadius: '8px',
    fontSize: '12px',
  },
  itemStyle: { color: '#e4e4e7' },
  labelStyle: { color: '#a1a1aa' },
} as const

export const TOOLTIP_CURSOR = { fill: 'rgba(255,255,255,0.04)' } as const

export const TOOLTIP_CURSOR_DASHED = { strokeDasharray: '3 3' } as const

export const ANIMATION = {
  bar:     { animationBegin: 500,  animationDuration: 1200, animationEasing: 'ease-out' as const },
  line:    { animationBegin: 300,  animationDuration: 1500, animationEasing: 'ease-out' as const },
  pie:     { animationBegin: 400,  animationDuration: 1400, animationEasing: 'ease-out' as const },
  scatter: { animationBegin: 200,  animationDuration: 1000, animationEasing: 'ease-out' as const },
} as const

export const BAR_RADIUS = [4, 4, 0, 0] as const

export const PIE_DONUT = {
  innerRadius: 60,
  outerRadius: 100,
  strokeWidth: 0,
  startAngle: 90,
  endAngle: -270,
} as const

export const LEGEND_STYLE = {
  verticalAlign: 'bottom' as const,
  iconType: 'circle' as const,
  iconSize: 8,
  wrapperStyle: { fontSize: '11px', color: '#a1a1aa' },
} as const

export const CHART_MARGIN = { top: 20, right: 30, left: 20, bottom: 5 } as const

/** Resolve a semantic color for a data label, falling back to the rotating palette. */
export function getSemanticColor(label: string, index: number): string {
  const lower = label.toLowerCase().trim()

  // 1) Exact match in FINISH_COLORS (e.g. "KO/TKO", "SUB", "U-DEC")
  if (FINISH_COLORS[lower]) return FINISH_COLORS[lower]
  if (FINISH_COLORS[label]) return FINISH_COLORS[label]

  // 2) Exact match in SEMANTIC_COLORS (e.g. "ko_tko", "submission")
  if (lower in SEMANTIC_COLORS) return SEMANTIC_COLORS[lower as keyof typeof SEMANTIC_COLORS]

  // 3) Partial match for common MMA domains
  if (/ko|tko|knockout/.test(lower)) return SEMANTIC_COLORS.ko_tko
  if (/sub|submission/.test(lower)) return SEMANTIC_COLORS.submission
  if (/dec|decision|판정/.test(lower)) return SEMANTIC_COLORS.decision
  if (/takedown|td/.test(lower)) return SEMANTIC_COLORS.takedown
  if (/strik|타격/.test(lower)) return SEMANTIC_COLORS.striking
  if (/grappl|ground|그라운드/.test(lower)) return SEMANTIC_COLORS.grappling

  // 4) Fallback: rotating palette
  return CHART_COLORS[index % CHART_COLORS.length]
}
