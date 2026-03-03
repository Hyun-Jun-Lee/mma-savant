'use client'

import { useEventDetail } from '@/hooks/useEventDetail'
import { EventDetailSkeleton } from './EventDetailSkeleton'
import { EventHeader } from './EventHeader'
import { EventSummaryStats } from './EventSummaryStats'
import { FightCard } from './FightCard'
import { AlertCircle, HelpCircle, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip'

interface Props {
  eventId: number
}

export function EventDetailClient({ eventId }: Props) {
  const { data, loading, error, retry } = useEventDetail(eventId)

  if (loading) return <EventDetailSkeleton />

  if (error || !data) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-6">
        <div className="flex flex-col items-center justify-center gap-3 py-20 text-center">
          <AlertCircle className="h-8 w-8 text-zinc-600" />
          <p className="text-sm text-zinc-500">
            {error || 'Failed to load event data'}
          </p>
          <Button
            size="sm"
            variant="ghost"
            className="text-xs text-zinc-400 hover:text-zinc-200"
            onClick={retry}
          >
            <RefreshCw className="mr-1.5 h-3 w-3" />
            Retry
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 space-y-4">
      <EventHeader event={data.event} summary={data.summary} />

      <EventSummaryStats summary={data.summary} />

      {data.matches.length > 0 ? (
        <div className="space-y-3">
          <div className="flex items-center gap-1.5">
            <h2 className="text-sm font-semibold text-zinc-100">
              Fight Card ({data.matches.length})
            </h2>
            <Tooltip>
              <TooltipTrigger asChild>
                <HelpCircle className="h-3.5 w-3.5 shrink-0 cursor-help text-zinc-600 hover:text-zinc-400 transition-colors" />
              </TooltipTrigger>
              <TooltipContent
                side="top"
                className="max-w-[260px] bg-zinc-900 text-zinc-200 border border-white/[0.06]"
              >
                카드를 클릭하면 상세 스탯을 확인할 수 있습니다. 강조된 카드는 메인 이벤트, 메달 아이콘은 승리 선수를 나타냅니다.
              </TooltipContent>
            </Tooltip>
          </div>
          {data.matches.map((match) => (
            <FightCard key={match.match_id} match={match} />
          ))}
        </div>
      ) : (
        <div className="rounded-xl border border-white/[0.06] bg-white/[0.03] p-5">
          <p className="py-8 text-center text-sm text-zinc-600">
            No fight records available
          </p>
        </div>
      )}
    </div>
  )
}
