# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MMA Savant는 MMA(종합격투기) 데이터 수집, 분석, AI 채팅 서비스를 제공하는 플랫폼입니다.

### 주요 구성 요소

| 구성 요소 | 기술 스택 | 위치 |
|-----------|-----------|------|
| **Frontend** | Next.js 15, React 19, TypeScript, Tailwind CSS 4 | `frontend/` |
| **Backend API** | FastAPI, SQLAlchemy (async), PostgreSQL 16 | `src/` |
| **LLM Agent** | LangChain, LangGraph, Anthropic/OpenRouter | `src/llm/` |
| **Data Collector** | Playwright, Prefect, httpx, Crawl4AI | `src/data_collector/` |
| **Database** | PostgreSQL 16, Redis 8.0 (캐싱) | Docker |
| **Infra** | Docker Compose, Nginx (리버스 프록시) | 프로젝트 루트 |

### 시스템 흐름

```
[사용자] → [Nginx :80] → [Next.js :3001] → [FastAPI :8000] → [PostgreSQL]
                                ↓                   ↓               ↓
                         NextAuth (Google)    WebSocket 채팅    Redis (캐싱)
                                ↓                   ↓
                         JWT 토큰 교환      LLM Agent (ReAct)
                                               ↓
                                        AI 응답 스트리밍
```

---

## 개발 환경

### 패키지 매니저
- **Backend**: `uv` — 반드시 `uv run python` 사용 (`python` 직접 실행 금지)
- **Frontend**: `npm`

### 서비스 실행

```bash
# 전체 서비스 (Docker)
docker-compose up -d

# Frontend 개발 서버
cd frontend && npm run dev    # Turbopack 사용

# Backend 개발 서버 (기본 포트: 8000, SERVER_PORT 환경변수로 변경 가능)
cd src && uvicorn main_api:app --reload --port 8000
```

### 테스트

```bash
# Backend 테스트 (프로젝트 루트에서)
uv run python -m pytest src/

# Frontend 린트
cd frontend && npm run lint
```

### 데이터베이스

```bash
# 테이블 초기화
cd src && uv run python database/init_tables.py
```

---

## Backend 작업 가이드

### 디렉토리 구조

**패턴**: Repository → Service → Router

```
src/
├── api/                # API 라우터 (엔드포인트 정의)
│   ├── main.py         # 라우터 등록 (8개 라우터)
│   ├── auth/           # 인증 (signup, login, Google OAuth)
│   ├── user/           # 사용자 CRUD
│   ├── chat/           # 채팅 세션 관리
│   ├── websocket/      # WebSocket 매니저, 실시간 채팅
│   ├── admin/          # 관리자 API (사용자 관리, 캐시 무효화)
│   ├── dashboard/      # 대시보드 통계 (4개 탭 집계)
│   ├── fighter/        # 파이터 상세
│   └── event/          # 이벤트 상세
│
├── fighter/            # 파이터 도메인
├── match/              # 매치 도메인
├── event/              # 이벤트 도메인
├── user/               # 사용자 도메인
├── conversation/       # 대화 도메인
├── dashboard/          # 대시보드 도메인 (models.py 없음, 집계 전용)
│
├── common/             # 공통 유틸리티
│   ├── base_model.py   # BaseModel (SQLAlchemy), BaseSchema (Pydantic)
│   ├── models.py       # WeightClassSchema (16개 체급 매핑)
│   ├── enums.py        # WeightClassEnum, LLMProvider
│   └── utils.py        # utc_now, normalize_name, @with_retry 등
│
├── database/           # DB 연결
│   └── connection/
│       ├── postgres_conn.py  # async/sync 엔진, 세션 팩토리
│       └── redis_conn.py     # Redis 클라이언트, 커넥션 풀
│
├── llm/                # LLM/AI 레이어
│   ├── agent_manager.py     # 2-Phase ReAct 에이전트
│   ├── langchain_service.py # LLM 서비스 팩토리
│   ├── model_factory.py     # 프로바이더별 모델 생성
│   ├── prompts.py           # Phase 1/2 프롬프트 템플릿
│   ├── stream_processor.py  # 응답 스트리밍 처리
│   ├── providers/           # Anthropic, HuggingFace, OpenRouter, OpenAI
│   └── tools/               # SQL 실행 도구 (LangChain Tool)
│
├── data_collector/     # 데이터 수집 파이프라인
│   ├── scrapers/       # Playwright/httpx 스크래퍼 (fighters, events, matches, rankings)
│   ├── workflows/      # Prefect 워크플로우 (ufc_stats_flow, tasks, data_store)
│   ├── scripts/        # geocode_events, scrape_nationality
│   └── main.py         # 스케줄러 (매주 수요일)
│
├── config.py           # 환경 설정 (DB, Redis, LLM, Auth, Admin)
├── main_api.py         # FastAPI 앱 초기화 (CORS, lifespan)
└── tests/              # 테스트 (도메인별 하위 디렉토리)
```

