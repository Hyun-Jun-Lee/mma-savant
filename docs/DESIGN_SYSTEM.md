# MMA Savant Design System

> 프론트엔드 디자인 시스템 레퍼런스. 모든 UI 구현은 이 문서의 토큰과 패턴을 따른다.

---

## 1. Foundation

### 1.1 Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | Next.js 15 (App Router, RSC) |
| UI Primitives | shadcn/ui (new-york style) + Radix UI |
| Styling | Tailwind CSS 4 + oklch color space |
| Variant Management | class-variance-authority (CVA) |
| Charts | Recharts |
| Icons | Lucide React |
| Maps | Leaflet |
| Fonts | Geist Sans (본문), Geist Mono (코드) |

### 1.2 Theme

- **다크 모드 전용** — `<html className="dark">` 하드코딩
- 라이트 모드 미지원 (변수는 정의되어 있으나 사용되지 않음)
- 색공간: **oklch** (CSS Custom Properties)
- `font-variant-numeric: tabular-nums` 전역 적용

---

## 2. Color System

### 2.1 Neutral Scale (Zinc)

앱 전체에서 사용하는 기본 중성 팔레트.

| Token | Hex | 용도 |
|-------|-----|------|
| `zinc-50` | `#fafafa` | — |
| `zinc-100` | `#f4f4f5` | 주요 텍스트 (`text-zinc-100`) |
| `zinc-200` | `#e4e4e7` | 강조 텍스트, 카드 제목 |
| `zinc-300` | `#d4d4d8` | 보조 텍스트, 수치 |
| `zinc-400` | `#a1a1aa` | 비활성 텍스트, 차트 라벨 |
| `zinc-500` | `#71717a` | 라벨, 설명 텍스트 |
| `zinc-600` | `#52525b` | 비활성, 구분선 |
| `zinc-800` | `#27272a` | 스크롤바 트랙 |
| `zinc-900` | `#18181b` | 툴팁 배경, 팝오버 |

### 2.2 Background Layers

| Layer | Value | 용도 |
|-------|-------|------|
| 최상위 | `bg-[#050507]` | body 배경 |
| 네비게이션 | `bg-[#050507]/80` + `backdrop-blur-md` | 글래스 효과 |
| 카드 | `bg-white/[0.03]` | 기본 카드 |
| 카드 호버 | `bg-white/[0.05]` | 호버 상태 |
| 아이콘 박스 | `bg-white/[0.06]` | 아이콘 컨테이너 |
| 버튼/필터 | `bg-white/[0.04]` | PillTabs, WeightClassFilter |
| 활성 상태 | `bg-white/10` | 선택된 탭, 네비게이션 활성 |
| 강한 호버 | `bg-white/[0.08]` | 버튼 호버 |
| Auth 카드 | `bg-white/5` + `backdrop-blur-sm` | 로그인/회원가입 |

### 2.3 Border System

| Token | 용도 |
|-------|------|
| `border-white/[0.03]` | 테이블 행 구분 (마지막 행 제외) |
| `border-white/[0.04]` | 이벤트 카드, 약한 구분 |
| `border-white/[0.06]` | **기본 카드 테두리** (가장 빈번) |
| `border-white/[0.12]` | 카드 호버 테두리 |
| `border-white/10` | Auth 입력필드, 채팅 구분선 |
| `border-white/20` | Auth 카드, 아바타 |

### 2.4 Semantic Chart Colors (`CHART_COLORS`)

도메인별 시맨틱 색상. `src/lib/utils.ts`에 정의.

