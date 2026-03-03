'use client'

import { motion } from 'framer-motion'
import CountUp from 'react-countup'
import type { LucideIcon } from 'lucide-react'

interface StatCardProps {
  label: string
  value: number | string
  icon?: LucideIcon
  iconColor?: string
  index?: number
}

export function StatCard({ label, value, icon: Icon, iconColor, index = 0 }: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 28, filter: 'blur(4px)' }}
      animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
      transition={{
        duration: 0.7,
        ease: [0.23, 1, 0.32, 1],
        delay: index * 0.15,
      }}
      className="rounded-xl border border-white/[0.06] bg-white/[0.03] p-5 transition-colors hover:bg-white/[0.05]"
    >
      <div className="flex items-center gap-3">
        {Icon && (
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white/[0.06]">
            <Icon className={`h-4 w-4 ${iconColor ?? 'text-zinc-400'}`} />
          </div>
        )}
        <div className="min-w-0">
          <p className="text-xs font-medium text-zinc-500">{label}</p>
          <p className="mt-0.5 text-2xl font-bold tracking-tight text-zinc-100">
            {typeof value === 'number' ? (
              <CountUp
                end={value}
                duration={1.5}
                separator=","
                easingFn={(t, b, c, d) => {
                  const p = t / d
                  return b + c * (1 - Math.pow(1 - p, 3))
                }}
              />
            ) : (
              value
            )}
          </p>
        </div>
      </div>
    </motion.div>
  )
}
