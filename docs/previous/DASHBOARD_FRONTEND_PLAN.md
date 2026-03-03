# Dashboard 프론트엔드 구현 계획

---

## 1. 라우트 구조 변경

### Before

```
/              → 랜딩 페이지 (Hero + CTA)
/chat          → AI 채팅 (AuthGuard)
/profile       → 프로필
/settings      → 어드민
```

### After

```
/              → Dashboard (인증 불필요 — 공개 데이터)
/chat          → AI 채팅 (AuthGuard 유지)
/profile       → 프로필 (변경 없음)
/settings      → 어드민 (변경 없음)
```

### 글로벌 네비게이션 바

현재 각 페이지가 자체 nav를 가지고 있음 (`page.tsx` 인라인, `ChatContainer` 내장 등).
→ **공통 `GlobalNav` 컴포넌트**를 만들어 `layout.tsx`에 배치.

```
┌──────────────────────────────────────────────────────┐
│  [MS] MMA Savant     [Dashboard] [AI Chat]   [Avatar]│
└──────────────────────────────────────────────────────┘
```

- `Dashboard` / `AI Chat`: 현재 페이지에 따라 active 스타일
- `Avatar`: 기존 `UserProfile` 컴포넌트 재사용 (로그인 시), 미로그인 시 `Sign in` 버튼
- AI Chat은 인증 필요하므로 미로그인 시 클릭하면 `/auth/signin`으로 리다이렉트

### 렌더링 전략

| 탭 | 렌더링 방식 | 이유 |
|---|---|---|
| Home | **SSR + ISR** | 필터 없음, 공개 데이터, 변경 빈도 낮음 |
| Overview | CSR | weightClassId 필터에 따라 동적 |
| Striking | CSR | weightClassId 필터에 따라 동적 |
| Grappling | CSR | weightClassId 필터에 따라 동적 |

- `app/page.tsx`를 Server Component로 만들어 Home 데이터를 서버에서 fetch
- `next: { revalidate: 300 }` (5분) 주기로 ISR 재생성
- 서버 사이드 fetch용 환경 변수: `BACKEND_URL` (NEXT_PUBLIC 아님)

```typescript
// app/page.tsx (Server Component)
export const revalidate = 300

async function getHomeData() {
  const res = await fetch(`${process.env.BACKEND_URL}/api/dashboard/home`, {
    next: { revalidate: 300 },
  })
  if (!res.ok) throw new Error('Failed to fetch home data')
  return res.json()
}

export default async function DashboardPage() {
  const homeData = await getHomeData()
  return (
    <Suspense fallback={<DashboardSkeleton />}>
      <DashboardPageClient initialHomeData={homeData} />
    </Suspense>
  )
}
```

#### 환경 변수 추가

```env
# frontend/.env.local
BACKEND_URL=http://localhost:8002  # 서버 사이드 전용 (NEXT_PUBLIC 아님)
# Docker 배포 시: BACKEND_URL=http://backend:8002
```

### URL 상태 관리

`activeTab`과 `weightClassId`를 URL 쿼리 파라미터로 관리한다.

- 링크 공유 가능 (예: `/?tab=striking&weight_class=5`)
- 브라우저 뒤로가기/앞으로가기 지원
- 새로고침 시 상태 유지
- **탭 전환**은 `router.replace()` (히스토리 오염 방지)
- **체급 필터 변경**은 `router.push()` (의미 있는 상태 변경)

```typescript
// components/dashboard/DashboardPage.tsx
'use client'
import { useSearchParams, useRouter, usePathname } from 'next/navigation'

export function DashboardPageClient({ initialHomeData }) {
  const searchParams = useSearchParams()
  const router = useRouter()
  const pathname = usePathname()

  const activeTab = searchParams.get('tab') || 'home'
  const weightClassId = searchParams.get('weight_class')
    ? Number(searchParams.get('weight_class'))
    : undefined

  const setTab = (tab: string) => {
    const params = new URLSearchParams(searchParams.toString())
    if (tab === 'home') params.delete('tab')
    else params.set('tab', tab)
    router.replace(`${pathname}?${params}`, { scroll: false })
  }

  const setWeightClass = (id?: number) => {
    const params = new URLSearchParams(searchParams.toString())
    if (id === undefined) params.delete('weight_class')
    else params.set('weight_class', id.toString())
    router.push(`${pathname}?${params}`, { scroll: false })
  }
}
```

