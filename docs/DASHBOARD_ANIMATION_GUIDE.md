# MMA Savant 대시보드 애니메이션 개선 가이드

---

## 개요

현재 대시보드는 차트 hover 시 살짝 강조되는 정도의 인터랙션만 적용되어 있어 전반적으로 밋밋한 인상을 준다. 기존 스택(React + Next.js + Tailwind + Recharts + shadcn/ui)을 유지하면서, **Framer Motion**과 **Recharts 내장 애니메이션**, **CSS 효과**를 레이어별로 추가하여 시각적 생동감을 높인다.

---

## 의존성 추가

| 패키지 | 용도 | 필수 여부 |
|--------|------|----------|
| `framer-motion` | 카드 등장, 탭 전환, hover 인터랙션 | 필수 |
| `react-countup` | Summary 카드 숫자 카운트업 (직접 구현도 가능) | 선택 |

---

## 적용 영역별 상세

### 1. 카드 등장 애니메이션 (ChartCard)

**현재**: 모든 카드가 페이지 로드 시 동시에 나타남
**개선**: 카드가 순차적으로 아래에서 올라오며 fade-in + blur 해제

- 라이브러리: Framer Motion
- 적용 대상: `ChartCard` 공통 래퍼
- 동작 방식:
  - `initial`: opacity 0, translateY 28px, blur 4px
  - `animate`: opacity 1, translateY 0, blur 0
  - `transition`: 0.7초, cubic-bezier(0.23, 1, 0.32, 1)
  - 각 카드에 `index` prop을 전달하여 `delay: index * 0.1초`로 순차 등장 (staggered)
- 우선순위: **최상** — 가장 적은 노력으로 가장 큰 체감 효과

---

### 2. 카드 Hover 효과 강화 (ChartCard)

**현재**: `hover:scale-[1.01]`, `hover:border-white/[0.12]` 정도의 미세한 변화
**개선**: 보라색 글로우 + 상단 그래디언트 라인 + 마우스 추적 라이팅

적용할 효과 3가지:

1. **보라색 글로우 보더**: hover 시 `boxShadow: 0 0 28px rgba(139, 92, 246, 0.12)`, `borderColor: rgba(139, 92, 246, 0.3)`, `translateY: -3px`
2. **상단 그래디언트 라인**: `::before` 가상 요소로 카드 상단에 `linear-gradient(90deg, transparent, purple, transparent)` — 평소 opacity 0, hover 시 0.7
3. **마우스 추적 Radial Gradient**: `::after` 가상 요소 + `onMouseMove`로 `--mouse-x`, `--mouse-y` CSS 변수 업데이트 → `radial-gradient(600px circle at var(--mouse-x) var(--mouse-y), rgba(139, 92, 246, 0.04), transparent 40%)`

- 라이브러리: Framer Motion (`whileHover`) + CSS 가상 요소
- 적용 대상: `ChartCard` 공통 래퍼
- 우선순위: **높음**

---

### 3. Recharts 차트별 진입 애니메이션

**현재**: Recharts 기본 애니메이션 (거의 눈에 띄지 않음)
**개선**: 차트 타입별로 `animationBegin`, `animationDuration`, `animationEasing` 설정

모든 차트 공통으로 `animationEasing="ease-out"` 적용.

