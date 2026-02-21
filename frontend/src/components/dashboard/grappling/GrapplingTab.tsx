import { ChartCard } from '../ChartCard'
import { WeightClassFilter } from '../WeightClassFilter'
import { Skeleton } from '@/components/ui/skeleton'
import { useChartFilter } from '@/hooks/useChartFilter'
import { chartApi } from '@/services/dashboardApi'
import { TakedownChart } from './TakedownChart'
import { SubmissionTechChart } from './SubmissionTechChart'
import { ControlTimeChart } from './ControlTimeChart'
import { GroundStrikesChart } from './GroundStrikesChart'
import { SubmissionEfficiencyChart } from './SubmissionEfficiencyChart'
import type { GrapplingResponse } from '@/types/dashboard'

interface GrapplingTabProps {
  data: GrapplingResponse | null
  loading: boolean
  error: string | null
  onRetry: () => void
}

export function GrapplingTab({ data, loading, error, onRetry }: GrapplingTabProps) {
  const {
    data: takedownAccuracy,
    loading: tdLoading,
    weightClassId: tdWc,
    setWeightClassId: setTdWc,
  } = useChartFilter({
    initialData: data?.takedown_accuracy,
    fetchFn: chartApi.getTakedownAccuracy,
  })

  const {
    data: subTechniques,
    loading: stLoading,
    weightClassId: stWc,
    setWeightClassId: setStWc,
  } = useChartFilter({
    initialData: data?.submission_techniques,
    fetchFn: chartApi.getSubTechniques,
  })

  const {
    data: groundStrikes,
    loading: gsLoading,
    weightClassId: gsWc,
    setWeightClassId: setGsWc,
  } = useChartFilter({
    initialData: data?.ground_strikes,
    fetchFn: chartApi.getGroundStrikes,
  })

  const {
    data: subEfficiency,
    loading: seLoading,
    weightClassId: seWc,
    setWeightClassId: setSeWc,
  } = useChartFilter({
    initialData: data?.submission_efficiency,
    fetchFn: chartApi.getSubEfficiency,
  })

  return (
    <div className="space-y-4">
      {/* Row 1: Takedown Bullet + Submission Techniques */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ChartCard
          title="Takedown Accuracy"
          description="Top fighters by takedown accuracy"
          tooltip="테이크다운 정확도 상위 파이터입니다. 넓은 바는 시도, 좁은 바는 성공 수이며 오른쪽 %가 정확도입니다."
          headerRight={<WeightClassFilter value={tdWc} onChange={setTdWc} />}
          loading={!data && loading}
          error={error}
          onRetry={onRetry}
        >
          {tdLoading ? (
            <Skeleton className="h-[280px] bg-white/[0.06]" />
          ) : (
            takedownAccuracy && <TakedownChart data={takedownAccuracy} />
          )}
        </ChartCard>
        <ChartCard
          title="Submission Techniques"
          description="Most common submission finishes"
          tooltip="UFC에서 가장 많이 사용된 서브미션 기술 순위를 보여줍니다."
          headerRight={<WeightClassFilter value={stWc} onChange={setStWc} />}
          loading={!data && loading}
          error={error}
          onRetry={onRetry}
        >
          {stLoading ? (
            <Skeleton className="h-[280px] bg-white/[0.06]" />
          ) : (
            subTechniques && <SubmissionTechChart data={subTechniques} />
          )}
        </ChartCard>
      </div>

      {/* Row 2: Control Time + Ground Strikes + Submission Efficiency */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <ChartCard
          title="Control Time"
          description="Average control time by weight class"
          tooltip="체급별 경기당 평균 그라운드 컨트롤 시간을 보여줍니다."
          loading={loading}
          error={error}
          onRetry={onRetry}
        >
          {data && <ControlTimeChart data={data.control_time} />}
        </ChartCard>
        <ChartCard
          title="Ground Strikes"
          description="Attempts vs landed with accuracy bubble size"
          tooltip="그라운드 타격 시도 vs 적중을 산점도로 표시합니다. 점 크기는 정확도, 대각선은 참고 비율입니다."
          headerRight={<WeightClassFilter value={gsWc} onChange={setGsWc} />}
          loading={!data && loading}
          error={error}
          onRetry={onRetry}
        >
          {gsLoading ? (
            <Skeleton className="h-[280px] bg-white/[0.06]" />
          ) : (
            groundStrikes && <GroundStrikesChart data={groundStrikes} />
          )}
        </ChartCard>
        <ChartCard
          title="Submission Efficiency"
          description="Attempts vs finishes with average ratio"
          tooltip="서브미션 시도 대비 성공 비율을 보여줍니다. 점선은 전체 평균 효율입니다."
          headerRight={<WeightClassFilter value={seWc} onChange={setSeWc} />}
          loading={!data && loading}
          error={error}
          onRetry={onRetry}
        >
          {seLoading ? (
            <Skeleton className="h-[280px] bg-white/[0.06]" />
          ) : (
            subEfficiency && <SubmissionEfficiencyChart data={subEfficiency} />
          )}
        </ChartCard>
      </div>
    </div>
  )
}
