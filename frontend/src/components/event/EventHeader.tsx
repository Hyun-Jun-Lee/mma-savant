'use client'

import type { EventInfo, EventSummary } from '@/types/event'
import { Calendar, MapPin, Swords, Clock } from 'lucide-react'
import { formatDate } from '@/lib/utils'

interface Props {
  event: EventInfo
  summary: EventSummary
}

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = Math.round(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

export function EventHeader({ event, summary }: Props) {
  return (
    <div className="rounded-xl border border-white/[0.06] bg-white/[0.03] p-5 transition-all duration-300 ease-out hover:border-white/[0.12] hover:bg-white/[0.05]">
      <h1 className="text-2xl font-bold text-zinc-100">{event.name}</h1>

      <div className="mt-2 flex flex-wrap items-center gap-4 text-sm text-zinc-400">
        {event.event_date && (
          <span className="flex items-center gap-1.5">
            <Calendar className="h-3.5 w-3.5" />
            {formatDate(event.event_date)}
          </span>
        )}
        {event.location && (
          <span className="flex items-center gap-1.5">
            <MapPin className="h-3.5 w-3.5" />
            {event.location}
          </span>
        )}
        <span className="flex items-center gap-1.5">
          <Swords className="h-3.5 w-3.5" />
          {summary.total_bouts} Bouts
        </span>
        {summary.avg_fight_duration_seconds > 0 && (
          <span className="flex items-center gap-1.5">
            <Clock className="h-3.5 w-3.5" />
            Avg. {formatDuration(summary.avg_fight_duration_seconds)}
          </span>
        )}
      </div>
    </div>
  )
}
