# MMA Savant Development TODO

## 📋 개요
이 문서는 MMA Savant 프로젝트의 아키텍처 개선과 코드 품질 향상을 위한 작업 목록입니다. 모든 작업은 `docs/SPEC.md`에 정의된 아키텍처 가이드라인을 준수해야 합니다.

---

## 🔴 높은 우선순위 (High Priority)

### 1. Domain 완성도 향상
**대상**: 현재 도메인의 누락된 구성 요소 보완

#### 1.1 create dto & adjust in service
- [x] `src/event/dto.py` - Event 관련 DTO 클래스 생성
- [x] `src/event/services.py` - Event 서비스 레이어 구현
- [x] `src/match/dto.py` - Match 관련 DTO 클래스 생성
- [x] `src/match/services.py` - Match 서비스 레이어 DTO 반영
- [x] `src/composition/dto.py` - Composition 관련 DTO 클래스 생성
- [x] `src/composition/event_composer.py` - event_composer에 필요한 dto 생성 및 서비스 레이어 DTO 반영
- [x] `src/tests/composer/test_event_composer.py` - event_composer 테스트 작성
- [x] `src/composition/match_composer.py` - match_composer에 필요한 dto 생성 및 서비스 레이어 DTO 반영
- [x] `src/tests/composer/test_match_composer.py` - match_composer 테스트 작성
- [x] `src/composition/fighter_composer.py` - fighter_composer에 필요한 dto 생성 및 서비스 레이어 DTO 반영
- [x] `src/tests/composer/test_fighter_composer.py` - fighter_composer 테스트 작성

#### 1.2 tools 구현
- [x] `src/tools/event_tools.py` - event_tools 구현
- [x] `src/tools/match_tools.py` - match_tools 구현
- [x] `src/tools/fighter_tools.py` - fighter_tools 구현
- [x] `src/tools/composition_tools.py` - composition_tools 구현


#### 1.3 Exception Handling
- [x] `src/event/exceptions.py` - Event 도메인 예외 생성
- [x] `src/event/services.py` - Event 도메인 예외 service 적용
- [x] `src/tests/event/test_event_services.py` - Event 도메인 예외 service 테스트
- [x] `src/match/exceptions.py` - Match 도메인 예외 생성
- [x] `src/match/services.py` - Match 도메인 예외 service 적용
- [x] `src/tests/match/test_match_services.py` - Match 도메인 예외 service 테스트
- [x] `src/fighter/exceptions.py` - Fighter 도메인 예외 생성
- [x] `src/fighter/services.py` - Fighter 도메인 예외 service 적용
- [x] `src/tests/fighter/test_fighter_services.py` - Fighter 도메인 예외 service 테스트
- [x] `src/composition/exceptions.py` - Composition 도메인 예외 생성
- [x] `src/composition/*_composer.py` - Composition 도메인 예외 composer 적용
- [x] `src/tests/composer/test_*.py` - Composition 도메인 예외 composer 테스트


#### 1.4 User & Conversation
- [x] `src/user/repositories.py` - User Repository 구현 (로그인, 회원가입, 기본 CURD)
- [ ] `src/conversation/repositories.py` - Conversation Repository 구현
- [ ] `src/user/services.py` - User 서비스 레이어 구현
- [ ] `src/conversation/services.py` - Conversation 서비스 레이어 구현
- [ ] `src/user/exceptions.py` - User 도메인 예외 생성
- [ ] `src/conversation/exceptions.py` - Conversation 도메인 예외 생성


### 2. Repository 패턴 일관성 개선
**대상**: 현재 Repository 함수들의 일관성 향상

#### 2.1 Repository Function Standardization
- [ ] `src/match/repositories.py` - 함수 시그니처 SPEC 준수로 수정
- [ ] `src/event/repositories.py` - 함수 시그니처 SPEC 준수로 수정
- [ ] `src/user/repositories.py` - 함수 시그니처 SPEC 준수로 수정
- [ ] `src/conversation/repositories.py` - 함수 시그니처 SPEC 준수로 수정

#### 2.2 Repository Response Standardization
- [ ] 모든 Repository 함수가 Schema 객체만 반환하도록 수정
- [ ] SQLAlchemy 모델 직접 반환 제거
- [ ] 에러 핸들링을 서비스 레이어로 이동

### 3. 스크래핑 워크플로우 개선
**대상**: 데이터 수집 비즈니스 로직 아키텍처 준수

#### 3.1 Workflow Architecture Compliance
- [ ] `src/data_collector/workflows/tasks.py` - 함수들을 SPEC 패턴에 맞게 리팩토링
- [ ] `src/data_collector/scrapers/` - 각 스크래퍼를 순수 함수로 변환
- [ ] 스크래핑 결과 검증 로직을 별도 함수로 분리
- [ ] 데이터 변환 로직을 별도 함수로 분리

#### 3.2 Error Handling in Scrapers
- [ ] 스크래핑 관련 예외 클래스 생성 (`src/data_collector/exceptions.py`)
- [ ] 네트워크 오류, 파싱 오류 등 세분화된 예외 처리
- [ ] 재시도 로직 구현

