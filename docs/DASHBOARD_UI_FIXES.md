# Dashboard UI 수정 사항 정리

> 작성일: 2026-02-13
> 최종 업데이트: 2026-02-13

---

## 공통 이슈: Bar 차트 hover 개선


### ✅ 1) Tooltip cursor 흰색 배경 제거

**현상**: 여러 차트에서 마우스를 올리면 흰색 배경의 기본 Tooltip이 나타남
**원인**: Recharts의 `<Tooltip>` 기본 `cursor` 속성이 흰색 하이라이트를 그림
**해결**: `cursor={false}` 또는 `cursor={{ fill: 'rgba(255,255,255,0.04)' }}` 적용하여 은은한 강조로 변경
**영향 범위**: FightDuration, StrikingAccuracy, KoTkoLeaders, TakedownAccuracy, SubmissionTech, ControlTime (총 6개 차트)

### ✅ 2) ChartCard hover 시 살짝 확대/강조 애니메이션

**현상**: 차트 카드에 마우스를 올려도 시각적 피드백이 없어 인터랙션이 밋밋함
**해결**: `ChartCard` 컴포넌트에 CSS transition 추가

```tsx
// ChartCard.tsx — 카드 wrapper div에 적용
className="... transition-all duration-300 ease-out hover:scale-[1.01] hover:border-white/[0.12] hover:shadow-lg hover:shadow-black/20"
```

**세부 사항:**
- `hover:scale-[1.01]` — 1% 확대 (너무 크면 레이아웃이 흔들리므로 미세하게)
- `hover:border-white/[0.12]` — 테두리가 살짝 밝아져 선택된 느낌
- `hover:shadow-lg hover:shadow-black/20` — 아래쪽 그림자로 떠오르는 느낌
- `transition-all duration-300 ease-out` — 부드러운 전환 (300ms)
- **영향 범위**: 모든 ChartCard (17개) — `ChartCard.tsx` 한 곳만 수정하면 전체 적용

---

## 1. Overview 탭

### ✅ 1.1 Finish Methods — Tooltip 라벨 개선

| 항목 | 내용 |
|------|------|
| **현재** | hover 시 `Count: 245` 형태로 표시 |
| **변경** | `KO/TKO: 245`, `M-DEC: 87` 처럼 method 이름 + count 표시 |
| **수정 파일** | `overview/FinishMethodsChart.tsx` |
| **수정 내용** | Tooltip `formatter`에서 반환값의 두 번째 요소(label)를 `'Count'` 대신 실제 `method_category` 이름으로 변경 |

### ✅ 1.2 Weight Class Activity — 통합 뷰 + finish 데이터 보정

| 항목 | 내용 |
|------|------|
| ~~**현재 문제 1**~~ | ~~X축 라벨에서 `weight` → `w`로 축약해서 "Lightw", "Middlew" 등 어색하게 잘림~~ |
| ~~**현재 문제 2**~~ | ~~Fights/Rates 2개 탭으로 분리되어 있음~~ |
| ~~**현재 문제 3**~~ | ~~Scatter dot이 `ko_tko_count`/`ko_tko_rate`만 표시 (SUB 미포함)~~ |
| **수정 파일** | `overview/WeightClassActivityChart.tsx` |

**완료된 변경 내용:**
1. **X축 축약**: `ABBREVIATIONS` 맵 사용 (`"Light"`, `"W.Straw"` 등)
2. **PillTabs 제거**: 단일 Bar 차트(total_fights)로 통합
3. **Scatter dot**: `finish_count` (= `ko_tko_count + sub_count`) 로 변경
4. **커스텀 Tooltip**: `short` 제거, 체급 전체 이름 표시, Finishes 아래 KO/TKO · SUB 들여쓰기 표시

### 🔲 1.3 Fight Duration — 평균 종료 시간 (백엔드 필요)

