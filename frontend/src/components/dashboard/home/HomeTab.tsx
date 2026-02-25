import { Users, Swords, Calendar } from 'lucide-react'
import { StatCard } from '../StatCard'
import { ChartCard } from '../ChartCard'
import { RecentEvents } from './RecentEvents'
import { UpcomingEvents } from './UpcomingEvents'
import { EventMapChart } from './EventMapChart'
import { RankingsTable } from './RankingsTable'
import type { HomeResponse } from '@/types/dashboard'

interface HomeTabProps {
  data: HomeResponse
}

export function HomeTab({ data }: HomeTabProps) {
  const { summary, recent_events, upcoming_events, rankings, event_map } = data

  return (
    <div className="space-y-6">
      {/* Summary Stats */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard label="Total Fighters" value={summary.total_fighters} icon={Users} />
        <StatCard label="Total Matches" value={summary.total_matches} icon={Swords} />
        <StatCard label="Total Events" value={summary.total_events} icon={Calendar} />
      </div>
      {/* Events Row */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <RecentEvents events={recent_events} />
        <UpcomingEvents events={upcoming_events} />
      </div>

      {/* Event Location Map */}
      {event_map && event_map.length > 0 && (
        <ChartCard
          title="Event Locations"
          description="UFC events around the world"
          tooltip="전 세계 UFC 대회 개최지를 지도에 표시합니다. 마커 크기는 이벤트 횟수에 비례합니다."
        >
          <EventMapChart data={event_map} />
        </ChartCard>
      )}

      {/* Rankings */}
      <RankingsTable rankings={rankings} />
    </div>
  )
}
