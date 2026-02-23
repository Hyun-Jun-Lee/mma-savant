import { Suspense } from 'react'
import { DashboardPageClient } from '@/components/dashboard/DashboardPage'
import { Skeleton } from '@/components/ui/skeleton'

function DashboardSkeleton() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-6">
      <Skeleton className="mb-6 h-10 w-80 bg-white/[0.06]" />
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-24 bg-white/[0.06]" />
        ))}
      </div>
      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Skeleton className="h-64 bg-white/[0.06]" />
        <Skeleton className="h-64 bg-white/[0.06]" />
      </div>
    </div>
  )
}

export default function DashboardPage() {
  return (
    <Suspense fallback={<DashboardSkeleton />}>
      <DashboardPageClient />
    </Suspense>
  )
}
