import { ChartCard } from '../ChartCard'
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
  return (
    <div className="space-y-4">
      {/* Row 1: Radar + Bullet */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ChartCard
          title="Strike Targets"
          description="Significant strike distribution by body area"
          tooltip="Head, Body, Leg 부위별 유효 타격 분포를 레이더 차트로 보여줍니다."
          loading={loading}
          error={error}
          onRetry={onRetry}
        >
          {data && <StrikeTargetsChart data={data.strike_targets} />}
        </ChartCard>
        <ChartCard
          title="Striking Accuracy"
          description="Top fighters by significant strike accuracy"
          tooltip="유효 타격 정확도 상위 파이터입니다. 넓은 바는 시도, 좁은 바는 적중 수이며 오른쪽 %가 정확도입니다."
          loading={loading}
          error={error}
          onRetry={onRetry}
        >
          {data && <StrikingAccuracyChart data={data.striking_accuracy} />}
        </ChartCard>
      </div>

      {/* Row 2: Bar + Lollipop */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ChartCard
          title="KO/TKO Leaders"
          description="Top fighters by KO and TKO finishes"
          tooltip="KO/TKO 피니시 횟수가 가장 많은 상위 파이터를 보여줍니다."
          loading={loading}
          error={error}
          onRetry={onRetry}
        >
          {data && <KoTkoLeadersChart data={data.ko_tko_leaders} />}
        </ChartCard>
        <ChartCard
          title="Sig. Strikes Per Fight"
          description="Top fighters by average significant strikes"
          tooltip="경기당 평균 유효 타격 수 상위 파이터입니다. 점선은 전체 평균입니다."
          loading={loading}
          error={error}
          onRetry={onRetry}
        >
          {data && <SigStrikesChart data={data.sig_strikes_per_fight} />}
        </ChartCard>
      </div>
    </div>
  )
}