| 항목 | 상태 |
|------|------|
| ✅ **Tooltip cursor** | `cursor={{ fill: 'rgba(255,255,255,0.04)' }}` 적용 완료 |
| ✅ **그래프 margin** | `margin.top` 5 → 20으로 조정, ReferenceLine 라벨 잘림 해소 |
| 🔲 **ReferenceLine 라벨** | `Avg R2.3 (3:42)` 형태로 평균 종료 시간 표시 — **백엔드 수정 필요** |

> **백엔드 변경 필요**: `repositories.py`에 평균 종료 시간 계산 쿼리 추가, `dto.py`에 `avg_time` 필드 추가

### 🔲 1.4 Leaderboard — UFC 전적만 표시 (데이터 이슈)

| 항목 | 내용 |
|------|------|
| **현재 문제** | 체급 필터 없이 전체 조회 시 `fighter.wins` (MMA 전체 커리어 전적) 사용 |
| **수정 파일** | `src/dashboard/repositories.py` |

**변경 내용: "All MMA / UFC Only" 토글 필터 추가**

| 수정 위치 | 내용 |
|-----------|------|
| **프론트: `overview/LeaderboardChart.tsx`** | 기존 PillTabs 옆에 "All MMA / UFC Only" 토글 추가 |
| **프론트: `services/dashboardApi.ts`** | `getOverview(weightClassId?, ucfOnly?)` 파라미터 추가 |
| **백엔드: `api/dashboard/routes.py`** | overview 엔드포인트에 `ufc_only: bool = False` 쿼리 파라미터 추가 |
| **백엔드: `dashboard/services.py`** | `ufc_only` 값에 따라 다른 leaderboard 쿼리 호출 |
| **백엔드: `dashboard/repositories.py`** | `get_leaderboard_wins`, `get_leaderboard_winrate`에 `ufc_only` 분기 추가 |

---

## 2. Striking 탭

### ✅ 2.1 Strike Targets — Radar 차트 개선

| 항목 | 내용 |
|------|------|
| ~~**현재 문제 1**~~ | ~~Radar 배경에 100000, 200000 등 큰 숫자가 보여 지저분함~~ |
| ~~**현재 문제 2**~~ | ~~Tooltip에 `Landed: 12345`만 표시, 비율 정보 없음~~ |
| **수정 파일** | `striking/StrikeTargetsChart.tsx` |

**완료된 변경 내용:**
1. `PolarRadiusAxis tick={false}` — 배경 숫자 제거
2. Tooltip `formatter` — `12,345 (42.3%)` 형태로 전체 합산 대비 비율 표시

> **이름 검토**: "Strike Targets" 유지 vs "Sig. Strike Distribution" — **피드백 필요**

### ✅ 2.2 Striking Accuracy — Bullet 차트 정렬 + hover

| 항목 | 상태 |
|------|------|
| ✅ **바 겹침 수정** | 두 Bar 모두 `barSize={16}`, Attempted `fillOpacity={0.15}`, `barGap={-16}` |
| ✅ **hover 스타일** | `cursor={{ fill: 'rgba(255,255,255,0.04)' }}` |
| ✅ **최소 경기 수** | 백엔드 `HAVING` 조건 5경기 → **10경기**로 변경 완료 |

### ✅ 2.3 KO/TKO Leaders — hover 개선

| 항목 | 내용 |
|------|------|
| ~~**현재 문제**~~ | ~~hover 시 흰색 배경 + Tooltip에 중복 count 표시~~ |

**완료**: `cursor={false}` 적용 — LabelList로 이미 숫자 표시 중이므로 흰색 커서만 제거

---

## 3. Grappling 탭

### ✅ 3.1 Takedown Accuracy — Striking Accuracy와 동일 수정

**완료된 변경 내용:**
- 바 겹침 정렬: 두 Bar 모두 `barSize={16}`, Attempted `fillOpacity={0.15}`, `barGap={-16}`
- hover 스타일: `cursor={{ fill: 'rgba(255,255,255,0.04)' }}`
- 최소 경기 수: 백엔드 5경기 → **10경기** 변경 완료

