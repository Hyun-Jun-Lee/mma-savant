'use client'

import { motion } from 'framer-motion'
import CountUp from 'react-countup'

interface StatCardProps {
  label: string
  value: number | string
  index?: number
}

export function StatCard({ label, value, index = 0 }: StatCardProps) {
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
      <div className="min-w-0">
        <p className="text-3xl font-bold tracking-tight text-zinc-100">
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
        <p className="mt-1 text-xs font-medium text-zinc-500">{label}</p>
      </div>
    </motion.div>
  )
}
