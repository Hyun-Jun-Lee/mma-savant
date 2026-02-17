'use client'

import { useCallback, useEffect } from 'react'
import { useSearchParams, useRouter, usePathname } from 'next/navigation'
import { useDashboard } from '@/hooks/useDashboard'
import { PillTabs } from './PillTabs'
import { WeightClassFilter } from './WeightClassFilter'
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
  const weightClassId = searchParams.get('weight_class')
    ? Number(searchParams.get('weight_class'))
    : undefined

  const setTab = useCallback(
    (tab: string) => {
      const params = new URLSearchParams(searchParams.toString())
      if (tab === 'home') {
        params.delete('tab')
        params.delete('weight_class')
      } else {
        params.set('tab', tab)
      }
      const qs = params.toString()
      router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: false })
    },
    [searchParams, router, pathname]
  )

  const setWeightClass = useCallback(
    (id?: number) => {
      const params = new URLSearchParams(searchParams.toString())
      if (id === undefined) params.delete('weight_class')
      else params.set('weight_class', id.toString())
      const qs = params.toString()
      router.push(qs ? `${pathname}?${qs}` : pathname, { scroll: false })
    },
    [searchParams, router, pathname]
  )

  // 탭 전환 시 데이터 fetch
  useEffect(() => {
    if (activeTab !== 'home') {
      fetchTab(activeTab, weightClassId)
    }
  }, [activeTab, weightClassId, fetchTab])

  const showFilter = activeTab !== 'home'

  return (
    <div className="mx-auto max-w-7xl px-4 py-6">
      {/* Tab Bar + Filter */}
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <PillTabs
          tabs={[...TABS]}
          activeKey={activeTab}
          onChange={setTab}
        />
        {showFilter && (
          <WeightClassFilter
            value={weightClassId}
            onChange={setWeightClass}
          />
        )}
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
            onRetry={() => fetchTab('overview', weightClassId)}
          />
        )}
        {activeTab === 'striking' && (
          <StrikingTab
            data={state.striking.data}
            loading={state.striking.loading}
            error={state.striking.error}
            onRetry={() => fetchTab('striking', weightClassId)}
          />
        )}
        {activeTab === 'grappling' && (
          <GrapplingTab
            data={state.grappling.data}
            loading={state.grappling.loading}
            error={state.grappling.error}
            onRetry={() => fetchTab('grappling', weightClassId)}
          />
        )}
      </div>
    </div>
  )
}
