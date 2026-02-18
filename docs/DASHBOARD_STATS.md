# Dashboard 통계 화면 기획

MMA Savant 대시보드에 표시할 통계 자료 목록 및 API 구현 가이드

---

## API 아키텍처

레이아웃: **Layout E (Bento Grid)** 확정 — `docs/dashboard-prototype-E.html` 참조

### 엔드포인트 (탭별 Aggregate)

| Tab | Endpoint | 설명 | 추가 파라미터 |
|-----|----------|------|-------------|
| Home | `GET /api/dashboard/home` | 요약 카드 + 최근/향후 이벤트 + 랭킹 | — |
| Overview | `GET /api/dashboard/overview` | 피니시·체급·이벤트·리더보드·라운드 | `weight_class_id`, `ufc_only` |
| Striking | `GET /api/dashboard/striking` | 타격 부위·정확도·KO/TKO·경기당 유효타격 | `weight_class_id`, `min_fights`, `limit` |
| Grappling | `GET /api/dashboard/grappling` | 테이크다운·서브미션·컨트롤타임·그라운드 | `weight_class_id`, `min_fights`, `limit` |

### 공통 파라미터

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| `weight_class_id` | int? | None | 체급 필터. 미전송 시 전체 |
| `ufc_only` | bool | false | Leaderboard: UFC 전적만 집계 (Overview 전용) |
| `min_fights` | int | 10 | 최소 경기 수 필터 (Striking/Grappling) |
| `limit` | int | 10 | TOP N 반환 수 (Striking/Grappling) |

### 공통 규칙

**weight_class_id 필터**
- `?weight_class_id=3` 전송 시 해당 체급만 집계, 미전송 시 전체
- 탭 내 일부 차트는 필터 무시 (모든 체급 비교가 목적인 차트)

**min_fights 필터 (최소 경기 수)**
- 백엔드: 3가지 기준(10/20/30)으로 각각 쿼리하여 `{min10, min20, min30}` 구조로 한 번에 반환
- 프론트엔드: PillTabs(`10+ Fights` / `20+ Fights` / `30+ Fights`)로 클라이언트 전환 (API 재요청 없음)
- 적용 차트: 3-2 타격 정확도, 3-4 경기당 유효타격, 4-1 테이크다운 성공률

**ufc_only 필터 (UFC Only 토글)**
- `ufc_only=true`: `fighter_match` 테이블 기반 집계 (UFC 경기만 포함)
- `ufc_only=false` (기본값): `fighter` 테이블 직접 조회 (MMA 전체 커리어 전적)
- 프론트엔드: 토글 스위치(All MMA ↔ UFC Only)로 전환, 기본값 **UFC Only**

**TOP N (리더보드 계열) 처리**
- 항상 **10건** 반환 — 프론트엔드에서 기본 5건만 표시, "더보기" 클릭 시 나머지 5건 노출
- 별도 API 재요청 없이 클라이언트 측에서 처리

**Open Weight / Catch Weight 제외**
- 체급 비교 차트(2-2 Weight Class Activity, 4-3 Control Time)에서 프론트엔드 필터링으로 제외

---

## 데이터 소스

현재 DB 테이블 기반으로 모든 항목 구현 가능

| 테이블 | 활용 데이터 |
|--------|------------|
| `fighter` | name, wins, losses, draws, height, weight, reach, stance, birthdate, belt |
| `event` | name, location, event_date |
| `match` | method, result_round, time, is_main_event, weight_class_id, event_id |
| `fighter_match` | fighter_id, match_id, result (win/loss/draw/nc) |
| `weight_class` | name (12개 체급) |
| `ranking` | fighter_id, weight_class_id, ranking (0=챔피언, 1-15) |
| `match_statistics` | knockdowns, sig_str_landed/attempted, td_landed/attempted, submission_attempts, control_time_seconds |
| `strike_detail` | head/body/leg/clinch/ground strikes (landed/attempts) |

---

## Tab 1: Home

- **Endpoint**: `GET /api/dashboard/home`
- **필터**: 없음

### 1-1. 요약 카드 (Summary Cards)

대시보드 최상단에 핵심 수치를 카드 형태로 표시:

| 카드 | 쿼리 |
|------|------|
| 총 선수 수 | `SELECT COUNT(*) FROM fighter` |
| 총 경기 수 | `SELECT COUNT(*) FROM match` |
| 총 이벤트 수 | `SELECT COUNT(*) FROM event` |

### 1-2. 최근 이벤트 (Recent Events)

