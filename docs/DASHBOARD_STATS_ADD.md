# Dashboard 통계 화면 기획 — V2 추가분

기존 `DASHBOARD_STATS.md`에 추가할 차트 14개의 상세 기획

---

## 추가 엔드포인트

### 차트별 개별 엔드포인트 (추가분)

| Chart | Endpoint | 추가 파라미터 |
|-------|----------|-------------|
| 분야별 1등 | `GET /api/dashboard/chart/category-leaders` | — |
| 개최지 맵 | `GET /api/dashboard/chart/event-map` | — |
| 피니시율 추이 | `GET /api/dashboard/chart/finish-rate-trend` | `weight_class_id` |
| 국적 분포 | `GET /api/dashboard/chart/nationality-distribution` | `weight_class_id` |
| 체급별 키-리치 | `GET /api/dashboard/chart/physique-comparison` | — |
| 넉다운 리더 | `GET /api/dashboard/chart/knockdown-leaders` | `weight_class_id`, `limit` |
| 체급별 유효타격 | `GET /api/dashboard/chart/sig-strikes-by-weight-class` | — |
| 라운드별 타격 | `GET /api/dashboard/chart/round-strike-trend` | `weight_class_id` |
| 공방 효율 | `GET /api/dashboard/chart/strike-exchange-ratio` | `weight_class_id`, `min_fights`, `limit` |
| 스탠스별 승률 | `GET /api/dashboard/chart/stance-winrate` | `weight_class_id` |
| TD 시도 TOP | `GET /api/dashboard/chart/td-attempts-leaders` | `weight_class_id`, `min_fights`, `limit` |
| TD-SUB 상관 | `GET /api/dashboard/chart/td-sub-correlation` | `weight_class_id` |
| 체급별 TD | `GET /api/dashboard/chart/td-by-weight-class` | — |
| TD 디펜스 | `GET /api/dashboard/chart/td-defense-leaders` | `weight_class_id`, `min_fights`, `limit` |

### 공통 규칙 (추가분)

**weight_class 필터 미제공 차트 (추가)**
- 1-5 분야별 1등, 1-6 개최지 맵, 2-8 체급별 키-리치, 3-7 체급별 유효타격, 4-8 체급별 TD 시도율

**min_fights 필터 적용 차트 (추가)**
- 3-9 공방 효율, 4-6 경기당 TD 시도, 4-9 TD 디펜스

**필수 스키마 변경 (선행 작업)**
- `event` 테이블: `latitude FLOAT`, `longitude FLOAT` 컬럼 추가 → 1-6 개최지 맵
- `fighter` 테이블: `nationality VARCHAR` 컬럼 추가 → 2-7 국적 분포

---

## Tab 1: Home (추가)

### 1-5. 분야별 1등 선수들 (Category Leaders)

- **차트 유형**: 카드 그리드 (2×4 또는 2×3 Bento Grid)
  - 각 카드: 분야명 + 선수 이름 + 수치 + 아이콘/뱃지
  - 8개 분야, 카드 클릭 시 해당 선수 프로필 또는 관련 차트 탭으로 이동
- **데이터 소스**: 기존 차트 쿼리에서 TOP 1만 추출
- **설명**: "각 분야 역대 최고 선수는 누구인가?"를 한눈에 보여주는 종합 리더보드
- **weight_class 필터**: X — 전체 대상
- **8개 분야**:

| # | 분야 | 수치 | 출처 차트 |
|---|------|------|----------|
| 1 | 최다승 | wins | 2-4 Leaderboard |
| 2 | 최고 승률 (10경기+) | win_rate% | 2-4 Leaderboard |
| 3 | KO/TKO 최다 | ko_tko_finishes | 3-3 KO/TKO Leaders |
| 4 | 서브미션 최다 | sub_finishes | 4-5 Submission Efficiency |
| 5 | 타격 정확도 1위 (10경기+) | accuracy% | 3-2 Striking Accuracy |
| 6 | 경기당 유효타격 1위 (10경기+) | sig_str_per_fight | 3-4 Sig Strikes/Fight |
| 7 | 테이크다운 성공률 1위 (10경기+) | td_accuracy% | 4-1 Takedown Accuracy |
| 8 | 넉다운 최다 | total_knockdowns | 3-5 Knockdown Leaders (신규) |

