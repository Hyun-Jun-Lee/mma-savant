'use client'

import { useFighterDetail } from '@/hooks/useFighterDetail'
import { FighterDetailSkeleton } from './FighterDetailSkeleton'
import { ProfileHeader } from './ProfileHeader'
import { RecordCard } from './RecordCard'
import { FinishBreakdownChart } from './FinishBreakdownChart'
import { CareerStatsCard } from './CareerStatsCard'
import { FightHistoryTable } from './FightHistoryTable'
import { AlertCircle, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface Props {
  fighterId: number
}

export function FighterDetailClient({ fighterId }: Props) {
  const { data, loading, error, retry } = useFighterDetail(fighterId)

  if (loading) return <FighterDetailSkeleton />

  if (error || !data) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-6">
        <div className="flex flex-col items-center justify-center gap-3 py-20 text-center">
          <AlertCircle className="h-8 w-8 text-zinc-600" />
          <p className="text-sm text-zinc-500">
            {error || '데이터를 불러올 수 없습니다'}
          </p>
          <Button
            size="sm"
            variant="ghost"
            className="text-xs text-zinc-400 hover:text-zinc-200"
            onClick={retry}
          >
            <RefreshCw className="mr-1.5 h-3 w-3" />
            재시도
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 space-y-4">
      <ProfileHeader profile={data.profile} />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <RecordCard record={data.record} />
        <FinishBreakdownChart breakdown={data.record.finish_breakdown} />
      </div>

      <CareerStatsCard stats={data.stats} />

      <FightHistoryTable fights={data.fight_history} />
    </div>
  )
}
