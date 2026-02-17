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

export const dashboardApi = {
  getOverview: (weightClassId?: number) =>
    dashboardFetch<OverviewResponse>(
      withWeightClass('/api/dashboard/overview', weightClassId)
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