| 차트 | 컴포넌트 | animationBegin | animationDuration | 시각 효과 |
|------|----------|---------------|-------------------|----------|
| Finish Methods (도넛) | `<Pie>` | 400ms | 1400ms | `startAngle: 90`, `endAngle: -270` → 시계방향 회전하며 그려짐 |
| Events Timeline (Area) | `<Area>` | 600ms | 1800ms | 왼쪽에서 오른쪽으로 선이 그어지며 영역 채워짐 |
| Weight Class Activity (Bar) | `<Bar>` | 500ms | 1200ms | 바가 0에서 위로 자라남 |
| Fight Duration (Bar) | `<Bar>` | 600ms | 1000ms | 바가 0에서 위로 자라남 |
| Strike Targets (Radar) | `<Radar>` | 500ms | 1200ms | 중심에서 바깥으로 펼쳐짐 |
| KO/TKO Leaders (수평 Bar) | `<Bar>` | 500ms | 1200ms | 바가 왼쪽에서 오른쪽으로 자라남 |
| Striking Accuracy (Bullet) | Background `<Bar>` | 200ms | 900ms | 배경 바 먼저 등장 |
| | Foreground `<Bar>` | 500ms | 900ms | 전경 바 딜레이 후 등장 |
| Takedown Accuracy (Bullet) | Background `<Bar>` | 200ms | 900ms | 배경 바 먼저 등장 |
| | Foreground `<Bar>` | 500ms | 900ms | 전경 바 딜레이 후 등장 |
| Sig. Strikes (Lollipop) | `<Bar>` + `<Scatter>` | 400ms / 700ms | 1000ms / 800ms | 바 먼저, 점은 딜레이 후 |
| Finish Rate Trend (Stacked Area) | `<Area>` | 500ms | 1500ms | 순차적으로 영역 채워짐 |
| TD-Sub Correlation (Scatter) | `<Scatter>` | 600ms | 1200ms | 점들이 페이드인 |

- 적용 대상: 각 차트 컴포넌트 (`FinishMethodsChart.tsx`, `KoTkoLeadersChart.tsx`, `TakedownChart.tsx` 등)
- 기존 props에 애니메이션 props만 추가하면 되므로 변경 범위가 작음
- 우선순위: **높음**

---

### 4. Summary 카드 숫자 카운트업

**현재**: 숫자가 즉시 표시됨
**개선**: 0에서 목표값까지 부드럽게 올라가는 카운트업 효과

- 대상: Home 탭 상단 Summary Cards (Total Fighters, Total Matches, Total Events)
- 동작:
  - `requestAnimationFrame` 기반으로 약 1.5초간 0 → 목표값
  - easing: cubic ease-out (`1 - (1 - progress)^3`)
  - 각 카드마다 150ms 딜레이를 두어 순차적으로 카운트
- 구현 방식: `react-countup` 패키지 또는 커스텀 훅
- 우선순위: **중간** — Home 탭에만 해당

---

### 5. PillTabs 전환 애니메이션

**현재**: 탭 클릭 시 데이터가 즉시 교체됨
**개선**: 두 가지 효과 동시 적용

1. **인디케이터 슬라이드**: 활성 탭 배경이 `transform: translateX()`로 부드럽게 이동. `transition: 0.3초, cubic-bezier(0.23, 1, 0.32, 1)`.
2. **차트 내용 전환**: Framer Motion `AnimatePresence` + `mode="wait"` 사용. 기존 차트 왼쪽으로 사라짐(`exit: opacity 0, x -12`) → 새 차트 오른쪽에서 등장(`initial: opacity 0, x 12`). duration 0.25초.

- 라이브러리: Framer Motion (`AnimatePresence`)
- 적용 대상: `PillTabs`를 사용하는 모든 차트 (Striking Accuracy, Sig. Strikes, Takedown Accuracy, TD Attempts, TD Defense 등)
- `key={activeKey}`를 설정하여 탭 변경 시 자동으로 exit/enter 트리거
- 우선순위: **중간**

---

### 6. CSS 글로벌 효과

`globals.css`에 추가할 항목들:

1. **Tooltip 스타일 통일**: 모든 Recharts 툴팁에 `backdrop-filter: blur(12px)`, `box-shadow: 0 8px 32px rgba(0,0,0,0.5)` 적용
2. **스크롤바**: 다크 테마에 맞는 커스텀 스크롤바 (`#27272a` thumb, transparent track)
3. **ActiveDot 강화**: Area/Line 차트의 활성 점에 `stroke: 배경색`, `strokeWidth: 2` 추가하여 점이 떠있는 느낌