### 도메인 디렉토리 표준 구조

각 도메인 디렉토리는 기본 6개 파일로 구성:

```
{domain}/
├── __init__.py
├── models.py          # SQLAlchemy 모델 + Pydantic 스키마 (같은 파일)
├── repositories.py    # DB 접근 레이어 (raw SQL/ORM 쿼리)
├── services.py        # 비즈니스 로직 (여러 repository 조합)
├── dto.py             # Data Transfer Objects (API 요청/응답)
└── exceptions.py      # 도메인별 예외 클래스
```

**예외**: `dashboard/`는 집계 전용이라 `models.py` 없음, `conversation/`은 `message_manager.py` 추가 보유

### DB 세션 사용

```python
# FastAPI 라우터에서 (의존성 주입)
from database.connection.postgres_conn import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession

@router.get("/endpoint")
async def handler(session: AsyncSession = Depends(get_async_db)):
    result = await SomeRepository.some_method(session)
    return result
```

```python
# 서비스/유틸에서 (컨텍스트 매니저)
from database.connection.postgres_conn import get_async_db_context

async with get_async_db_context() as session:
    result = await SomeRepository.some_method(session)
```

### Redis 캐싱

```python
from database.connection.redis_conn import redis_client

# 동기 클라이언트 (대시보드 캐싱에 사용)
cached = redis_client.get("cache_key")
redis_client.setex("cache_key", 604800, json_data)  # 7일 TTL
```

### 등록된 라우터 (src/api/main.py)

| 라우터 | 경로 접두사 | 설명 |
|--------|------------|------|
| `auth_router` | `/api/user` | 회원가입, 로그인, Google OAuth |
| `user_router` | `/api/user` | 사용자 프로필, 사용량 |
| `chat_router` | `/api/chat` | 채팅 세션 CRUD |
| `websocket_router` | `/ws/chat` | WebSocket 실시간 채팅 |
| `admin_router` | `/api/admin` | 관리자 전용 API |
| `dashboard_router` | `/api/dashboard` | 대시보드 통계 (4개 탭) |
| `fighter_router` | `/api/fighters` | 파이터 상세 |
| `event_router` | `/api/events` | 이벤트 상세 |

---

## Frontend 작업 가이드

### 디렉토리 구조

**패턴**: hooks → services → components → pages

