'use client'

import { type ReactNode } from 'react'
import { motion } from 'framer-motion'
import { Skeleton } from '@/components/ui/skeleton'
import { AlertCircle, HelpCircle, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip'

interface ChartCardProps {
  title: string
  description?: ReactNode
  tooltip?: string
  badge?: string
  className?: string
  headerRight?: ReactNode
  loading?: boolean
  error?: string | null
  onRetry?: () => void
  children: ReactNode
  index?: number
}

export function ChartCard({
  title,
  description,
  tooltip,
  badge,
  className = '',
  headerRight,
  loading,
  error,
  onRetry,
  children,
  index = 0,
}: ChartCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 28, filter: 'blur(4px)' }}
      animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
      transition={{
        duration: 0.7,
        ease: [0.23, 1, 0.32, 1],
        delay: index * 0.1,
      }}
      whileHover={{
        y: -3,
        boxShadow: '0 0 28px rgba(139, 92, 246, 0.12)',
        borderColor: 'rgba(139, 92, 246, 0.3)',
        transition: { duration: 0.3, ease: 'easeOut' },
      }}
      className={`relative overflow-hidden rounded-xl border border-white/[0.06] bg-white/[0.03] p-5 before:pointer-events-none before:absolute before:inset-x-0 before:top-0 before:h-px before:bg-gradient-to-r before:from-transparent before:via-violet-500 before:to-transparent before:opacity-0 before:transition-opacity before:duration-300 hover:border-white/[0.12] hover:bg-white/[0.05] hover:before:opacity-70 ${className}`}
    >
      {/* Header */}
      <div className="mb-4 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-1.5">
            {badge && (
              <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-medium text-emerald-400">
                {badge}
              </span>
            )}
            <h3 className="text-sm font-semibold text-zinc-100">{title}</h3>
            {tooltip && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <HelpCircle className="h-3.5 w-3.5 shrink-0 cursor-help text-zinc-600 hover:text-zinc-400 transition-colors" />
                </TooltipTrigger>
                <TooltipContent
                  side="top"
                  className="max-w-[240px] bg-zinc-900 text-zinc-200 border border-white/[0.06]"
                >
                  {tooltip}
                </TooltipContent>
              </Tooltip>
            )}
          </div>
          {description && (
            <p className="mt-0.5 text-xs text-zinc-500">{description}</p>
          )}
        </div>
        {headerRight && <div className="shrink-0">{headerRight}</div>}
      </div>

      {/* Content */}
      {loading ? (
        <div className="space-y-3">
          <Skeleton className="h-4 w-3/4 bg-white/[0.06]" />
          <Skeleton className="h-[200px] w-full bg-white/[0.06]" />
          <Skeleton className="h-4 w-1/2 bg-white/[0.06]" />
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center gap-3 py-12 text-center">
          <AlertCircle className="h-8 w-8 text-zinc-600" />
          <p className="text-sm text-zinc-500">Unable to load data</p>
          {onRetry && (
            <Button
              size="sm"
              variant="ghost"
              className="text-xs text-zinc-400 hover:text-zinc-200"
              onClick={onRetry}
            >
              <RefreshCw className="mr-1.5 h-3 w-3" />
              Retry
            </Button>
          )}
        </div>
      ) : (
        children
      )}
    </motion.div>
  )
}