- **표시 형태**: 카드 리스트 (최근 5개)
- **데이터**: 이벤트명, 장소, 날짜, 경기 수, 메인 이벤트 정보
- **참고 쿼리**:
  ```sql
  SELECT
    e.id,
    e.name,
    e.location,
    e.event_date,
    COUNT(m.id) AS total_fights,
    -- 메인 이벤트 정보
    (
      SELECT f1.name || ' vs ' || f2.name
      FROM match main_m
      JOIN fighter_match fm1 ON main_m.id = fm1.match_id
      JOIN fighter_match fm2 ON main_m.id = fm2.match_id AND fm1.id < fm2.id
      JOIN fighter f1 ON fm1.fighter_id = f1.id
      JOIN fighter f2 ON fm2.fighter_id = f2.id
      WHERE main_m.event_id = e.id AND main_m.is_main_event = true
      LIMIT 1
    ) AS main_event
  FROM event e
  LEFT JOIN match m ON e.id = m.event_id
  WHERE e.event_date <= CURRENT_DATE
    AND e.event_date IS NOT NULL
  GROUP BY e.id, e.name, e.location, e.event_date
  ORDER BY e.event_date DESC
  LIMIT 5;
  ```

### 1-3. 향후 이벤트 (Upcoming Events)

- **표시 형태**: 카드 리스트 (향후 5개)
- **데이터**: 이벤트명, 장소, 날짜, D-day 카운트
- **참고 쿼리**:
  ```sql
  SELECT
    e.id,
    e.name,
    e.location,
    e.event_date,
    e.event_date - CURRENT_DATE AS days_until
  FROM event e
  WHERE e.event_date > CURRENT_DATE
    AND e.event_date IS NOT NULL
  ORDER BY e.event_date ASC
  LIMIT 5;
  ```

### 1-4. 체급별 챔피언 & 랭킹 (Division Rankings)

- **표시 형태**: 카드형 리스트 (체급 선택 드롭다운)
- **데이터 소스**: `ranking` + `fighter` + `weight_class` 조인
- **설명**: 현재 UFC 랭킹 현황. ranking=0은 챔피언, 1-15는 랭커
- **응답**: 전체 체급 랭킹을 한 번에 반환, 프론트엔드에서 드롭다운으로 체급 전환
- **참고 쿼리**:
  ```sql
  SELECT
    wc.id AS weight_class_id,
    wc.name AS weight_class,
    r.ranking,
    f.name AS fighter_name,
    f.wins, f.losses, f.draws
  FROM ranking r
  JOIN fighter f ON r.fighter_id = f.id
  JOIN weight_class wc ON r.weight_class_id = wc.id
  ORDER BY wc.id, r.ranking;
  ```

### Home 응답 구조

```json
{
  "summary": {
    "total_fighters": 3892,
    "total_matches": 7214,
    "total_events": 742
  },
  "recent_events": [
    {
      "id": 740,
      "name": "UFC 310",
      "location": "Las Vegas, Nevada",
      "event_date": "2024-12-07",
      "total_fights": 13,
      "main_event": "Pantoja vs Asakura"
    }
  ],
  "upcoming_events": [
    {
      "id": 741,
      "name": "UFC 311",
      "location": "Los Angeles, California",
      "event_date": "2025-01-18",
      "days_until": 42
    }
  ],
  "rankings": [
    {
      "weight_class_id": 4,
      "weight_class": "Lightweight",
      "fighters": [
        { "ranking": 0, "fighter_name": "Islam Makhachev", "wins": 26, "losses": 1, "draws": 0 },
        { "ranking": 1, "fighter_name": "Arman Tsarukyan", "wins": 22, "losses": 3, "draws": 0 }
      ]
    }
  ]
}
```

---

## Tab 2: Overview

- **Endpoint**: `GET /api/dashboard/overview?weight_class_id=&ufc_only=`
- **포함 항목**: 5개 (피니시 분포, 체급별 활동, 이벤트 추이, 리더보드, 종료 라운드)

### 2-1. 피니시 방법 분포 (Finish Method Breakdown)

- **차트 유형**: 도넛/파이 차트
- **데이터 소스**: `match.method`
- **분류 기준**: KO, TKO, SUB, U-DEC(만장일치 판정), S-DEC(스플릿 판정), M-DEC(다수 판정)
- **설명**: UFC 전체 경기의 "판정 vs 피니시" 비율
- **weight_class 필터**: O
- **참고 쿼리**:
  ```sql
  SELECT
    CASE
      WHEN method LIKE 'KO-%' THEN 'KO'
      WHEN method LIKE 'TKO-%' THEN 'TKO'
      WHEN method LIKE 'SUB-%' THEN 'SUB'
      WHEN method LIKE 'U-DEC%' THEN 'U-DEC'
      WHEN method LIKE 'S-DEC%' THEN 'S-DEC'
      WHEN method LIKE 'M-DEC%' THEN 'M-DEC'
      ELSE 'Other'
    END AS method_category,
    COUNT(*) AS count
  FROM match m
  WHERE m.method IS NOT NULL
    AND (:weight_class_id IS NULL OR m.weight_class_id = :weight_class_id)
  GROUP BY method_category
  ORDER BY count DESC;
  ```

