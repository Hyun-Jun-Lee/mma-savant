import { Skeleton } from '@/components/ui/skeleton'

export function FighterDetailSkeleton() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-6 space-y-4">
      <Skeleton className="h-32 bg-white/[0.06]" />
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Skeleton className="h-40 bg-white/[0.06]" />
        <Skeleton className="h-40 bg-white/[0.06]" />
      </div>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Skeleton className="h-48 bg-white/[0.06]" />
        <Skeleton className="h-48 bg-white/[0.06]" />
      </div>
      <Skeleton className="h-64 bg-white/[0.06]" />
    </div>
  )
}