- **참고 쿼리**:
  ```sql
  -- 1. 최다승
  SELECT f.name, f.wins
  FROM fighter f
  ORDER BY f.wins DESC
  LIMIT 1;

  -- 2. 최고 승률 (10경기 이상)
  SELECT f.name,
    ROUND(f.wins * 100.0 / NULLIF(f.wins + f.losses + f.draws, 0), 1) AS win_rate
  FROM fighter f
  WHERE (f.wins + f.losses + f.draws) >= 10
  ORDER BY win_rate DESC
  LIMIT 1;

  -- 3. KO/TKO 피니시 최다
  SELECT f.name, COUNT(*) AS ko_tko_finishes
  FROM fighter_match fm
  JOIN fighter f ON fm.fighter_id = f.id
  JOIN match m ON fm.match_id = m.id
  WHERE fm.result = 'win'
    AND (m.method LIKE 'KO-%' OR m.method LIKE 'TKO-%')
  GROUP BY f.id, f.name
  ORDER BY ko_tko_finishes DESC
  LIMIT 1;

  -- 4. 서브미션 피니시 최다
  SELECT f.name, COUNT(*) AS sub_finishes
  FROM fighter_match fm
  JOIN fighter f ON fm.fighter_id = f.id
  JOIN match m ON fm.match_id = m.id
  WHERE fm.result = 'win'
    AND m.method LIKE 'SUB-%'
  GROUP BY f.id, f.name
  ORDER BY sub_finishes DESC
  LIMIT 1;

  -- 5. 타격 정확도 1위 (10경기+)
  SELECT f.name,
    ROUND(SUM(ms.sig_str_landed) * 100.0 / NULLIF(SUM(ms.sig_str_attempted), 0), 1) AS accuracy
  FROM match_statistics ms
  JOIN fighter_match fm ON ms.fighter_match_id = fm.id
  JOIN fighter f ON fm.fighter_id = f.id
  GROUP BY f.id, f.name
  HAVING COUNT(DISTINCT fm.match_id) >= 10 AND SUM(ms.sig_str_attempted) > 0
  ORDER BY accuracy DESC
  LIMIT 1;

  -- 6. 경기당 유효타격 1위 (10경기+)
  SELECT f.name,
    ROUND(SUM(ms.sig_str_landed)::numeric / COUNT(DISTINCT fm.match_id), 2) AS sig_str_per_fight
  FROM match_statistics ms
  JOIN fighter_match fm ON ms.fighter_match_id = fm.id
  JOIN fighter f ON fm.fighter_id = f.id
  GROUP BY f.id, f.name
  HAVING COUNT(DISTINCT fm.match_id) >= 10
  ORDER BY sig_str_per_fight DESC
  LIMIT 1;

  -- 7. 테이크다운 성공률 1위 (10경기+, TD 시도 10회+)
  SELECT f.name,
    ROUND(SUM(ms.td_landed) * 100.0 / NULLIF(SUM(ms.td_attempted), 0), 1) AS td_accuracy
  FROM match_statistics ms
  JOIN fighter_match fm ON ms.fighter_match_id = fm.id
  JOIN fighter f ON fm.fighter_id = f.id
  GROUP BY f.id, f.name
  HAVING COUNT(DISTINCT fm.match_id) >= 10 AND SUM(ms.td_attempted) >= 10
  ORDER BY td_accuracy DESC
  LIMIT 1;

  -- 8. 넉다운 최다
  SELECT f.name, SUM(ms.knockdowns) AS total_knockdowns
  FROM match_statistics ms
  JOIN fighter_match fm ON ms.fighter_match_id = fm.id
  JOIN fighter f ON fm.fighter_id = f.id
  GROUP BY f.id, f.name
  ORDER BY total_knockdowns DESC
  LIMIT 1;
  ```

### 1-6. 이벤트 개최지 맵 (Event Location Map)

- **차트 유형**: 세계 지도 + 마커/버블
  - 마커 크기: 해당 도시 이벤트 횟수에 비례
  - 마커 클릭 시 도시명, 이벤트 수, 최근 이벤트 정보 툴팁
  - 라이브러리: `react-simple-maps` 또는 `deck.gl` 또는 Leaflet
- **데이터 소스**: `event.location` + `event.latitude` + `event.longitude` (신규 컬럼)
- **설명**: UFC가 전 세계 어디에서 대회를 개최하는지 지리적 분포를 시각화
- **weight_class 필터**: X
- **선행 작업**: `event` 테이블에 `latitude`, `longitude` 컬럼 추가 + geocoding 마이그레이션 (상단 Q4 참조)
- **참고 쿼리**:
  ```sql
  SELECT
    location,
    latitude,
    longitude,
    COUNT(*) AS event_count,
    MAX(event_date) AS last_event_date,
    (
      SELECT e2.name FROM event e2
      WHERE e2.location = e.location
      ORDER BY e2.event_date DESC
      LIMIT 1
    ) AS last_event_name
  FROM event e
  WHERE latitude IS NOT NULL AND longitude IS NOT NULL
  GROUP BY location, latitude, longitude
  ORDER BY event_count DESC;
  ```

### Home 추가 응답 구조

```json
{
  "category_leaders": [
    { "category": "most_wins", "label": "최다승", "name": "Jim Miller", "value": 26, "unit": "wins" },
    { "category": "best_winrate", "label": "최고 승률", "name": "Khabib Nurmagomedov", "value": 100.0, "unit": "%" },
    { "category": "most_ko_tko", "label": "KO/TKO 최다", "name": "Derrick Lewis", "value": 21, "unit": "finishes" },
    { "category": "most_submissions", "label": "서브미션 최다", "name": "Charles Oliveira", "value": 16, "unit": "finishes" },
    { "category": "best_striking_acc", "label": "타격 정확도", "name": "Max Holloway", "value": 62.1, "unit": "%" },
    { "category": "most_sig_str", "label": "경기당 유효타격", "name": "Max Holloway", "value": 7.49, "unit": "per fight" },
    { "category": "best_td_acc", "label": "테이크다운 성공률", "name": "Khabib Nurmagomedov", "value": 63.2, "unit": "%" },
    { "category": "most_knockdowns", "label": "넉다운 최다", "name": "Derrick Lewis", "value": 22, "unit": "knockdowns" }
  ],
  "event_map": [
    {
      "location": "Las Vegas, Nevada, USA",
      "latitude": 36.1699,
      "longitude": -115.1398,
      "event_count": 245,
      "last_event_date": "2024-12-07",
      "last_event_name": "UFC 310"
    }
  ]
}
```

---

## Tab 2: Overview (추가)

### 2-6. 연도별 피니시율 추이 (Finish Rate Trend by Year)

