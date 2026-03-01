# Fighter Detail Page - Full Stack Spec

## Overview
Fighter를 클릭했을 때 보여줄 상세 정보 페이지.
Backend API 1개 + Frontend 페이지/컴포넌트 구현.

---

## Part 1: Backend API

### 엔드포인트

```
GET /api/fighters/{fighter_id}
```

- 인증 불필요
- Response: `FighterDetailResponseDTO`

---

### Response 구조

```jsonc
{
  // ── Section 1: Profile ──
  "profile": {
    "id": 1,
    "name": "Islam Makhachev",
    "nickname": null,                    // null 허용
    "nationality": "Russia",             // null 허용
    "stance": "Southpaw",               // null 허용
    "belt": true,
    "height_cm": 178.0,                 // null 허용 (데이터 없는 fighter)
    "weight_kg": 70.3,                  // null 허용
    "reach_cm": 178.0,                  // null 허용
    "birthdate": "1991-10-27",          // null 허용
    "age": 34,                          // birthdate null이면 null
    "rankings": { "Lightweight": 0 }    // 랭킹 없으면 빈 {}
  },

  // ── Section 2: Record Summary ──
  "record": {
    "wins": 26,
    "losses": 1,
    "draws": 0,
    "win_rate": 96.3,                   // 경기 0일 때 0.0
    "current_streak": { "type": "win", "count": 14 },  // 경기 없으면 {"type":"none","count":0}
    "finish_breakdown": {               // 승리 없으면 모두 0
      "ko_tko": 4,
      "submission": 12,
      "decision": 10
    }
  },

  // ── Section 3: Career Stats ──
  // fight_history가 빈 배열이면 stats도 null
  "stats": {
    "striking": {
      "sig_str_landed": 1200,
      "sig_str_attempted": 2400,
      "sig_str_accuracy": 50.0,         // attempted=0이면 0.0
      "knockdowns": 5,
      "head_landed": 600,
      "head_attempted": 1200,
      "body_landed": 300,
      "body_attempted": 600,
      "leg_landed": 300,
      "leg_attempted": 600,
      "match_count": 27
    },
    "grappling": {
      "td_landed": 80,
      "td_attempted": 120,
      "td_accuracy": 66.7,             // attempted=0이면 0.0
      "control_time_seconds": 5400,
      "avg_control_time_seconds": 200,
      "submission_attempts": 30,
      "match_count": 27
    }
  },

  // ── Section 4+5: Fight History + Per-Match Stats ──
  // 매치 없으면 빈 배열 []
  "fight_history": [
    {
      "match_id": 123,
      "result": "Win",
      "method": "Submission",           // null 허용
      "round": 3,                       // null 허용
      "time": "2:45",                   // null 허용
      "event_name": "UFC 302",          // null 허용
      "event_date": "2024-06-01",       // null 허용
      "weight_class": "Lightweight",    // null 허용
      "is_main_event": true,
      "opponent": {
        "id": 45,
        "name": "Dustin Poirier",
        "nationality": "United States"  // null 허용
      },
      "stats": {                        // 스탯 데이터 없으면 null
        "basic": {
          "knockdowns": 0,
          "sig_str_landed": 44,
          "sig_str_attempted": 88,
          "total_str_landed": 66,
          "total_str_attempted": 110,
          "td_landed": 5,
          "td_attempted": 8,
          "control_time_seconds": 420,
          "submission_attempts": 3
        },
        "sig_str": {
          "head_landed": 20,
          "head_attempted": 40,
          "body_landed": 12,
          "body_attempted": 24,
          "leg_landed": 12,
          "leg_attempted": 24,
          "clinch_landed": 5,
          "clinch_attempted": 10,
          "ground_landed": 8,
          "ground_attempted": 16
        }
      }
    }
  ]
}
```

---

### Backend 변경 파일 목록 (5개)

#### 1. `src/fighter/dto.py` — DTO 추가

모든 nullable 필드에 `Optional` + `= None` 기본값 적용.

