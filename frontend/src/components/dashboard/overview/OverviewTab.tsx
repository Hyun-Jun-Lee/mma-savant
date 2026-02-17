import { ChartCard } from '../ChartCard'
import { FinishMethodsChart } from './FinishMethodsChart'
import { WeightClassActivityChart } from './WeightClassActivityChart'
import { EventsTimelineChart } from './EventsTimelineChart'
import { LeaderboardChart } from './LeaderboardChart'
import { FightDurationChart } from './FightDurationChart'
import type { OverviewResponse } from '@/types/dashboard'

interface OverviewTabProps {
  data: OverviewResponse | null
  loading: boolean
  error: string | null
  onRetry: () => void
}

export function OverviewTab({ data, loading, error, onRetry }: OverviewTabProps) {
  return (
    <div className="space-y-4">
      {/* Row 1: Donut + Timeline */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ChartCard
          title="Finish Methods"
          description="Distribution of fight outcomes"
          tooltip="KO/TKO, Submission, Decision 등 경기 종료 방식의 비율을 도넛 차트로 보여줍니다."
          loading={loading}
          error={error}
          onRetry={onRetry}
        >
          {data && <FinishMethodsChart data={data.finish_methods} />}
        </ChartCard>
        <ChartCard
          title="Events Timeline"
          description="UFC events per year"
          tooltip="연도별 UFC 이벤트 개최 수 추이를 보여줍니다."
          loading={loading}
          error={error}
          onRetry={onRetry}
        >
          {data && <EventsTimelineChart data={data.events_timeline} />}
        </ChartCard>
      </div>

      {/* Row 2: Weight Class Activity + Fight Duration */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <ChartCard
          title="Weight Class Activity"
          description="Fight count and finish rates by division"
          tooltip="체급별 총 경기 수와 피니시/KO 비율을 비교합니다. Fights/Rates 탭으로 전환할 수 있습니다."
          className="lg:col-span-2"
          loading={loading}
          error={error}
          onRetry={onRetry}
        >
          {data && <WeightClassActivityChart data={data.weight_class_activity} />}
        </ChartCard>
        <ChartCard
          title="Fight Duration"
          description="Finish round distribution"
          tooltip="경기가 몇 라운드에서 끝나는지 분포를 보여줍니다. 점선은 평균 종료 라운드입니다."
          loading={loading}
          error={error}
          onRetry={onRetry}
        >
          {data && <FightDurationChart data={data.fight_duration} />}
        </ChartCard>
      </div>

      {/* Row 3: Leaderboard (full width) */}
      <ChartCard
        title="Leaderboard"
        description="Top fighters by wins and win rate"
        tooltip="총 승수 또는 승률 기준 상위 파이터를 보여줍니다. 최소 경기 수(10/20/30)로 필터링할 수 있습니다."
        loading={loading}
        error={error}
        onRetry={onRetry}
      >
        {data && <LeaderboardChart data={data.leaderboard} />}
      </ChartCard>
    </div>
  )
}