- **차트 유형**: Line Chart (다중 라인)
  - 4개 라인: KO율, TKO율, SUB율, 판정율(DEC)
  - X축: 연도, Y축: 비율(%)
  - 각 라인 색상 구분 + 범례(Legend)
  - Recharts `LineChart` + `Line` × 4 + `Legend` + `Tooltip`
- **데이터 소스**: `match.method` + `event.event_date`
- **설명**: "UFC가 점점 판정 위주로 변하고 있는가?" — 연도별 피니시 비율 변화 추이
- **weight_class 필터**: O
- **참고 쿼리**:
  ```sql
  SELECT
    EXTRACT(YEAR FROM e.event_date) AS year,
    COUNT(*) AS total_fights,
    ROUND(COUNT(CASE WHEN m.method LIKE 'KO-%' THEN 1 END) * 100.0 / COUNT(*), 1) AS ko_rate,
    ROUND(COUNT(CASE WHEN m.method LIKE 'TKO-%' THEN 1 END) * 100.0 / COUNT(*), 1) AS tko_rate,
    ROUND(COUNT(CASE WHEN m.method LIKE 'SUB-%' THEN 1 END) * 100.0 / COUNT(*), 1) AS sub_rate,
    ROUND(COUNT(CASE WHEN m.method LIKE '%-DEC%' THEN 1 END) * 100.0 / COUNT(*), 1) AS dec_rate
  FROM match m
  JOIN event e ON m.event_id = e.id
  WHERE e.event_date IS NOT NULL
    AND m.method IS NOT NULL
    AND (:weight_class_id IS NULL OR m.weight_class_id = :weight_class_id)
  GROUP BY year
  HAVING COUNT(*) >= 10
  ORDER BY year;
  ```

### 2-7. 선수 국적 분포 (Fighter Nationality Distribution)

- **차트 유형**: Treemap
  - 각 블록 크기 = 해당 국적 선수 수, 블록 내부에 국가명 + 선수 수 표시
  - TOP 15 국가는 개별 블록, 나머지는 "Others"로 묶음
  - Recharts `Treemap` + 커스텀 `Content` 컴포넌트
- **데이터 소스**: `fighter.nationality` (신규 컬럼)
- **설명**: UFC 선수들의 국적 다양성을 시각화. 어떤 국가가 가장 많은 UFC 선수를 배출하는지
- **weight_class 필터**: O — 체급 필터 시 해당 체급에서 활동한 선수의 국적 분포
- **선행 작업**: `fighter` 테이블에 `nationality VARCHAR` 컬럼 추가 + 크롤링 마이그레이션 (상단 Q5 참조)
- **참고 쿼리**:
  ```sql
  -- 전체
  SELECT
    f.nationality,
    COUNT(*) AS fighter_count
  FROM fighter f
  WHERE f.nationality IS NOT NULL
  GROUP BY f.nationality
  ORDER BY fighter_count DESC;

  -- 체급 필터 시: 해당 체급에서 경기한 선수만
  SELECT
    f.nationality,
    COUNT(DISTINCT f.id) AS fighter_count
  FROM fighter f
  JOIN fighter_match fm ON f.id = fm.fighter_id
  JOIN match m ON fm.match_id = m.id
  WHERE f.nationality IS NOT NULL
    AND m.weight_class_id = :weight_class_id
  GROUP BY f.nationality
  ORDER BY fighter_count DESC;
  ```

### 2-8. 체급별 평균 키-리치 비교 (Physique Comparison by Weight Class)

- **차트 유형**: Overlay Bar Chart (수평)
  - Y축: 체급 (Strawweight → Heavyweight)
  - X축: cm 수치
  - 넓은 반투명 바: 키(height_cm), 좁은 채색 바: 리치(reach_cm) — 겹쳐서 표시
  - 리치가 키보다 항상 크므로, 채색 바가 반투명 바를 넘어서는 부분 = 리치 이점
  - Recharts `ComposedChart`(horizontal layout) — `Bar` 2개 overlay (`barSize` 차이로 겹침)
- **데이터 소스**: `fighter.height_cm`, `fighter.reach_cm` + 체급 정보 (fighter → fighter_match → match → weight_class)
- **설명**: 체급별 선수의 평균 신체 스펙을 비교. 리치와 키의 차이가 큰 체급은 어디인지 파악
- **weight_class 필터**: X — 모든 체급 비교가 목적
- **프론트엔드 필터**: Open Weight, Catch Weight 제외
- **참고 쿼리**:
  ```sql
  SELECT
    wc.name AS weight_class,
    ROUND(AVG(f.height_cm)::numeric, 1) AS avg_height_cm,
    ROUND(AVG(f.reach_cm)::numeric, 1) AS avg_reach_cm,
    ROUND(AVG(f.reach_cm - f.height_cm)::numeric, 1) AS avg_reach_advantage,
    COUNT(DISTINCT f.id) AS fighter_count
  FROM fighter f
  JOIN fighter_match fm ON f.id = fm.fighter_id
  JOIN match m ON fm.match_id = m.id
  JOIN weight_class wc ON m.weight_class_id = wc.id
  WHERE f.height_cm IS NOT NULL
    AND f.reach_cm IS NOT NULL
  GROUP BY wc.id, wc.name
  ORDER BY AVG(f.weight_kg) ASC;
  ```

### Overview 추가 응답 구조

