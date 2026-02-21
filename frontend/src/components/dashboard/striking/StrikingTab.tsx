import { ChartCard } from '../ChartCard'
import { WeightClassFilter } from '../WeightClassFilter'
import { Skeleton } from '@/components/ui/skeleton'
import { useChartFilter } from '@/hooks/useChartFilter'
import { chartApi } from '@/services/dashboardApi'
import { StrikeTargetsChart } from './StrikeTargetsChart'
import { StrikingAccuracyChart } from './StrikingAccuracyChart'
import { KoTkoLeadersChart } from './KoTkoLeadersChart'
import { SigStrikesChart } from './SigStrikesChart'
import type { StrikingResponse } from '@/types/dashboard'

interface StrikingTabProps {
  data: StrikingResponse | null
  loading: boolean
  error: string | null
  onRetry: () => void
}

export function StrikingTab({ data, loading, error, onRetry }: StrikingTabProps) {
  const {
    data: strikeTargets,
    loading: stLoading,
    weightClassId: stWc,
    setWeightClassId: setStWc,
  } = useChartFilter({
    initialData: data?.strike_targets,
    fetchFn: chartApi.getStrikeTargets,
  })

  const {
    data: strikingAccuracy,
    loading: saLoading,
    weightClassId: saWc,
    setWeightClassId: setSaWc,
  } = useChartFilter({
    initialData: data?.striking_accuracy,
    fetchFn: chartApi.getStrikingAccuracy,
  })

  const {
    data: koTkoLeaders,
    loading: ktLoading,
    weightClassId: ktWc,
    setWeightClassId: setKtWc,
  } = useChartFilter({
    initialData: data?.ko_tko_leaders,
    fetchFn: chartApi.getKoTkoLeaders,
  })

  const {
    data: sigStrikes,
    loading: ssLoading,
    weightClassId: ssWc,
    setWeightClassId: setSsWc,
  } = useChartFilter({
    initialData: data?.sig_strikes_per_fight,
    fetchFn: chartApi.getSigStrikes,
  })

  return (
    <div className="space-y-4">
      {/* Row 1: Radar + Bullet */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ChartCard
          title="Strike Targets"
          description="Significant strike distribution by body area"
          tooltip="Head, Body, Leg 부위별 유효 타격 분포를 레이더 차트로 보여줍니다."
          headerRight={<WeightClassFilter value={stWc} onChange={setStWc} />}
          loading={!data && loading}
          error={error}
          onRetry={onRetry}
        >
          {stLoading ? (
            <Skeleton className="h-[280px] bg-white/[0.06]" />
          ) : (
            strikeTargets && <StrikeTargetsChart data={strikeTargets} />
          )}
        </ChartCard>
        <ChartCard
          title="Striking Accuracy"
          description="Top fighters by significant strike accuracy"
          tooltip="유효 타격 정확도 상위 파이터입니다. 넓은 바는 시도, 좁은 바는 적중 수이며 오른쪽 %가 정확도입니다."
          headerRight={<WeightClassFilter value={saWc} onChange={setSaWc} />}
          loading={!data && loading}
          error={error}
          onRetry={onRetry}
        >
          {saLoading ? (
            <Skeleton className="h-[280px] bg-white/[0.06]" />
          ) : (
            strikingAccuracy && <StrikingAccuracyChart data={strikingAccuracy} />
          )}
        </ChartCard>
      </div>

      {/* Row 2: Bar + Lollipop */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ChartCard
          title="KO/TKO Leaders"
          description="Top fighters by KO and TKO finishes"
          tooltip="KO/TKO 피니시 횟수가 가장 많은 상위 파이터를 보여줍니다."
          headerRight={<WeightClassFilter value={ktWc} onChange={setKtWc} />}
          loading={!data && loading}
          error={error}
          onRetry={onRetry}
        >
          {ktLoading ? (
            <Skeleton className="h-[280px] bg-white/[0.06]" />
          ) : (
            koTkoLeaders && <KoTkoLeadersChart data={koTkoLeaders} />
          )}
        </ChartCard>
        <ChartCard
          title="Sig. Strikes Per Fight"
          description="Top fighters by average significant strikes"
          tooltip="경기당 평균 유효 타격 수 상위 파이터입니다. 점선은 전체 평균입니다."
          headerRight={<WeightClassFilter value={ssWc} onChange={setSsWc} />}
          loading={!data && loading}
          error={error}
          onRetry={onRetry}
        >
          {ssLoading ? (
            <Skeleton className="h-[280px] bg-white/[0.06]" />
          ) : (
            sigStrikes && <SigStrikesChart data={sigStrikes} />
          )}
        </ChartCard>
      </div>
    </div>
  )
}
