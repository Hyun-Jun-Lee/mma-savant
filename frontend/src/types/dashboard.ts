// ── Home ──
export interface DashboardSummary {
  total_fighters: number
  total_matches: number
  total_events: number
}

export interface RecentEvent {
  id: number
  name: string
  location: string
  event_date: string
  total_fights: number
  main_event: string | null
}

export interface UpcomingEvent {
  id: number
  name: string
  location: string
  event_date: string
  days_until: number
}

export interface RankingFighter {
  ranking: number // 0 = 챔피언
  fighter_name: string
  wins: number
  losses: number
  draws: number
}

export interface WeightClassRanking {
  weight_class_id: number
  weight_class: string
  fighters: RankingFighter[]
}

export interface HomeResponse {
  summary: DashboardSummary
  recent_events: RecentEvent[]
  upcoming_events: UpcomingEvent[]
  rankings: WeightClassRanking[]
}

// ── Overview ──
export interface FinishMethod {
  method_category: string
  count: number
}

export interface WeightClassActivity {
  weight_class: string
  total_fights: number
  ko_tko_count: number
  sub_count: number
  finish_rate: number
  ko_tko_rate: number
  sub_rate: number
}

export interface EventTimeline {
  year: number
  event_count: number
}

export interface LeaderboardFighter {
  name: string
  wins: number
  losses: number
  draws: number
  win_rate: number
}

export interface FightDurationRound {
  result_round: number
  fight_count: number
  percentage: number
}

export interface OverviewResponse {
  finish_methods: FinishMethod[]
  weight_class_activity: WeightClassActivity[]
  events_timeline: EventTimeline[]
  leaderboard: {
    wins: LeaderboardFighter[]
    winrate_min10: LeaderboardFighter[]
    winrate_min20: LeaderboardFighter[]
    winrate_min30: LeaderboardFighter[]
  }
  fight_duration: {
    rounds: FightDurationRound[]
    avg_round: number
    avg_time_seconds: number | null
  }
}

// ── Striking ──
export interface StrikeTarget {
  target: string
  landed: number
}

export interface StrikingAccuracyFighter {
  name: string
  total_sig_landed: number
  total_sig_attempted: number
  accuracy: number
}

export interface KoTkoLeader {
  name: string
  ko_tko_finishes: number
}

export interface SigStrikesLeader {
  name: string
  sig_str_per_fight: number
  total_fights: number
}

export interface MinFightsLeaderboard<T> {
  min10: T[]
  min20: T[]
  min30: T[]
}

export interface StrikingResponse {
  strike_targets: StrikeTarget[]
  striking_accuracy: MinFightsLeaderboard<StrikingAccuracyFighter>
  ko_tko_leaders: KoTkoLeader[]
  sig_strikes_per_fight: MinFightsLeaderboard<SigStrikesLeader>
}

// ── Grappling ──
export interface TakedownLeader {
  name: string
  total_td_landed: number
  total_td_attempted: number
  td_accuracy: number
}

export interface SubmissionTechnique {
  technique: string
  count: number
}

export interface ControlTimeByClass {
  weight_class: string
  avg_control_seconds: number
  total_fights: number
}

export interface GroundStrikesLeader {
  name: string
  total_ground_landed: number
  total_ground_attempted: number
  accuracy: number
}

export interface SubmissionEfficiencyFighter {
  name: string
  total_sub_attempts: number
  sub_finishes: number
}

export interface GrapplingResponse {
  takedown_accuracy: MinFightsLeaderboard<TakedownLeader>
  submission_techniques: SubmissionTechnique[]
  control_time: ControlTimeByClass[]
  ground_strikes: GroundStrikesLeader[]
  submission_efficiency: {
    fighters: SubmissionEfficiencyFighter[]
    avg_efficiency_ratio: number
  }
}