```json
{
  "finish_rate_trend": [
    {
      "year": 2024,
      "total_fights": 580,
      "ko_rate": 8.2,
      "tko_rate": 22.4,
      "sub_rate": 14.1,
      "dec_rate": 50.3
    }
  ],
  "nationality_distribution": [
    { "nationality": "USA", "fighter_count": 1245 },
    { "nationality": "Brazil", "fighter_count": 620 },
    { "nationality": "Russia", "fighter_count": 180 }
  ],
  "physique_comparison": [
    {
      "weight_class": "Strawweight",
      "avg_height_cm": 160.2,
      "avg_reach_cm": 163.5,
      "avg_reach_advantage": 3.3,
      "fighter_count": 85
    },
    {
      "weight_class": "Heavyweight",
      "avg_height_cm": 188.4,
      "avg_reach_cm": 197.8,
      "avg_reach_advantage": 9.4,
      "fighter_count": 210
    }
  ]
}
```

---

## Tab 3: Striking (추가)

### 3-5. 넉다운 리더 TOP (Knockdown Leaders)

- **차트 유형**: 수평 Bar Chart
  - X축: 넉다운 수, Y축: 선수명
  - Recharts `BarChart`(horizontal) + 오른쪽 label로 넉다운 수 표시
- **데이터 소스**: `match_statistics.knockdowns`
- **설명**: 넉다운을 가장 많이 기록한 선수 TOP 10. KO/TKO 리더(3-3)와 보완 관계 — 3-3은 피니시 기준, 이건 넉다운 횟수 기준
- **weight_class 필터**: O
- **참고 쿼리**:
  ```sql
  SELECT
    f.name,
    SUM(ms.knockdowns) AS total_knockdowns,
    COUNT(DISTINCT fm.match_id) AS total_fights,
    ROUND(SUM(ms.knockdowns)::numeric / COUNT(DISTINCT fm.match_id), 2) AS kd_per_fight
  FROM match_statistics ms
  JOIN fighter_match fm ON ms.fighter_match_id = fm.id
  JOIN fighter f ON fm.fighter_id = f.id
  JOIN match m ON fm.match_id = m.id
  WHERE (:weight_class_id IS NULL OR m.weight_class_id = :weight_class_id)
  GROUP BY f.id, f.name
  HAVING SUM(ms.knockdowns) > 0
  ORDER BY total_knockdowns DESC
  LIMIT 10;
  ```

### 3-7. 체급별 경기당 평균 유효타격 (Sig. Strikes per Fight by Weight Class)

- **차트 유형**: Bar Chart (세로)
  - X축: 체급, Y축: 경기당 평균 유효타격 수
  - Recharts `BarChart` + `Bar`
- **데이터 소스**: `match_statistics.sig_str_landed` + `weight_class`
- **설명**: 어떤 체급이 가장 타격이 많은지 모든 체급을 비교. 먼저 전 체급 비교용으로 구현, 이후 개별 체급 필터 확장 가능
- **weight_class 필터**: X — 모든 체급 비교가 목적
- **프론트엔드 필터**: Open Weight, Catch Weight 제외
- **참고 쿼리**:
  ```sql
  SELECT
    wc.name AS weight_class,
    ROUND(
      SUM(ms.sig_str_landed)::numeric / COUNT(DISTINCT fm.match_id), 2
    ) AS avg_sig_str_per_fight,
    COUNT(DISTINCT fm.match_id) AS total_fights
  FROM match_statistics ms
  JOIN fighter_match fm ON ms.fighter_match_id = fm.id
  JOIN match m ON fm.match_id = m.id
  JOIN weight_class wc ON m.weight_class_id = wc.id
  GROUP BY wc.id, wc.name
  ORDER BY avg_sig_str_per_fight DESC;
  ```

### 3-8. 라운드별 타격 강도 변화 (Strike Volume by Round)

- **차트 유형**: Stacked Area Chart 또는 Grouped Bar Chart
  - X축: 라운드(R1, R2, R3, R4, R5)
  - Y축: 평균 유효타격 수
  - 선택지 A (Area): 부위별 스택 — Head/Body/Leg/Clinch/Ground 층층이
  - 선택지 B (Bar): 라운드별 총 유효타격 수 바 + 정확도 라인 오버레이
  - Recharts `AreaChart` + `Area` × 5 (stacked) 또는 `ComposedChart` + `Bar` + `Line`
- **데이터 소스**: `strike_detail` (round 1~5), `match_statistics` (round 1~5)
- **설명**: "경기 후반으로 갈수록 타격이 줄어드는가?" — 라운드 진행에 따른 타격 패턴 변화
- **weight_class 필터**: O
- **참고 쿼리**:
  ```sql
  -- 라운드별 평균 유효타격 + 부위별 분포
  SELECT
    sd.round,
    ROUND(AVG(sd.head_strikes_landed + sd.body_strikes_landed + sd.leg_strikes_landed
              + sd.clinch_strikes_landed + sd.ground_strikes_landed)::numeric, 1) AS avg_total_strikes,
    ROUND(AVG(sd.head_strikes_landed)::numeric, 1) AS avg_head,
    ROUND(AVG(sd.body_strikes_landed)::numeric, 1) AS avg_body,
    ROUND(AVG(sd.leg_strikes_landed)::numeric, 1) AS avg_leg,
    ROUND(AVG(sd.clinch_strikes_landed)::numeric, 1) AS avg_clinch,
    ROUND(AVG(sd.ground_strikes_landed)::numeric, 1) AS avg_ground,
    COUNT(*) AS sample_count
  FROM strike_detail sd
  JOIN fighter_match fm ON sd.fighter_match_id = fm.id
  JOIN match m ON fm.match_id = m.id
  WHERE sd.round > 0
    AND (:weight_class_id IS NULL OR m.weight_class_id = :weight_class_id)
  GROUP BY sd.round
  ORDER BY sd.round;
  ```

