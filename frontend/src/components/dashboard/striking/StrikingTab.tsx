import { ChartCard } from '../ChartCard'
import { WeightClassFilter } from '../WeightClassFilter'
import { Skeleton } from '@/components/ui/skeleton'
import { useChartFilter } from '@/hooks/useChartFilter'
import { chartApi } from '@/services/dashboardApi'
import { StrikeTargetsChart } from './StrikeTargetsChart'
import { StrikingAccuracyChart } from './StrikingAccuracyChart'
import { KoTkoLeadersChart } from './KoTkoLeadersChart'
import { SigStrikesChart } from './SigStrikesChart'
import { SigStrikesByWcChart } from './SigStrikesByWcChart'
import { StrikeExchangeChart } from './StrikeExchangeChart'
import { StanceWinrateChart } from './StanceWinrateChart'
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

  const {
    data: strikeExchange,
    loading: seLoading,
    weightClassId: seWc,
    setWeightClassId: setSeWc,
  } = useChartFilter({
    initialData: data?.strike_exchange,
    fetchFn: chartApi.getStrikeExchange,
  })

  const {
    data: stanceWinrate,
    loading: swLoading,
    weightClassId: swWc,
    setWeightClassId: setSwWc,
  } = useChartFilter({
    initialData: data?.stance_winrate,
    fetchFn: chartApi.getStanceWinrate,
  })

  return (
    <div className="space-y-4">
      {/* Row 1: KO/TKO Leaders + Striking Accuracy */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ChartCard
          title="KO/TKO Leaders"
          description="Top fighters by KO and TKO finishes"
          tooltip="Shows top fighters with the most KO/TKO finishes."
          headerRight={<WeightClassFilter value={ktWc} onChange={setKtWc} />}
          loading={!data && loading}
          error={error}
          onRetry={onRetry}
          index={0}
        >
          {ktLoading ? (
            <Skeleton className="h-[280px] bg-white/[0.06]" />
          ) : (
            koTkoLeaders && <KoTkoLeadersChart data={koTkoLeaders} />
          )}
        </ChartCard>
        <ChartCard
          title="Stance Winrate"
          description="Win rates by stance matchup (matrix table)"
          tooltip="Color-coded matrix table showing win rates by stance matchup. Compare Orthodox/Southpaw/Switch matchup advantages."
          headerRight={<WeightClassFilter value={swWc} onChange={setSwWc} />}
          loading={!data && loading}
          error={error}
          onRetry={onRetry}
          index={1}
        >
          {swLoading ? (
            <Skeleton className="h-[280px] bg-white/[0.06]" />
          ) : (
            stanceWinrate && <StanceWinrateChart data={stanceWinrate} />
          )}
        </ChartCard>
      </div>

      {/* Row 2: Strike Exchange (full width) */}
      <ChartCard
        title="Strike Exchange"
        description="Striking differential per fight"
        tooltip="Shows striking differential per fight (landed minus taken). Positive values indicate dominance."
        headerRight={<WeightClassFilter value={seWc} onChange={setSeWc} />}
        loading={!data && loading}
        error={error}
        onRetry={onRetry}
        index={2}
      >
        {seLoading ? (
          <Skeleton className="h-[280px] bg-white/[0.06]" />
        ) : (
          strikeExchange && <StrikeExchangeChart data={strikeExchange} />
        )}
      </ChartCard>

      {/* Row 3: Stance Winrate + Sig. Strikes Per Fight */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ChartCard
          title="Striking Accuracy"
          description="Top fighters by significant strike accuracy"
          tooltip="Top fighters by striking accuracy. Bar length = accuracy %, label on right = percentage."
          headerRight={<WeightClassFilter value={saWc} onChange={setSaWc} />}
          loading={!data && loading}
          error={error}
          onRetry={onRetry}
          index={3}
        >
          {saLoading ? (
            <Skeleton className="h-[280px] bg-white/[0.06]" />
          ) : (
            strikingAccuracy && <StrikingAccuracyChart data={strikingAccuracy} />
          )}
        </ChartCard>
        <ChartCard
          title="Sig. Strikes Per Fight"
          description="Top fighters by average significant strikes"
          tooltip="Top fighters by average significant strikes per fight. Dashed line indicates the overall average."
          headerRight={<WeightClassFilter value={ssWc} onChange={setSsWc} />}
          loading={!data && loading}
          error={error}
          onRetry={onRetry}
          index={4}
        >
          {ssLoading ? (
            <Skeleton className="h-[280px] bg-white/[0.06]" />
          ) : (
            sigStrikes && <SigStrikesChart data={sigStrikes} />
          )}
        </ChartCard>
      </div>

      {/* Row 4: Strike Targets + Sig Strikes by Weight Class */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ChartCard
          title="Strike Targets"
          description="Significant strike distribution by body area"
          tooltip="Radar chart showing significant strike distribution by target area: Head, Body, Leg."
          headerRight={<WeightClassFilter value={stWc} onChange={setStWc} />}
          loading={!data && loading}
          error={error}
          onRetry={onRetry}
          index={5}
        >
          {stLoading ? (
            <Skeleton className="h-[280px] bg-white/[0.06]" />
          ) : (
            strikeTargets && <StrikeTargetsChart data={strikeTargets} />
          )}
        </ChartCard>
        <ChartCard
          title="Sig. Strikes by Weight Class"
          description="Average significant strikes per fight by division"
          tooltip="Compares average significant strikes per fight across weight classes."
          loading={loading}
          error={error}
          onRetry={onRetry}
          index={6}
        >
          {data && <SigStrikesByWcChart data={data.sig_strikes_by_weight_class} />}
        </ChartCard>
      </div>
    </div>
  )
}