### 2-2. 체급별 경기 수 & 피니시 분포 (Weight Class Activity)

- **차트 유형**: ComposedChart — 수평 바(경기 수) + 도트(비율 %)
  - Recharts `ComposedChart` + `Bar` + `Scatter` 조합
  - 커스텀 Tooltip으로 Total Fights, Finishes(%), KO/TKO, SUB 상세 표시
- **데이터 소스**: `match` + `weight_class` 조인
- **설명**: 어떤 체급이 가장 활발하고 액션이 많은지 비교. KO/TKO/SUB 비율까지 한눈에 파악
- **weight_class 필터**: X — 모든 체급 비교가 목적
- **프론트엔드 필터**: Open Weight, Catch Weight 제외
- **참고 쿼리**:
  ```sql
  SELECT
    wc.name AS weight_class,
    COUNT(*) AS total_fights,
    COUNT(CASE WHEN m.method LIKE 'KO-%' THEN 1 END) AS ko_count,
    COUNT(CASE WHEN m.method LIKE 'TKO-%' THEN 1 END) AS tko_count,
    COUNT(CASE WHEN m.method LIKE 'SUB-%' THEN 1 END) AS sub_count,
    ROUND(
      COUNT(CASE WHEN m.method LIKE 'KO-%' OR m.method LIKE 'TKO-%' OR m.method LIKE 'SUB-%' THEN 1 END) * 100.0 / COUNT(*), 1
    ) AS finish_rate,
    ROUND(COUNT(CASE WHEN m.method LIKE 'KO-%' THEN 1 END) * 100.0 / COUNT(*), 1) AS ko_rate,
    ROUND(COUNT(CASE WHEN m.method LIKE 'TKO-%' THEN 1 END) * 100.0 / COUNT(*), 1) AS tko_rate,
    ROUND(COUNT(CASE WHEN m.method LIKE 'SUB-%' THEN 1 END) * 100.0 / COUNT(*), 1) AS sub_rate
  FROM match m
  JOIN weight_class wc ON m.weight_class_id = wc.id
  WHERE m.method IS NOT NULL
  GROUP BY wc.name
  ORDER BY total_fights DESC;
  ```

### 2-3. 연도별 이벤트 수 추이 (UFC Growth Timeline)

- **차트 유형**: 라인/에어리어 차트
- **데이터 소스**: `event.event_date`
- **설명**: UFC의 성장 추이를 시각적으로 보여줌
- **weight_class 필터**: X — 이벤트에 여러 체급 포함
- **참고 쿼리**:
  ```sql
  SELECT
    EXTRACT(YEAR FROM event_date) AS year,
    COUNT(*) AS event_count
  FROM event
  WHERE event_date IS NOT NULL
  GROUP BY year
  ORDER BY year;
  ```

### 2-4. 최다승 & 최고 승률 TOP (Fighter Leaderboard)

- **차트 유형**: 바 차트 (탭으로 최다승/최고승률 전환)
- **데이터 소스**: `fighter.wins`, `fighter.losses`, `fighter.draws`
- **설명**: 역대 최고의 선수를 한눈에 확인
- **인터랙션** (프론트엔드):
  - 탭: 최다승 / 최고승률 전환
  - 최고승률 탭에 최소 경기 수 PillTabs: `10+ Fights` | `20+ Fights` | `30+ Fights`
  - 토글 스위치: `All MMA` ↔ `UFC Only` (기본값: UFC Only)
  - "더보기" 버튼: 10건 중 나머지 5건 표시
- **weight_class 필터**: O
- **ufc_only 필터**: O — 3가지 분기:
  - `weight_class_id` 있음 → `fighter_match → match` JOIN (이미 UFC only)
  - `ufc_only=true` (기본) → `fighter_match` JOIN (weight_class 없이)
  - `ufc_only=false` → `fighter` 테이블 직접 조회 (MMA 전체 커리어)