---

## 2. 파일 구조

### 신규 파일

```
frontend/src/
├── app/
│   ├── page.tsx                          # Dashboard (Server Component — ISR)
│   └── layout.tsx                        # GlobalNav 추가
│
├── components/
│   ├── layout/
│   │   └── GlobalNav.tsx                 # 글로벌 네비게이션 바
│   │
│   ├── dashboard/
│   │   ├── DashboardPage.tsx             # 메인 컨테이너 (탭 관리 + 필터)
│   │   ├── WeightClassFilter.tsx         # 체급 필터 드롭다운
│   │   ├── StatCard.tsx                  # 요약 카드 (숫자 + 라벨)
│   │   ├── ChartCard.tsx                 # 차트 감싸는 카드 (제목 + 설명 + 차트영역)
│   │   ├── ExpandableList.tsx            # TOP 5 → 10 더보기 래퍼
│   │   ├── PillTabs.tsx                  # 탭 전환 (pill 스타일)
│   │   │
│   │   ├── home/
│   │   │   ├── HomeTab.tsx               # Home 탭 레이아웃
│   │   │   ├── RecentEvents.tsx          # 최근 이벤트 카드 리스트
│   │   │   ├── UpcomingEvents.tsx        # 향후 이벤트 카드 리스트
│   │   │   └── RankingsTable.tsx         # 체급별 랭킹 테이블
│   │   │
│   │   ├── overview/
│   │   │   ├── OverviewTab.tsx           # Overview 탭 레이아웃
│   │   │   ├── FinishMethodsChart.tsx    # 2-1 도넛 차트
│   │   │   ├── WeightClassActivityChart.tsx # 2-2 ComposedChart (바+도트+탭)
│   │   │   ├── EventsTimelineChart.tsx   # 2-3 라인/에어리어 차트
│   │   │   ├── LeaderboardChart.tsx      # 2-4 바 차트 (최다승/최고승률 탭)
│   │   │   └── FightDurationChart.tsx    # 2-5 바 차트 + ReferenceLine
│   │   │
│   │   ├── striking/
│   │   │   ├── StrikingTab.tsx           # Striking 탭 레이아웃
│   │   │   ├── StrikeTargetsChart.tsx    # 3-1 RadarChart
│   │   │   ├── StrikingAccuracyChart.tsx # 3-2 Bullet Chart (attempted/landed overlay)
│   │   │   ├── KoTkoLeadersChart.tsx     # 3-3 스택 바
│   │   │   └── SigStrikesChart.tsx       # 3-4 Lollipop Chart (stem + dot)
│   │   │
│   │   └── grappling/
│   │       ├── GrapplingTab.tsx          # Grappling 탭 레이아웃
│   │       ├── TakedownChart.tsx         # 4-1 Bullet Chart (attempted/landed overlay)
│   │       ├── SubmissionTechChart.tsx   # 4-2 가로 바
│   │       ├── ControlTimeChart.tsx      # 4-3 바 차트
│   │       ├── GroundStrikesChart.tsx    # 4-4 Scatter Chart (버블, 3축)
│   │       └── SubmissionEfficiencyChart.tsx # 4-5 ScatterChart + ReferenceLine
│   │
│   └── ui/
│       ├── tabs.tsx                      # shadcn/ui Tabs (신규 추가)
│       └── select.tsx                    # shadcn/ui Select (신규 추가)
│
├── services/
│   └── dashboardApi.ts                   # 대시보드 API 클라이언트
│
├── types/
│   └── dashboard.ts                      # 대시보드 응답 타입
│
└── hooks/
    └── useDashboard.ts                   # 대시보드 데이터 페칭 훅
```

### 수정 파일

| 파일 | 변경 내용 |
|------|----------|
| `app/page.tsx` | 랜딩 페이지 → Server Component (ISR, `DashboardPageClient`에 initialHomeData 전달) |
| `app/layout.tsx` | `GlobalNav` 추가 |
| `components/auth/UserProfile.tsx` | GlobalNav에서 재사용할 수 있도록 스타일 props 추가 |

### 삭제 없음

기존 `page.tsx`의 랜딩 페이지 코드는 덮어쓰기 (별도 보존 불필요).

---

## 3. 타입 정의 (`types/dashboard.ts`)

