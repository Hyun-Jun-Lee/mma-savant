# Dashboard 통계 화면 기획

MMA Savant 대시보드에 표시할 통계 자료 목록 및 API 구현 가이드

---

## API 아키텍처

레이아웃: **Layout E (Bento Grid)** 확정 — `docs/dashboard-prototype-E.html` 참조

| # | Endpoint | 설명 | weight_class | limit |
|---|----------|------|:---:|:---:|
| - | `GET /api/dashboard/summary` | 요약 카드 (선수·경기·이벤트·챔피언 수) | X | X |
| 1 | `GET /api/dashboard/finish-methods` | 피니시 방법 분포 | O | X |
| 2 | `GET /api/dashboard/weight-class-activity` | 체급별 경기 수 & 피니시율 | X | X |
| 3 | `GET /api/dashboard/events-timeline` | 연도별 이벤트 추이 | X | X |
| 4 | `GET /api/dashboard/leaderboard` | 최다승 / 최고승률 TOP | O | O |
| 5 | `GET /api/dashboard/rankings` | 체급별 챔피언 & 랭킹 | O | X |
| 6 | `GET /api/dashboard/fight-duration` | 경기 종료 라운드 분포 | O | X |
| 7 | `GET /api/dashboard/striking-accuracy` | 타격 정확도 TOP | O | O |
| 8 | `GET /api/dashboard/strike-targets` | 타격 부위별 분포 | O | X |
| 9 | `GET /api/dashboard/takedown-accuracy` | 테이크다운 성공률 TOP | O | O |
| 10 | `GET /api/dashboard/submission-techniques` | 서브미션 기술 분포 | O | O |
| 11 | `GET /api/dashboard/control-time` | 체급별 평균 컨트롤 타임 | X | X |
| 12 | `GET /api/dashboard/ground-strikes` | 그라운드 스트라이크 TOP | O | O |
| 13 | `GET /api/dashboard/submission-efficiency` | 서브미션 효율성 | O | O |
| 14 | `GET /api/dashboard/ko-tko-leaders` | KO/TKO 피니시 TOP | O | O |
| 15 | `GET /api/dashboard/sig-strikes-per-fight` | 경기당 유효타격 TOP | O | O |

### 공통 쿼리 파라미터

**weight_class 필터**
- **지원 (O)**: `?weight_class_id=3`. 미전송 시 전체 체급 집계
- **제외 (X)**:
  - `#2 weight-class-activity`, `#11 control-time` — 모든 체급 비교가 차트의 목적
  - `#3 events-timeline` — 이벤트에 여러 체급 포함
  - `summary` — 전체 집계 지표

**limit 파라미터** (TOP N 리더보드 계열)
- **지원 (O)**: `?limit=5` (기본값 5). 프론트엔드 "더보기" 클릭 시 `limit=10` 재요청
- **허용 값**: 5 또는 10 (백엔드에서 검증, 그 외 값은 5로 fallback)
- **대상**: #4, #7, #9, #10, #12, #13, #14, #15 (총 8개)

---

## 데이터 소스

현재 DB 테이블 기반으로 모든 항목 구현 가능

| 테이블 | 활용 데이터 |
|--------|------------|
| `fighter` | name, wins, losses, draws, height, weight, reach, stance, birthdate, belt |
| `event` | name, location, event_date |
| `match` | method, result_round, time, is_main_event, weight_class_id |
| `fighter_match` | fighter_id, match_id, result (win/loss/draw/nc) |
| `weight_class` | name (12개 체급) |
| `ranking` | fighter_id, weight_class_id, ranking (0=챔피언, 1-15) |
| `match_statistics` | knockdowns, sig_str_landed/attempted, td_landed/attempted, submission_attempts, control_time_seconds |
| `strike_detail` | head/body/leg/clinch/ground strikes (landed/attempts) |

---

## 요약 카드

- **Endpoint**: `GET /api/dashboard/summary`

