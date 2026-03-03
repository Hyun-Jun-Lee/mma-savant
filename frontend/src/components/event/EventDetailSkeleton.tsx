import { Skeleton } from '@/components/ui/skeleton'

export function EventDetailSkeleton() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-6 space-y-4">
      {/* Header */}
      <Skeleton className="h-24 bg-white/[0.06]" />
      {/* Summary stats */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Skeleton className="h-20 bg-white/[0.06]" />
        <Skeleton className="h-20 bg-white/[0.06]" />
        <Skeleton className="h-20 bg-white/[0.06]" />
        <Skeleton className="h-20 bg-white/[0.06]" />
      </div>
      {/* Fight cards */}
      <div className="space-y-3">
        <Skeleton className="h-20 bg-white/[0.06]" />
        <Skeleton className="h-20 bg-white/[0.06]" />
        <Skeleton className="h-20 bg-white/[0.06]" />
        <Skeleton className="h-20 bg-white/[0.06]" />
      </div>
    </div>
  )
}