| 도메인 | Hex | Tailwind | 사용처 |
|--------|-----|----------|--------|
| KO/TKO | `#ef4444` | `red-500` | KoTkoLeaders, KnockdownLeaders, FinishRateTrend |
| Submission | `#a855f7` | `purple-500` | SubmissionTech, SubmissionEfficiency, FinishRateTrend |
| Takedown | `#10b981` | `emerald-500` | Takedown, TdAttempts, TdDefense, ControlTime |
| Striking | `#f59e0b` | `amber-500` | SigStrikes, SigStrikesByWc, FightDuration |
| General | `#8b5cf6` | `violet-500` | Leaderboard, WeightClassActivity, StrikingAccuracy |
| Timeline | `#06b6d4` | `cyan-500` | EventsTimeline, ControlTime |
| Decision | `#06b6d4` | `cyan-500` | FinishMethods, FinishRateTrend |

### 2.5 Fight Outcome Colors (`FINISH_COLORS`)

경기 결과 표시용 시맨틱 맵. 차트 및 배지에 공통 사용.

| 결과 | Hex | 용도 |
|------|-----|------|
| KO/TKO | `#ef4444` | 바, 배지, 트렌드 라인 |
| SUB | `#a855f7` | 바, 배지, 트렌드 라인 |
| U-DEC | `#06b6d4` | 도넛 차트 |
| S-DEC | `#0891b2` | 도넛 차트 |
| M-DEC | `#22d3ee` | 도넛 차트 |
| DQ/Other | `#71717a` | 도넛 차트 |

### 2.6 Status & Accent Colors

| 용도 | 클래스 | 배경 + 텍스트 |
|------|--------|---------------|
| 승리 / 성공 | `text-emerald-400` | `bg-emerald-500/20 text-emerald-300` |
| 패배 / 위험 | `text-red-400` | `bg-red-500/20 text-red-300` |
| 무승부 / 경고 | `text-amber-400` | `bg-amber-500/20 text-amber-300` |
| 챔피언 | `text-yellow-400` | `bg-yellow-500/20 text-yellow-400` |
| 링크 호버 | `text-blue-400` | FighterTick 호버 `#60a5fa` |
| CTA (Auth) | `bg-red-600` | `hover:bg-red-700` |

### 2.7 Fight Comparison Colors (FightCard)

경기 상세 비교 UI(Physical, StatBars, StrikeTarget, 라인 차트)에서 사용하는 result 기반 컬러 규칙.

#### Result Color Mapping

| Result | Bar | Text (우세 시) | Chart Line (hex) |
|--------|-----|---------------|-----------------|
| **Win** | `bg-emerald-500/80` | `text-emerald-400/80` | `#10b981cc` |
| **Loss** | `bg-red-500/40` | `text-red-400/40` | `#ef444466` |
| **기타** | `bg-zinc-500/80` | `text-zinc-400/80` | `#71717acc` |

#### Opacity 규칙

| 대상 | Opacity | 설명 |
|------|---------|------|
| 승리 선수 | **80%** | 기본 opacity. 바, 텍스트, 차트 라인 모두 적용 |
| 패배 선수 | **40%** | 억제된 opacity. 승리 선수 대비 시각적 위계 형성 |

#### 적용 원칙

- 수치상 우세한 쪽에 **해당 선수의 result 색상**을 적용 (항상 emerald가 아님)
- 승리 선수 우세 → emerald, 패배 선수 우세 → red
- 열세한 쪽은 `text-zinc-300` (Physical) 또는 `text-zinc-500` (StatBars)로 표시

---

## 3. Typography

### 3.1 Font Scale

| Token | Size | Weight | 용도 |
|-------|------|--------|------|
| `text-3xl font-bold` | 30px | 700 | W-L-D 레코드 숫자 |
| `text-2xl font-bold tracking-tight` | 24px | 700 | StatCard 숫자 |
| `text-xl` | 20px | — | 강조 수치 |
| `text-lg font-semibold` | 18px | 600 | 차트 카드 시각화 |
| `text-sm font-semibold` | 14px | 600 | 카드 제목, 네비게이션 |
| `text-sm` | 14px | 400 | 본문 텍스트 |
| `text-xs font-medium` | 12px | 500 | 라벨, 설명 |
| `text-xs` | 12px | 400 | 차트 축, 필터, 배지 |
| `text-[10px]` | 10px | — | 아주 작은 배지, 차트 LabelList |
| `fontSize: 11` (SVG) | 11px | — | Recharts 축 텍스트 |