### 3-9. 공방 효율 TOP (Strike Exchange Ratio Leaders)

- **차트 유형**: 수평 Bar Chart (Diverging Bar 또는 일반 바)
  - 각 선수: [내 유효타격 — 피격 유효타격] 또는 차이값(Differential) 바
  - 오른쪽 label: differential 수치 + ratio
  - Recharts `BarChart`(horizontal) + 2색 바 또는 단일 differential 바
- **데이터 소스**: `match_statistics` + `fighter_match` self-join (상대 sig_str_landed = 내 피격)
- **설명**: "내가 때리는 것 대비 얼마나 덜 맞는가?" — 경기당 유효타격 차이(differential)가 가장 큰 선수 TOP 10. 공격력과 방어력을 동시에 평가
- **min_fights 필터**: 10/20/30 PillTabs (백엔드 3세트 반환)
- **weight_class 필터**: O
- **참고 쿼리**:
  ```sql
  SELECT
    f.name,
    COUNT(DISTINCT fm_mine.match_id) AS total_fights,
    ROUND(SUM(ms_mine.sig_str_landed)::numeric / COUNT(DISTINCT fm_mine.match_id), 2) AS sig_landed_per_fight,
    ROUND(SUM(ms_opp.sig_str_landed)::numeric / COUNT(DISTINCT fm_mine.match_id), 2) AS sig_absorbed_per_fight,
    ROUND(
      (SUM(ms_mine.sig_str_landed) - SUM(ms_opp.sig_str_landed))::numeric
      / COUNT(DISTINCT fm_mine.match_id), 2
    ) AS differential_per_fight
  FROM fighter_match fm_mine
  JOIN fighter_match fm_opp
    ON fm_mine.match_id = fm_opp.match_id AND fm_mine.id != fm_opp.id
  JOIN match_statistics ms_mine ON fm_mine.id = ms_mine.fighter_match_id
  JOIN match_statistics ms_opp ON fm_opp.id = ms_opp.fighter_match_id
  JOIN fighter f ON fm_mine.fighter_id = f.id
  JOIN match m ON fm_mine.match_id = m.id
  WHERE ms_mine.round = ms_opp.round
    AND (:weight_class_id IS NULL OR m.weight_class_id = :weight_class_id)
  GROUP BY f.id, f.name
  HAVING COUNT(DISTINCT fm_mine.match_id) >= :min_fights
  ORDER BY differential_per_fight DESC
  LIMIT 10;
  ```

### 3-10. 스탠스간 승률 (Win Rate by Stance Matchup)

- **차트 유형**: Heatmap 또는 Grouped Bar Chart
  - Heatmap: 행=승자 스탠스, 열=패자 스탠스, 셀 값=승률(%), 색상 강도=승률
  - 대안 Grouped Bar: X축=매치업(Orth vs South, South vs Orth 등), Y축=승률
  - Recharts: 커스텀 Heatmap (`ScatterChart` + 커스텀 Cell) 또는 `BarChart`
- **데이터 소스**: `fighter.stance` + `fighter_match` self-join
- **설명**: "사우스포가 정통파 상대로 유리한가?" — 스탠스 매치업별 승률을 시각화
- **weight_class 필터**: O
- **참고 쿼리**:
  ```sql
  SELECT
    f_w.stance AS winner_stance,
    f_l.stance AS loser_stance,
    COUNT(*) AS wins,
    -- 전체 해당 매치업 수 대비 승률 계산을 위해 서브쿼리 또는 윈도우 함수 사용
    ROUND(
      COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY
        LEAST(f_w.stance, f_l.stance), GREATEST(f_w.stance, f_l.stance)
      ), 1
    ) AS win_rate
  FROM fighter_match fm_w
  JOIN fighter_match fm_l
    ON fm_w.match_id = fm_l.match_id AND fm_w.id != fm_l.id
  JOIN fighter f_w ON fm_w.fighter_id = f_w.id
  JOIN fighter f_l ON fm_l.fighter_id = f_l.id
  JOIN match m ON fm_w.match_id = m.id
  WHERE fm_w.result = 'win'
    AND f_w.stance IN ('Orthodox', 'Southpaw', 'Switch')
    AND f_l.stance IN ('Orthodox', 'Southpaw', 'Switch')
    AND (:weight_class_id IS NULL OR m.weight_class_id = :weight_class_id)
  GROUP BY f_w.stance, f_l.stance
  ORDER BY f_w.stance, f_l.stance;
  ```
  
  ```
  -- 응답 예시: 행렬 형태
  -- Orthodox vs Orthodox: 50.0% (정의상)
  -- Orthodox vs Southpaw: 54.2% → Southpaw vs Orthodox: 45.8%
  -- Orthodox vs Switch: 51.3% → Switch vs Orthodox: 48.7%
  ```

### Striking 추가 응답 구조

