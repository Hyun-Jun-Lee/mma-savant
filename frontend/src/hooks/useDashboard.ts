'use client'

import { useCallback, useRef, useState } from 'react'
import { dashboardApi } from '@/services/dashboardApi'
import type {
  OverviewResponse,
  StrikingResponse,
  GrapplingResponse,
} from '@/types/dashboard'

type TabKey = 'overview' | 'striking' | 'grappling'

interface TabState<T> {
  data: T | null
  loading: boolean
  error: string | null
}

interface DashboardState {
  overview: TabState<OverviewResponse>
  striking: TabState<StrikingResponse>
  grappling: TabState<GrapplingResponse>
}

const initialTabState = <T>(): TabState<T> => ({
  data: null,
  loading: false,
  error: null,
})

const fetchers = {
  overview: dashboardApi.getOverview,
  striking: dashboardApi.getStriking,
  grappling: dashboardApi.getGrappling,
} as const

export function useDashboard() {
  const [state, setState] = useState<DashboardState>({
    overview: initialTabState(),
    striking: initialTabState(),
    grappling: initialTabState(),
  })

  // ref로 캐시 판단 (useCallback 의존성에서 state를 제거하여 무한 루프 방지)
  const stateRef = useRef(state)
  stateRef.current = state

  const lastWeightClassRef = useRef<Record<TabKey, number | undefined>>({
    overview: undefined,
    striking: undefined,
    grappling: undefined,
  })

  const fetchTab = useCallback(
    async (tab: TabKey, weightClassId?: number) => {
      const cached = stateRef.current[tab]
      const lastWc = lastWeightClassRef.current[tab]

      // 이미 데이터가 있고 체급 필터가 동일하면 스킵
      if (cached.data && lastWc === weightClassId) return

      setState((prev) => ({
        ...prev,
        [tab]: { ...prev[tab], loading: true, error: null },
      }))

      try {
        const data = await fetchers[tab](weightClassId)
        lastWeightClassRef.current[tab] = weightClassId
        setState((prev) => ({
          ...prev,
          [tab]: { data, loading: false, error: null },
        }))
      } catch (err) {
        setState((prev) => ({
          ...prev,
          [tab]: {
            ...prev[tab],
            loading: false,
            error: err instanceof Error ? err.message : 'Unknown error',
          },
        }))
      }
    },
    []
  )

  const invalidateTab = useCallback((tab: TabKey) => {
    lastWeightClassRef.current[tab] = undefined
    setState((prev) => ({
      ...prev,
      [tab]: initialTabState(),
    }))
  }, [])

  return { state, fetchTab, invalidateTab }
}