### 3.2 Text Color Hierarchy

```
zinc-100  ← 제목, 주요 텍스트
zinc-200  ← 카드 내 강조 텍스트, 파이터 이름
zinc-300  ← 보조 수치
zinc-400  ← 비활성 텍스트, 차트 Y축
zinc-500  ← 라벨, 설명, X축
zinc-600  ← 구분자, 비활성 아이콘
```

### 3.3 Text Formatting Utilities

- `toTitleCase()` — 소문자 이름 → Title Case
- `formatDate()` — ISO 날짜 → "Nov 15, 2025"
- `abbreviateWeightClass()` — "Featherweight" → "Feather", "Women's Flyweight" → "W.Fly"

---

## 4. Spacing

### 4.1 Scale (4px 기반)

| Token | Value | 주요 용도 |
|-------|-------|----------|
| `0.5` | 2px | `mt-0.5` 미세 간격 |
| `1` | 4px | `gap-1` 아이콘-텍스트 |
| `1.5` | 6px | `gap-1.5` 아이콘-라벨 |
| `2` | 8px | `py-2` 테이블 행 |
| `2.5` | 10px | `py-2.5` 테이블 행 (넓은) |
| `3` | 12px | `gap-3` 컴포넌트 간, `mb-3` 탭-차트 |
| `4` | 16px | `gap-4` 그리드 간격, `mb-4` 섹션 |
| `5` | 20px | `p-5` **카드 패딩** (표준) |
| `6` | 24px | `space-y-6` 대 섹션 간격 |
| `8` | 32px | `py-8` 빈 상태 |
| `12` | 48px | `py-12` 에러 상태 |

### 4.2 Layout Constraints

| 용도 | 값 |
|------|-----|
| 콘텐츠 최대 너비 | `max-w-7xl` (1280px) |
| 수평 패딩 | `px-4` |
| 네비게이션 높이 | `h-14` (56px) |
| 채팅 높이 | `h-[calc(100vh-3.5rem)]` |

---

## 5. Border & Radius

### 5.1 Radius Scale

| Token | Value | 용도 |
|-------|-------|------|
| `rounded-full` | 50% | 배지, 아바타, 프로그레스 바 |
| `rounded-xl` | 12px | **카드** (ChartCard, StatCard, RecordCard) |
| `rounded-lg` | 8px | 툴팁, 팝오버, PillTabs 컨테이너 |
| `rounded-md` | 6px | 버튼, 탭 항목, 로고 |
| `rounded-sm` | 2px | 다이얼로그 닫기 버튼 |

### 5.2 Chart Bar Radius

| 방향 | Radius |
|------|--------|
| 세로 바 (위로) | `radius={[4, 4, 0, 0]}` |
| 가로 바 (오른쪽) | `radius={[0, 4, 4, 0]}` |
| 가로 바 (세밀) | `radius={[0, 3, 3, 0]}` |
| 로리팝 줄기 | `radius={[0, 2, 2, 0]}` |

---

## 6. Shadows & Effects

| Token | 용도 |
|-------|------|
| `shadow-lg` | 차트 툴팁, 드롭다운 |
| `shadow-lg shadow-black/20` | ChartCard 호버 |
| `shadow-sm` | shadcn Card 기본 |
| `backdrop-blur-md` | 네비게이션 |
| `backdrop-blur-sm` | Auth 카드, 채팅 영역 |

---

## 7. Transitions & Animations

### 7.1 Transitions

| Pattern | Duration | Easing | 용도 |
|---------|----------|--------|------|
| `transition-colors` | — | — | 버튼, 링크 호버 (가장 빈번) |
| `transition-all duration-300 ease-out` | 300ms | ease-out | ChartCard 호버 |
| `transition-transform` | — | — | ChevronDown 회전 |

