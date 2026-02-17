import { Suspense } from 'react'
import { DashboardPageClient } from '@/components/dashboard/DashboardPage'
import { Skeleton } from '@/components/ui/skeleton'
import type { HomeResponse } from '@/types/dashboard'

export const revalidate = 300

async function getHomeData(): Promise<HomeResponse | null> {
  try {
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8002'
    const res = await fetch(`${backendUrl}/api/dashboard/home`, {
      next: { revalidate: 300 },
    })
    if (!res.ok) return null
    return res.json()
  } catch {
    // 빌드 시점에 백엔드가 미실행일 수 있음 — 런타임에 재시도
    return null
  }
}

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

export default async function DashboardPage() {
  const homeData = await getHomeData()
  return (
    <Suspense fallback={<DashboardSkeleton />}>
      <DashboardPageClient initialHomeData={homeData} />
    </Suspense>
  )
}