대시보드 최상단에 핵심 수치를 카드 형태로 표시:

| 카드 | 쿼리 |
|------|------|
| 총 선수 수 | `SELECT COUNT(*) FROM fighter` |
| 총 경기 수 | `SELECT COUNT(*) FROM match` |
| 총 이벤트 수 | `SELECT COUNT(*) FROM event` |
| 현재 챔피언 수 | `SELECT COUNT(*) FROM fighter WHERE belt = true` |

---

## 통계 항목 (15가지)

### 1. 피니시 방법 분포 (Finish Method Breakdown)

- **Endpoint**: `GET /api/dashboard/finish-methods?weight_class_id=`
- **차트 유형**: 도넛/파이 차트
- **데이터 소스**: `match.method`
- **분류 기준**: KO, TKO, SUB, U-DEC(만장일치 판정), S-DEC(스플릿 판정), M-DEC(다수 판정)
- **설명**: UFC 전체 경기의 "판정 vs 피니시" 비율. MMA 팬들이 가장 관심 있는 지표 중 하나
- **weight_class 필터**: `JOIN match → weight_class` + `WHERE` 절 추가
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
  JOIN weight_class wc ON m.weight_class_id = wc.id
  WHERE m.method IS NOT NULL
    AND (:weight_class_id IS NULL OR m.weight_class_id = :weight_class_id)
  GROUP BY method_category
  ORDER BY count DESC;
  ```

---

### 2. 체급별 경기 수 & 피니시 분포 (Weight Class Activity)

- **Endpoint**: `GET /api/dashboard/weight-class-activity`
- **차트 유형**: ComposedChart — 스택 바(KO/TKO/SUB 건수) + 도트(피니시율 %)
  - 왼쪽 Y축: 경기 수 (스택 바: KO·TKO·SUB 색상 구분)
  - 오른쪽 Y축: 피니시율 % (도트/라인)
  - Recharts `ComposedChart` + `Bar`(stacked) + `Line`(dot only) 조합
- **데이터 소스**: `match` + `weight_class` 조인
- **설명**: 어떤 체급이 가장 활발하고 액션이 많은지 비교하면서, KO/TKO/SUB 비율까지 한눈에 파악. 기존 #16(체급별 KO/TKO 비율)의 정보를 흡수
- **피니시 판정 기준**: method가 KO/TKO/SUB으로 시작하면 피니시
- **weight_class 필터**: X — 모든 체급 비교가 차트의 목적
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
    ) AS finish_rate
  FROM match m
  JOIN weight_class wc ON m.weight_class_id = wc.id
  WHERE m.method IS NOT NULL
  GROUP BY wc.name
  ORDER BY total_fights DESC;
  ```

---

### 3. 연도별 이벤트 수 추이 (UFC Growth Timeline)

- **Endpoint**: `GET /api/dashboard/events-timeline`
- **차트 유형**: 라인/에어리어 차트
- **데이터 소스**: `event.event_date`
- **설명**: UFC의 성장 추이를 시각적으로 보여줌. 연도별 이벤트 증감 트렌드
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

---

### 4. 최다승 & 최고 승률 TOP (Fighter Leaderboard)

- **Endpoint**: `GET /api/dashboard/leaderboard?weight_class_id=&tab=wins|winrate&min_fights=10&limit=5`
- **차트 유형**: 바 차트 (탭으로 최다승/최고승률 전환)
- **데이터 소스**: `fighter.wins`, `fighter.losses`, `fighter.draws`
- **설명**: 역대 최고의 선수를 한눈에 확인. 팬들이 가장 자주 찾는 정보
- **인터랙션**:
  - 탭: 최다승 / 최고승률 전환
  - 최고승률 탭에 최소 경기 수 드롭다운: `10경기 이상` | `20경기 이상` | `30경기 이상`
  - "더보기" 버튼: `limit=10`으로 재요청
