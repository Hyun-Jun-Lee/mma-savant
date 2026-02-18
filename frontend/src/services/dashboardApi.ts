import type {
  OverviewResponse,
  StrikingResponse,
  GrapplingResponse,
} from '@/types/dashboard'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002'

async function dashboardFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`)
  if (!res.ok) throw new Error(`Dashboard API error: ${res.status}`)
  return res.json()
}

function withWeightClass(path: string, weightClassId?: number): string {
  return weightClassId ? `${path}?weight_class_id=${weightClassId}` : path
}

function buildOverviewPath(weightClassId?: number, ufcOnly?: boolean): string {
  const params = new URLSearchParams()
  if (weightClassId) params.set('weight_class_id', weightClassId.toString())
  if (ufcOnly) params.set('ufc_only', 'true')
  const qs = params.toString()
  return qs ? `/api/dashboard/overview?${qs}` : '/api/dashboard/overview'
}

export const dashboardApi = {
  getOverview: (weightClassId?: number, ufcOnly?: boolean) =>
    dashboardFetch<OverviewResponse>(
      buildOverviewPath(weightClassId, ufcOnly)
    ),

  getStriking: (weightClassId?: number) =>
    dashboardFetch<StrikingResponse>(
      withWeightClass('/api/dashboard/striking', weightClassId)
    ),

  getGrappling: (weightClassId?: number) =>
    dashboardFetch<GrapplingResponse>(
      withWeightClass('/api/dashboard/grappling', weightClassId)
    ),
}