```json
{
  "knockdown_leaders": [
    { "name": "Derrick Lewis", "total_knockdowns": 22, "total_fights": 30, "kd_per_fight": 0.73 }
  ],
  "sig_strikes_by_weight_class": [
    { "weight_class": "Bantamweight", "avg_sig_str_per_fight": 48.2, "total_fights": 890 }
  ],
  "round_strike_trend": [
    {
      "round": 1,
      "avg_total_strikes": 22.5,
      "avg_head": 12.3, "avg_body": 3.8, "avg_leg": 4.1,
      "avg_clinch": 1.2, "avg_ground": 1.1,
      "sample_count": 14200
    },
    {
      "round": 2,
      "avg_total_strikes": 20.1,
      "avg_head": 11.0, "avg_body": 3.5, "avg_leg": 3.6,
      "avg_clinch": 1.1, "avg_ground": 0.9,
      "sample_count": 9800
    }
  ],
  "strike_exchange_ratio": {
    "min10": [
      {
        "name": "Max Holloway",
        "total_fights": 30,
        "sig_landed_per_fight": 7.49,
        "sig_absorbed_per_fight": 4.21,
        "differential_per_fight": 3.28
      }
    ],
    "min20": [],
    "min30": []
  },
  "stance_winrate": [
    { "winner_stance": "Orthodox", "loser_stance": "Southpaw", "wins": 1245, "win_rate": 54.2 },
    { "winner_stance": "Southpaw", "loser_stance": "Orthodox", "wins": 1053, "win_rate": 45.8 },
    { "winner_stance": "Orthodox", "loser_stance": "Orthodox", "wins": 3420, "win_rate": 50.0 },
    { "winner_stance": "Southpaw", "loser_stance": "Southpaw", "wins": 280, "win_rate": 50.0 }
  ]
}
```

---

## Tab 4: Grappling (추가)

### 4-6. 경기당 테이크다운 시도 TOP (Takedown Attempts per Fight Leaders)

- **차트 유형**: Lollipop Chart (줄기 + 점)
  - Bar: 얇은 stem, Scatter: 끝점 dot (3-4와 동일 패턴)
  - ReferenceLine: 전체 평균값 점선
  - Recharts `ComposedChart`(vertical) — `Bar`(stem) + `Scatter`(dot)
- **데이터 소스**: `match_statistics.td_attempted`
- **설명**: 경기당 테이크다운 시도가 가장 많은 선수 TOP 10. 4-1(성공률)과 보완 — "성공률은 낮아도 미친 듯이 시도하는 선수" 식별
- **min_fights 필터**: 10/20/30 PillTabs (백엔드 3세트 반환)
- **weight_class 필터**: O
- **참고 쿼리**:
  ```sql
  SELECT
    f.name,
    ROUND(SUM(ms.td_attempted)::numeric / COUNT(DISTINCT fm.match_id), 2) AS td_attempts_per_fight,
    SUM(ms.td_attempted) AS total_td_attempted,
    SUM(ms.td_landed) AS total_td_landed,
    COUNT(DISTINCT fm.match_id) AS total_fights
  FROM match_statistics ms
  JOIN fighter_match fm ON ms.fighter_match_id = fm.id
  JOIN fighter f ON fm.fighter_id = f.id
  JOIN match m ON fm.match_id = m.id
  WHERE (:weight_class_id IS NULL OR m.weight_class_id = :weight_class_id)
  GROUP BY f.id, f.name
  HAVING COUNT(DISTINCT fm.match_id) >= :min_fights
  ORDER BY td_attempts_per_fight DESC
  LIMIT 10;

  -- 평균값 (ReferenceLine용)
  SELECT ROUND(AVG(td_attempts_per_fight)::numeric, 2) AS avg_td_attempts
  FROM (
    SELECT SUM(ms.td_attempted)::numeric / COUNT(DISTINCT fm.match_id) AS td_attempts_per_fight
    FROM match_statistics ms
    JOIN fighter_match fm ON ms.fighter_match_id = fm.id
    JOIN match m ON fm.match_id = m.id
    WHERE (:weight_class_id IS NULL OR m.weight_class_id = :weight_class_id)
    GROUP BY fm.fighter_id
    HAVING COUNT(DISTINCT fm.match_id) >= :min_fights
  ) sub;
  ```

### 4-7. 테이크다운 vs 서브미션 상관관계 (Takedown-Submission Correlation)

- **차트 유형**: Scatter Plot (4사분면 분석)
  - X축: 총 테이크다운 성공 수, Y축: 총 서브미션 피니시 수
  - 4사분면 의미:
    - 우상: 올라운더 (TD 많고 SUB도 많음)
    - 우하: 레슬러형 (TD 많지만 SUB 적음)
    - 좌상: 유술가형 (TD 적지만 SUB 많음)
    - 좌하: 스트라이커형 (TD도 SUB도 적음)
  - ReferenceLine 2개: X평균, Y평균 (사분면 구분선)
  - Recharts `ScatterChart` + `Scatter` + `ReferenceLine` × 2
- **데이터 소스**: `match_statistics.td_landed` + `match.method LIKE 'SUB-%'`
- **설명**: "테이크다운을 많이 하는 선수가 서브미션도 잘 잡는가?" — 선수 스타일 분류
- **weight_class 필터**: O
- **참고 쿼리**:
  ```sql
  SELECT
    f.name,
    SUM(ms.td_landed) AS total_td_landed,
    COUNT(CASE WHEN m.method LIKE 'SUB-%' AND fm.result = 'win' THEN 1 END) AS sub_finishes,
    COUNT(DISTINCT fm.match_id) AS total_fights
  FROM match_statistics ms
  JOIN fighter_match fm ON ms.fighter_match_id = fm.id
  JOIN fighter f ON fm.fighter_id = f.id
  JOIN match m ON fm.match_id = m.id
  WHERE (:weight_class_id IS NULL OR m.weight_class_id = :weight_class_id)
  GROUP BY f.id, f.name
  HAVING COUNT(DISTINCT fm.match_id) >= 5;
  -- LIMIT 없음 — 산점도는 조건 충족 전체 선수 반환

  -- 평균값 (ReferenceLine용)
  SELECT
    ROUND(AVG(total_td_landed)::numeric, 1) AS avg_td,
    ROUND(AVG(sub_finishes)::numeric, 1) AS avg_sub
  FROM (위 쿼리) sub;
  ```

