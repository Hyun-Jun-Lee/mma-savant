import { Users, Swords, Calendar, Clock } from 'lucide-react'
import { StatCard } from '../StatCard'
import { ChartCard } from '../ChartCard'
import { RecentEvents } from './RecentEvents'
import { UpcomingEvents } from './UpcomingEvents'
import { EventMapChart } from './EventMapChart'
import { NationalityBarChart } from './NationalityBarChart'
import { RankingsTable } from './RankingsTable'
import { formatDate } from '@/lib/utils'
import type { HomeResponse } from '@/types/dashboard'

interface HomeTabProps {
  data: HomeResponse
}

export function HomeTab({ data }: HomeTabProps) {
  const { summary, recent_events, upcoming_events, rankings, event_map, nationality_distribution } = data

  const latestEventDate = recent_events.length > 0
    ? recent_events.reduce((latest, e) => e.event_date > latest ? e.event_date : latest, recent_events[0].event_date)
    : null

  return (
    <div className="space-y-6">
      {/* Summary Stats */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard label="Total Fighters" value={summary.total_fighters} icon={Users} iconColor="text-blue-400" index={0} />
        <StatCard label="Total Matches" value={summary.total_matches} icon={Swords} iconColor="text-red-400" index={1} />
        <StatCard label="Total Events" value={summary.total_events} icon={Calendar} iconColor="text-amber-400" index={2} />
      </div>
      {/* Events Row */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <RecentEvents events={recent_events} totalEvents={summary.total_events} index={0} />
        <UpcomingEvents events={upcoming_events} index={1} />
      </div>

      {/* Event Location Map */}
      {event_map && event_map.length > 0 && (
        <ChartCard
          title="Event Locations"
          description="UFC events around the world"
          tooltip="Shows UFC event locations on a world map. Marker size is proportional to event count."
          index={0}
        >
          <EventMapChart data={event_map} />
        </ChartCard>
      )}

      {/* Nationality Distribution */}
      {nationality_distribution && nationality_distribution.length > 0 && (
        <ChartCard
          title="Nationality Distribution"
          description="Fighter count by nationality (Top 15 + Others)"
          tooltip="Shows fighter nationality distribution. Bar length is proportional to fighter count."
          index={1}
        >
          <NationalityBarChart data={nationality_distribution} />
        </ChartCard>
      )}

      {/* Rankings */}
      <RankingsTable rankings={rankings} index={2} />

      {/* Data Freshness */}
      {latestEventDate && (
        <div className="flex items-center justify-center gap-1.5 text-xs text-zinc-600">
          <Clock className="h-3 w-3" />
          <span>Data as of {formatDate(latestEventDate)}</span>
        </div>
      )}
    </div>
  )
}