```typescript
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
  ranking: number        // 0 = 챔피언
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
  ko_count: number
  tko_count: number
  sub_count: number
  finish_rate: number
  ko_rate: number
  tko_rate: number
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
  ko_finishes: number
  tko_finishes: number
  total_ko_tko: number
}

export interface SigStrikesLeader {
  name: string
  sig_str_per_fight: number
  total_fights: number
}

export interface StrikingResponse {
  strike_targets: StrikeTarget[]
  striking_accuracy: StrikingAccuracyFighter[]
  ko_tko_leaders: KoTkoLeader[]
  sig_strikes_per_fight: SigStrikesLeader[]
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
  takedown_accuracy: TakedownLeader[]
  submission_techniques: SubmissionTechnique[]
  control_time: ControlTimeByClass[]
  ground_strikes: GroundStrikesLeader[]
  submission_efficiency: {
    fighters: SubmissionEfficiencyFighter[]
    avg_efficiency_ratio: number
  }
}
```

---

## 4. API 서비스 (`services/dashboardApi.ts`)

대시보드는 공개 데이터이므로 인증이 필요 없다. 기존 `lib/api.ts`의 `api.get()`은 NextAuth 세션 → JWT 교환 로직이 포함되어 있으므로, 대시보드 전용 fetch 함수를 별도로 사용한다.

> Home 탭 데이터는 ISR Server Component에서 `BACKEND_URL`로 직접 fetch하므로 이 서비스에 포함하지 않는다.

```typescript
import type { OverviewResponse, StrikingResponse, GrapplingResponse } from '@/types/dashboard'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002'

async function dashboardFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`)
  if (!res.ok) throw new Error(`Dashboard API error: ${res.status}`)
  return res.json()
}

function withWeightClass(path: string, weightClassId?: number): string {
  return weightClassId ? `${path}?weight_class_id=${weightClassId}` : path
}