- **weight_class 필터**: 전체(default)는 `fighter` 테이블 직접 조회, 체급 필터 시 `fighter_match → match` JOIN으로 해당 체급 승수만 집계
- **참고 쿼리**:
  ```sql
  -- 최다승 TOP (전체, weight_class_id 미전송)
  SELECT name, wins, losses, draws
  FROM fighter
  ORDER BY wins DESC
  LIMIT :limit;  -- 기본 5, 더보기 10

  -- 최다승 TOP (체급 필터 시)
  SELECT
    f.name,
    COUNT(CASE WHEN fm.result = 'win' THEN 1 END) AS wins,
    COUNT(CASE WHEN fm.result = 'loss' THEN 1 END) AS losses,
    COUNT(CASE WHEN fm.result = 'draw' THEN 1 END) AS draws
  FROM fighter f
  JOIN fighter_match fm ON f.id = fm.fighter_id
  JOIN match m ON fm.match_id = m.id
  WHERE m.weight_class_id = :weight_class_id
  GROUP BY f.id, f.name
  ORDER BY wins DESC
  LIMIT :limit;

  -- 최고 승률 TOP (전체, 드롭다운 선택값을 :min_fights 파라미터로 전달)
  SELECT
    name, wins, losses, draws,
    ROUND(wins * 100.0 / (wins + losses + draws), 1) AS win_rate
  FROM fighter
  WHERE (wins + losses + draws) >= :min_fights  -- 10, 20, 30 중 선택
  ORDER BY win_rate DESC
  LIMIT :limit;

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
  LIMIT :limit;
  ```

---

### 5. 현재 체급별 챔피언 & 랭킹 (Division Rankings)

- **Endpoint**: `GET /api/dashboard/rankings?weight_class_id=`
- **차트 유형**: 카드형 리스트 (체급 선택 드롭다운)
- **데이터 소스**: `ranking` + `fighter` + `weight_class` 조인
- **설명**: 현재 UFC 랭킹 현황. ranking=0은 챔피언, 1-15는 랭커
- **참고 쿼리**:
  ```sql
  SELECT
    wc.name AS weight_class,
    r.ranking,
    f.name AS fighter_name,
    f.wins, f.losses, f.draws
  FROM ranking r
  JOIN fighter f ON r.fighter_id = f.id
  JOIN weight_class wc ON r.weight_class_id = wc.id
  WHERE wc.id = :weight_class_id
  ORDER BY r.ranking;
  ```

---

### 6. 평균 경기 종료 라운드 & 시간 (Fight Duration Analysis)

- **Endpoint**: `GET /api/dashboard/fight-duration?weight_class_id=`
- **차트 유형**: 세로 바 차트 + ReferenceLine(평균 라운드)
  - X축: R1~R5 (이산값이므로 히스토그램 대신 바 차트)
  - Y축: 비율(%) — 각 바에 비율(%)과 건수를 툴팁으로 표시
  - ReferenceLine: 평균 종료 라운드 (점선)
  - Recharts `BarChart` + `ReferenceLine` 조합
- **데이터 소스**: `match.result_round`, `match.time`
- **설명**: "평균적으로 UFC 경기는 몇 라운드에서 끝나는가". 1라운드 피니시 비율 등 흥미로운 통계 도출
- **참고 쿼리**:
  ```sql
  SELECT
    result_round,
    COUNT(*) AS fight_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) AS percentage
  FROM match
  WHERE result_round IS NOT NULL
    AND (:weight_class_id IS NULL OR weight_class_id = :weight_class_id)
  GROUP BY result_round
  ORDER BY result_round;
  ```

---

### 7. 타격 정확도 TOP 선수 (Striking Accuracy Leaders)

