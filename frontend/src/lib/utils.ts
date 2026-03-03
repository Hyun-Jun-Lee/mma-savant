import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/** Convert lowercase name to Title Case: "derrick lewis" → "Derrick Lewis" */
export function toTitleCase(str: string): string {
  return str.replace(/\b\w/g, (char) => char.toUpperCase())
}

/** Format ISO date string to user-friendly format: "2025-11-15" → "Nov 15, 2025" */
export function formatDate(dateStr: string): string {
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

/** Weight class abbreviation map: remove "weight", add "W." for women's */
export const WEIGHT_CLASS_ABBR: Record<string, string> = {
  strawweight: 'Straw',
  flyweight: 'Fly',
  bantamweight: 'Bantam',
  featherweight: 'Feather',
  lightweight: 'Light',
  welterweight: 'Welter',
  middleweight: 'Middle',
  'light heavyweight': 'LHW',
  heavyweight: 'Heavy',
  "women's strawweight": 'W.Straw',
  "women's flyweight": 'W.Fly',
  "women's bantamweight": 'W.Bantam',
  "women's featherweight": 'W.Feather',
}

export function abbreviateWeightClass(wc: string): string {
  return WEIGHT_CLASS_ABBR[wc.toLowerCase()] ?? wc
}

/** Semantic color mapping for fight outcomes */
export const FINISH_COLORS: Record<string, string> = {
  'KO/TKO': '#ef4444',
  'ko_tko': '#ef4444',
  'SUB': '#a855f7',
  'submission': '#a855f7',
  'U-DEC': '#06b6d4',
  'S-DEC': '#0891b2',
  'M-DEC': '#22d3ee',
  'decision': '#06b6d4',
  'Overturned': '#71717a',
  'DQ': '#71717a',
  'Other': '#71717a',
  'Could Not Continue': '#71717a',
}

/** Semantic color tokens for dashboard charts */
export const CHART_COLORS = {
  ko_tko: '#ef4444',
  submission: '#a855f7',
  takedown: '#10b981',
  striking: '#f59e0b',
  general: '#8b5cf6',
  timeline: '#06b6d4',
  grappling: '#10b981',
  decision: '#06b6d4',
} as const