export const dashboardApi = {
  getOverview: (weightClassId?: number) =>
    dashboardFetch<OverviewResponse>(withWeightClass('/api/dashboard/overview', weightClassId)),

  getStriking: (weightClassId?: number) =>
    dashboardFetch<StrikingResponse>(withWeightClass('/api/dashboard/striking', weightClassId)),

  getGrappling: (weightClassId?: number) =>
    dashboardFetch<GrapplingResponse>(withWeightClass('/api/dashboard/grappling', weightClassId)),
}
```

---

## 5. 데이터 페칭 훅 (`hooks/useDashboard.ts`)

각 탭별 데이터를 독립적으로 관리. 탭 전환 시 이미 로드된 데이터는 캐싱.

> `activeTab`과 `weightClassId`는 URL searchParams로 관리하므로 훅 상태에 포함하지 않음.

```typescript
// 상태 구조
interface DashboardState {
  overview: { data: OverviewResponse | null; loading: boolean; error: string | null }
  striking: { data: StrikingResponse | null; loading: boolean; error: string | null }
  grappling: { data: GrapplingResponse | null; loading: boolean; error: string | null }
}
```

- **Home 탭**: ISR로 서버에서 데이터 제공 (`initialHomeData` prop), 클라이언트 상태 관리 불필요
- **Overview/Striking/Grappling**: `weightClassId` 변경 시 재요청
- 탭 전환 시 해당 탭 데이터가 null이면 자동 fetch, 이미 있으면 캐시 사용
- `weightClassId` 변경 시 Overview/Striking/Grappling 캐시 무효화

---

## 6. 컴포넌트 설계

### 6-1. 공통 컴포넌트

#### `GlobalNav`
```
┌──────────────────────────────────────────────────────┐
│  [MS] MMA Savant     [Dashboard] [AI Chat]   [Avatar]│
└──────────────────────────────────────────────────────┘
```
- `usePathname()`으로 현재 경로 감지 → active 스타일
- 다크 테마 (bg-zinc-900 계열, 기존 디자인 톤 유지)
- sticky top, z-50

#### `DashboardPage`
```
┌──────────────────────────────────────────────────────┐
│  [Home] [Overview] [Striking] [Grappling]            │
│                                    [체급 필터 ▼]     │
├──────────────────────────────────────────────────────┤
│                                                      │
│  (활성 탭의 콘텐츠)                                   │
│                                                      │
└──────────────────────────────────────────────────────┘
```
- 대시보드 탭: shadcn/ui `Tabs` 또는 커스텀 pill 탭
- 체급 필터: shadcn/ui `Select` — Home 탭에서는 숨김
- 탭/필터 상태: URL searchParams로 관리 (섹션 1 "URL 상태 관리" 참조)
- `useDashboard` 훅으로 데이터 페칭

#### `ChartCard`
```typescript
interface ChartCardProps {
  title: string
  description?: string
  className?: string          // 그리드 span 제어
  headerRight?: ReactNode     // 탭이나 필터 슬롯
  loading?: boolean           // true일 때 Skeleton 렌더링
  error?: string | null       // 값 있을 때 ErrorFallback 렌더링
  children: ReactNode         // 차트 렌더링 영역
}
```
- 프로토타입의 `b-card` 스타일 재현
- 다크 배경, subtle border, hover 효과
- `loading=true`: 차트 영역에 shadcn/ui `Skeleton` 렌더링
- `error` 값 존재: "데이터를 불러올 수 없습니다" + 재시도 버튼

#### `StatCard`
```typescript
interface StatCardProps {
  label: string
  value: number | string
  icon?: LucideIcon
}
```

#### `ExpandableList`
- 기본 5건 표시, "더보기" 버튼 클릭 시 10건으로 확장
- 차트 데이터는 항상 10건을 받아두고 프론트에서 slice

#### `PillTabs`
```typescript
interface PillTabsProps {
  tabs: { key: string; label: string }[]
  activeKey: string
  onChange: (key: string) => void
}
```

### 6-2. 탭별 레이아웃 (Bento Grid)

각 탭 컴포넌트는 CSS Grid로 차트 카드를 배치. 프로토타입의 레이아웃을 따름.

#### Home 탭
```
┌────────┬────────┬────────┐
│Fighters│Matches │Events  │  ← StatCard × 3
├────────┴────────┴────────┤
│  최근 이벤트  │ 향후 이벤트  │  ← 카드 리스트 × 2
├──────────────┴───────────┤
│     체급별 챔피언 & 랭킹    │  ← 테이블 (드롭다운 체급 전환)
└──────────────────────────┘
```

#### Overview 탭
```
┌──────────────┬───────────┐
│ 피니시 분포    │ 이벤트 추이 │  ← 도넛 + 라인
├──────────┬───┴───────────┤
│ 체급별 활동 (3col)│ 종료라운드│  ← ComposedChart + 바
├──────────┴───────────────┤
│     리더보드 (full width)   │  ← 바 차트 + 탭
└──────────────────────────┘
```

#### Striking 탭
```
┌──────────────┬───────────┐
│ 타격 부위 레이더│ 정확도 TOP │
├──────────────┼───────────┤
│ KO/TKO TOP   │ 유효타격 TOP│
└──────────────┴───────────┘
```

#### Grappling 탭
```
┌──────────────┬───────────┐
│ 테이크다운 TOP │ 서브미션기술│
├────────┬─────┴─┬─────────┤
│컨트롤타임│그라운드│서브미션효율│
└────────┴───────┴─────────┘
```

---

## 7. Recharts 차트 매핑

| 통계 항목 | Recharts 컴포넌트 | 특이사항 |
|----------|------------------|---------|
| 2-1 피니시 분포 | `PieChart` + `Pie` + `Cell` | 도넛 (innerRadius) |
| 2-2 체급별 활동 | `ComposedChart` + `Bar` + `Scatter` | 이중 YAxis, PillTabs로 비율 전환 |
| 2-3 이벤트 추이 | `AreaChart` + `Area` | fill gradient |
| 2-4 리더보드 | `BarChart` + `Bar` | 탭 전환 (최다승/최고승률) |
| 2-5 종료 라운드 | `BarChart` + `Bar` + `ReferenceLine` | 평균 라운드 점선 |
| 3-1 타격 부위 | `RadarChart` + `Radar` + `PolarGrid` | 5축 |
| 3-2 타격 정확도 | `BarChart` + `Bar` × 2 (overlay) | Bullet Chart — `barGap={-26}`, attempted(반투명) + landed(채색) |
| 3-3 KO/TKO TOP | `BarChart` + `Bar` × 2 (stacked) | `stackId="ko"` |
| 3-4 유효타격 | `ComposedChart` + `Bar` + `Scatter` | Lollipop — stem(barSize=3) + dot(크기=경기수), `ReferenceLine`(평균) |
| 4-1 테이크다운 | `BarChart` + `Bar` × 2 (overlay) | Bullet Chart — 3-2와 동일 패턴, green 계열 |
| 4-2 서브미션 기술 | `BarChart` + `Bar` (horizontal) | `layout="vertical"` |
| 4-3 컨트롤 타임 | `BarChart` + `Bar` | Y축 mm:ss formatter |
| 4-4 그라운드 | `ScatterChart` + `ZAxis` + `ReferenceLine` | Bubble — X:시도, Y:적중, Z:정확도(버블크기), 대각선 기준선 |
| 4-5 서브미션 효율 | `ScatterChart` + `Scatter` + `ReferenceLine` | 대각선 기준선, TOP 5 라벨 |

---

## 8. 디자인 방향

### 테마
- **다크 모드 전용** (기존 서비스와 동일한 zinc-900 계열)
- 프로토타입(`dashboard-prototype-E.html`)의 컬러 팔레트 따름:
  - 배경: `#050507` (거의 블랙)
  - 카드: `rgba(255,255,255,0.03)` (매우 subtle)
  - 보더: `rgba(255,255,255,0.06)`
  - 텍스트: `#f4f4f5` / `#a1a1aa` / `#52525b`
  - 차트 색상: purple `#8b5cf6`, cyan `#06b6d4`, green `#10b981`, amber `#f59e0b`, red `#ef4444`, pink `#ec4899`