```python
class FighterProfileDTO(BaseModel):
    id: int
    name: str
    nickname: Optional[str] = None
    nationality: Optional[str] = None
    stance: Optional[str] = None
    belt: bool = False
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    reach_cm: Optional[float] = None
    birthdate: Optional[str] = None
    age: Optional[int] = None
    rankings: Dict[str, int] = {}


class FinishBreakdownDTO(BaseModel):
    ko_tko: int = 0
    submission: int = 0
    decision: int = 0


class FighterRecordDTO(BaseModel):
    wins: int = 0
    losses: int = 0
    draws: int = 0
    win_rate: float = 0.0
    current_streak: Dict[str, Any] = {"type": "none", "count": 0}
    finish_breakdown: FinishBreakdownDTO = FinishBreakdownDTO()


class StrikingStatsDTO(BaseModel):
    sig_str_landed: int = 0
    sig_str_attempted: int = 0
    sig_str_accuracy: float = 0.0
    knockdowns: int = 0
    head_landed: int = 0
    head_attempted: int = 0
    body_landed: int = 0
    body_attempted: int = 0
    leg_landed: int = 0
    leg_attempted: int = 0
    match_count: int = 0


class GrapplingStatsDTO(BaseModel):
    td_landed: int = 0
    td_attempted: int = 0
    td_accuracy: float = 0.0
    control_time_seconds: int = 0
    avg_control_time_seconds: int = 0
    submission_attempts: int = 0
    match_count: int = 0


class CareerStatsDTO(BaseModel):
    striking: StrikingStatsDTO = StrikingStatsDTO()
    grappling: GrapplingStatsDTO = GrapplingStatsDTO()


class OpponentDTO(BaseModel):
    id: int
    name: str
    nationality: Optional[str] = None


class PerMatchBasicStatsDTO(BaseModel):
    knockdowns: int = 0
    sig_str_landed: int = 0
    sig_str_attempted: int = 0
    total_str_landed: int = 0
    total_str_attempted: int = 0
    td_landed: int = 0
    td_attempted: int = 0
    control_time_seconds: int = 0
    submission_attempts: int = 0


class PerMatchSigStrDTO(BaseModel):
    head_landed: int = 0
    head_attempted: int = 0
    body_landed: int = 0
    body_attempted: int = 0
    leg_landed: int = 0
    leg_attempted: int = 0
    clinch_landed: int = 0
    clinch_attempted: int = 0
    ground_landed: int = 0
    ground_attempted: int = 0


class PerMatchStatsDTO(BaseModel):
    basic: Optional[PerMatchBasicStatsDTO] = None
    sig_str: Optional[PerMatchSigStrDTO] = None


class FightHistoryItemDTO(BaseModel):
    match_id: int
    result: str
    method: Optional[str] = None
    round: Optional[int] = None
    time: Optional[str] = None
    event_name: Optional[str] = None
    event_date: Optional[date] = None
    weight_class: Optional[str] = None
    is_main_event: bool = False
    opponent: OpponentDTO
    stats: Optional[PerMatchStatsDTO] = None


class FighterDetailResponseDTO(BaseModel):
    profile: FighterProfileDTO
    record: FighterRecordDTO
    stats: Optional[CareerStatsDTO] = None     # 매치 0이면 null
    fight_history: List[FightHistoryItemDTO] = []
```

---

#### 2. `src/fighter/repositories.py` — 쿼리 함수 3개 추가

**쿼리 효율화 전략:**
- fight_history + opponent + event + weight_class를 **단일 쿼리**로 JOIN (N+1 방지)
- per_match_stats는 `IN` 절로 **배치 조회** (2 쿼리로 모든 매치 스탯 한번에)
- finish_breakdown은 `FILTER` 절로 **단일 집계 쿼리**
- 기존 aggregate 함수 2개 재사용 (추가 쿼리 없음)

**총 DB 쿼리 수: 6회** (fighter 1 + ranking 1 + fight_history 1 + finish_breakdown 1 + basic_agg 1 + sig_str_agg 1 + per_match_stats 2 = 8회)

→ 최적화: per_match_stats의 basic/sig_str을 UNION 없이 **2 쿼리**로 `IN (:ids)` 배치 조회.
총 8 쿼리지만 모두 인덱스 기반 단순 조회이므로 충분히 빠름.

