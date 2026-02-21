'use client'

import { useCallback, useEffect } from 'react'
import { useSearchParams, useRouter, usePathname } from 'next/navigation'
import { useDashboard } from '@/hooks/useDashboard'
import { PillTabs } from './PillTabs'
import { HomeTab } from './home/HomeTab'
import { OverviewTab } from './overview/OverviewTab'
import { StrikingTab } from './striking/StrikingTab'
import { GrapplingTab } from './grappling/GrapplingTab'
import type { HomeResponse } from '@/types/dashboard'

const TABS = [
  { key: 'home', label: 'Home' },
  { key: 'overview', label: 'Overview' },
  { key: 'striking', label: 'Striking' },
  { key: 'grappling', label: 'Grappling' },
] as const

type TabKey = (typeof TABS)[number]['key']

interface DashboardPageClientProps {
  initialHomeData: HomeResponse | null
}

export function DashboardPageClient({
  initialHomeData,
}: DashboardPageClientProps) {
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
    if (activeTab !== 'home') {
      fetchTab(activeTab)
    }
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
        {activeTab === 'home' && initialHomeData && (
          <HomeTab data={initialHomeData} />
        )}
        {activeTab === 'home' && !initialHomeData && (
          <div className="py-20 text-center text-sm text-zinc-500">
            데이터를 불러올 수 없습니다. 백엔드 서버를 확인해주세요.
          </div>
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
