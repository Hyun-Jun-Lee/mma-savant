# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MMA Savant는 MMA(종합격투기) 데이터 수집, 분석, AI 채팅 서비스를 제공하는 플랫폼입니다.

### 주요 구성 요소

| 구성 요소 | 기술 스택 | 위치 |
|-----------|-----------|------|
| **Frontend** | Next.js 15, React 19, TypeScript, Tailwind CSS | `frontend/` |
| **Backend API** | FastAPI, SQLAlchemy, PostgreSQL | `src/` |
| **Data Collector** | Playwright, Prefect, httpx | `src/data_collector/` |
| **Database** | PostgreSQL, Redis (캐싱) | Docker |

### 시스템 흐름

```
[사용자] → [Next.js Frontend] → [FastAPI Backend] → [PostgreSQL]
              ↓                        ↓
         NextAuth (Google)      WebSocket (실시간 채팅)
              ↓                        ↓
         JWT 토큰 교환           AI 응답 스트리밍
```

---

## 주요 작업별 가이드

### Backend 작업 시

**디렉토리**: `src/`

**패턴**: Repository → Service → Router

```
src/
├── user/           # 사용자 관리 (OAuth, 프로필, 사용량)
├── auth/           # JWT 인증, 의존성
├── chat/           # 채팅 세션, 메시지
├── conversation/   # 대화 관리
├── admin/          # 관리자 API
└── database/       # DB 세션, 초기화
```

**주요 파일**:
- `src/user/models.py` - User 스키마/모델 정의
- `src/auth/dependencies.py` - `get_current_user` 등 인증 의존성
- `src/config.py` - 환경 설정

**DB 세션 사용**:
```python
from database.session import get_async_session

async with get_async_session() as session:
    # DB 작업
    pass
```

---

### Frontend 작업 시

**디렉토리**: `frontend/src/`

**패턴**: hooks → components → pages

```
frontend/src/
├── app/            # Next.js App Router 페이지
│   ├── chat/       # 채팅 페이지 (보호됨)
│   ├── profile/    # 프로필 페이지 (보호됨)
│   └── auth/       # 로그인 페이지
├── components/     # React 컴포넌트
│   ├── chat/       # 채팅 UI
│   ├── profile/    # 프로필 UI
│   └── ui/         # shadcn/ui 기본 컴포넌트
├── hooks/          # 커스텀 훅 (useAuth, useSocket, useChatSession, useUser)
├── services/       # API 클라이언트 (chatApi, userApi)
├── store/          # Zustand 상태 관리
└── types/          # TypeScript 타입 정의
```

**주요 파일**:
- `frontend/src/types/api.ts` - API 응답 타입 (Backend와 일치 필요)
- `frontend/src/lib/auth.ts` - NextAuth 설정
- `frontend/src/services/userApi.ts` - 사용자 API 호출

---

### 인증 관련 작업 시

**인증 플로우**:
```
1. 사용자 → Google OAuth 로그인 (NextAuth)
2. Frontend → POST /api/auth/google-token (Google 토큰 전송)
3. Backend → JWT 토큰 발급 (24시간 유효)
4. Frontend → Authorization: Bearer <jwt> 헤더로 API 호출
```

**관련 파일**:
- Frontend: `frontend/src/lib/auth.ts`, `frontend/src/lib/api.ts`
- Backend: `src/auth/jwt_handler.py`, `src/auth/dependencies.py`

---

### WebSocket 채팅 작업 시

**연결**: `ws://localhost:8002/ws/chat?token={jwt}&conversation_id={id}`

**이벤트 흐름**:
```
Client → "message" (질문)
Server → "thinking_start" → "stream_chunk"(반복) → "stream_end"
```

**관련 파일**:
- Frontend: `frontend/src/lib/realSocket.ts`, `frontend/src/hooks/useSocket.ts`
- Backend: `src/websocket/` 디렉토리

---

### Data Collector 작업 시

**디렉토리**: `src/data_collector/`

```
src/data_collector/
├── scrapers/       # Playwright 스크래퍼
├── workflows/      # Prefect 워크플로우
└── main.py         # 스케줄러 (매주 수요일)
```

**실행**:
```bash
cd src/data_collector
python main.py
```

---

## 개발 명령어

### 서비스 실행

```bash
# 전체 서비스 (Docker)
docker-compose up -d

# Frontend 개발 서버
cd frontend && npm run dev

# Backend 개발 서버
cd src && uvicorn main:app --reload --port 8002
```

### 테스트

```bash
# Backend 테스트
python -m pytest src/

# Frontend 테스트 (설정 필요)
cd frontend && npm test
```

### 데이터베이스

```bash
# 테이블 초기화
cd src && python database/init_tables.py
```

---

## 환경 변수

### Backend (`src/.env`)
```
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=ufc_stats
REDIS_HOST=localhost
REDIS_PORT=6379
NEXTAUTH_SECRET=your_secret  # JWT 서명 (Frontend와 공유)
```

### Frontend (`frontend/.env.local`)
```
NEXTAUTH_SECRET=your_secret
NEXTAUTH_URL=http://localhost:3000
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
NEXT_PUBLIC_API_URL=http://localhost:8002
NEXT_PUBLIC_WS_URL=ws://localhost:8002
```

---

## 문서 참조

### docs/API_INTERFACE.md

API 엔드포인트 명세서. 다음 내용 포함:
- **Authentication**: Google OAuth → JWT 토큰 교환
- **User Management**: 프로필 조회/수정, 사용량 추적
- **Chat Session**: 세션 CRUD, 메시지 히스토리
- **WebSocket**: 실시간 채팅 프로토콜, 이벤트 타입
- **Admin API**: 사용자 관리, 시스템 통계

**참조 시점**: API 추가/수정, 프론트엔드 연동, 에러 코드 확인


## 주의사항

### Frontend ↔ Backend 타입 동기화
`frontend/src/types/api.ts`의 타입은 Backend 스키마와 일치해야 합니다.
- Backend: `src/user/models.py` → `UserProfileResponse`
- Frontend: `frontend/src/types/api.ts` → `UserProfileResponse`

### 필드명 컨벤션
- 프로필 이미지: `picture` (Backend/Frontend 모두)
- 날짜/시간: ISO 8601 형식 (`created_at`, `updated_at`)
