export interface EventInfo {
  id: number
  name: string
  event_date: string
  location: string | null
  url: string | null
}

export interface BasicMatchStat {
  fighter_match_id: number
  knockdowns: number
  control_time_seconds: number
  submission_attempts: number
  sig_str_landed: number
  sig_str_attempted: number
  total_str_landed: number
  total_str_attempted: number
  td_landed: number
  td_attempted: number
  round: number
}

export interface EventFighterStat {
  fighter_id: number
  name: string
  nickname: string | null
  nationality: string | null
  result: string | null
  ranking: number | null
  stats: BasicMatchStat | null
  round_stats: BasicMatchStat[] | null
}

export interface EventMatch {
  match_id: number
  weight_class: string | null
  method: string | null
  result_round: number | null
  time: string | null
  order: number | null
  is_main_event: boolean
  fighters: EventFighterStat[]
}

export interface EventSummary {
  total_bouts: number
  ko_tko_count: number
  submission_count: number
  decision_count: number
  other_count: number
  avg_fight_duration_seconds: number
}

export interface EventDetailResponse {
  event: EventInfo
  matches: EventMatch[]
  summary: EventSummary
}