##### 2-1. `get_fight_history(session, fighter_id)`

```sql
-- 단일 쿼리로 fight + opponent + event + weight_class 전부 조회
-- N+1 문제 없음: JOIN으로 한 번에 가져옴
SELECT
    fm.id              AS fighter_match_id,
    fm.match_id,
    fm.result,
    m.method,
    m.result_round,
    m.time,
    m.is_main_event,
    m.weight_class_id,
    e.name             AS event_name,
    e.event_date,
    opp_f.id           AS opponent_id,
    opp_f.name         AS opponent_name,
    opp_f.nationality  AS opponent_nationality
FROM fighter_match fm
JOIN match m          ON m.id = fm.match_id
LEFT JOIN event e     ON e.id = m.event_id           -- event 없을 수 있음
LEFT JOIN fighter_match opp
    ON opp.match_id = fm.match_id
    AND opp.fighter_id != fm.fighter_id                -- self-join으로 상대 찾기
LEFT JOIN fighter opp_f ON opp_f.id = opp.fighter_id  -- opponent 정보 없을 수 있음
WHERE fm.fighter_id = :fighter_id
ORDER BY e.event_date DESC NULLS LAST
```

**변경점 (효율화):**
- `JOIN` → `LEFT JOIN`으로 변경: event/opponent 데이터 없는 매치도 누락 없이 반환
- opponent가 없는 매치(취소/exhibition)도 `opponent=null`로 반환 가능

##### 2-2. `get_per_match_stats(session, fighter_match_ids)`

```sql
-- 쿼리 1: basic stats 배치 조회
SELECT fighter_match_id, knockdowns, sig_str_landed, sig_str_attempted,
       total_str_landed, total_str_attempted, td_landed, td_attempted,
       control_time_seconds, submission_attempts
FROM basic_match_stat
WHERE fighter_match_id = ANY(:ids) AND round = 0

-- 쿼리 2: sig_str stats 배치 조회
SELECT fighter_match_id, head_strikes_landed, head_strikes_attempts,
       body_strikes_landed, body_strikes_attempts,
       leg_strikes_landed, leg_strikes_attempts,
       clinch_strikes_landed, clinch_strikes_attempts,
       ground_strikes_landed, ground_strikes_attempts
FROM sig_str_match_stat
WHERE fighter_match_id = ANY(:ids) AND round = 0
```

**효율화:**
- 매치별 개별 쿼리 대신 `IN` 절로 한 번에 조회
- 30경기 fighter → 개별 60쿼리가 2쿼리로 감소

##### 2-3. `get_finish_breakdown(session, fighter_id)`

```sql
-- 단일 집계 쿼리 (FILTER 절 사용)
SELECT
    COUNT(*) FILTER (WHERE m.method ILIKE '%ko%' OR m.method ILIKE '%tko%') AS ko_tko,
    COUNT(*) FILTER (WHERE m.method ILIKE '%sub%')                          AS submission,
    COUNT(*) FILTER (WHERE m.method ILIKE '%dec%')                          AS decision
FROM fighter_match fm
JOIN match m ON m.id = fm.match_id
WHERE fm.fighter_id = :fighter_id AND fm.result = 'Win'
```

**효율화:**
- 3개의 COUNT를 한 번의 쿼리로 처리 (FILTER 절)
- `LIKE` → `ILIKE`로 대소문자 무관 매칭

---

#### 3. `src/fighter/services.py` — 서비스 함수 추가

```python
async def get_fighter_detail(session, fighter_id) -> FighterDetailResponseDTO:
    # 1. fighter 기본 정보 (기존 함수 재사용)
    fighter = await fighter_repo.get_fighter_by_id(session, fighter_id)
    if not fighter:
        raise FighterNotFoundError(fighter_id)

    # 2. rankings (기존 함수 재사용)
    rankings = await fighter_repo.get_ranking_by_fighter_id(session, fighter_id)

    # 3. fight history (신규 - 단일 쿼리)
    fight_history_rows = await fighter_repo.get_fight_history(session, fighter_id)

    # 4. finish breakdown (신규 - 단일 쿼리)
    finish = await fighter_repo.get_finish_breakdown(session, fighter_id)

    # 5. career aggregate stats (기존 함수 재사용 - 2 쿼리)
    basic_agg = await match_repo.get_fighter_basic_stats_aggregate(session, fighter_id)
    sig_str_agg = await match_repo.get_fighter_sig_str_stats_aggregate(session, fighter_id)

    # 6. per-match stats (신규 - 2 쿼리 배치)
    fm_ids = [row["fighter_match_id"] for row in fight_history_rows]
    per_match_map = await fighter_repo.get_per_match_stats(session, fm_ids) if fm_ids else {}

    # 조합 → FighterDetailResponseDTO
    ...
```