- **응답에 4세트 포함**: wins + winrate_min10 + winrate_min20 + winrate_min30
- **참고 쿼리**:
  ```sql
  -- 최다승 TOP (전체) — win_rate 포함하여 shape 통일
  SELECT name, wins, losses, draws,
    ROUND(wins * 100.0 / NULLIF(wins + losses + draws, 0), 1) AS win_rate
  FROM fighter
  ORDER BY wins DESC
  LIMIT 10;

  -- 최다승 TOP (체급 필터 시) — win_rate 포함
  SELECT
    f.name,
    COUNT(CASE WHEN fm.result = 'win' THEN 1 END) AS wins,
    COUNT(CASE WHEN fm.result = 'loss' THEN 1 END) AS losses,
    COUNT(CASE WHEN fm.result = 'draw' THEN 1 END) AS draws,
    ROUND(
      COUNT(CASE WHEN fm.result = 'win' THEN 1 END) * 100.0 /
      NULLIF(COUNT(*), 0), 1
    ) AS win_rate
  FROM fighter f
  JOIN fighter_match fm ON f.id = fm.fighter_id
  JOIN match m ON fm.match_id = m.id
  WHERE m.weight_class_id = :weight_class_id
  GROUP BY f.id, f.name
  ORDER BY wins DESC
  LIMIT 10;

  -- 최고 승률 TOP (min_fights = 10, 20, 30 각각 실행)
  SELECT
    name, wins, losses, draws,
    ROUND(wins * 100.0 / NULLIF(wins + losses + draws, 0), 1) AS win_rate
  FROM fighter
  WHERE (wins + losses + draws) >= :min_fights
  ORDER BY win_rate DESC
  LIMIT 10;

  -- 최고 승률 TOP (체급 필터 시)
  SELECT
    f.name,
    COUNT(CASE WHEN fm.result = 'win' THEN 1 END) AS wins,
    COUNT(CASE WHEN fm.result = 'loss' THEN 1 END) AS losses,
    COUNT(CASE WHEN fm.result = 'draw' THEN 1 END) AS draws,
    ROUND(
      COUNT(CASE WHEN fm.result = 'win' THEN 1 END) * 100.0 /
      NULLIF(COUNT(*), 0), 1
    ) AS win_rate
  FROM fighter f
  JOIN fighter_match fm ON f.id = fm.fighter_id
  JOIN match m ON fm.match_id = m.id
  WHERE m.weight_class_id = :weight_class_id
  GROUP BY f.id, f.name
  HAVING COUNT(*) >= :min_fights
  ORDER BY win_rate DESC
  LIMIT 10;
  ```

### 2-5. 경기 종료 라운드 분포 (Fight Duration Analysis)

- **차트 유형**: 세로 바 차트 + ReferenceLine(평균 종료 시간)
  - X축: R1~R5 (이산값)
  - Y축: 비율(%) — 각 바에 비율(%)과 건수를 툴팁으로 표시
  - ReferenceLine: 평균 종료 시간 (점선, `Avg M:SS` 형식)
  - Recharts `BarChart` + `ReferenceLine` 조합
- **데이터 소스**: `match.result_round`, `match.time`
- **설명**: "평균적으로 UFC 경기는 몇 라운드에서 끝나는가"
- **weight_class 필터**: O
- **참고 쿼리**:
  ```sql
  -- 라운드별 분포
  SELECT
    result_round,
    COUNT(*) AS fight_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) AS percentage
  FROM match
  WHERE result_round IS NOT NULL
    AND (:weight_class_id IS NULL OR weight_class_id = :weight_class_id)
  GROUP BY result_round
  ORDER BY result_round;

  -- 평균 종료 라운드 (ReferenceLine용)
  SELECT ROUND(AVG(result_round)::numeric, 1) AS avg_round
  FROM match
  WHERE result_round IS NOT NULL
    AND (:weight_class_id IS NULL OR weight_class_id = :weight_class_id);

  -- 평균 종료 시간 (초 단위, ReferenceLine 라벨용)
  SELECT ROUND(AVG(
    CAST(SPLIT_PART(time, ':', 1) AS INTEGER) * 60 +
    CAST(SPLIT_PART(time, ':', 2) AS INTEGER)
  ))::int AS avg_time_seconds
  FROM match
  WHERE time IS NOT NULL AND result_round IS NOT NULL
    AND (:weight_class_id IS NULL OR weight_class_id = :weight_class_id);
  ```

### Overview 응답 구조

```json
{
  "finish_methods": [
    { "method_category": "TKO", "count": 2847 }
  ],
  "weight_class_activity": [
    {
      "weight_class": "Lightweight",
      "total_fights": 1120,
      "ko_tko_count": 392, "sub_count": 168,
      "finish_rate": 50.0, "ko_tko_rate": 35.0, "sub_rate": 15.0
    }
  ],
  "events_timeline": [
    { "year": 2024, "event_count": 42 }
  ],
  "leaderboard": {
    "wins": [
      { "name": "Jim Miller", "wins": 26, "losses": 18, "draws": 0, "win_rate": 59.1 }
    ],
    "winrate_min10": [
      { "name": "Khabib", "wins": 29, "losses": 0, "draws": 0, "win_rate": 100.0 }
    ],
    "winrate_min20": [],
    "winrate_min30": []
  },
  "fight_duration": {
    "rounds": [
      { "result_round": 1, "fight_count": 2890, "percentage": 40.1 }
    ],
    "avg_round": 2.1,
    "avg_time_seconds": 402
  }
}
```

