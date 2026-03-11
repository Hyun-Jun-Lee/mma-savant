import { ChartCard } from '../ChartCard'
import { WeightClassFilter } from '../WeightClassFilter'
import { Skeleton } from '@/components/ui/skeleton'
import { useChartFilter } from '@/hooks/useChartFilter'
import { chartApi } from '@/services/dashboardApi'
import { FinishMethodsChart } from './FinishMethodsChart'
import { WeightClassActivityChart } from './WeightClassActivityChart'
import { EventsTimelineChart } from './EventsTimelineChart'
import { LeaderboardChart } from './LeaderboardChart'
import { FightDurationChart } from './FightDurationChart'
import { FinishRateTrendChart } from './FinishRateTrendChart'
import type { OverviewResponse } from '@/types/dashboard'

interface OverviewTabProps {
  data: OverviewResponse | null
  loading: boolean
  error: string | null
  onRetry: () => void
}

export function OverviewTab({ data, loading, error, onRetry }: OverviewTabProps) {
  const {
    data: finishMethods,
    loading: fmLoading,
    weightClassId: fmWc,
    setWeightClassId: setFmWc,
  } = useChartFilter({
    initialData: data?.finish_methods,
    fetchFn: chartApi.getFinishMethods,
  })

  const {
    data: fightDuration,
    loading: fdLoading,
    weightClassId: fdWc,
    setWeightClassId: setFdWc,
  } = useChartFilter({
    initialData: data?.fight_duration,
    fetchFn: chartApi.getFightDuration,
  })

  const {
    data: finishRateTrend,
    loading: frtLoading,
    weightClassId: frtWc,
    setWeightClassId: setFrtWc,
  } = useChartFilter({
    initialData: data?.finish_rate_trend,
    fetchFn: chartApi.getFinishRateTrend,
  })

  return (
    <div className="space-y-4">
      {/* Row 1: Donut + Timeline */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ChartCard
          title="Finish Methods"
          description="Distribution of fight outcomes"
          tooltip="Donut chart showing the distribution of fight outcomes: KO/TKO, Submission, Decision, etc."
          headerRight={<WeightClassFilter value={fmWc} onChange={setFmWc} />}
          loading={!data && loading}
          error={error}
          onRetry={onRetry}
          index={0}
        >
          {fmLoading ? (
            <Skeleton className="h-[280px] bg-white/[0.06]" />
          ) : (
            finishMethods && <FinishMethodsChart data={finishMethods} />
          )}
        </ChartCard>
        <ChartCard
          title="Events Timeline"
          description="UFC events per year (area chart)"
          tooltip="Area chart showing the trend of UFC events held per year."
          loading={loading}
          error={error}
          onRetry={onRetry}
          index={1}
        >
          {data && <EventsTimelineChart data={data.events_timeline} />}
        </ChartCard>
      </div>

      {/* Row 2: Weight Class Activity + Fight Duration */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <ChartCard
          title="Weight Class Activity"
          description="Total fight count by division"
          tooltip="Horizontal bar chart showing total fight count per weight class, sorted by activity level."
          className="lg:col-span-2"
          loading={loading}
          error={error}
          onRetry={onRetry}
          index={2}
        >
          {data && <WeightClassActivityChart data={data.weight_class_activity} />}
        </ChartCard>
        <ChartCard
          title="Fight Duration"
          description="Finish method breakdown by round"
          tooltip="Stacked bar showing KO/TKO, Submission, and Decision/Other counts per round. Dashed line indicates the average finish round."
          headerRight={<WeightClassFilter value={fdWc} onChange={setFdWc} />}
          loading={!data && loading}
          error={error}
          onRetry={onRetry}
          index={3}
        >
          {fdLoading ? (
            <Skeleton className="h-[280px] bg-white/[0.06]" />
          ) : (
            fightDuration && <FightDurationChart data={fightDuration} />
          )}
        </ChartCard>
      </div>

      {/* Row 3: Finish Rate Trend */}
      <ChartCard
        title="Finish Rate Trend"
        description="Year-over-year finish method rates (line chart)"
        tooltip="Line chart showing year-over-year trends for KO/TKO, submission, and decision rates at 5-year intervals."
        headerRight={<WeightClassFilter value={frtWc} onChange={setFrtWc} />}
        loading={!data && loading}
        error={error}
        onRetry={onRetry}
        index={4}
      >
        {frtLoading ? (
          <Skeleton className="h-[280px] bg-white/[0.06]" />
        ) : (
          finishRateTrend && <FinishRateTrendChart data={finishRateTrend} />
        )}
      </ChartCard>

      {/* Row 4: Leaderboard (full width) */}
      <LeaderboardChart
        initialData={data?.leaderboard}
        parentLoading={loading}
        error={error}
        onRetry={onRetry}
        index={5}
      />
    </div>
  )
}