### 4. 테스트 커버리지 향상
**대상**: SPEC 가이드라인에 따른 테스트 구축

#### 4.1 Repository Layer Tests
- [ ] `src/fighter/test/` - Repository 함수들에 대한 테스트 추가
- [ ] `src/match/test/` - Repository 테스트 생성
- [ ] `src/event/test/` - Repository 테스트 생성
- [ ] `src/user/test/` - Repository 테스트 생성
- [ ] `src/conversation/test/` - Repository 테스트 생성

#### 4.2 Service Layer Tests
- [ ] 각 도메인의 서비스 레이어 테스트 구현
- [ ] 예외 상황 테스트 케이스 추가
- [ ] 비즈니스 로직 검증 테스트 추가

---

## 🟡 중간 우선순위 (Medium Priority)

### 5. Composition Layer 확장
**대상**: 크로스 도메인 비즈니스 로직 개선

#### 5.1 Additional Composition Functions
- [ ] `src/composition/event_composer.py` - 이벤트 관련 컴포지션 함수 추가
- [ ] `src/composition/match_composer.py` - 경기 관련 컴포지션 함수 생성
- [ ] `src/composition/analytics_composer.py` - 분석 관련 컴포지션 함수 생성

#### 5.2 Performance Optimization
- [ ] 컴포지션 함수에서 N+1 쿼리 문제 해결
- [ ] 배치 처리 로직 구현
- [ ] 캐싱 전략 구현

### 6. 타입 안정성 강화
**대상**: 전체 프로젝트 타입 시스템 개선

#### 6.1 Type Hints Completion
- [ ] `src/data_collector/` - 모든 함수에 완전한 타입 힌트 추가
- [ ] `src/tools/` - 타입 힌트 추가
- [ ] `src/common/` - 타입 힌트 보완

#### 6.2 Type Safety Tools
- [ ] MyPy 설정 파일 생성 (`mypy.ini`)
- [ ] `Dict[str, Any]` 사용 부분을 TypedDict로 교체
- [ ] Optional 타입 처리 개선
- [ ] 타입 체크 CI/CD 파이프라인 추가

### 7. 설정 관리 개선
**대상**: 설정 로딩 및 관리 로직

#### 7.1 Configuration Standardization
- [ ] `src/config.py` - 환경별 설정 분리
- [ ] 설정 검증 로직 추가
- [ ] 설정 로딩 에러 핸들링 개선

---

## 🟢 낮은 우선순위 (Low Priority)

### 8. 문서화 개선
**대상**: 코드 문서화 및 가이드 보완

#### 8.1 API Documentation
- [ ] 각 도메인 서비스의 API 문서 생성
- [ ] DTO 클래스 사용 예시 문서 작성
- [ ] 컴포지션 함수 사용 가이드 작성

#### 8.2 Architecture Documentation
- [ ] 도메인 간 의존성 다이어그램 생성
- [ ] 데이터 플로우 다이어그램 생성
- [ ] 배포 가이드 문서 작성

### 9. 성능 최적화
**대상**: 시스템 성능 개선

#### 9.1 Database Optimization
- [ ] 인덱스 최적화 검토
- [ ] 쿼리 성능 분석 도구 도입
- [ ] 데이터베이스 연결 풀 최적화

#### 9.2 Caching Strategy
- [ ] Redis 캐싱 구현
- [ ] 메모리 캐싱 전략 수립
- [ ] 캐시 무효화 로직 구현

---

## 🐳 인프라 개선 사항

### 10. Docker 설정 최적화
**대상**: 배포 환경 개선
- [ ] `Dockerfile_serve` 멀티스테이지 빌드 구현
- [ ] 비루트 사용자 설정
- [ ] 이미지 크기 최적화
- [ ] 보안 스캔 도구 추가

### 11. CI/CD 파이프라인 구축
**대상**: 개발 워크플로우 개선
- [ ] GitHub Actions 워크플로우 구성
- [ ] 자동 테스트 실행
- [ ] 코드 품질 검사 도구 연동
- [ ] 자동 배포 파이프라인 구축

---

## 🎯 성공 기준

### 아키텍처 준수 목표
- [ ] 모든 도메인이 SPEC.md 구조를 완전히 준수
- [ ] Repository 레이어 100% Schema 객체 반환 준수
- [ ] 서비스 레이어 100% 도메인 예외 사용
- [ ] 모든 함수에 완전한 타입 힌트 적용

### 코드 품질 목표
- [ ] 테스트 커버리지 80% 이상 달성
- [ ] MyPy 타입 체크 통과율 95% 이상
- [ ] 도메인 간 의존성 순환 참조 0개 유지
- [ ] 컴포지션 함수 성능 최적화 (N+1 쿼리 제거)

---

**참고**: 모든 작업은 `docs/SPEC.md`에 정의된 아키텍처 가이드라인을 준수해야 하며, 기존 코드를 수정할 때는 해당 도메인의 전체 구조를 고려하여 일관성을 유지해야 합니다.