- **Endpoint**: `GET /api/dashboard/striking-accuracy?weight_class_id=&limit=5`
- **차트 유형**: 수평 바 차트 (정확도 % 표시)
- **데이터 소스**: `match_statistics.sig_str_landed`, `match_statistics.sig_str_attempted`
- **설명**: 유효 타격 정확도가 가장 높은 선수. 스트라이킹 능력의 핵심 지표
- **필터**: 최소 5경기 이상 출전 선수
- **weight_class 필터**: `JOIN match → weight_class` + `WHERE` 절 추가
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
  LIMIT :limit;  -- 기본 5, 더보기 10
  ```

---

### 8. 타격 부위별 분포 (Strike Target Distribution)

- **Endpoint**: `GET /api/dashboard/strike-targets?weight_class_id=`
- **차트 유형**: 레이더 차트 (RadarChart)
  - 5개 축: Head / Body / Leg / Clinch / Ground
  - 체급 필터 적용 시 두 체급을 겹쳐서 전술 차이 비교 가능 (예: HW의 head 집중 vs FLW의 leg/clinch 다양)
  - Recharts `RadarChart` + `PolarGrid` + `Radar` 조합
- **데이터 소스**: `strike_detail` (head/body/leg/clinch/ground strikes)
- **설명**: UFC 선수들이 어디를 가장 많이 공격하는지 시각화. 5개 부위를 레이더 형태로 비교하면 체급별 전술 패턴이 극적으로 드러남
- **weight_class 필터**: `JOIN match → weight_class` + `WHERE` 절 추가
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

---

### 9. 테이크다운 성공률 TOP 선수 (Takedown Accuracy Leaders)

- **Endpoint**: `GET /api/dashboard/takedown-accuracy?weight_class_id=&limit=5`
- **차트 유형**: 수평 바 차트 (성공률 % + 성공/시도 수 표시)
- **데이터 소스**: `match_statistics.td_landed`, `match_statistics.td_attempted`
- **설명**: 테이크다운 성공률이 가장 높은 선수. 레슬링 기반 선수들의 핵심 지표
- **필터**: 최소 5경기 이상, 테이크다운 시도 10회 이상
- **weight_class 필터**: `JOIN match → weight_class` + `WHERE` 절 추가
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
  LIMIT :limit;  -- 기본 5, 더보기 10
  ```

---

### 10. 서브미션 기술 분포 (Submission Technique Breakdown)

- **Endpoint**: `GET /api/dashboard/submission-techniques?weight_class_id=&limit=5`
- **차트 유형**: 가로 바 차트 또는 트리맵
- **데이터 소스**: `match.method` (SUB- 접두사 경기만 필터)
- **설명**: 어떤 서브미션 기술이 가장 많이 성공하는지. Rear Naked Choke, Guillotine, Armbar 등 세부 기술별 빈도
- **weight_class 필터**: `JOIN match → weight_class` + `WHERE` 절 추가
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
  LIMIT :limit;  -- 기본 5, 더보기 10
  ```

---

### 11. 체급별 평균 컨트롤 타임 (Control Time by Weight Class)

- **Endpoint**: `GET /api/dashboard/control-time`
- **차트 유형**: 바 차트 (체급별 평균 초 단위, mm:ss로 표시)
- **데이터 소스**: `match_statistics.control_time_seconds` + `weight_class`
- **설명**: 어떤 체급에서 그라운드 컨트롤이 가장 많이 발생하는지. 체급 간 그래플링 성향 차이를 보여줌
- **weight_class 필터**: X — 모든 체급 비교가 차트의 목적
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

---

### 12. 그라운드 스트라이크 TOP 선수 (Ground Strikes Leaders)

- **Endpoint**: `GET /api/dashboard/ground-strikes?weight_class_id=&limit=5`
- **차트 유형**: 수평 바 차트
- **데이터 소스**: `strike_detail.ground_strikes_landed`
- **설명**: 그라운드에서 가장 많은 타격을 가하는 선수. 테이크다운 후 공격력을 보여주는 지표
- **필터**: 최소 5경기 이상
- **weight_class 필터**: `JOIN match → weight_class` + `WHERE` 절 추가
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
  LIMIT :limit;  -- 기본 5, 더보기 10
  ```

