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
  fighter_id: number
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

export interface EventMapLocation {
  location: string
  latitude: number
  longitude: number
  event_count: number
  last_event_date: string | null
  last_event_name: string | null
}

export interface NationalityDistribution {
  nationality: string
  fighter_count: number
}

export interface HomeResponse {
  summary: DashboardSummary
  recent_events: RecentEvent[]
  upcoming_events: UpcomingEvent[]
  rankings: WeightClassRanking[]
  event_map: EventMapLocation[]
  nationality_distribution: NationalityDistribution[]
}

// ── Fighter Search ──
export interface FighterSearchItem {
  fighter: {
    id: number
    name: string
    nickname: string | null
    wins: number
    losses: number
    draws: number
  }
  rankings: Record<string, number>
}

// ── Event List (paginated) ──
export interface EventListItem {
  id: number
  name: string
  location: string | null
  event_date: string | null
}

export interface EventListResponse {
  events: EventListItem[]
  total: number
  page: number
  limit: number
  year: number | null
  month: number | null
}

// ── Event Search ──
export interface EventSearchResult {
  event: EventListItem
  match_type: string
  relevance: number
}

export interface EventSearchResponse {
  results: EventSearchResult[]
  total: number
  query: string
  search_type: string
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
  fighter_id: number
  name: string
  wins: number
  losses: number
  draws: number
  ko_tko_wins: number
  sub_wins: number
  dec_wins: number
}

export interface WinStreakFighter {
  fighter_id: number
  name: string
  win_streak: number
  wins: number
  losses: number
  draws: number
}

export interface LoseStreakFighter {
  fighter_id: number
  name: string
  lose_streak: number
  wins: number
  losses: number
  draws: number
}

export interface FightDurationRound {
  result_round: number
  fight_count: number
  percentage: number
  ko_tko: number
  submission: number
  decision_other: number
}

export interface FinishRateTrend {
  year: number
  total_fights: number
  ko_tko_rate: number
  sub_rate: number
  dec_rate: number
}

export interface OverviewResponse {
  finish_methods: FinishMethod[]
  weight_class_activity: WeightClassActivity[]
  events_timeline: EventTimeline[]
  leaderboard: {
    wins: LeaderboardFighter[]
    win_streak: WinStreakFighter[]
    lose_streak: LoseStreakFighter[]
  }
  fight_duration: {
    rounds: FightDurationRound[]
    avg_round: number
    avg_time_seconds: number | null
  }
  finish_rate_trend: FinishRateTrend[]
}

// ── Striking ──
export interface StrikeTarget {
  target: string
  landed: number
}

export interface StrikingAccuracyFighter {
  fighter_id: number
  name: string
  total_sig_landed: number
  total_sig_attempted: number
  accuracy: number
}

export interface KoTkoLeader {
  fighter_id: number
  name: string
  ko_tko_finishes: number
}

export interface SigStrikesLeader {
  fighter_id: number
  name: string
  sig_str_per_fight: number
  total_fights: number
}

export interface MinFightsLeaderboard<T> {
  min10: T[]
  min15: T[]
  min20: T[]
}

export interface KnockdownLeader {
  fighter_id: number
  name: string
  total_knockdowns: number
  total_fights: number
  kd_per_fight: number
}

export interface SigStrikesByWeightClass {
  weight_class: string
  avg_sig_str_per_fight: number
  total_fights: number
}

export interface StrikeExchange {
  fighter_id: number
  name: string
  total_fights: number
  sig_landed_per_fight: number
  sig_absorbed_per_fight: number
  differential_per_fight: number
}

export interface StanceWinrate {
  winner_stance: string
  loser_stance: string
  wins: number
  win_rate: number
}

export interface StrikingResponse {
  strike_targets: StrikeTarget[]
  striking_accuracy: MinFightsLeaderboard<StrikingAccuracyFighter>
  ko_tko_leaders: KoTkoLeader[]
  sig_strikes_per_fight: MinFightsLeaderboard<SigStrikesLeader>
  knockdown_leaders: KnockdownLeader[]
  sig_strikes_by_weight_class: SigStrikesByWeightClass[]
  strike_exchange: MinFightsLeaderboard<StrikeExchange>
  stance_winrate: StanceWinrate[]
}

// ── Grappling ──
export interface TakedownLeader {
  fighter_id: number
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
  fighter_id: number
  name: string
  total_ground_landed: number
  total_ground_attempted: number
  accuracy: number
}

export interface SubmissionEfficiencyFighter {
  fighter_id: number
  name: string
  total_sub_attempts: number
  sub_finishes: number
}

export interface TdAttemptsLeader {
  fighter_id: number
  name: string
  td_attempts_per_fight: number
  total_td_attempted: number
  total_td_landed: number
  total_fights: number
}

export interface TdAttemptsLeaderboard extends MinFightsLeaderboard<TdAttemptsLeader> {
  avg_td_attempts: number
}

export interface TdSubCorrelationFighter {
  fighter_id: number
  name: string
  total_td_landed: number
  sub_finishes: number
  total_fights: number
  td_per_fight: number
  sub_per_fight: number
}

export interface TdSubQuadrant {
  fighters: TdSubCorrelationFighter[]
  count: number
}

export interface TdSubCorrelation {
  quadrants: Record<string, TdSubQuadrant>
  avg_td: number
  avg_sub: number
}

export interface TdDefenseLeader {
  fighter_id: number
  name: string
  opp_td_attempted: number
  opp_td_landed: number
  td_defended: number
  td_defense_rate: number
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
  td_attempts_leaders: TdAttemptsLeaderboard
  td_sub_correlation: TdSubCorrelation
  td_defense_leaders: MinFightsLeaderboard<TdDefenseLeader>
}