```
frontend/src/
├── app/                     # Next.js App Router 페이지
│   ├── page.tsx             # 메인 대시보드
│   ├── chat/                # AI 채팅 페이지 (보호됨)
│   ├── fighters/[id]/       # 파이터 상세 페이지
│   ├── events/[id]/         # 이벤트 상세 페이지
│   ├── profile/             # 프로필 페이지 (보호됨)
│   ├── settings/            # 설정/관리자 페이지
│   ├── auth/signin/         # 로그인
│   ├── auth/signup/         # 회원가입
│   └── api/auth/[...nextauth]/ # NextAuth API 라우트
│
├── components/
│   ├── dashboard/           # 대시보드 (4개 탭, 25+ 차트)
│   │   ├── ChartCard.tsx    # 차트 래퍼 (framer-motion 애니메이션)
│   │   ├── ChartTooltip.tsx # 공통 Recharts 툴팁
│   │   ├── PillTabs.tsx     # 탭 네비게이션 (애니메이션 인디케이터)
│   │   ├── StatCard.tsx     # KPI 카드 (CountUp 애니메이션)
│   │   ├── home/            # 홈 탭 (요약, 이벤트, 랭킹)
│   │   ├── overview/        # 오버뷰 탭 (피니시, 체급, 타임라인)
│   │   ├── striking/        # 타격 탭 (정확도, KO, 녹다운)
│   │   └── grappling/       # 그래플링 탭 (테이크다운, 서브미션)
│   ├── fighter/             # 파이터 상세 (프로필, 전적, 차트)
│   ├── event/               # 이벤트 상세 (헤더, 요약, 파이트카드)
│   ├── chat/                # 채팅 UI (메시지, 세션, 시각화)
│   ├── visualization/       # AI 응답 차트 렌더러 (Bar, Line, Pie, Scatter, Table)
│   ├── auth/                # 인증 컴포넌트 (LoginForm, AuthGuard)
│   ├── admin/               # 관리자 (UserTable, AdminStats)
│   ├── layout/              # GlobalNav
│   ├── ui/                  # shadcn/ui + Radix UI 기본 컴포넌트
│   └── providers/           # SessionProvider
│
├── hooks/                   # 커스텀 훅
│   ├── useAuth.ts           # 인증 상태 (NextAuth + localStorage)
│   ├── useDashboard.ts      # 대시보드 데이터 페칭 + 캐싱
│   ├── useFighterDetail.ts  # 파이터 상세 데이터
│   ├── useEventDetail.ts    # 이벤트 상세 데이터
│   ├── useChatSession.ts    # 채팅 세션 CRUD
│   ├── useSocket.ts         # WebSocket 스트리밍
│   ├── useUser.ts           # 사용자 프로필/사용량
│   └── useChartFilter.ts    # 체급 필터 상태
│
├── services/                # API 클라이언트
│   ├── dashboardApi.ts      # /api/dashboard/* (4개 탭 집계)
│   ├── fighterApi.ts        # /api/fighters/{id}
│   ├── eventApi.ts          # /api/events/{id}
│   ├── chatApi.ts           # /api/chat/* (세션, 히스토리)
│   ├── authApi.ts           # 인증 (signup, login, logout)
│   ├── userApi.ts           # 사용자 프로필
│   └── adminApi.ts          # 관리자 API
│
├── store/                   # Zustand 상태 관리
│   ├── authStore.ts         # 인증 상태
│   └── chatStore.ts         # 채팅 메시지, 세션, 스트리밍
│
├── types/                   # TypeScript 타입
│   ├── dashboard.ts         # 대시보드 응답 타입 (40+ 인터페이스)
│   ├── fighter.ts           # 파이터 상세 타입
│   ├── event.ts             # 이벤트 상세 타입
│   ├── chat.ts              # 채팅 메시지/세션 타입
│   ├── api.ts               # API 응답 공통 타입
│   ├── auth.ts              # 인증 타입
│   └── error.ts             # 에러 타입
│
├── lib/                     # 유틸리티
│   ├── api.ts               # fetch 래퍼 (Bearer 토큰, 에러 처리)
│   ├── auth.ts              # NextAuth 설정 (Google OAuth)
│   ├── utils.ts             # cn(), toTitleCase(), formatDate(), 색상 토큰
│   ├── realSocket.ts        # Socket.IO 클라이언트
│   └── visualizationParser.ts # AI 응답에서 차트 JSON 추출
│
└── config/
    └── env.ts               # 환경 변수 (NEXT_PUBLIC_API_URL)
```

### 주요 프론트엔드 라이브러리

| 라이브러리 | 용도 |
|-----------|------|
| `recharts` 3.x | 대시보드/AI 차트 시각화 |
| `framer-motion` 12.x | 컴포넌트 애니메이션 (입장, 호버, 탭 전환) |
| `react-countup` 6.x | 숫자 카운트업 애니메이션 |
| `zustand` 5.x | 상태 관리 (auth, chat) |
| `next-auth` 5.x-beta | Google OAuth 인증 |
| `socket.io-client` 4.x | WebSocket 실시간 채팅 |
| `leaflet` 1.9 | 이벤트 지도 시각화 |
| `lucide-react` | 아이콘 |
| `@radix-ui/*` | 헤드리스 UI 컴포넌트 |

### 공통 유틸리티 (`frontend/src/lib/utils.ts`)

| 함수/상수 | 설명 |
|-----------|------|
| `cn()` | Tailwind 클래스 병합 (clsx + tailwind-merge) |
| `toTitleCase()` | 소문자 이름 → Title Case 변환 |
| `formatDate()` | ISO 날짜 → "Nov 15, 2025" 형식 |
| `abbreviateWeightClass()` | 체급명 → 약어 (예: "Lightweight" → "LW") |
| `FINISH_COLORS` | 피니시 방식별 색상 (KO: red, SUB: purple, DEC: cyan) |
| `CHART_COLORS` | 대시보드 차트 색상 토큰 |

### Badge 시맨틱 variant

`frontend/src/components/ui/badge.tsx`에 정의된 variant:
- `ko`, `submission`, `decision` — 피니시 방식별
- `win`, `loss`, `draw` — 승패 결과별
- `champion`, `ranking` — 타이틀/랭킹

---

## 인증 관련 작업 시

