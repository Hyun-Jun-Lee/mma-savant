export interface FighterProfile {
  id: number
  name: string
  nickname: string | null
  nationality: string | null
  stance: string | null
  belt: boolean
  height_cm: number | null
  weight_kg: number | null
  reach_cm: number | null
  birthdate: string | null
  age: number | null
  weight_class: string | null
  rankings: Record<string, number>
}

export interface FinishBreakdown {
  ko_tko: number
  submission: number
  decision: number
}

export interface FighterRecord {
  wins: number
  losses: number
  draws: number
  win_rate: number
  current_streak: { type: string; count: number }
  finish_breakdown: FinishBreakdown
}

export interface StrikingStats {
  sig_str_landed: number
  sig_str_attempted: number
  sig_str_accuracy: number
  knockdowns: number
  opp_knockdowns: number
  head_landed: number
  head_attempted: number
  body_landed: number
  body_attempted: number
  leg_landed: number
  leg_attempted: number
  match_count: number
}

export interface GrapplingStats {
  td_landed: number
  td_attempted: number
  td_accuracy: number
  td_defense_rate: number
  opp_td_landed: number
  opp_td_attempted: number
  control_time_seconds: number
  avg_control_time_seconds: number
  submission_attempts: number
  top_submission: string | null
  match_count: number
}

export interface CareerStats {
  striking: StrikingStats
  grappling: GrapplingStats
}

export interface Opponent {
  id: number
  name: string
  nationality: string | null
}

export interface PerMatchBasicStats {
  knockdowns: number
  sig_str_landed: number
  sig_str_attempted: number
  total_str_landed: number
  total_str_attempted: number
  td_landed: number
  td_attempted: number
  control_time_seconds: number
  submission_attempts: number
}

export interface PerMatchSigStr {
  head_landed: number
  head_attempted: number
  body_landed: number
  body_attempted: number
  leg_landed: number
  leg_attempted: number
  clinch_landed: number
  clinch_attempted: number
  ground_landed: number
  ground_attempted: number
}

export interface PerMatchStats {
  basic: PerMatchBasicStats | null
  sig_str: PerMatchSigStr | null
}

export interface FightHistoryItem {
  match_id: number
  result: string
  method: string | null
  round: number | null
  time: string | null
  event_id: number | null
  event_name: string | null
  event_date: string | null
  weight_class: string | null
  is_main_event: boolean
  opponent: Opponent
  stats: PerMatchStats | null
}

export interface FighterDetailResponse {
  profile: FighterProfile
  record: FighterRecord
  stats: CareerStats | null
  fight_history: FightHistoryItem[]
}