### 4-8. 체급별 경기당 평균 테이크다운 시도 (Takedown Attempts by Weight Class)

- **차트 유형**: Bar Chart (세로)
  - X축: 체급, Y축: 경기당 평균 테이크다운 시도 수
  - 4-3(컨트롤 타임)과 나란히 배치하면 인사이트 극대화
  - Recharts `BarChart` + `Bar`
- **데이터 소스**: `match_statistics.td_attempted` + `weight_class`
- **설명**: "어느 체급이 가장 레슬링 중심인가?" — 체급별 테이크다운 활동량 비교
- **weight_class 필터**: X — 모든 체급 비교가 목적
- **프론트엔드 필터**: Open Weight, Catch Weight 제외
- **참고 쿼리**:
  ```sql
  SELECT
    wc.name AS weight_class,
    ROUND(
      SUM(ms.td_attempted)::numeric / COUNT(DISTINCT fm.match_id), 2
    ) AS avg_td_attempts_per_fight,
    ROUND(
      SUM(ms.td_landed)::numeric / COUNT(DISTINCT fm.match_id), 2
    ) AS avg_td_landed_per_fight,
    COUNT(DISTINCT fm.match_id) AS total_fights
  FROM match_statistics ms
  JOIN fighter_match fm ON ms.fighter_match_id = fm.id
  JOIN match m ON fm.match_id = m.id
  JOIN weight_class wc ON m.weight_class_id = wc.id
  GROUP BY wc.id, wc.name
  ORDER BY avg_td_attempts_per_fight DESC;
  ```

### 4-9. 테이크다운 디펜스 리더 TOP (Takedown Defense Leaders)

- **차트 유형**: Bullet Chart (시도 대비 방어 overlay 바)
  - 넓은 반투명 바: 상대 TD 시도, 좁은 채색 바: 방어 성공
  - 오른쪽 label로 defense_rate% 표시
  - 4-1(TD 성공률)과 동일 패턴, 색상만 변경 (red/orange 계열)
  - Recharts `BarChart`(vertical) — 2개 `Bar` overlay
- **데이터 소스**: `match_statistics` + `fighter_match` self-join (상대의 td_attempted/td_landed 역계산)
- **설명**: 상대의 테이크다운을 가장 잘 막는 선수. `상대 TD 시도 - 상대 TD 성공 = 내 방어 성공`
- **min_fights 필터**: 10/20/30 PillTabs (백엔드 3세트 반환)
- **weight_class 필터**: O — 각 체급별 TOP 10
- **참고 쿼리**:
  ```sql
  SELECT
    f.name,
    SUM(ms_opp.td_attempted) AS opp_td_attempted,
    SUM(ms_opp.td_landed) AS opp_td_landed,
    SUM(ms_opp.td_attempted) - SUM(ms_opp.td_landed) AS td_defended,
    ROUND(
      (SUM(ms_opp.td_attempted) - SUM(ms_opp.td_landed)) * 100.0
      / NULLIF(SUM(ms_opp.td_attempted), 0), 1
    ) AS td_defense_rate
  FROM fighter_match fm_mine
  JOIN fighter_match fm_opp
    ON fm_mine.match_id = fm_opp.match_id AND fm_mine.id != fm_opp.id
  JOIN match_statistics ms_opp ON fm_opp.id = ms_opp.fighter_match_id
  JOIN fighter f ON fm_mine.fighter_id = f.id
  JOIN match m ON fm_mine.match_id = m.id
  WHERE ms_opp.round > 0
    AND (:weight_class_id IS NULL OR m.weight_class_id = :weight_class_id)
  GROUP BY f.id, f.name
  HAVING COUNT(DISTINCT fm_mine.match_id) >= :min_fights
    AND SUM(ms_opp.td_attempted) >= 5
  ORDER BY td_defense_rate DESC
  LIMIT 10;
  ```

### Grappling 추가 응답 구조

```json
{
  "td_attempts_leaders": {
    "min10": [
      {
        "name": "Khabib Nurmagomedov",
        "td_attempts_per_fight": 5.42,
        "total_td_attempted": 130,
        "total_td_landed": 82,
        "total_fights": 24
      }
    ],
    "min20": [],
    "min30": [],
    "avg_td_attempts": 1.85
  },
  "td_sub_correlation": {
    "fighters": [
      { "name": "Charles Oliveira", "total_td_landed": 52, "sub_finishes": 16, "total_fights": 32 },
      { "name": "Khabib Nurmagomedov", "total_td_landed": 82, "sub_finishes": 3, "total_fights": 24 }
    ],
    "avg_td": 8.2,
    "avg_sub": 0.8
  },
  "td_by_weight_class": [
    {
      "weight_class": "Flyweight",
      "avg_td_attempts_per_fight": 2.45,
      "avg_td_landed_per_fight": 1.12,
      "total_fights": 620
    }
  ],
  "td_defense_leaders": {
    "min10": [
      {
        "name": "Jose Aldo",
        "opp_td_attempted": 85,
        "opp_td_landed": 12,
        "td_defended": 73,
        "td_defense_rate": 85.9
      }
    ],
    "min20": [],
    "min30": []
  }
}
```

---

## 구현 참고사항 (추가분)

### ⚠️ DB 라운드 데이터 구조

