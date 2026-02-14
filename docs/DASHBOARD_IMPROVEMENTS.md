# Dashboard Frontend 개선사항

> `DASHBOARD_FRONTEND_PLAN.md`에 대한 리뷰 후 확정된 개선 사항 정리.
> 기존 계획에 아래 내용을 반영하여 구현할 것.

---

## 1. 데이터 페칭: TanStack Query 도입

기존 계획의 `useDashboard` 단일 훅 대신 **TanStack Query(React Query)**를 도입하고, 탭별 독립 훅으로 분리한다.

### 이유

- 캐싱, 중복 요청 방지, stale-while-revalidate, 백그라운드 리페칭을 직접 구현할 필요 없음
- 탭별 독립 훅으로 관심사 분리가 깔끔해짐
- `weightClassId` 변경 시 캐시 무효화를 queryKey로 자동 처리

### 구현 방향

```bash
npm install @tanstack/react-query
```

```typescript
// hooks/useHomeData.ts
import { useQuery } from '@tanstack/react-query'
import { DashboardApiService } from '@/services/dashboardApi'

export function useHomeData() {
  return useQuery({
    queryKey: ['dashboard', 'home'],
    queryFn: () => DashboardApiService.getHome(),
    staleTime: 5 * 60 * 1000, // 5분 (공개 데이터이므로 넉넉하게)
  })
}

// hooks/useOverviewData.ts
export function useOverviewData(weightClassId?: number) {
  return useQuery({
    queryKey: ['dashboard', 'overview', weightClassId],
    queryFn: () => DashboardApiService.getOverview(weightClassId),
    staleTime: 5 * 60 * 1000,
  })
}

// hooks/useStrikingData.ts, hooks/useGrapplingData.ts도 동일 패턴
```

### 변경되는 파일 구조

```
hooks/
├── useDashboard.ts        # 삭제
├── useHomeData.ts          # 신규
├── useOverviewData.ts      # 신규
├── useStrikingData.ts      # 신규
└── useGrapplingData.ts     # 신규
```

### QueryProvider 설정

`app/layout.tsx`에 `QueryClientProvider`를 추가한다.

```typescript
// app/providers.tsx (Client Component)
'use client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 5 * 60 * 1000,
        retry: 1,
      },
    },
  }))
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
}
```

---

## 2. Home 탭 ISR(Incremental Static Regeneration) 활용

Home 탭은 인증 불필요한 공개 데이터이므로, Next.js Server Component + ISR을 활용한다.

### 동작 원리

- Next.js 서버가 사용자 대신 FastAPI 백엔드에 데이터를 요청하여 HTML을 미리 렌더링
- 이후 접속하는 사용자들은 캐시된 HTML을 즉시 받음 (FastAPI 호출 없음)
- `revalidate` 주기마다 백그라운드에서 갱신

```
첫 접속 → Next.js 서버 → FastAPI → HTML 생성 & 캐시
이후 접속 → 캐시된 HTML 즉시 반환
5분 경과 → 다음 요청 시 백그라운드 갱신
```

### 구현 방향

```typescript
// app/page.tsx (Server Component)
import { HomeTab } from '@/components/dashboard/home/HomeTab'

export const revalidate = 300 // 5분마다 재생성

async function getHomeData() {
  const res = await fetch(`${process.env.BACKEND_URL}/api/dashboard/home`, {
    next: { revalidate: 300 },
  })
  if (!res.ok) throw new Error('Failed to fetch home data')
  return res.json()
}

export default async function DashboardPage() {
  const homeData = await getHomeData()
  return <DashboardPageClient initialHomeData={homeData} />
}
```

### 적용 범위

| 탭 | 렌더링 방식 | 이유 |
|---|---|---|
| Home | SSR + ISR | 필터 없음, 공개 데이터, 변경 빈도 낮음 |
| Overview | CSR (TanStack Query) | weightClassId 필터에 따라 동적 |
| Striking | CSR (TanStack Query) | weightClassId 필터에 따라 동적 |
| Grappling | CSR (TanStack Query) | weightClassId 필터에 따라 동적 |

### 환경 변수 추가

```env
# frontend/.env.local
BACKEND_URL=http://localhost:8002  # 서버 사이드 전용 (NEXT_PUBLIC 아님)
```