### 반응형
- 데스크탑 우선 (1280px max-width)
- 태블릿: 2-column grid fallback
- 모바일: 1-column stack

### 애니메이션
- 카드 진입: `animate-fade-in` (기존 globals.css에 정의됨)
- 탭 전환: 콘텐츠 fade
- 차트: Recharts 기본 애니메이션 활용

---

## 9. shadcn/ui 추가 컴포넌트

설치 필요:
```bash
npx shadcn@latest add tabs
npx shadcn@latest add select
npx shadcn@latest add skeleton    # 로딩 상태
npx shadcn@latest add tooltip     # 차트 외 툴팁
```

---

## 10. 구현 순서

### Phase 1: 기반 구조
1. shadcn/ui 컴포넌트 추가 (`tabs`, `select`, `skeleton`, `tooltip`)
2. `types/dashboard.ts` 작성
3. `services/dashboardApi.ts` 작성 (인증 없는 대시보드 전용 fetch)
4. `hooks/useDashboard.ts` 작성
5. `GlobalNav` 컴포넌트 작성
6. `layout.tsx` 수정 (GlobalNav 배치)
7. 공통 컴포넌트 (`ChartCard`, `StatCard`, `PillTabs`, `ExpandableList`)
   - **`ChartCard`에 로딩/에러 상태 내장**: `loading` → Skeleton, `error` → ErrorFallback
   - Phase 2 이후 모든 차트가 자동으로 로딩/에러 처리를 가짐

### Phase 2: Home 탭
8. `DashboardPage` + 탭 구조
9. `HomeTab` + `StatCard` 3개
10. `RecentEvents` + `UpcomingEvents`
11. `RankingsTable` (체급 드롭다운)

### Phase 3: Overview 탭
12. `OverviewTab` 레이아웃
13. `FinishMethodsChart` (도넛)
14. `WeightClassActivityChart` (ComposedChart + 탭)
15. `EventsTimelineChart` (에어리어)
16. `LeaderboardChart` (탭 전환)
17. `FightDurationChart` (바 + ReferenceLine)

### Phase 4: Striking 탭
18. `StrikingTab` 레이아웃
19. `StrikeTargetsChart` (레이더)
20. `StrikingAccuracyChart` (Bullet Chart — attempted/landed overlay)
21. `KoTkoLeadersChart` (스택 바)
22. `SigStrikesChart` (Lollipop Chart — stem + dot)

### Phase 5: Grappling 탭
23. `GrapplingTab` 레이아웃
24. `TakedownChart` (Bullet Chart — attempted/landed overlay, green)
25. `SubmissionTechChart` (가로 바)
26. `ControlTimeChart` (바)
27. `GroundStrikesChart` (Bubble Chart — X:시도, Y:적중, Z:정확도)
28. `SubmissionEfficiencyChart` (Scatter + ReferenceLine)

### Phase 6: 마무리
29. `app/page.tsx` 교체 (Server Component — ISR 적용, `BACKEND_URL` 환경 변수 설정)
30. 체급 필터 연동 (Overview/Striking/Grappling)
31. 반응형 대응