`match_statistics`와 `strike_detail` 테이블에는 **`round=0`(합계) 행이 존재하지 않음**.
모든 행은 `round=1~5` (라운드별 데이터)만 포함.
따라서 경기 전체 합산이 필요한 경우 `WHERE round = 0`이 아닌 **`SUM()` 집계**를 사용해야 함.

또한 `fighter.stance` 컬럼에는 빈 문자열(`''`)이 847건 존재.
유효한 값: `Orthodox`(2768), `Southpaw`(607), `Switch`(219).
`Open Stance`(7), `Sideways`(3)은 샘플이 너무 적어 분석에서 제외.

### 공통 쿼리 패턴: fighter_match self-join

3-9(공방 효율), 3-10(스탠스 승률), 4-9(TD 디펜스) 에서 사용하는 핵심 패턴:

```sql
-- "같은 경기의 상대방 데이터" 접근 패턴
FROM fighter_match fm_mine
JOIN fighter_match fm_opp
  ON fm_mine.match_id = fm_opp.match_id
  AND fm_mine.id != fm_opp.id          -- 자기 자신 제외
JOIN match_statistics ms_mine ON fm_mine.id = ms_mine.fighter_match_id
JOIN match_statistics ms_opp ON fm_opp.id = ms_opp.fighter_match_id
-- ⚠️ round 조건: ms_mine.round = ms_opp.round (같은 라운드끼리 매칭)
-- DB에 round=0(합계) 행이 없으므로 SUM() 집계로 전체 합산
```

- `ms_mine.sig_str_landed` = 내가 적중한 유효타격
- `ms_opp.sig_str_landed` = 상대가 적중한 유효타격 = **내가 맞은 유효타격**
- `ms_opp.td_attempted - ms_opp.td_landed` = 상대 TD 시도 중 실패 = **내 TD 방어**

### weight_class 필터 무시 항목 (추가분)

기존: 2-2, 2-3, 4-3

추가: 1-5 분야별 1등, 1-6 개최지 맵, 2-8 체급별 키-리치, 3-7 체급별 유효타격, 4-8 체급별 TD 시도율

### min_fights 필터 적용 차트 (추가분)

기존: 3-2, 3-4, 4-1

추가: 3-9 공방 효율, 4-6 경기당 TD 시도, 4-9 TD 디펜스

### Redis 캐시 키 (추가분)

| 차트 | 캐시 키 패턴 |
|------|-------------|
| 분야별 1등 | `dashboard:chart:category-leaders` |
| 개최지 맵 | `dashboard:chart:event-map` |
| 피니시율 추이 | `dashboard:chart:finish-rate-trend:{wc\|all}` |
| 국적 분포 | `dashboard:chart:nationality:{wc\|all}` |
| 체급별 키-리치 | `dashboard:chart:physique-comparison` |
| 넉다운 리더 | `dashboard:chart:knockdown-leaders:{wc\|all}` |
| 체급별 유효타격 | `dashboard:chart:sig-strikes-by-wc` |
| 라운드별 타격 | `dashboard:chart:round-strike-trend:{wc\|all}` |
| 공방 효율 | `dashboard:chart:strike-exchange:{wc\|all}` |
| 스탠스별 승률 | `dashboard:chart:stance-winrate:{wc\|all}` |
| TD 시도 TOP | `dashboard:chart:td-attempts-leaders:{wc\|all}` |
| TD-SUB 상관 | `dashboard:chart:td-sub-corr:{wc\|all}` |
| 체급별 TD | `dashboard:chart:td-by-wc` |
| TD 디펜스 | `dashboard:chart:td-defense:{wc\|all}` |

### 선행 작업 (데이터 마이그레이션)

| 작업 | 영향 차트 | 우선순위 |
|------|----------|----------|
| `event` 테이블에 `latitude FLOAT`, `longitude FLOAT` 추가 + geocoding 스크립트 | 1-6 | 중간 |
| `fighter` 테이블에 `nationality VARCHAR` 추가 + 크롤링 스크립트 | 2-7 | 중간 |

나머지 12개 차트는 기존 DB 스키마만으로 즉시 구현 가능.

### Recharts 컴포넌트 매핑 (추가분)

| 차트 | Recharts 컴포넌트 |
|------|------------------|
| 1-5 분야별 1등 | 커스텀 카드 컴포넌트 (차트 아님) |
| 1-6 개최지 맵 | `react-simple-maps` 또는 Leaflet (Recharts 외부) |
| 2-6 피니시율 추이 | `LineChart` + `Line` × 4 |
| 2-7 국적 분포 | `Treemap` |
| 2-8 키-리치 | `ComposedChart`(horizontal) — `Bar` × 2 overlay (넓은 반투명 바 + 좁은 채색 바) |
| 3-5 넉다운 리더 | `BarChart` (수평) |
| 3-7 체급별 유효타격 | `BarChart` |
| 3-8 라운드별 타격 | `AreaChart` (stacked) 또는 `ComposedChart` |
| 3-9 공방 효율 | `BarChart` (수평, Diverging) |
| 3-10 스탠스 승률 | `BarChart` (grouped) 또는 커스텀 Heatmap |
| 4-6 TD 시도 TOP | `ComposedChart` — `Bar`(stem) + `Scatter`(dot) |
| 4-7 TD-SUB 상관 | `ScatterChart` + `ReferenceLine` × 2 |
| 4-8 체급별 TD | `BarChart` |
| 4-9 TD 디펜스 | `BarChart` (Bullet, 2-Bar overlay) |