---

### 13. 서브미션 시도 대비 피니시율 (Submission Efficiency)

- **Endpoint**: `GET /api/dashboard/submission-efficiency?weight_class_id=&limit=5`
- **차트 유형**: 산점도 + 대각선 기준선 + 선수 라벨
  - X축: 서브미션 시도 수, Y축: 서브미션 피니시 수
  - 대각선 ReferenceLine: 전체 평균 효율(피니시/시도) 비율 — 기준선 위 = 효율적, 아래 = 비효율적
  - TOP 5 선수는 이름 라벨 표시, 나머지는 hover 툴팁
  - Recharts `ScatterChart` + `ReferenceLine` 조합
- **데이터 소스**: `match_statistics.submission_attempts` + `match.method LIKE 'SUB-%'`
- **설명**: 서브미션을 많이 시도하는 선수가 실제로 피니시도 많이 하는가? 기준선으로 효율적 피니셔와 비효율적 선수를 시각적으로 구분
- **필터**: 서브미션 시도 5회 이상, 최소 5경기 이상
- **weight_class 필터**: `JOIN match → weight_class` + `WHERE` 절 추가
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
  ORDER BY sub_finishes DESC
  LIMIT :limit;  -- 기본 5, 더보기 10
  ```

---

### 14. KO/TKO 피니시 TOP 선수 (KO/TKO Finish Leaders)

- **Endpoint**: `GET /api/dashboard/ko-tko-leaders?weight_class_id=&limit=5`
- **차트 유형**: 수평 스택 바 차트 (KO / TKO 구분)
- **데이터 소스**: `match.method` + `fighter_match.result`
- **설명**: KO/TKO 피니시를 가장 많이 기록한 선수. "가장 화끈한 파이터" 순위
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
  LIMIT :limit;  -- 기본 5, 더보기 10
  ```

---

### 15. 경기당 유효타격 TOP 선수 (Sig. Strikes Per Fight Leaders)

- **Endpoint**: `GET /api/dashboard/sig-strikes-per-fight?weight_class_id=&limit=5`
- **차트 유형**: 수평 바 차트 (경기당 유효타격 수 표시)
- **데이터 소스**: `match_statistics.sig_str_landed` + 경기 수
- **설명**: 경기당 유효타격이 가장 많은 선수. 볼륨 스트라이커 식별 지표
- **필터**: 최소 5경기 이상 출전 선수
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
  LIMIT :limit;  -- 기본 5, 더보기 10
  ```

---

## 구현 참고사항

- 프론트엔드에 이미 Recharts가 설치되어 있어 바/라인/파이/산점도/레이더 차트 구현 가능
- 레이아웃: **Layout E (Bento Grid)** 확정 — `docs/dashboard-prototype-E.html` 참조
- 백엔드 API 엔드포인트를 통계 항목별로 분리 (총 16개, 기존 #16 ko-tko-rate는 #2에 흡수)
- Redis 캐싱: TTL 7일 (데이터 변동이 적으므로 긴 TTL 적용)
- 최소 경기 수: **5경기 통일** (#7 타격 정확도, #9 테이크다운, #12 그라운드 스트라이크, #13 서브미션 효율, #15 경기당 유효타격)
- weight_class 필터 지원 엔드포인트: 11개 / 미지원: 4개 (summary, #2, #3, #11)
- `limit` 파라미터: 기본값 5 (TOP 5 표시), "더보기" 클릭 시 `limit=10` 재요청. 대상 8개: #4, #7, #9, #10, #12, #13, #14, #15
- Recharts 컴포넌트 매핑: #2 `ComposedChart`, #6 `BarChart`+`ReferenceLine`, #8 `RadarChart`, #13 `ScatterChart`+`ReferenceLine`
