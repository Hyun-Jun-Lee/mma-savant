'use client'

import { motion } from 'framer-motion'
import CountUp from 'react-countup'
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts'
import type { EventSummary } from '@/types/event'

interface Props {
  summary: EventSummary
}

const FINISH_CONFIG = [
  { key: 'ko_tko_count' as const, label: 'KO/TKO', color: '#ef4444', textColor: 'text-red-400', bgColor: 'bg-red-500' },
  { key: 'submission_count' as const, label: 'Submission', color: '#a855f7', textColor: 'text-purple-400', bgColor: 'bg-purple-500' },
  { key: 'decision_count' as const, label: 'Decision', color: '#06b6d4', textColor: 'text-cyan-400', bgColor: 'bg-cyan-500' },
  { key: 'other_count' as const, label: 'Canceled', color: '#f59e0b', textColor: 'text-amber-400', bgColor: 'bg-amber-500' },
]

const cubicEaseOut = (t: number, b: number, c: number, d: number) => {
  const p = t / d
  return b + c * (1 - Math.pow(1 - p, 3))
}

export function EventSummaryStats({ summary }: Props) {
  const total = summary.total_bouts || 1

  const donutData = FINISH_CONFIG.map((item) => ({
    name: item.label,
    value: summary[item.key],
    color: item.color,
  })).filter((d) => d.value > 0)

  const emptyData = [{ value: 1, color: '#3f3f46' }]
  const chartData = donutData.length > 0 ? donutData : emptyData

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-5">
      {/* Donut Chart */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.7, ease: [0.23, 1, 0.32, 1] }}
        className="col-span-2 flex items-center justify-center rounded-xl border border-white/[0.06] bg-white/[0.03] p-4 sm:col-span-1"
      >
        <div className="relative h-20 w-20">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={26}
                outerRadius={37}
                paddingAngle={donutData.length > 1 ? 3 : 0}
                dataKey="value"
                strokeWidth={0}
              >
                {chartData.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-lg font-bold text-zinc-100">
              <CountUp end={summary.total_bouts} duration={1.5} easingFn={cubicEaseOut} />
            </span>
            <span className="text-[10px] text-zinc-500">Game</span>
          </div>
        </div>
      </motion.div>

      {/* Stat Cards */}
      {FINISH_CONFIG.map((item, index) => {
        const value = summary[item.key]
        const pct = Math.round((value / total) * 100)
        return (
          <motion.div
            key={item.key}
            initial={{ opacity: 0, y: 28, filter: 'blur(4px)' }}
            animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
            transition={{ duration: 0.7, ease: [0.23, 1, 0.32, 1], delay: index * 0.1 }}
            className="rounded-xl border border-white/[0.06] bg-white/[0.03] p-4 transition-all duration-300 ease-out hover:border-white/[0.12] hover:bg-white/[0.05]"
          >
            <p className="text-xs text-zinc-500">{item.label}</p>
            <div className="mt-1 flex items-baseline gap-1.5">
              <span className={`text-2xl font-bold tracking-tight ${item.textColor}`}>
                <CountUp end={value} duration={1.5} easingFn={cubicEaseOut} />
              </span>
              <span className="text-xs text-zinc-500">{pct}%</span>
            </div>
            <div className={`mt-3 h-0.5 w-10 rounded-full ${item.bgColor}`} />
          </motion.div>
        )
      })}
    </div>
  )
}