### 7.2 Animations

| 이름 | 정의 | 용도 |
|------|------|------|
| `animate-fade-in` | `opacity 0→1 + translateY 10→0`, 0.5s | 페이지 진입 |
| `animate-pulse` | 반복 투명도 | 스켈레톤, 연결 상태 점 |
| `animate-spin` | 360도 회전 | 로딩 스피너 |
| `animate-bounce` | 바운스 | 타이핑 인디케이터 |
| `animate-in slide-in-from-bottom-2` | 아래→위 슬라이드 | 채팅 메시지 버블 |
| `data-[state=open]:zoom-in-95` | 확대 | 다이얼로그, 팝오버 |

---

## 8. Component Catalog

### 8.1 Base Primitives (shadcn/ui)

15개 컴포넌트. `data-slot` 속성으로 CSS 타겟팅 가능.

| Component | Variants | 주요 Dark Override |
|-----------|----------|-------------------|
| `Button` | default, destructive, outline, secondary, ghost, link | `dark:bg-destructive/60` |
| `Card` | — | 시맨틱 색상 사용 |
| `Input` | — | `dark:bg-input/30` |
| `Textarea` | — | `dark:bg-input/30` |
| `Badge` | default, secondary, destructive, outline + MMA 도메인 8종 (ko, submission, decision, win, loss, draw, champion, ranking) | `dark:bg-destructive/60` |
| `Dialog` | showCloseButton prop | 오버레이 `bg-black/50` |
| `Tabs` | default, line | `dark:text-muted-foreground` |
| `Select` | sm, default | `dark:bg-input/30` |
| `Avatar` | — | — |
| `Label` | — | — |
| `Separator` | horizontal, vertical | — |
| `Skeleton` | — | `bg-white/[0.06]` override |
| `Tooltip` | — | 반전 컬러 |
| `DropdownMenu` | default, destructive | `focus:bg-destructive/10` |
| `ScrollArea` | — | — |

### 8.2 Dashboard Components

| Component | 역할 | 핵심 스타일 |
|-----------|------|------------|
| `ChartCard` | 차트 래퍼 | `rounded-xl`, `p-5`, `hover:scale-[1.01]`, loading/error 상태 |
| `StatCard` | 요약 숫자 | `rounded-xl`, `p-5`, 아이콘 박스 `h-9 w-9` |
| `PillTabs` | 필터 탭 | `rounded-lg`, `bg-white/[0.04]`, sm/md 사이즈 |
| `WeightClassFilter` | 체급 드롭다운 | `h-8 w-[180px]`, `text-xs` |
| `ChartTooltip` | Recharts 툴팁 래퍼 | `rounded-lg`, `bg-zinc-900`, `text-xs` |

### 8.3 Chart Patterns

#### FighterTick (차트 Y축 파이터 이름)
```tsx
<text
  fill="#a1a1aa"
  fontSize={11}
  style={{ cursor: 'pointer' }}
  onClick={() => router.push(`/fighters/${fighter_id}`)}
  onMouseEnter={(e) => { e.currentTarget.setAttribute('fill', '#60a5fa') }}
  onMouseLeave={(e) => { e.currentTarget.setAttribute('fill', '#a1a1aa') }}
>
  {toTitleCase(name)}
</text>
```

#### Show More/Less
```tsx
<button className="mt-2 flex w-full items-center justify-center gap-1 rounded-lg py-1.5 text-xs text-zinc-500 transition-colors hover:bg-white/[0.04] hover:text-zinc-300">
  <ChevronDown className={`h-3.5 w-3.5 transition-transform ${expanded ? 'rotate-180' : ''}`} />
  {expanded ? 'Show Less' : `Show All ${total}`}
</button>
```

#### Recharts 공통 설정