---

## 3. URL 상태 관리

`activeTab`과 `weightClassId`를 URL 쿼리 파라미터로 관리한다.

### 이유

- 링크 공유 가능 (예: `/?tab=striking&weight_class=5`)
- 브라우저 뒤로가기/앞으로가기 지원
- 새로고침 시 상태 유지

### 구현 방향

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

  const updateParams = (updates: Record<string, string | undefined>) => {
    const params = new URLSearchParams(searchParams.toString())
    Object.entries(updates).forEach(([key, value]) => {
      if (value === undefined) params.delete(key)
      else params.set(key, value)
    })
    router.push(`${pathname}?${params.toString()}`, { scroll: false })
  }

  const setTab = (tab: string) => updateParams({ tab: tab === 'home' ? undefined : tab })
  const setWeightClass = (id?: number) => updateParams({ weight_class: id?.toString() })

  // ...
}
```

---

## 4. 차트 변경 (4건)

기존 계획의 수평 바 차트 6개 중 4개를 다른 차트 유형으로 변경한다. 시각적 다양성 확보 및 데이터 특성에 맞는 표현이 목적.

### 변경 요약

| 항목 | 변경 전 | 변경 후 | Recharts 구성 |
|---|---|---|---|
| 3-2 타격 정확도 | 수평 바 | **Bullet Chart** | `BarChart(vertical)` — 2개 `Bar` overlay (`barGap={-26}`) |
| 3-4 유효타격/경기 | 수평 바 | **Lollipop Chart** | `ComposedChart(vertical)` — `Bar`(stem) + `Scatter`(dot) |
| 4-1 테이크다운 | 수평 바 | **Bullet Chart** | `BarChart(vertical)` — 2개 `Bar` overlay (3-2와 동일 패턴) |
| 4-4 그라운드 타격 | 수평 바 | **Scatter Chart** | `ScatterChart` + `ZAxis` + `ReferenceLine`(대각선) |

### 4-1. 3-2 Striking Accuracy → Bullet Chart

시도(attempted) 대비 적중(landed)을 overlay 바로 직관적 비교.

```
핵심 구조:
- 넓은 반투명 바: attempted (barSize={22})
- 좁은 채색 바: landed (barSize={13})
- barGap={-26}으로 겹침
- 오른쪽 label로 accuracy% 표시
- Cell 색상: accuracy >= 62 → #8b5cf6, >= 55 → #7c3aed, else → #6d28d9
```

```typescript
// components/dashboard/striking/StrikingAccuracyChart.tsx
<BarChart data={data} layout="vertical" barGap={-26}>
  <Bar dataKey="attempted" fill="rgba(139,92,246,0.1)" barSize={22} radius={[0,5,5,0]} />
  <Bar dataKey="landed" barSize={13} radius={[0,5,5,0]}
    label={{ position: "right", formatter: (v) => `${findAccuracy(v)}%` }}>
    {data.map((e, i) => <Cell key={i} fill={getAccuracyColor(e.accuracy)} />)}
  </Bar>
</BarChart>
```

### 4-2. 3-4 Sig Strikes Per Fight → Lollipop Chart

경기당 유효타격을 줄기(stem) + 점(dot)으로 표현. 점 크기로 총 경기수를 인코딩.

```
핵심 구조:
- ComposedChart layout="vertical"
- Bar: stem 역할 (barSize={3}, 얇은 선)
- Scatter: 끝점 dot (커스텀 shape 컴포넌트)
  - dot 반지름: total_fights * 0.45 (최소 6, 최대 14)
  - dot 옆에 "{total_fights}F" 텍스트 라벨