---

## Tab 3: Striking

- **Endpoint**: `GET /api/dashboard/striking?weight_class_id=&min_fights=10&limit=10`
- **포함 항목**: 4개 (타격 부위, 타격 정확도, KO/TKO TOP, 경기당 유효타격)

### 3-1. 타격 부위별 분포 (Strike Target Distribution)

- **차트 유형**: 레이더 차트 (RadarChart)
  - 5개 축: Head / Body / Leg / Clinch / Ground
  - Recharts `RadarChart` + `PolarGrid` + `Radar` 조합
- **데이터 소스**: `strike_detail` (head/body/leg/clinch/ground strikes)
- **설명**: UFC 선수들이 어디를 가장 많이 공격하는지 시각화
- **weight_class 필터**: O
- **참고 쿼리**:
  ```sql
  SELECT
    SUM(sd.head_strikes_landed) AS head,
    SUM(sd.body_strikes_landed) AS body,
    SUM(sd.leg_strikes_landed) AS leg,
    SUM(sd.clinch_strikes_landed) AS clinch,
    SUM(sd.ground_strikes_landed) AS ground
  FROM strike_detail sd
  JOIN fighter_match fm ON sd.fighter_match_id = fm.id
  JOIN match m ON fm.match_id = m.id
  WHERE (:weight_class_id IS NULL OR m.weight_class_id = :weight_class_id);
  ```

### 3-2. 타격 정확도 TOP (Striking Accuracy Leaders)

- **차트 유형**: Bullet Chart (시도 대비 적중 overlay 바)
  - 넓은 반투명 바: attempted, 좁은 채색 바: landed (barGap으로 겹침)
  - 오른쪽 label로 accuracy% 표시
  - Recharts `BarChart`(vertical) — 2개 `Bar` overlay (`barGap={-26}`)
- **데이터 소스**: `match_statistics.sig_str_landed`, `match_statistics.sig_str_attempted`
- **설명**: 유효 타격 정확도가 가장 높은 선수. 시도 대비 적중을 직관적으로 비교
- **min_fights 필터**: 10/20/30 PillTabs (백엔드에서 3세트 반환, 프론트 전환)
- **weight_class 필터**: O
- **참고 쿼리**:
  ```sql
  SELECT
    f.name,
    SUM(ms.sig_str_landed) AS total_sig_landed,
    SUM(ms.sig_str_attempted) AS total_sig_attempted,
    ROUND(SUM(ms.sig_str_landed) * 100.0 / NULLIF(SUM(ms.sig_str_attempted), 0), 1) AS accuracy
  FROM match_statistics ms
  JOIN fighter_match fm ON ms.fighter_match_id = fm.id
  JOIN fighter f ON fm.fighter_id = f.id
  JOIN match m ON fm.match_id = m.id
  WHERE (:weight_class_id IS NULL OR m.weight_class_id = :weight_class_id)
  GROUP BY f.id, f.name
  HAVING COUNT(DISTINCT fm.match_id) >= 5 AND SUM(ms.sig_str_attempted) > 0
  ORDER BY accuracy DESC
  LIMIT 10;
  ```

### 3-3. KO/TKO 피니시 TOP (KO/TKO Finish Leaders)

- **차트 유형**: 수평 바 차트
- **데이터 소스**: `match.method` + `fighter_match.result`
- **설명**: KO/TKO 피니시를 가장 많이 기록한 선수
- **weight_class 필터**: O
- **참고 쿼리**:
  ```sql
  SELECT
    f.name,
    COUNT(CASE WHEN m.method LIKE 'KO-%' THEN 1 END) AS ko_finishes,
    COUNT(CASE WHEN m.method LIKE 'TKO-%' THEN 1 END) AS tko_finishes,
    COUNT(*) AS total_ko_tko
  FROM fighter_match fm
  JOIN fighter f ON fm.fighter_id = f.id
  JOIN match m ON fm.match_id = m.id
  WHERE fm.result = 'win'
    AND (m.method LIKE 'KO-%' OR m.method LIKE 'TKO-%')
    AND (:weight_class_id IS NULL OR m.weight_class_id = :weight_class_id)
  GROUP BY f.id, f.name
  ORDER BY total_ko_tko DESC
  LIMIT 10;
  ```

### 3-4. 경기당 유효타격 TOP (Sig. Strikes Per Fight Leaders)