---

## 적용 우선순위 종합

| 순위 | 작업 | 난이도 | 체감 효과 | 영향 범위 |
|------|------|--------|----------|----------|
| 1 | ChartCard 등장 애니메이션 (staggered fade-in) | 낮음 | 매우 큼 | 전체 |
| 2 | Recharts animationBegin/Duration 설정 | 낮음 | 큼 | 전체 차트 |
| 3 | ChartCard hover 글로우 + 마우스 추적 | 낮음~중간 | 큼 | 전체 |
| 4 | PillTabs AnimatePresence 전환 | 중간 | 중간 | PillTabs 사용 차트 |
| 5 | Summary 카드 카운트업 | 낮음 | 중간 | Home 탭 |
| 6 | CSS 글로벌 효과 (툴팁, 스크롤바) | 낮음 | 낮음 | 전체 |

1~3번만 적용해도 대시보드의 첫인상이 크게 달라진다.

---

## ChartCard 수정 포인트

현재 `ChartCard.tsx`에서 변경이 필요한 부분:

1. 최상위 `<div>`를 Framer Motion의 `<motion.div>`로 교체
2. `index` prop 추가 (순차 등장용)
3. 기존 CSS `transition-all` 클래스 제거 → Framer Motion `whileHover`로 대체
4. `onMouseMove` 핸들러 추가 (마우스 추적 라이팅용)
5. `::before`, `::after` 가상 요소는 CSS 또는 Tailwind `before:`, `after:` 유틸리티로 추가

---

## 차트 컴포넌트 수정 포인트

각 차트 컴포넌트에서 Recharts 요소에 props만 추가:

- `<Pie>`: `animationBegin`, `animationDuration`, `animationEasing`, `startAngle`, `endAngle`
- `<Bar>`: `animationBegin`, `animationDuration`, `animationEasing`
- `<Area>`, `<Line>`: `animationBegin`, `animationDuration`, `animationEasing`
- `<Radar>`: `animationBegin`, `animationDuration`
- `<Scatter>`: `animationBegin`, `animationDuration`

Bullet Chart (2-Bar overlay) 패턴의 경우, Background Bar의 `animationBegin`을 Foreground Bar보다 300ms 앞서게 설정.

---

## 색상 참조 (현재 테마 기준)

| 용도 | 색상값 |
|------|--------|
| 글로우 보더 (hover) | `rgba(139, 92, 246, 0.3)` |
| 글로우 shadow (hover) | `rgba(139, 92, 246, 0.12)` |
| 상단 그래디언트 라인 | `rgba(139, 92, 246, 1)` (양쪽 transparent) |
| 마우스 추적 radial | `rgba(139, 92, 246, 0.04)` |
| Accent Purple | `#8b5cf6` |
| Accent Cyan | `#06b6d4` |
| Accent Emerald | `#10b981` |
| Accent Red | `#ef4444` |
| Accent Amber | `#f59e0b` |

---

## 주의사항

- Framer Motion의 `initial`/`animate`는 **SSR 환경(Next.js)**에서 hydration mismatch를 일으킬 수 있으므로, 필요 시 `<LazyMotion>` + `domAnimation`을 사용하거나 `useReducedMotion` 훅으로 접근성을 고려할 것
- Recharts 애니메이션은 **데이터가 변경될 때마다** 다시 실행되므로, 필터 변경 시 자연스러운 전환이 자동으로 이루어짐
- `AnimatePresence`의 `mode="wait"`은 exit 애니메이션이 끝난 후 enter가 시작되므로, duration을 짧게(0.2~0.3초) 유지해야 체감 속도가 느려지지 않음
- 카드 등장 애니메이션의 `delay`가 너무 길면 사용자가 빈 화면을 오래 보게 되므로, 카드 간 간격은 0.08~0.12초가 적당
