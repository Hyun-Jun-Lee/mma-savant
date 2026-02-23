import { useState, useEffect } from 'react'

interface UseChartFilterOptions<T> {
  /** Tab initial load data (passed from parent) */
  initialData: T | undefined
  /** Chart-level API fetch function -- takes weightClassId only */
  fetchFn: (weightClassId?: number) => Promise<T>
}

interface UseChartFilterReturn<T> {
  /** Current data to display (filtered result or initial data) */
  data: T | undefined
  /** Loading state */
  loading: boolean
  /** Currently selected weight class ID (undefined = all) */
  weightClassId: number | undefined
  /** Weight class change handler */
  setWeightClassId: (id: number | undefined) => void
}

export function useChartFilter<T>({
  initialData,
  fetchFn,
}: UseChartFilterOptions<T>): UseChartFilterReturn<T> {
  const [weightClassId, setWeightClassId] = useState<number | undefined>()
  const [chartData, setChartData] = useState<T | undefined>()
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    // When weightClassId is undefined, use tab initial data
    if (weightClassId === undefined) {
      setChartData(undefined)
      return
    }

    let cancelled = false
    setLoading(true)
    fetchFn(weightClassId)
      .then((result) => {
        if (!cancelled) setChartData(result)
      })
      .catch(console.error)
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => { cancelled = true }
  }, [weightClassId, fetchFn])

  return {
    data: chartData ?? initialData,
    loading,
    weightClassId,
    setWeightClassId,
  }
}
