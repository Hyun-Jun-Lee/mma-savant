import Link from 'next/link'
import { Clock } from 'lucide-react'
import { ChartCard } from '../ChartCard'
import type { UpcomingEvent } from '@/types/dashboard'

interface UpcomingEventsProps {
  events: UpcomingEvent[]
  index?: number
}

export function UpcomingEvents({ events, index }: UpcomingEventsProps) {
  return (
    <ChartCard title="Upcoming Events" description="Scheduled UFC events" tooltip="List of upcoming UFC events. Shows days remaining until each event." index={index}>
      <div className="space-y-3">
        {events.map((event) => (
          <Link
            key={event.id}
            href={`/events/${event.id}`}
            className="flex items-start justify-between gap-3 rounded-lg border border-white/[0.04] bg-white/[0.02] p-3 transition-colors hover:border-white/[0.08] hover:bg-white/[0.04]"
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
          </Link>
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
