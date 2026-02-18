import { Users, Swords, Calendar } from 'lucide-react'
import { StatCard } from '../StatCard'
import { RecentEvents } from './RecentEvents'
import { UpcomingEvents } from './UpcomingEvents'
import { RankingsTable } from './RankingsTable'
import type { HomeResponse } from '@/types/dashboard'

interface HomeTabProps {
  data: HomeResponse
}

export function HomeTab({ data }: HomeTabProps) {
  const { summary, recent_events, upcoming_events, rankings } = data

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

      {/* Rankings */}
      <RankingsTable rankings={rankings} />
    </div>
  )
}
