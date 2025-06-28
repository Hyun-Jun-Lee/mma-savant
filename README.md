# MMA Savant 프로젝트 구조

MMA Savant는 종합격투기(MMA) 데이터를 수집하고 분석하는 플랫폼입니다. 이 프로젝트는 크게 두 부분으로 나뉩니다:
1. `crawlers`: 데이터 수집을 담당하는 크롤러
2. `src`: 웹 서비스 API 및 백엔드 로직

## 전체 구조

```
mma-savant/
├── crawlers/            # 데이터 수집 크롤러
├── src/                 # 백엔드 API 서비스
├── docker-compose.yml   # 도커 컴포즈 설정
├── init_table.sql       # 데이터베이스 테이블 생성 SQL
└── README.md            # 프로젝트 설명
```

## Crawlers

크롤러는 MMA 데이터를 외부 사이트에서 수집하고 데이터베이스에 저장합니다.

```
crawlers/
├── alembic/             # 데이터베이스 마이그레이션
├── core/                # 코어 크롤링 기능
├── data/                # 저장된 데이터 파일
├── database/            # 데이터베이스 연결 관리
├── downloaded_pages/    # 다운로드된 웹 페이지
├── models/              # SQLAlchemy 모델 정의
│   ├── base.py          # 기본 모델 클래스
│   ├── event_model.py   # 이벤트 모델
│   ├── fighter_model.py # 파이터 및 랭킹 모델
│   ├── match_model.py   # 경기 관련 모델
│   └── weight_class_model.py  # 체급 모델
├── output/              # 출력 결과 저장
├── repository/          # 데이터 저장소 패턴 구현
│   ├── base_repository.py     # 기본 저장소 클래스
│   ├── fighter_repository.py  # 파이터 저장소
│   └── ranking_repository.py  # 랭킹 저장소
├── sample_data/         # 샘플 데이터
├── schemas/             # Pydantic 스키마
├── scrapers/            # 웹 스크래퍼 모듈
│   ├── ranking_scraper.py     # 랭킹 정보 스크래퍼
│   └── ... (기타 스크래퍼)
├── workflows/           # 작업 흐름 관리
├── entrypoint.sh        # 컨테이너 진입점 스크립트
├── init_weight_classes.py     # 체급 초기화 스크립트
└── main.py              # 메인 실행 파일
```

## Source (Backend API)

백엔드 API 서비스는 크롤링된 데이터를 활용하여 웹 서비스를 제공합니다.

```
src/
├── common/              # 공통 유틸리티
├── composition/         # 의존성 주입 컴포지션
├── conversation/        # 대화형 API 기능
├── database/            # 데이터베이스 연결 관리
├── event/               # 이벤트 관련 API
├── exceptions/          # 예외 처리
├── fighter/             # 파이터 관련 API
│   ├── dto.py           # 데이터 전송 객체
│   ├── models.py        # 모델 정의
│   ├── repositories.py  # 저장소 구현
│   ├── routers.py       # API 라우터
│   └── services.py      # 서비스 로직
├── match/               # 경기 관련 API
├── tools/               # 유틸리티 도구
├── user/                # 사용자 관리
├── config.py            # 설정 관리
└── main.py              # 메인 API 서버
```

## 데이터베이스 스키마

프로젝트는 다음과 같은 주요 테이블을 사용합니다:

- `fighter`: 파이터 정보 저장
- `weight_class`: 체급 정보 저장
- `event`: 이벤트 정보 저장
- `match`: 경기 정보 저장
- `ranking`: 파이터 랭킹 정보 저장
- `fighter_match`: 파이터와 경기 관계 저장
- `strike_detail`: 스트라이크 상세 통계 저장
- `match_statistics`: 경기 통계 저장

데이터베이스 스키마는 `init_table.sql`에 정의되어 있으며, 외래 키 제약 조건과 인덱스를 통해 데이터 무결성과 쿼리 성능을 보장합니다.

## 실행 방법

프로젝트는 Docker를 통해 실행할 수 있으며, `docker-compose.yml` 파일에 정의된 서비스를 통해 전체 스택을 구동할 수 있습니다.

```bash
docker-compose up -d
```
