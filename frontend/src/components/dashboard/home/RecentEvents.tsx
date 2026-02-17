import { Calendar } from 'lucide-react'
import { ChartCard } from '../ChartCard'
import type { RecentEvent } from '@/types/dashboard'

interface RecentEventsProps {
  events: RecentEvent[]
}

export function RecentEvents({ events }: RecentEventsProps) {
  return (
    <ChartCard title="Recent Events" description="Latest UFC events" tooltip="최근 종료된 UFC 이벤트 목록입니다. 메인 이벤트와 총 경기 수를 확인할 수 있습니다.">
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
              {event.main_event && (
                <p className="mt-1 text-xs text-zinc-400">
                  Main: {event.main_event}
                </p>
              )}
            </div>
            <div className="shrink-0 text-right">
              <div className="flex items-center gap-1 text-xs text-zinc-500">
                <Calendar className="h-3 w-3" />
                {new Date(event.event_date).toLocaleDateString('en-US', {
                  month: 'short',
                  day: 'numeric',
                  year: 'numeric',
                })}
              </div>
              <p className="mt-0.5 text-xs text-zinc-600">
                {event.total_fights} fights
              </p>
            </div>
          </div>
        ))}
        {events.length === 0 && (
          <p className="py-8 text-center text-sm text-zinc-600">
            No recent events
          </p>
        )}
      </div>
    </ChartCard>
  )
}