| 요소 | 설정 |
|------|------|
| X축 텍스트 | `fill: '#52525b', fontSize: 11` |
| Y축 텍스트 | `fill: '#a1a1aa', fontSize: 11` |
| 축선/틱선 | `axisLine={false} tickLine={false}` |
| 커서 오버레이 | `cursor={{ fill: 'rgba(255,255,255,0.04)' }}` |
| 기준선 | `stroke="#71717a" strokeDasharray="4 4"` |
| 차트 높이 | 280px (기본), 180px (접힘), 320px (펼침) |
| 여백 | `margin={{ top: 5, right: 10, left: -10, bottom: 0 }}` |

---

## 9. Layout Patterns

### 9.1 Page Structure
```
<nav>  — sticky, h-14, backdrop-blur, max-w-7xl
<main>
  <div className="mx-auto max-w-7xl px-4 py-6">
    ...
  </div>
</main>
```

### 9.2 Grid System

| 패턴 | 용도 |
|------|------|
| `grid-cols-1 gap-4 sm:grid-cols-3` | StatCard 3열 |
| `grid-cols-1 gap-4 lg:grid-cols-2` | 차트 2열 |
| `grid-cols-2 gap-3 sm:grid-cols-4` | CategoryLeaders 4열 |
| `space-y-6` | 대 섹션 간격 |
| `space-y-4` | 소 섹션 간격 |

### 9.3 Responsive Breakpoints

| Breakpoint | Width | 주요 변화 |
|------------|-------|----------|
| `sm` | 640px | 3열 그리드, 4열 리더 |
| `md` | 768px | — |
| `lg` | 1024px | 2열 차트 그리드 |

---

## 10. Interaction States

### 10.1 카드 호버
```
hover:scale-[1.01]
hover:border-white/[0.12]
hover:bg-white/[0.05]
hover:shadow-lg hover:shadow-black/20
transition-all duration-300 ease-out
```

### 10.2 네비게이션
```
활성: bg-white/10 text-white
비활성: text-zinc-400 hover:bg-white/[0.06] hover:text-zinc-200
```

### 10.3 PillTabs
```
활성: bg-white/10 text-white
비활성: text-zinc-500 hover:text-zinc-300
```

### 10.4 링크 (파이터 이름)
```
hover:text-blue-400 hover:underline transition-colors
```

### 10.5 데이터 프레시니스
```
text-xs text-zinc-600, Clock 아이콘 h-3 w-3
하단 중앙 정렬
```

---

## 11. Loading & Error States

### 11.1 Skeleton
```tsx
<Skeleton className="h-[200px] w-full bg-white/[0.06]" />
```

### 11.2 Error
```tsx
<div className="flex flex-col items-center justify-center gap-3 py-12 text-center">
  <AlertCircle className="h-8 w-8 text-zinc-600" />
  <p className="text-sm text-zinc-500">데이터를 불러올 수 없습니다</p>
  <Button size="sm" variant="ghost">
    <RefreshCw className="mr-1.5 h-3 w-3" /> 재시도
  </Button>
</div>
```

### 11.3 Empty State
```tsx
<p className="py-8 text-center text-sm text-zinc-600">No data available</p>
```

---

## 12. Scrollbar

다크 테마 커스텀 스크롤바 (WebKit):

| 요소 | 색상 |
|------|------|
| Track | `#27272a` (zinc-800) |
| Thumb | `#52525b` (zinc-600) |
| Thumb hover | `#71717a` (zinc-500) |
| Width/Height | 8px |
| Radius | 4px |

---

## 13. Chat UI

AI 채팅 인터페이스 전용 패턴. **기존 디자인 토큰을 재사용**하며, 채팅 고유 요소만 추가 정의한다.

### 13.1 Page Layout

| 요소 | 값 | 비고 |
|------|----|------|
| 페이지 배경 | `bg-[#050507]` | 대시보드와 동일, 그래디언트 사용 금지 |
| 콘텐츠 최대 너비 | `max-w-4xl` (메시지), `max-w-7xl` (그리드) | |
| 페이지 높이 | `h-[calc(100vh-3.5rem)]` | 네비 제외 전체 높이 |
| 상단 입력바 | `backdrop-blur-sm` + `border-b border-white/[0.06]` | 네비와 동일한 글래스 패턴 |