### ✅ 3.2 Submission Techniques — hover 개선

**완료**: `cursor={{ fill: 'rgba(255,255,255,0.04)' }}` 적용

### ✅ 3.3 Control Time — hover + 체급 축약 개선

**완료된 변경 내용:**
- `cursor={{ fill: 'rgba(255,255,255,0.04)' }}` 적용
- 체급 축약: `ABBREVIATIONS` 맵 사용 (`replace('weight','w')` → `"Light"`, `"W.Straw"` 등)

### ✅ 3.4 Ground Strikes — 축 라벨 개선

**완료된 변경 내용:**
1. 축 라벨 색상: `#52525b` → `#a1a1aa` (zinc-400), fontSize 10 → 11
2. Tooltip `labelFormatter`로 선수 이름 이미 표시됨 (기존 구현 확인 완료)

### ✅ 3.5 Submission Efficiency — Ground Strikes와 동일

**완료**: 축 라벨 색상 `#a1a1aa`, fontSize 11로 변경

---

## 수정 범위 요약

### 프론트엔드 수정

| # | 파일 | 수정 내용 | 상태 |
|---|------|-----------|------|
| 1 | `ChartCard.tsx` | hover 애니메이션 (scale, border, shadow) | ✅ |
| 2 | `overview/FinishMethodsChart.tsx` | Tooltip 라벨을 method 이름으로 변경 | ✅ |
| 3 | `overview/WeightClassActivityChart.tsx` | PillTabs 제거, X축 축약, dot→finish_count, 커스텀 Tooltip | ✅ |
| 4 | `overview/FightDurationChart.tsx` | cursor 스타일 + margin 조정 | ✅ |
| 5 | `overview/LeaderboardChart.tsx` | "All MMA / UFC Only" 토글 필터 추가 | 🔲 |
| 6 | `striking/StrikeTargetsChart.tsx` | Radar 숫자 제거, Tooltip 비율 추가 | ✅ |
| 7 | `striking/StrikingAccuracyChart.tsx` | 바 겹침 수정, cursor 수정 | ✅ |
| 8 | `striking/KoTkoLeadersChart.tsx` | cursor={false} 적용 | ✅ |
| 9 | `grappling/TakedownChart.tsx` | 바 겹침 수정, cursor 수정 | ✅ |
| 10 | `grappling/SubmissionTechChart.tsx` | cursor 스타일 수정 | ✅ |
| 11 | `grappling/ControlTimeChart.tsx` | cursor + 체급 축약 개선 | ✅ |
| 12 | `grappling/GroundStrikesChart.tsx` | 축 라벨 밝게 | ✅ |
| 13 | `grappling/SubmissionEfficiencyChart.tsx` | 축 라벨 밝게 | ✅ |

### 백엔드 수정

| # | 파일 | 수정 내용 | 상태 |
|---|------|-----------|------|
| 1 | `src/dashboard/repositories.py` | 최소 경기 수 5 → 10 변경 (6개 쿼리) | ✅ |
| 2 | `src/dashboard/repositories.py` | Leaderboard: UFC Only 토글 분기 추가 | 🔲 |
| 3 | `src/dashboard/repositories.py` | FightDuration: 평균 종료 시간 쿼리 추가 | 🔲 |
| 4 | `src/dashboard/dto.py` | FightDuration DTO에 `avg_time` 필드 추가 | 🔲 |

---

## 미완료 항목 (백엔드 수정 필요)

1. **Fight Duration avg_time** — 백엔드에 평균 종료 시간 계산 추가 필요
2. **Leaderboard UFC Only 토글** — 프론트 + 백엔드 모두 수정 필요

## 피드백 필요 항목

1. **Strike Targets 카드 이름**: "Strike Targets" 유지 vs 다른 이름 (예: "Sig. Strike Distribution")?
