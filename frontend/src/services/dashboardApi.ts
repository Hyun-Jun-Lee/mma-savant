import type {
  OverviewResponse,
  StrikingResponse,
  GrapplingResponse,
  FinishMethod,
  StrikeTarget,
  KoTkoLeader,
  StrikingAccuracyFighter,
  SigStrikesLeader,
  TakedownLeader,
  SubmissionTechnique,
  GroundStrikesLeader,
  MinFightsLeaderboard,
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

// ── Chart-level API ──

function buildChartParams(params: {
  weightClassId?: number
  ufcOnly?: boolean
  minFights?: number
  limit?: number
}): string {
  const sp = new URLSearchParams()
  if (params.weightClassId) sp.set('weight_class_id', params.weightClassId.toString())
  if (params.ufcOnly) sp.set('ufc_only', 'true')
  if (params.minFights) sp.set('min_fights', params.minFights.toString())
  if (params.limit) sp.set('limit', params.limit.toString())
  const qs = sp.toString()
  return qs ? `?${qs}` : ''
}

export const chartApi = {
  // Overview
  getFinishMethods: (wc?: number) =>
    dashboardFetch<FinishMethod[]>(
      `/api/dashboard/chart/finish-methods${buildChartParams({ weightClassId: wc })}`
    ),

  getFightDuration: (wc?: number) =>
    dashboardFetch<OverviewResponse['fight_duration']>(
      `/api/dashboard/chart/fight-duration${buildChartParams({ weightClassId: wc })}`
    ),

  getLeaderboard: (wc?: number, ufcOnly?: boolean) =>
    dashboardFetch<OverviewResponse['leaderboard']>(
      `/api/dashboard/chart/leaderboard${buildChartParams({ weightClassId: wc, ufcOnly })}`
    ),

  // Striking
  getStrikeTargets: (wc?: number) =>
    dashboardFetch<StrikeTarget[]>(
      `/api/dashboard/chart/strike-targets${buildChartParams({ weightClassId: wc })}`
    ),

  getStrikingAccuracy: (wc?: number) =>
    dashboardFetch<MinFightsLeaderboard<StrikingAccuracyFighter>>(
      `/api/dashboard/chart/striking-accuracy${buildChartParams({ weightClassId: wc })}`
    ),

  getKoTkoLeaders: (wc?: number) =>
    dashboardFetch<KoTkoLeader[]>(
      `/api/dashboard/chart/ko-tko-leaders${buildChartParams({ weightClassId: wc })}`
    ),

  getSigStrikes: (wc?: number) =>
    dashboardFetch<MinFightsLeaderboard<SigStrikesLeader>>(
      `/api/dashboard/chart/sig-strikes${buildChartParams({ weightClassId: wc })}`
    ),

  // Grappling
  getTakedownAccuracy: (wc?: number) =>
    dashboardFetch<MinFightsLeaderboard<TakedownLeader>>(
      `/api/dashboard/chart/takedown-accuracy${buildChartParams({ weightClassId: wc })}`
    ),

  getSubTechniques: (wc?: number) =>
    dashboardFetch<SubmissionTechnique[]>(
      `/api/dashboard/chart/submission-techniques${buildChartParams({ weightClassId: wc })}`
    ),

  getGroundStrikes: (wc?: number) =>
    dashboardFetch<GroundStrikesLeader[]>(
      `/api/dashboard/chart/ground-strikes${buildChartParams({ weightClassId: wc })}`
    ),

  getSubEfficiency: (wc?: number) =>
    dashboardFetch<GrapplingResponse['submission_efficiency']>(
      `/api/dashboard/chart/submission-efficiency${buildChartParams({ weightClassId: wc })}`
    ),
}
