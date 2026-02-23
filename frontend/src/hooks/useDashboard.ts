'use client'

import { useCallback, useRef, useState } from 'react'
import { dashboardApi } from '@/services/dashboardApi'
import type {
  HomeResponse,
  OverviewResponse,
  StrikingResponse,
  GrapplingResponse,
} from '@/types/dashboard'

type TabKey = 'home' | 'overview' | 'striking' | 'grappling'

interface TabState<T> {
  data: T | null
  loading: boolean
  error: string | null
}

interface DashboardState {
  home: TabState<HomeResponse>
  overview: TabState<OverviewResponse>
  striking: TabState<StrikingResponse>
  grappling: TabState<GrapplingResponse>
}

const initialTabState = <T>(): TabState<T> => ({
  data: null,
  loading: false,
  error: null,
})

interface FetchOptions {
  ufcOnly?: boolean
  silent?: boolean
}

export function useDashboard() {
  const [state, setState] = useState<DashboardState>({
    home: initialTabState(),
    overview: initialTabState(),
    striking: initialTabState(),
    grappling: initialTabState(),
  })

  // ref로 캐시 판단 (useCallback 의존성에서 state를 제거하여 무한 루프 방지)
  const stateRef = useRef(state)
  stateRef.current = state

  const lastParamsRef = useRef<Record<TabKey, string | undefined>>({
    home: undefined,
    overview: undefined,
    striking: undefined,
    grappling: undefined,
  })

  const fetchTab = useCallback(
    async (tab: TabKey, weightClassId?: number, options?: FetchOptions) => {
      const cached = stateRef.current[tab]
      const paramsKey = `${weightClassId ?? 'all'}:${options?.ufcOnly ?? false}`
      const lastParams = lastParamsRef.current[tab]

      // 이미 데이터가 있고 파라미터가 동일하면 스킵
      if (cached.data && lastParams === paramsKey) return

      // silent: 기존 데이터 유지한 채 백그라운드로 fetch (로딩 스켈레톤 없음)
      if (!options?.silent) {
        setState((prev) => ({
          ...prev,
          [tab]: { ...prev[tab], loading: true, error: null },
        }))
      }

      try {
        let data
        if (tab === 'home') {
          data = await dashboardApi.getHome()
        } else if (tab === 'overview') {
          data = await dashboardApi.getOverview(weightClassId, options?.ufcOnly)
        } else if (tab === 'striking') {
          data = await dashboardApi.getStriking(weightClassId)
        } else {
          data = await dashboardApi.getGrappling(weightClassId)
        }
        lastParamsRef.current[tab] = paramsKey
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
    lastParamsRef.current[tab] = undefined
    setState((prev) => ({
      ...prev,
      [tab]: initialTabState(),
    }))
  }, [])

  return { state, fetchTab, invalidateTab }
}
