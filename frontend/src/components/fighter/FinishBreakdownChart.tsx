'use client'

import { motion } from 'framer-motion'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Label } from 'recharts'
import type { FinishBreakdown } from '@/types/fighter'
import { FINISH_COLORS } from '@/lib/utils'

interface Props {
  breakdown: FinishBreakdown
}

const LABELS: Record<string, string> = {
  ko_tko: 'KO/TKO',
  submission: 'Submission',
  decision: 'Decision',
}

export function FinishBreakdownChart({ breakdown }: Props) {
  const total = breakdown.ko_tko + breakdown.submission + breakdown.decision

  if (total === 0) {
    return (
      <div className="rounded-xl border border-white/[0.06] bg-white/[0.03] p-5 transition-all duration-300 ease-out hover:border-white/[0.12] hover:bg-white/[0.05]">
        <h3 className="text-sm font-semibold text-zinc-100">
          Finish Breakdown
        </h3>
        <p className="mt-4 text-center text-sm text-zinc-500">
          No wins to display
        </p>
      </div>
    )
  }

  const data = [
    { name: 'KO/TKO', value: breakdown.ko_tko, color: FINISH_COLORS.ko_tko },
    {
      name: 'Submission',
      value: breakdown.submission,
      color: FINISH_COLORS.submission,
    },
    { name: 'Decision', value: breakdown.decision, color: FINISH_COLORS.decision },
  ].filter((d) => d.value > 0)

  return (
    <motion.div
      initial={{ opacity: 0, y: 28, filter: 'blur(4px)' }}
      animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
      transition={{ duration: 0.7, ease: [0.23, 1, 0.32, 1] }}
      className="rounded-xl border border-white/[0.06] bg-white/[0.03] p-5 transition-all duration-300 ease-out hover:border-white/[0.12] hover:bg-white/[0.05]"
    >
      <h3 className="mb-4 text-sm font-semibold text-zinc-100">
        Finish Breakdown
      </h3>

      <div className="flex items-center justify-center gap-6">
        <div className="h-[160px] w-[160px] shrink-0">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={45}
                outerRadius={70}
                paddingAngle={2}
                dataKey="value"
                stroke="none"
                animationBegin={400}
                animationDuration={1400}
                animationEasing="ease-out"
                startAngle={90}
                endAngle={-270}
              >
                {data.map((entry) => (
                  <Cell key={entry.name} fill={entry.color} />
                ))}
                <Label
                  value={`${total} Wins`}
                  position="center"
                  style={{ fill: '#e4e4e7', fontSize: '13px', fontWeight: 600 }}
                />
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: '#27272a',
                  border: '1px solid rgba(255,255,255,0.06)',
                  borderRadius: '8px',
                  fontSize: '12px',
                  color: '#e4e4e7',
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Legend */}
        <div className="flex flex-col gap-2">
          {Object.entries(LABELS).map(([key, label]) => {
            const value = breakdown[key as keyof FinishBreakdown]
            if (value === 0) return null
            const pct = Math.round((value / total) * 100)
            return (
              <div key={key} className="flex items-center gap-2 text-sm">
                <div
                  className="h-2.5 w-2.5 rounded-full"
                  style={{
                    backgroundColor: FINISH_COLORS[key],
                  }}
                />
                <span className="text-zinc-400">{label}</span>
                <span className="font-medium text-zinc-200">
                  {value} ({pct}%)
                </span>
              </div>
            )
          })}
        </div>
      </div>
    </motion.div>
  )
}