- ReferenceLine: 평균값 점선 (AVG 라벨)
- 색상: amber 계열 (#f59e0b)
```

```typescript
// components/dashboard/striking/SigStrikesChart.tsx
const LollipopDot = ({ cx, cy, payload }) => {
  const r = Math.max(6, Math.min(14, payload.total_fights * 0.45));
  return (
    <g>
      <circle cx={cx} cy={cy} r={r + 4} fill="rgba(245,158,11,0.12)" />
      <circle cx={cx} cy={cy} r={r} fill="#f59e0b" fillOpacity={0.85} />
      <text x={cx + r + 8} y={cy + 4} fill="#71717a" fontSize={10}>{payload.total_fights}F</text>
    </g>
  );
};

<ComposedChart data={data} layout="vertical">
  <Bar dataKey="stem" barSize={3} />
  <Scatter dataKey="sig_per_fight" shape={<LollipopDot />} />
</ComposedChart>
```

### 4-3. 4-1 Takedown Accuracy → Bullet Chart

3-2와 동일한 Bullet Chart 패턴. 색상만 green 계열로 변경.

```
핵심 구조:
- 3-2와 동일한 overlay 바 패턴
- 배경 바: attempted, fill="rgba(16,185,129,0.1)"
- 전경 바: landed
- Cell 색상: accuracy >= 58 → #10b981, >= 52 → #059669, else → #047857
- label: accuracy%
```

### 4-4. 4-4 Ground Strikes → Scatter Chart (버블)

3축 데이터(시도/적중/정확도)를 2D + 버블 크기로 표현.

```
핵심 구조:
- ScatterChart
- XAxis: attempted (시도)
- YAxis: landed (적중)
- ZAxis: accuracy → 버블 크기 (range={[250, 650]})
- 버블 색상: accuracy >= 75 → #10b981(green), >= 65 → #06b6d4(cyan), else → #8b5cf6(purple)
- ReferenceLine 대각선 2개:
  - 100% 기준선: segment [{x:100,y:100}, {x:500,y:500}]
  - 70% 기준선: segment [{x:143,y:100}, {x:520,y:364}]
- 하단에 선수 이름 태그 (hover 시 해당 버블 하이라이트)
```

```typescript
// components/dashboard/grappling/GroundStrikesChart.tsx
<ScatterChart>
  <XAxis type="number" dataKey="attempted" />
  <YAxis type="number" dataKey="landed" />
  <ZAxis type="number" dataKey="accuracy" range={[250, 650]} />
  <ReferenceLine segment={[{x:100,y:100},{x:500,y:500}]} /> {/* 100% 대각선 */}
  <ReferenceLine segment={[{x:143,y:100},{x:520,y:364}]} /> {/* 70% 대각선 */}
  <Scatter data={data}>
    {data.map((e, i) => (
      <Cell key={i} fill={getColor(e.accuracy)} fillOpacity={highlighted === i ? 0.8 : 0.15} />
    ))}
  </Scatter>
</ScatterChart>
```

### 변경되지 않는 차트

| 항목 | 유형 | 유지 이유 |
|---|---|---|
| 3-3 KO/TKO TOP | 스택 바 | 이미 차별화된 차트 유형 |
| 4-2 서브미션 기술 | 수평 바 | 단일 축(기술명 + 횟수) 데이터에 수평 바가 가장 적합 |

---

## 5. 기타 개선 사항

### API 서비스 방어적 처리

```typescript
// 기존 (non-null assertion)
return response.data!

// 변경
if (!response.data) throw new Error('Empty response from dashboard API')
return response.data
```

### 로딩/에러 상태를 Phase 1에서 선처리

기존 계획의 Phase 6(마무리)에 있던 로딩/에러 처리를 Phase 1로 이동. ChartCard 레벨에서 Skeleton 및 ErrorFallback 패턴을 먼저 구축한 뒤 각 차트에 적용.

```typescript
// components/dashboard/ChartCard.tsx
interface ChartCardProps {
  title: string
  description?: string
  loading?: boolean
  error?: string | null
  children: ReactNode
}

// loading=true일 때 Skeleton 렌더링
// error가 있을 때 ErrorFallback 렌더링
```

### 공통 차트 색상 상수

```typescript
// lib/chartColors.ts
export const CHART_COLORS = {
  purple: '#8b5cf6',
  cyan: '#06b6d4',
  green: '#10b981',
  amber: '#f59e0b',
  red: '#ef4444',
  pink: '#ec4899',
} as const

export const STRIKING_PALETTE = { primary: CHART_COLORS.purple, bg: 'rgba(139,92,246,0.1)' }
export const GRAPPLING_PALETTE = { primary: CHART_COLORS.green, bg: 'rgba(16,185,129,0.1)' }
export const SIG_STRIKES_PALETTE = { primary: CHART_COLORS.amber, bg: 'rgba(245,158,11,0.1)' }
```
