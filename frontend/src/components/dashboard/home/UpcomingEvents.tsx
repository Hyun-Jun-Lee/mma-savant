import { Clock } from 'lucide-react'
import { ChartCard } from '../ChartCard'
import type { UpcomingEvent } from '@/types/dashboard'

interface UpcomingEventsProps {
  events: UpcomingEvent[]
}

export function UpcomingEvents({ events }: UpcomingEventsProps) {
  return (
    <ChartCard title="Upcoming Events" description="Scheduled UFC events" tooltip="예정된 UFC 이벤트 목록입니다. D-day로 남은 일수를 확인할 수 있습니다.">
      <div className="space-y-3">
        {events.map((event) => (
          <div
            key={event.id}
            className="flex items-start justify-between gap-3 rounded-lg border border-white/[0.04] bg-white/[0.02] p-3"
          >
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-zinc-200">
                {event.name}
              </p>
              <p className="mt-0.5 text-xs text-zinc-500">{event.location}</p>
            </div>
            <div className="shrink-0 text-right">
              <p className="text-xs text-zinc-500">
                {new Date(event.event_date).toLocaleDateString('en-US', {
                  month: 'short',
                  day: 'numeric',
                  year: 'numeric',
                })}
              </p>
              <div className="mt-0.5 flex items-center justify-end gap-1 text-xs font-medium text-amber-500/80">
                <Clock className="h-3 w-3" />
                D-{event.days_until}
              </div>
            </div>
          </div>
        ))}
        {events.length === 0 && (
          <p className="py-8 text-center text-sm text-zinc-600">
            No upcoming events
          </p>
        )}
      </div>
    </ChartCard>
  )
}