- **차트 유형**: Lollipop Chart (줄기 + 점)
  - Bar: 얇은 stem (barSize={3}), Scatter: 끝점 dot
  - ReferenceLine: 평균값 점선 (라벨: `insideBottomRight`로 최상위 선수와 겹침 방지)
  - 커스텀 Tooltip: `Sig/Fight: value` 단일 항목만 표시
  - Recharts `ComposedChart`(vertical) — `Bar`(stem) + `Scatter`(dot)
- **데이터 소스**: `match_statistics.sig_str_landed` + 경기 수
- **설명**: 경기당 유효타격이 가장 많은 선수. 볼륨 스트라이커 식별 지표
- **min_fights 필터**: 10/20/30 PillTabs (백엔드에서 3세트 반환, 프론트 전환)
- **weight_class 필터**: O
- **참고 쿼리**:
  ```sql
  SELECT
    f.name,
    ROUND(SUM(ms.sig_str_landed)::numeric / COUNT(DISTINCT fm.match_id), 2) AS sig_str_per_fight,
    COUNT(DISTINCT fm.match_id) AS total_fights
  FROM match_statistics ms
  JOIN fighter_match fm ON ms.fighter_match_id = fm.id
  JOIN fighter f ON fm.fighter_id = f.id
  JOIN match m ON fm.match_id = m.id
  WHERE (:weight_class_id IS NULL OR m.weight_class_id = :weight_class_id)
  GROUP BY f.id, f.name
  HAVING COUNT(DISTINCT fm.match_id) >= 5
  ORDER BY sig_str_per_fight DESC
  LIMIT 10;
  ```

### Striking 응답 구조

```json
{
  "strike_targets": [
    { "target": "Head", "landed": 185200 },
    { "target": "Body", "landed": 62400 },
    { "target": "Leg", "landed": 78600 },
    { "target": "Clinch", "landed": 34200 },
    { "target": "Ground", "landed": 41800 }
  ],
  "striking_accuracy": {
    "min10": [
      { "name": "Holloway", "total_sig_landed": 3245, "total_sig_attempted": 5226, "accuracy": 62.1 }
    ],
    "min20": [],
    "min30": []
  },
  "ko_tko_leaders": [
    { "name": "Derrick Lewis", "ko_tko_finishes": 21 }
  ],
  "sig_strikes_per_fight": {
    "min10": [
      { "name": "Max Holloway", "sig_str_per_fight": 7.49, "total_fights": 30 }
    ],
    "min20": [],
    "min30": []
  }
}
```

---

## Tab 4: Grappling

- **Endpoint**: `GET /api/dashboard/grappling?weight_class_id=&min_fights=10&limit=10`
- **포함 항목**: 5개 (테이크다운, 서브미션 기술, 컨트롤 타임, 그라운드 스트라이크, 서브미션 효율)

### 4-1. 테이크다운 성공률 TOP (Takedown Accuracy Leaders)

- **차트 유형**: Bullet Chart (시도 대비 성공 overlay 바)
  - 넓은 반투명 바: attempted, 좁은 채색 바: landed (barGap으로 겹침)
  - 오른쪽 label로 td_accuracy% 표시
  - Recharts `BarChart`(vertical) — 2개 `Bar` overlay (3-2와 동일 패턴, 색상만 green 계열)
- **데이터 소스**: `match_statistics.td_landed`, `match_statistics.td_attempted`
- **설명**: 테이크다운 성공률이 가장 높은 선수. 시도 대비 성공을 직관적으로 비교
- **min_fights 필터**: 10/20/30 PillTabs (백엔드에서 3세트 반환, 프론트 전환)
- **추가 조건**: 테이크다운 시도 10회 이상
- **weight_class 필터**: O
- **참고 쿼리**:
  ```sql
  SELECT
    f.name,
    SUM(ms.td_landed) AS total_td_landed,
    SUM(ms.td_attempted) AS total_td_attempted,
    ROUND(SUM(ms.td_landed) * 100.0 / NULLIF(SUM(ms.td_attempted), 0), 1) AS td_accuracy
  FROM match_statistics ms
  JOIN fighter_match fm ON ms.fighter_match_id = fm.id
  JOIN fighter f ON fm.fighter_id = f.id
  JOIN match m ON fm.match_id = m.id
  WHERE (:weight_class_id IS NULL OR m.weight_class_id = :weight_class_id)
  GROUP BY f.id, f.name
  HAVING COUNT(DISTINCT fm.match_id) >= 5 AND SUM(ms.td_attempted) >= 10
  ORDER BY td_accuracy DESC
  LIMIT 10;
  ```

### 4-2. 서브미션 기술 분포 (Submission Technique Breakdown)

