'use client'

import type { ReactNode } from 'react'
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
  description?: string
  tooltip?: string
  className?: string
  headerRight?: ReactNode
  loading?: boolean
  error?: string | null
  onRetry?: () => void
  children: ReactNode
}

export function ChartCard({
  title,
  description,
  tooltip,
  className = '',
  headerRight,
  loading,
  error,
  onRetry,
  children,
}: ChartCardProps) {
  return (
    <div
      className={`rounded-xl border border-white/[0.06] bg-white/[0.03] p-5 transition-all duration-300 ease-out hover:scale-[1.01] hover:border-white/[0.12] hover:bg-white/[0.05] hover:shadow-lg hover:shadow-black/20 ${className}`}
    >
      {/* Header */}
      <div className="mb-4 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-1.5">
            <h3 className="text-sm font-semibold text-zinc-100">{title}</h3>
            {tooltip && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <HelpCircle className="h-3.5 w-3.5 shrink-0 cursor-help text-zinc-600 hover:text-zinc-400 transition-colors" />
                </TooltipTrigger>
                <TooltipContent
                  side="top"
                  className="max-w-[240px] bg-zinc-800 text-zinc-200 border border-white/[0.06]"
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
          <p className="text-sm text-zinc-500">데이터를 불러올 수 없습니다</p>
          {onRetry && (
            <Button
              size="sm"
              variant="ghost"
              className="text-xs text-zinc-400 hover:text-zinc-200"
              onClick={onRetry}
            >
              <RefreshCw className="mr-1.5 h-3 w-3" />
              재시도
            </Button>
          )}
        </div>
      ) : (
        children
      )}
    </div>
  )
}
