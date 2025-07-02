# MMA Savant 리팩토링 TODO 목록

## 📋 개요
이 문서는 MMA Savant 프로젝트의 비즈니스 로직을 함수형 프로그래밍으로 리팩토링하고 전반적인 코드 품질을 개선하기 위한 작업 목록입니다.

---

## 🔴 높은 우선순위 (High Priority)

### 1. 데이터 변환 로직 함수형 리팩토링
**대상**: 비즈니스 로직의 데이터 변환 부분
- [ ] `src/fighter/models.py` - FighterModel의 from_schema/to_schema 메서드를 함수형으로 변경
- [ ] `src/match/models.py` - MatchModel, FighterMatchModel의 변환 로직을 함수형으로 변경
- [ ] `src/event/models.py` - EventModel의 변환 로직을 함수형으로 변경
- [ ] `src/common/models.py` - WeightClassModel의 변환 로직을 함수형으로 변경
- [ ] 공통 변환 함수 라이브러리 생성 (`src/common/transformers.py`)

### 2. Repository 패턴 함수형 개선
**대상**: 데이터 접근 로직 단순화
- [ ] Generic 함수형 repository 구현 (`src/common/repositories.py`)
  - [ ] `get_by_id[T]` 함수 구현
  - [ ] `create[T]` 함수 구현  
  - [ ] `update[T]` 함수 구현
  - [ ] `delete[T]` 함수 구현
  - [ ] `find_by_condition[T]` 함수 구현
- [ ] `src/fighter/repositories.py` - Generic 함수 기반으로 리팩토링
- [ ] `src/match/repositories.py` - Generic 함수 기반으로 리팩토링
- [ ] `src/event/repositories.py` - Generic 함수 기반으로 리팩토링
- [ ] `src/user/repositories.py` - Generic 함수 기반으로 리팩토링
- [ ] `src/conversation/repositories.py` - Generic 함수 기반으로 리팩토링

### 3. 스크래핑 파이프라인 함수형 재구성
**대상**: 데이터 수집 비즈니스 로직
- [ ] 공통 파싱 함수 라이브러리 생성 (`src/data_collector/parsers/`)
  - [ ] `validate_data()` 함수 구현
  - [ ] `normalize_text()` 함수 구현
  - [ ] `convert_units()` 함수 구현
  - [ ] `extract_attributes()` 함수 구현
- [ ] `src/data_collector/scrapers/fighter_scraper.py` - 함수형 파이프라인으로 리팩토링
- [ ] `src/data_collector/scrapers/event_scraper.py` - 함수형 파이프라인으로 리팩토링
- [ ] `src/data_collector/scrapers/match_scraper.py` - 함수형 파이프라인으로 리팩토링
- [ ] 함수 조합을 위한 compose 유틸리티 구현

### 4. 의존성 주입 시스템 구축
**대상**: 서비스 계층의 테스트 가능성 향상
- [ ] 함수형 의존성 주입 컨테이너 구현 (`src/common/container.py`)
- [ ] `src/fighter/services.py` - 함수형 의존성 주입으로 리팩토링
- [ ] `src/match/services.py` - 함수형 의존성 주입으로 리팩토링
- [ ] `src/composition/services.py` - 함수형 의존성 주입으로 리팩토링
- [ ] 서비스 팩토리 함수들 구현

---

## 🟡 중간 우선순위 (Medium Priority)

### 5. 설정 관리 함수형 개선
**대상**: 설정 로딩 및 관리 로직
- [ ] `src/config.py` - Config 클래스를 불변 데이터 클래스로 변경
- [ ] 환경별 설정 로딩 함수 구현 (`load_config()`)
- [ ] 설정 검증 함수 구현 (`validate_config()`)
- [ ] 런타임 설정 변경 방지 로직 추가

### 6. 타입 안정성 강화
**대상**: 전체 프로젝트 타입 시스템 개선
- [ ] MyPy 설정 파일 생성 (`mypy.ini`)
- [ ] `Dict[str, Any]` 사용 부분을 TypedDict로 교체
- [ ] Optional 타입 처리 개선 (None 체크 로직 추가)
- [ ] 제네릭 타입 힌트 적용
- [ ] 타입 체크 CI/CD 파이프라인 추가

---

## 🐳 인프라 개선 사항

### 7. Docker 설정 최적화
**대상**: 배포 환경 개선
- [ ] `Dockerfile_serve` Python 버전을 3.12로 통일
- [ ] 멀티스테이지 빌드 구현
  - [ ] Builder 스테이지 구현
  - [ ] Runtime 스테이지 구현
- [ ] 비루트 사용자(appuser) 생성 및 적용
- [ ] 이미지 크기 최적화
- [ ] 보안 스캔 도구 추가

---

## 🎯 성공 기준

### 코드 품질 목표
- [ ] 비즈니스 로직에서 클래스 기반 메서드 50% 이상 함수형으로 전환
- [ ] Repository 중복 코드 80% 이상 제거
- [ ] 스크래핑 파이프라인 코드 재사용성 70% 이상 향상
- [ ] MyPy 타입 체크 통과율 95% 이상
---