**Null 안전 처리:**
- `fighter.birthdate` 파싱 실패 시 `age = None`
- `basic_agg`/`sig_str_agg`가 `match_count=0`이면 `stats = None`
- `fight_history_rows` 빈 리스트면 `fight_history = []`, `current_streak = {"type":"none","count":0}`
- opponent가 없는 row는 필터링하여 제외

---

#### 4. `src/api/fighter/routes.py` — 신규 라우터

```python
router = APIRouter(prefix="/api/fighters", tags=["Fighter"])

@router.get("/{fighter_id}", response_model=FighterDetailResponseDTO)
async def get_fighter_detail(fighter_id: int, db = Depends(get_async_db)):
    ...
```

---

#### 5. `src/api/main.py` — 라우터 등록

```python
from api.fighter.routes import router as fighter_router
api_router.include_router(fighter_router)
```

---

## Part 2: Frontend

### 라우팅 구조

```
/fighters/[id]    → Fighter Detail 페이지
```

Dashboard 랭킹 테이블, 리더보드 등에서 fighter 이름 클릭 시 이 페이지로 이동.

---

### 변경 파일 목록 (8개)

#### 1. `frontend/src/types/fighter.ts` — 타입 정의 (신규)

Backend DTO와 1:1 매핑되는 TypeScript 인터페이스.

```typescript
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
  rankings: Record<string, number>       // {} if no rankings
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
  control_time_seconds: number
  avg_control_time_seconds: number
  submission_attempts: number
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
```

---

#### 2. `frontend/src/services/fighterApi.ts` — API 서비스 (신규)

기존 `dashboardApi.ts` 패턴을 그대로 따름.

```typescript
import type { FighterDetailResponse } from '@/types/fighter'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002'

async function fighterFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`)
  if (!res.ok) throw new Error(`Fighter API error: ${res.status}`)
  return res.json()
}