**인증 플로우**:
```
1. 사용자 → Google OAuth 로그인 (NextAuth)
2. Frontend → POST /api/auth/google-token (Google 토큰 전송)
3. Backend → JWT 토큰 발급 (24시간 유효)
4. Frontend → Authorization: Bearer <jwt> 헤더로 API 호출
```

**관련 파일**:
- Frontend: `frontend/src/lib/auth.ts`, `frontend/src/lib/api.ts`
- Backend: `src/api/auth/routes.py`, `src/auth/dependencies.py`

---

## WebSocket 채팅 작업 시

**연결**: `ws://localhost:8000/ws/chat?token={jwt}&conversation_id={id}`

**이벤트 흐름**:
```
Client → "message" (질문)
Server → "thinking_start" → "stream_chunk"(반복) → "stream_end"
```

**AI 에이전트**: 2-Phase ReAct 패턴
- Phase 1: 의도 분석 + SQL 도구 실행 (LangGraph)
- Phase 2: 결과 처리 + 시각화 데이터 생성

**관련 파일**:
- Frontend: `frontend/src/lib/realSocket.ts`, `frontend/src/hooks/useSocket.ts`
- Backend: `src/api/websocket/manager.py`, `src/llm/agent_manager.py`

---

## 대시보드 작업 시

**4개 탭 구성** (각 탭은 집계 API 1개 호출):

| 탭 | 엔드포인트 | 주요 차트 |
|----|-----------|----------|
| Home | `GET /api/dashboard/home` | 요약 통계, 최근/예정 이벤트, 랭킹, 국적 분포, 지도 |
| Overview | `GET /api/dashboard/overview` | 피니시 방법, 체급 활동, 타임라인, 리더보드, 경기 시간 |
| Striking | `GET /api/dashboard/striking` | 타격 정확도, KO/TKO, 녹다운, 유효 타격, 스탠스 승률 |
| Grappling | `GET /api/dashboard/grappling` | 테이크다운, 서브미션, 컨트롤 타임, 그라운드 타격 |

**캐싱**: Redis 7일 TTL, 관리자 API로 수동 무효화 가능
**필터**: `weight_class_id`, `min_fights`, `limit` 쿼리 파라미터

---

## 환경 변수

### Backend (`src/.env`)
```
# Database
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=ufc_stats

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Auth
NEXTAUTH_SECRET=your_secret      # JWT 서명 (Frontend와 공유)
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24시간

# LLM
LLM_PROVIDER=anthropic            # anthropic | openrouter | openai | huggingface
ANTHROPIC_API_KEY=your_key
OPENROUTER_API_KEY=your_key

# Admin
ADMIN_USERNAME=admin
ADMIN_PW=your_password
```

### Frontend (`frontend/.env.local`)
```
NEXTAUTH_SECRET=your_secret
NEXTAUTH_URL=http://localhost:3000
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 문서 참조

| 문서 | 내용 | 참조 시점 |
|------|------|----------|
| `docs/API_INTERFACE.md` | API 엔드포인트 명세 (인증, 사용자, 채팅, WebSocket, Admin) | API 추가/수정, 프론트엔드 연동 |
| `docs/DASHBOARD_STATS.md` | 대시보드 4개 탭 통계 쿼리 명세 (36+ 차트) | 대시보드 차트 추가/수정 |
| `docs/DESIGN_SYSTEM.md` | 프론트엔드 디자인 시스템 (색상, 타이포, 컴포넌트) | UI 작업, 스타일 일관성 |

---

## 주의사항

### Frontend ↔ Backend 타입 동기화
- Backend DTO (`src/{domain}/dto.py`) 변경 시 Frontend 타입 (`frontend/src/types/`) 동기화 필요
- 예: `src/fighter/dto.py` → `frontend/src/types/fighter.ts`

### 필드명 컨벤션
- 프로필 이미지: `picture` (Backend/Frontend 모두)
- 날짜/시간: ISO 8601 형식 (`created_at`, `updated_at`)
- 파이터 이름: DB에는 소문자, 프론트엔드에서 `toTitleCase()` 적용

### 체급 (Weight Class)
- `src/common/models.py`의 `WeightClassSchema`에 16개 체급 ID 매핑
- 프론트엔드 약어 매핑: `frontend/src/lib/utils.ts`의 `WEIGHT_CLASS_ABBR`

### 대시보드 캐싱
- Redis 7일 TTL로 캐싱 (`dashboard/services.py`)
- 인증 불필요 (공개 API)
- 캐시 무효화: Admin API 또는 TTL 만료
