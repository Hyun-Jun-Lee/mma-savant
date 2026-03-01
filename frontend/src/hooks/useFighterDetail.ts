'use client'

import { useCallback, useEffect, useState } from 'react'
import { fighterApi } from '@/services/fighterApi'
import type { FighterDetailResponse } from '@/types/fighter'

export function useFighterDetail(fighterId: number) {
  const [data, setData] = useState<FighterDetailResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetch = useCallback(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    fighterApi
      .getDetail(fighterId)
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
  }, [fighterId])

  useEffect(() => {
    return fetch()
  }, [fetch])

  return { data, loading, error, retry: fetch }
}
