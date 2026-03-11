import { ChartCard } from '../ChartCard'
import { WeightClassFilter } from '../WeightClassFilter'
import { Skeleton } from '@/components/ui/skeleton'
import { useChartFilter } from '@/hooks/useChartFilter'
import { chartApi } from '@/services/dashboardApi'
import { TakedownChart } from './TakedownChart'
import { SubmissionTechChart } from './SubmissionTechChart'
import { GroundStrikesChart } from './GroundStrikesChart'
import { SubmissionEfficiencyChart } from './SubmissionEfficiencyChart'
import { TdAttemptsChart } from './TdAttemptsChart'
import { TdSubCorrelationChart } from './TdSubCorrelationChart'
import { TdDefenseChart } from './TdDefenseChart'
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

  const {
    data: tdAttemptsLeaders,
    loading: taLoading,
    weightClassId: taWc,
    setWeightClassId: setTaWc,
  } = useChartFilter({
    initialData: data?.td_attempts_leaders,
    fetchFn: chartApi.getTdAttemptsLeaders,
  })

  const {
    data: tdSubCorrelation,
    loading: tscLoading,
    weightClassId: tscWc,
    setWeightClassId: setTscWc,
  } = useChartFilter({
    initialData: data?.td_sub_correlation,
    fetchFn: chartApi.getTdSubCorrelation,
  })

  const {
    data: tdDefenseLeaders,
    loading: tddLoading,
    weightClassId: tddWc,
    setWeightClassId: setTddWc,
  } = useChartFilter({
    initialData: data?.td_defense_leaders,
    fetchFn: chartApi.getTdDefenseLeaders,
  })

  return (
    <div className="space-y-4">
      {/* Row 1: Takedown Bullet + Submission Techniques */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ChartCard
          title="Takedown Accuracy"
          description="Top fighters by takedown accuracy"
          tooltip="Top fighters by takedown accuracy. Wide bar = attempts, narrow bar = landed, percentage on right = accuracy."
          headerRight={<WeightClassFilter value={tdWc} onChange={setTdWc} />}
          loading={!data && loading}
          error={error}
          onRetry={onRetry}
          index={0}
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
          tooltip="Shows the most commonly used submission techniques in the UFC."
          headerRight={<WeightClassFilter value={stWc} onChange={setStWc} />}
          loading={!data && loading}
          error={error}
          onRetry={onRetry}
          index={1}
        >
          {stLoading ? (
            <Skeleton className="h-[280px] bg-white/[0.06]" />
          ) : (
            subTechniques && <SubmissionTechChart data={subTechniques} />
          )}
        </ChartCard>
      </div>

      {/* Row 2: Ground Strikes + Submission Efficiency */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ChartCard
          title="Ground Strikes"
          description="Top fighters by ground strike accuracy"
          tooltip="Ranked list of fighters by ground strike accuracy, showing landed and attempted counts."
          headerRight={<WeightClassFilter value={gsWc} onChange={setGsWc} />}
          loading={!data && loading}
          error={error}
          onRetry={onRetry}
          index={2}
        >
          {gsLoading ? (
            <Skeleton className="h-[280px] bg-white/[0.06]" />
          ) : (
            groundStrikes && <GroundStrikesChart data={groundStrikes} />
          )}
        </ChartCard>
        <ChartCard
          title="Submission Efficiency"
          description="Top fighters by submission finish rate"
          tooltip="Ranked list of fighters by submission efficiency, showing finishes and attempts with average ratio."
          headerRight={<WeightClassFilter value={seWc} onChange={setSeWc} />}
          loading={!data && loading}
          error={error}
          onRetry={onRetry}
          index={3}
        >
          {seLoading ? (
            <Skeleton className="h-[280px] bg-white/[0.06]" />
          ) : (
            subEfficiency && <SubmissionEfficiencyChart data={subEfficiency} />
          )}
        </ChartCard>
      </div>

      {/* Row 3: TD Attempts Leaders + TD Defense */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ChartCard
          title="TD Attempts Leaders"
          description="Top fighters by takedown attempts per fight"
          tooltip="Top fighters by takedown attempts per fight. Dashed line indicates the overall average."
          headerRight={<WeightClassFilter value={taWc} onChange={setTaWc} />}
          loading={!data && loading}
          error={error}
          onRetry={onRetry}
          index={4}
        >
          {taLoading ? (
            <Skeleton className="h-[280px] bg-white/[0.06]" />
          ) : (
            tdAttemptsLeaders && <TdAttemptsChart data={tdAttemptsLeaders} />
          )}
        </ChartCard>
        <ChartCard
          title="TD Defense Leaders"
          description="Top fighters by takedown defense rate"
          tooltip="Top fighters by takedown defense rate. Shows the percentage of opponent takedown attempts successfully defended."
          headerRight={<WeightClassFilter value={tddWc} onChange={setTddWc} />}
          loading={!data && loading}
          error={error}
          onRetry={onRetry}
          index={5}
        >
          {tddLoading ? (
            <Skeleton className="h-[280px] bg-white/[0.06]" />
          ) : (
            tdDefenseLeaders && <TdDefenseChart data={tdDefenseLeaders} />
          )}
        </ChartCard>
      </div>

      {/* Row 4: TD-Sub Correlation */}
      <ChartCard
        title="TD-Submission Correlation"
        description={
          <span className="flex items-center gap-2">
            Classifies fighters by takedown and submission style
            <span className="flex items-center gap-1.5">
              <span className="flex items-center gap-0.5">
                <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-500/60" />
                <span className="text-zinc-600">TD</span>
              </span>
              <span className="flex items-center gap-0.5">
                <span className="inline-block h-1.5 w-1.5 rounded-full bg-purple-500/60" />
                <span className="text-zinc-600">SUB</span>
              </span>
            </span>
          </span>
        }
        tooltip="Quadrant grid classifying fighters by takedown and submission performance relative to averages."
        headerRight={<WeightClassFilter value={tscWc} onChange={setTscWc} />}
        loading={!data && loading}
        error={error}
        onRetry={onRetry}
        index={6}
      >
        {tscLoading ? (
          <Skeleton className="h-[280px] bg-white/[0.06]" />
        ) : (
          tdSubCorrelation && <TdSubCorrelationChart data={tdSubCorrelation} />
        )}
      </ChartCard>
    </div>
  )
}