### 13.2 Chat Bubbles

유저와 AI 어시스턴트 메시지를 시각적으로 구분하는 버블 스타일.

#### User Bubble

| 요소 | 값 |
|------|----|
| 배경 | `bg-white/[0.06]` |
| 테두리 | `border border-white/[0.06]` |
| 텍스트 | `text-zinc-100` |
| 아바타 배경 | `bg-white/[0.06]` |
| 아바타 테두리 | `border border-white/[0.06]` |
| 라운딩 | `rounded-lg` |

#### Assistant Bubble

| 요소 | 값 |
|------|----|
| 배경 | 없음 (투명) |
| 텍스트 | `prose prose-invert prose-sm` (Tailwind Typography) |
| 아바타 배경 | `bg-violet-500/20` |
| 아바타 텍스트/아이콘 | `text-violet-400` |
| 아바타 테두리 | `border border-white/[0.06]` |

> AI 시맨틱 색상으로 `violet-500`을 사용한다. 기존 `CHART_COLORS.general`(`#8b5cf6`, violet-500)과 동일하여 별도 토큰 없이 재사용.

#### Bubble 공통

| 요소 | 값 |
|------|----|
| 아바타 크기 | `w-8 h-8` |
| 입장 애니메이션 | `animate-in slide-in-from-bottom-2` |
| 타임스탬프 | `text-xs text-zinc-500` |
| 메시지 간격 | `gap-3` (아바타↔콘텐츠), `space-y-4` (메시지 간) |

### 13.3 Session Cards (HistoryView)

세션 목록과 히스토리 카드는 **대시보드 카드 패턴**을 그대로 따른다.

| 요소 | 값 | 대시보드 동일 여부 |
|------|----|----------------|
| 카드 배경 | `bg-white/[0.03]` | ChartCard 동일 |
| 카드 테두리 | `border border-white/[0.06]` | ChartCard 동일 |
| 카드 호버 배경 | `hover:bg-white/[0.05]` | ChartCard 동일 |
| 카드 호버 테두리 | `hover:border-white/[0.12]` | ChartCard 동일 |
| 패딩 | `p-5` | ChartCard 동일 |
| 라운딩 | `rounded-xl` | ChartCard 동일 |
| 그리드 | `grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4` | 대시보드 그리드 |

### 13.4 Input Area

| 요소 | 값 | 비고 |
|------|----|------|
| 입력 배경 | `bg-white/[0.03]` | shadcn Input의 dark 패턴 |
| 입력 텍스트 | `text-zinc-100` | |
| 플레이스홀더 | `text-zinc-500` | |
| 포커스 | `focus:ring-0 focus:outline-0` | 최소한의 포커스 |
| 전송 버튼 배경 | `bg-white/[0.04]` | 필터 버튼 패턴 |
| 전송 버튼 호버 | `hover:bg-white/[0.08]` | 강한 호버 패턴 |
| 전송 아이콘 | `text-zinc-400 hover:text-zinc-100` | |
| 높이 | `h-12` | |

### 13.5 Session Sidebar

| 요소 | 값 | 비고 |
|------|----|------|
| 배경 | `bg-[#050507]/95 backdrop-blur-md` | 네비게이션 글래스 패턴 응용 |
| 오버레이 | `bg-black/50` | shadcn Dialog overlay |
| 테두리 | `border-l border-white/[0.06]` | |
| 그림자 | `shadow-lg` | |
| 세션 아이템 기본 | `bg-white/[0.03]` + `border border-white/[0.06]` | 카드 패턴 |
| 세션 아이템 활성 | `bg-white/10` + `border-white/[0.12]` | 활성 상태 패턴 |
| 세션 아이템 호버 | `hover:bg-white/[0.05]` | 카드 호버 |

