'use client'

import { useCallback, useEffect } from 'react'
import { useSearchParams, useRouter, usePathname } from 'next/navigation'
import { useDashboard } from '@/hooks/useDashboard'
import { PillTabs } from './PillTabs'
import { HomeTab } from './home/HomeTab'
import { OverviewTab } from './overview/OverviewTab'
import { StrikingTab } from './striking/StrikingTab'
import { GrapplingTab } from './grappling/GrapplingTab'
import { Skeleton } from '@/components/ui/skeleton'

const TABS = [
  { key: 'home', label: 'Home' },
  { key: 'overview', label: 'Overview' },
  { key: 'striking', label: 'Striking' },
  { key: 'grappling', label: 'Grappling' },
] as const

type TabKey = (typeof TABS)[number]['key']

export function DashboardPageClient() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const pathname = usePathname()
  const { state, fetchTab } = useDashboard()

  const activeTab = (searchParams.get('tab') as TabKey) || 'home'

  const setTab = useCallback(
    (tab: string) => {
      const params = new URLSearchParams(searchParams.toString())
      if (tab === 'home') {
        params.delete('tab')
      } else {
        params.set('tab', tab)
      }
      const qs = params.toString()
      router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: false })
    },
    [searchParams, router, pathname]
  )

  // Fetch tab data on tab switch
  useEffect(() => {
    fetchTab(activeTab)
  }, [activeTab, fetchTab]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="mx-auto max-w-7xl px-4 py-6">
      {/* Tab Bar */}
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <PillTabs
          tabs={[...TABS]}
          activeKey={activeTab}
          onChange={setTab}
        />
      </div>

      {/* Tab Content */}
      <div className="animate-fade-in">
        {activeTab === 'home' && state.home.loading && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-24 bg-white/[0.06]" />
              ))}
            </div>
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              <Skeleton className="h-64 bg-white/[0.06]" />
              <Skeleton className="h-64 bg-white/[0.06]" />
            </div>
          </div>
        )}
        {activeTab === 'home' && state.home.error && (
          <div className="py-20 text-center text-sm text-zinc-500">
            데이터를 불러올 수 없습니다. 백엔드 서버를 확인해주세요.
          </div>
        )}
        {activeTab === 'home' && state.home.data && (
          <HomeTab data={state.home.data} />
        )}
        {activeTab === 'overview' && (
          <OverviewTab
            data={state.overview.data}
            loading={state.overview.loading}
            error={state.overview.error}
            onRetry={() => fetchTab('overview')}
          />
        )}
        {activeTab === 'striking' && (
          <StrikingTab
            data={state.striking.data}
            loading={state.striking.loading}
            error={state.striking.error}
            onRetry={() => fetchTab('striking')}
          />
        )}
        {activeTab === 'grappling' && (
          <GrapplingTab
            data={state.grappling.data}
            loading={state.grappling.loading}
            error={state.grappling.error}
            onRetry={() => fetchTab('grappling')}
          />
        )}
      </div>
    </div>
  )
}