- **차트 유형**: 가로 바 차트
- **데이터 소스**: `match.method` (SUB- 접두사 경기만 필터)
- **설명**: 어떤 서브미션 기술이 가장 많이 성공하는지
- **weight_class 필터**: O
- **참고 쿼리**:
  ```sql
  SELECT
    REPLACE(m.method, 'SUB-', '') AS technique,
    COUNT(*) AS count
  FROM match m
  WHERE m.method LIKE 'SUB-%'
    AND (:weight_class_id IS NULL OR m.weight_class_id = :weight_class_id)
  GROUP BY technique
  ORDER BY count DESC
  LIMIT 10;
  ```

### 4-3. 체급별 평균 컨트롤 타임 (Control Time by Weight Class)

- **차트 유형**: 바 차트 (체급별 평균 초 단위, M:SS로 표시)
- **데이터 소스**: `match_statistics.control_time_seconds` + `weight_class`
- **설명**: 어떤 체급에서 그라운드 컨트롤이 가장 많이 발생하는지
- **weight_class 필터**: X — 모든 체급 비교가 목적
- **프론트엔드 필터**: Open Weight, Catch Weight 제외
- **참고 쿼리**:
  ```sql
  SELECT
    wc.name AS weight_class,
    ROUND(AVG(ms.control_time_seconds), 0) AS avg_control_seconds,
    COUNT(DISTINCT fm.match_id) AS total_fights
  FROM match_statistics ms
  JOIN fighter_match fm ON ms.fighter_match_id = fm.id
  JOIN match m ON fm.match_id = m.id
  JOIN weight_class wc ON m.weight_class_id = wc.id
  WHERE ms.control_time_seconds > 0
  GROUP BY wc.name
  ORDER BY avg_control_seconds DESC;
  ```

### 4-4. 그라운드 스트라이크 TOP (Ground Strikes Leaders)

- **차트 유형**: Scatter Chart (버블)
  - X축: attempted (시도), Y축: landed (적중), Z축(버블 크기): accuracy
  - 대각선 ReferenceLine 2개: 100% 기준선, 70% 기준선
  - 버블 색상: accuracy ≥75 → green, ≥65 → cyan, else → purple
  - Recharts `ScatterChart` + `ZAxis` + `ReferenceLine`(segment)
- **데이터 소스**: `strike_detail.ground_strikes_landed`, `strike_detail.ground_strikes_attempts`
- **설명**: 그라운드 타격의 시도/적중/정확도를 3축으로 시각화
- **필터**: 최소 5경기 이상
- **weight_class 필터**: O
- **참고 쿼리**:
  ```sql
  SELECT
    f.name,
    SUM(sd.ground_strikes_landed) AS total_ground_landed,
    SUM(sd.ground_strikes_attempts) AS total_ground_attempted,
    ROUND(SUM(sd.ground_strikes_landed) * 100.0 / NULLIF(SUM(sd.ground_strikes_attempts), 0), 1) AS accuracy
  FROM strike_detail sd
  JOIN fighter_match fm ON sd.fighter_match_id = fm.id
  JOIN fighter f ON fm.fighter_id = f.id
  JOIN match m ON fm.match_id = m.id
  WHERE (:weight_class_id IS NULL OR m.weight_class_id = :weight_class_id)
  GROUP BY f.id, f.name
  HAVING COUNT(DISTINCT fm.match_id) >= 5 AND SUM(sd.ground_strikes_attempts) > 0
  ORDER BY total_ground_landed DESC
  LIMIT 10;
  ```

### 4-5. 서브미션 효율성 (Submission Efficiency)

- **차트 유형**: 산점도 + 대각선 기준선 + 선수 라벨
  - X축: 서브미션 시도 수, Y축: 서브미션 피니시 수
  - 대각선 ReferenceLine: 전체 평균 효율(피니시/시도) 비율
  - TOP 1 선수만 이름 라벨 표시, 나머지는 hover 툴팁
  - Recharts `ScatterChart` + `ReferenceLine`(segment) + `Label` 조합