### 13.6 Dialogs & Popups

채팅 전용 다이얼로그(세션 상세, 에러, 사용량 제한)는 **shadcn Dialog**를 기반으로 한다.

| 요소 | 값 | 비고 |
|------|----|------|
| 배경 | `bg-[#050507]` | 페이지 배경과 동일 |
| 테두리 | `border border-white/[0.06]` | 카드 테두리 |
| 라운딩 | `rounded-xl` | 카드 라운딩 |
| 오버레이 | `bg-black/50` | shadcn 기본 |
| 닫기 버튼 | `text-zinc-400 hover:text-zinc-100 hover:bg-white/[0.08]` | |
| 에러 아이콘 | `bg-red-500/20 text-red-400` | Status 색상 |
| 경고 아이콘 | `bg-amber-500/20 text-amber-400` | Status 색상 |

### 13.7 Loading & Typing States

| 요소 | 값 | 비고 |
|------|----|------|
| 로딩 카드 배경 | `bg-white/[0.03]` | 카드 패턴 |
| 로딩 카드 테두리 | `border border-white/[0.06]` | 카드 테두리 |
| 스켈레톤 | `bg-white/[0.06] animate-pulse` | 기존 Skeleton 패턴 |
| 타이핑 인디케이터 점 | `w-2 h-2 bg-zinc-400 animate-bounce` | |
| 타이핑 텍스트 | `text-xs text-zinc-400` | |

### 13.8 QuestionAnswer Card (세션 상세 내 메시지)

| 요소 | 값 | 비고 |
|------|----|------|
| 유저 메시지 배경 | `bg-white/[0.03]` | 카드 패턴 |
| AI 메시지 배경 | `bg-violet-500/5` | AI 시맨틱 색상의 약한 배경 |
| AI 메시지 테두리 | `border border-violet-500/10` | AI 시맨틱 색상의 약한 테두리 |
| 유저 아이콘 박스 | `bg-white/[0.06]` | 아이콘 박스 패턴 |
| AI 아이콘 박스 | `bg-violet-500/20` | AI 시맨틱 색상 |

---

## 14. File Structure

```
src/
├── app/
│   ├── globals.css              ← 테마 변수, 애니메이션, 스크롤바
│   ├── layout.tsx               ← 루트 레이아웃 (dark, Geist, providers)
│   ├── page.tsx                 ← 대시보드 페이지
│   ├── auth/                    ← 로그인/회원가입
│   ├── chat/                    ← AI 채팅
│   └── fighters/[id]/           ← 파이터 상세
├── components/
│   ├── ui/                      ← 15개 shadcn/ui primitives
│   ├── dashboard/
│   │   ├── ChartCard.tsx        ← 차트 래퍼
│   │   ├── StatCard.tsx         ← 요약 카드
│   │   ├── PillTabs.tsx         ← 필터 탭
│   │   ├── ChartTooltip.tsx     ← Recharts 툴팁
│   │   ├── WeightClassFilter.tsx← 체급 필터
│   │   ├── home/                ← 홈 탭 차트들
│   │   ├── overview/            ← 오버뷰 탭 차트들
│   │   ├── striking/            ← 타격 탭 차트들
│   │   └── grappling/           ← 그래플링 탭 차트들
│   ├── fighter/                 ← 파이터 상세 컴포넌트
│   ├── chat/                    ← 채팅 UI
│   ├── visualization/           ← 채팅용 차트 렌더러
│   ├── auth/                    ← 인증 폼
│   └── layout/                  ← GlobalNav
├── hooks/                       ← useAuth, useDashboard, useFighterDetail 등
├── lib/
│   └── utils.ts                 ← cn(), toTitleCase, formatDate, CHART_COLORS 등
├── services/                    ← API 클라이언트
└── types/                       ← TypeScript 인터페이스
```
