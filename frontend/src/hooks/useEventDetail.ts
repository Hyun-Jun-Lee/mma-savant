'use client'

import { useCallback, useEffect, useState } from 'react'
import { eventApi } from '@/services/eventApi'
import type { EventDetailResponse } from '@/types/event'

export function useEventDetail(eventId: number) {
  const [data, setData] = useState<EventDetailResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetch = useCallback(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    eventApi
      .getDetail(eventId)
      .then((res) => {
        if (!cancelled) setData(res)
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Unknown error')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [eventId])

  useEffect(() => {
    return fetch()
  }, [fetch])

  return { data, loading, error, retry: fetch }
}