export const fighterApi = {
  getDetail: (fighterId: number) =>
    fighterFetch<FighterDetailResponse>(`/api/fighters/${fighterId}`),
}
```

---

#### 3. `frontend/src/hooks/useFighterDetail.ts` — 데이터 페칭 훅 (신규)

기존 `useDashboard` 패턴(state + fetch + cache) 따름.

```typescript
export function useFighterDetail(fighterId: number) {
  const [data, setData] = useState<FighterDetailResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    fighterApi.getDetail(fighterId)
      .then(res => { if (!cancelled) setData(res) })
      .catch(err => { if (!cancelled) setError(err.message) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [fighterId])

  return { data, loading, error, retry: () => { ... } }
}
```

---

#### 4. `frontend/src/app/fighters/[id]/page.tsx` — 페이지 (신규)

```typescript
// Server component (App Router)
import { Suspense } from 'react'
import { FighterDetailClient } from '@/components/fighter/FighterDetailPage'
import { FighterDetailSkeleton } from '@/components/fighter/FighterDetailSkeleton'

export default function FighterPage({ params }: { params: { id: string } }) {
  return (
    <Suspense fallback={<FighterDetailSkeleton />}>
      <FighterDetailClient fighterId={Number(params.id)} />
    </Suspense>
  )
}
```

---

#### 5. `frontend/src/components/fighter/FighterDetailPage.tsx` — 메인 컴포넌트 (신규)

useFighterDetail 훅으로 데이터 fetch 후 각 섹션 컴포넌트 렌더링.

```
┌─────────────────────────────────────────────┐
│  FighterDetailPage                          │
│  ┌────────────────────────────────────────┐ │
│  │ ProfileHeader                         │ │
│  │ 이름 / 닉네임 / 국적 / 벨트 / 랭킹    │ │
│  │ height / weight / reach / stance / age │ │
│  └────────────────────────────────────────┘ │
│  ┌──────────────┐ ┌───────────────────────┐ │
│  │ RecordCard   │ │ FinishBreakdownChart  │ │
│  │ W-L-D        │ │ KO/SUB/DEC 도넛 차트  │ │
│  │ 승률 / streak │ │ (Recharts PieChart)   │ │
│  └──────────────┘ └───────────────────────┘ │
│  ┌──────────────────┐ ┌───────────────────┐ │
│  │ StrikingStats    │ │ GrapplingStats    │ │
│  │ 유효타 / KD      │ │ TD / 컨트롤타임   │ │
│  │ head/body/leg    │ │ 서브미션          │ │
│  └──────────────────┘ └───────────────────┘ │
│  ┌────────────────────────────────────────┐ │
│  │ FightHistory (테이블)                  │ │
│  │ 결과│상대│이벤트│방법│라운드│날짜       │ │
│  │  ▸ 클릭 시 PerMatchStats 펼침         │ │
│  │    ┌──────────────────────────────┐    │ │
│  │    │ 양 선수 스탯 바 비교 (basic) │    │ │
│  │    │ sig_str 상세 표              │    │ │
│  │    └──────────────────────────────┘    │ │
│  └────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

**레이아웃 규칙 (기존 Dashboard와 동일):**
- `mx-auto max-w-7xl px-4 py-6`
- 카드: `rounded-xl border border-white/[0.06] bg-white/[0.03] p-5`
- 호버: `hover:scale-[1.01] hover:border-white/[0.12] hover:bg-white/[0.05]`
- 그리드: `grid grid-cols-1 gap-4 lg:grid-cols-2`
- 스켈레톤: `<Skeleton className="h-XX bg-white/[0.06]" />`
- 에러: `AlertCircle` 아이콘 + 재시도 버튼

---

#### 6. `frontend/src/components/fighter/` — 섹션 컴포넌트 (신규, 5개)

##### `ProfileHeader.tsx`
- 이름 (text-2xl font-bold), 닉네임 (text-zinc-500)
- 국적 텍스트, 벨트 뱃지 (`bg-yellow-500/20 text-yellow-400`)
- 체격 정보: height / weight / reach → 가로 배치 (`flex gap-6`)
- stance, age
- 랭킹 뱃지: `{weight_class}: #{rank}` 또는 `Champion` (rank=0)
- **null 처리**: 값 없으면 `-` 또는 해당 항목 숨김

##### `RecordCard.tsx`
- W-L-D 큰 숫자 표시 (Win=green, Loss=red, Draw=zinc)
- 승률 프로그레스바
- 연승/연패 streak 뱃지
- **null 처리**: 경기 0이면 "No fights recorded" 표시

##### `FinishBreakdownChart.tsx`
- Recharts `PieChart` (도넛): KO/TKO, Submission, Decision
- 색상: KO=`#ef4444`, SUB=`#a855f7`, DEC=`#06b6d4`
- **null 처리**: 승리 0이면 "No wins to display" 표시

##### `CareerStatsCard.tsx`
- Striking / Grappling 2칸 그리드
- 각 스탯은 `label: value` 형태, 적중률은 프로그레스바
- head/body/leg 비율 → 수평 스택 바
- **null 처리**: `stats === null`이면 "No stats available" 표시

##### `FightHistoryTable.tsx`
- 테이블 or 리스트 (모바일 반응형)
- 각 row: 결과 뱃지(Win=green/Loss=red) | 상대 (클릭 가능 링크) | 이벤트 | 방법 | 라운드 | 날짜
- row 클릭 → accordion 펼침: `PerMatchStats` 표시
  - basic stats: 수평 바 차트 (landed / attempted)
  - sig_str stats: 부위별 표
- opponent 클릭 → `/fighters/{opponent.id}`로 이동
- **null 처리**:
  - `fight_history` 빈 배열 → "No fight records" 표시
  - `stats === null` → "Stats not available" 표시
  - `method/round/time null` → `-` 표시

---

#### 7. `frontend/src/components/fighter/FighterDetailSkeleton.tsx` — 로딩 스켈레톤 (신규)

기존 Dashboard 스켈레톤 패턴 따름.

```typescript
export function FighterDetailSkeleton() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-6 space-y-4">
      {/* Profile header skeleton */}
      <Skeleton className="h-32 bg-white/[0.06]" />
      {/* Record + Chart row */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Skeleton className="h-40 bg-white/[0.06]" />
        <Skeleton className="h-40 bg-white/[0.06]" />
      </div>
      {/* Stats row */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Skeleton className="h-48 bg-white/[0.06]" />
        <Skeleton className="h-48 bg-white/[0.06]" />
      </div>
      {/* Fight history skeleton */}
      <Skeleton className="h-64 bg-white/[0.06]" />
    </div>
  )
}
```

---

#### 8. `frontend/src/components/layout/GlobalNav.tsx` — 네비게이션 수정 불필요

Fighter Detail은 독립 페이지. Dashboard나 랭킹에서 이름 클릭 시 이동.
상단 네비게이션에 별도 탭 추가는 불필요.

대신 **기존 Dashboard 랭킹 테이블에서 fighter 이름에 `<Link>`를 추가**하는 것은 추후 작업.

---

### Frontend 네이밍 & 디렉토리

```
frontend/src/
├── app/fighters/[id]/page.tsx              # 라우트 페이지
├── components/fighter/
│   ├── FighterDetailPage.tsx               # 메인 orchestrator
│   ├── FighterDetailSkeleton.tsx           # 로딩 상태
│   ├── ProfileHeader.tsx                   # 프로필 헤더
│   ├── RecordCard.tsx                      # 전적 카드
│   ├── FinishBreakdownChart.tsx            # 피니시 도넛 차트
│   ├── CareerStatsCard.tsx                 # 커리어 통계
│   └── FightHistoryTable.tsx               # 경기 이력 + 확장
├── hooks/useFighterDetail.ts               # 데이터 페칭 훅
├── services/fighterApi.ts                  # API 클라이언트
└── types/fighter.ts                        # 타입 정의
```

---

## 구현 순서

| Step | 작업 | 파일 |
|------|------|------|
| **Backend** | | |
| 1 | DTO 정의 | `src/fighter/dto.py` |
| 2 | Repository 쿼리 3개 | `src/fighter/repositories.py` |
| 3 | Service 조합 로직 | `src/fighter/services.py` |
| 4 | Router 생성 | `src/api/fighter/routes.py` (신규) |
| 5 | Router 등록 | `src/api/main.py` |
| 6 | Backend 테스트 | `cd src && uv run python -m pytest tests/ -v` |
| **Frontend** | | |
| 7 | 타입 정의 | `frontend/src/types/fighter.ts` |
| 8 | API 서비스 | `frontend/src/services/fighterApi.ts` |
| 9 | 데이터 훅 | `frontend/src/hooks/useFighterDetail.ts` |
| 10 | 페이지 라우트 | `frontend/src/app/fighters/[id]/page.tsx` |
| 11 | 메인 컴포넌트 | `frontend/src/components/fighter/FighterDetailPage.tsx` |
| 12 | 섹션 컴포넌트 5개 | `frontend/src/components/fighter/*.tsx` |
| 13 | 스켈레톤 | `frontend/src/components/fighter/FighterDetailSkeleton.tsx` |
| 14 | Frontend 빌드 확인 | `cd frontend && npm run build` |

---

## 주의사항

- `round = 0` 행은 매치 전체 합산 스탯. 개별 라운드 스탯(round=1,2,...)은 이번 스코프에서 제외.
- `birthdate`가 문자열로 저장되어 있으므로 파싱 시 예외 처리 필요.
- 기존 `get_fighter_basic_stats_aggregate`, `get_fighter_sig_str_stats_aggregate` 재사용하여 쿼리 중복 방지.
- Frontend에서 모든 nullable 필드에 대해 fallback UI 필요 (`null` → `-` 또는 숨김).
- opponent 클릭으로 다른 fighter detail 페이지로 이동 가능하게 구현.