- **데이터 소스**: `match_statistics.submission_attempts` + `match.method LIKE 'SUB-%'`
- **설명**: 서브미션을 많이 시도하는 선수가 실제로 피니시도 많이 하는가?
- **필터**: 서브미션 시도 5회 이상, 최소 경기 수 `min_fights` 적용 (기본 10)
- **weight_class 필터**: O
- **참고 쿼리**:
  ```sql
  SELECT
    f.name,
    SUM(ms.submission_attempts) AS total_sub_attempts,
    COUNT(CASE WHEN m.method LIKE 'SUB-%' AND fm.result = 'win' THEN 1 END) AS sub_finishes
  FROM match_statistics ms
  JOIN fighter_match fm ON ms.fighter_match_id = fm.id
  JOIN fighter f ON fm.fighter_id = f.id
  JOIN match m ON fm.match_id = m.id
  WHERE (:weight_class_id IS NULL OR m.weight_class_id = :weight_class_id)
  GROUP BY f.id, f.name
  HAVING SUM(ms.submission_attempts) >= 5
    AND COUNT(DISTINCT fm.match_id) >= 5
  ORDER BY sub_finishes DESC;
  -- LIMIT 없음 — 산점도 차트는 조건 충족 전체 선수 반환

  -- 평균 효율 비율 (기준선용)
  SELECT
    ROUND(
      SUM(sub_finishes)::numeric / NULLIF(SUM(total_sub_attempts), 0), 3
    ) AS avg_efficiency_ratio
  FROM (위 쿼리) sub;
  ```

### Grappling 응답 구조

```json
{
  "takedown_accuracy": {
    "min10": [
      { "name": "Khabib", "total_td_landed": 82, "total_td_attempted": 130, "td_accuracy": 63.2 }
    ],
    "min20": [],
    "min30": []
  },
  "submission_techniques": [
    { "technique": "Rear Naked Choke", "count": 412 }
  ],
  "control_time": [
    { "weight_class": "Heavyweight", "avg_control_seconds": 142, "total_fights": 780 }
  ],
  "ground_strikes": [
    { "name": "Khabib", "total_ground_landed": 389, "total_ground_attempted": 450, "accuracy": 86.4 }
  ],
  "submission_efficiency": {
    "fighters": [
      { "name": "C. Oliveira", "total_sub_attempts": 42, "sub_finishes": 8 }
    ],
    "avg_efficiency_ratio": 0.178
  }
}
```

---

## 구현 참고사항

### 백엔드

- **파일 구조**: `src/dashboard/` (dto.py, repositories.py, services.py, exceptions.py) + `src/api/dashboard/routes.py`
- **패턴**: Repository → Service → Router (기존 프로젝트 컨벤션)
- **Redis 캐싱**: TTL 7일. 캐시 키 패턴: `dashboard:{tab}:{weight_class_id|all}` (overview는 `:ufc` 접미사 추가)
- **최소 경기 수**: 기본값 10경기. PillTabs 대상 차트는 10/20/30으로 3세트 반환
- **TOP N 항목**: 항상 10건 반환 (프론트엔드에서 5/10 전환)
- **weight_class 필터 무시 항목**: 2-2 체급별 활동, 2-3 이벤트 추이, 4-3 컨트롤 타임
- **Rankings**: Home 응답에 전체 체급 랭킹 포함 (프론트엔드 드롭다운으로 체급 전환, API 재요청 없음)
- **Leaderboard**: overview 응답에 4세트 포함 (wins, winrate_min10, winrate_min20, winrate_min30) + `ufc_only` 파라미터

### 프론트엔드

- Recharts — Bar/Line/Pie/Scatter/Radar/Composed 차트 사용
- 레이아웃: **Layout E (Bento Grid)** — `docs/dashboard-prototype-E.html` 참조
- 탭 전환: Home / Overview / Striking / Grappling (PillTabs)
- 체급 필터: WeightClassFilter 드롭다운 (Overview/Striking/Grappling 탭)
- **PillTabs (min_fights)**: `10+ Fights` / `20+ Fights` / `30+ Fights` — API 재요청 없이 프론트 전환
- **UFC Only 토글**: Leaderboard 차트에 `All MMA ↔ UFC Only` 스위치 (기본값: UFC Only, API 재호출)
- **Silent fetch**: 토글 변경 시 기존 데이터를 유지하면서 백그라운드 리패치 (로딩 스켈레톤 미표시)
- **Open Weight 제외**: Weight Class Activity, Control Time 차트에서 프론트엔드 필터링
- Recharts 컴포넌트 매핑:
  - 2-1 `PieChart` (도넛)
  - 2-2 `ComposedChart` (`Bar` + `Scatter`)
  - 2-3 `AreaChart`
  - 2-4 `BarChart` (Leaderboard)
  - 2-5 `BarChart` + `ReferenceLine`
  - 3-1 `RadarChart`
  - 3-2 `BarChart` (Bullet, 2-Bar overlay)
  - 3-3 `BarChart` (수평)
  - 3-4 `ComposedChart` (Lollipop, `Bar`+`Scatter`)
  - 4-1 `BarChart` (Bullet, 2-Bar overlay)
  - 4-3 `BarChart` (M:SS 포맷)
  - 4-4 `ScatterChart` (Bubble)
  - 4-5 `ScatterChart` + `ReferenceLine`(segment)
