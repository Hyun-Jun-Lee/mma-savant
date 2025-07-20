# MMA Savant 백엔드 API 구현 계획

## 📋 프로젝트 개요
MMA Savant 챗봇 서비스의 백엔드 API 구현 계획서

**기존**: FastAPI + PostgreSQL (MMA 데이터 수집)  
**추가**: 채팅 API + WebSocket + 사용자 관리  
**LLM 연동**: OpenAI/Claude API + Tool 기반 MMA 데이터 조회  

---

## 🛠️ 기술 스택

### Backend Core
- **FastAPI** (기존 확장)
- **PostgreSQL** (기존 DB 확장)
- **Redis** (세션 및 캐싱)
- **WebSocket** (실시간 채팅)

### Authentication & Security
- **JWT 토큰** (NextAuth.js 연동)
- **OAuth 2.0** (Google 로그인)
- **CORS 설정**

### LLM Integration
- **OpenAI API** 또는 **Claude API**
- **Function Calling/Tools** (MMA 데이터 조회)
- **Streaming Response** (실시간 응답)

---

## 🎯 API 구현 TODO

### Phase 1: 기본 인증 및 사용자 관리 (1-2일) ✅ 완료

#### 1.1 JWT 토큰 검증 미들웨어
- [x] NextAuth.js JWT 토큰 검증 로직 구현 (`src/api/auth/jwt_handler.py`)
- [x] 토큰 만료 및 갱신 처리
- [x] 인증 데코레이터/의존성 주입 구현 (`src/api/auth/dependencies.py`)

#### 1.2 사용자 관리 API
- [x] **GET /api/user/profile** - 사용자 프로필 조회
  ```python
  # Headers: Authorization: Bearer {jwt_token}
  # Response: {"id": int, "email": str, "name": str, "picture": str, "created_at": datetime}
  ```
- [x] **PUT /api/user/profile** - 사용자 프로필 업데이트
  ```python
  # Body: {"name": str, "picture": str}
  # Response: {"success": bool, "user": UserProfileResponse}
  ```
- [x] **GET /api/user/me** - 현재 사용자 정보 조회 (별칭)
- [x] **POST /api/user/increment-usage** - 사용자 요청 횟수 증가
- [x] **GET /api/user/check-auth** - 인증 상태 확인

#### 1.3 데이터베이스 스키마 확장
- [x] `user` 테이블 OAuth 필드 확장 (`email`, `name`, `picture`, `provider_id`, `provider`)
- [x] NextAuth.js 호환 사용자 스키마 정의 (`src/user/models.py`)
- [x] OAuth 사용자 리포지토리 함수 추가 (`src/user/repositories.py`)
- [x] OAuth 사용자 서비스 로직 구현 (`src/user/services.py`)

---

### Phase 2: 채팅 세션 관리 (1-2일) ✅ 완료

#### 2.1 채팅 세션 API
- [x] **POST /api/chat/session** - 새 채팅 세션 생성
  ```python
  # Headers: Authorization: Bearer {jwt_token}
  # Body: {"title": str} (optional)
  # Response: ChatSessionResponse
  ```
- [x] **GET /api/chat/sessions** - 사용자 채팅 세션 목록
  ```python
  # Query: ?limit=20&offset=0
  # Response: {"sessions": [ChatSessionResponse], "total_sessions": int}
  ```
- [x] **GET /api/chat/session/{session_id}** - 특정 채팅 세션 조회
- [x] **DELETE /api/chat/session/{session_id}** - 채팅 세션 삭제
- [x] **PUT /api/chat/session/{session_id}/title** - 세션 제목 업데이트
- [x] **GET /api/chat/session/{session_id}/validate** - 세션 접근 권한 확인

#### 2.2 채팅 히스토리 API
- [x] **GET /api/chat/history** - 채팅 히스토리 조회
  ```python
  # Query: ?session_id=str&limit=50&offset=0
  # Response: ChatHistoryResponse (messages, total_messages, has_more)
  ```
- [x] **POST /api/chat/message** - 채팅 메시지 저장 (백업용)
  ```python
  # Body: {"content": str, "role": str, "session_id": str}
  # Response: ChatMessageResponse
  ```

#### 2.3 구현된 기능
- [x] conversation 모델 확장 (title 필드 추가, 세션 관리 메서드)
- [x] 채팅 세션 스키마 정의 (ChatSessionCreate, ChatSessionResponse 등)
- [x] repositories.py에 세션 관리 함수들 추가
- [x] services.py에 ChatSessionService 클래스 구현
- [x] API 라우터 구현 (`src/api/chat/routes.py`)
- [x] 메인 API 라우터에 채팅 라우터 등록

---

### Phase 3: LLM 통합 및 Tool 구현 (2-3일) ✅ 완료

#### 3.1 LLM 클라이언트 설정
- [x] Claude API 클라이언트 구성 (`src/llm/client.py`)
- [x] 스트리밍 응답 처리 로직 (AsyncGenerator 지원)
- [x] 에러 처리 및 재시도 로직 (exponential backoff)
- [x] 토큰 사용량 모니터링 (usage stats tracking)

#### 3.2 LLM 서비스 구현
- [x] MMA 전문 System Prompt 작성 (`src/llm/prompts.py`)
- [x] Tool 함수 매핑 및 실행 로직 (MCP Tool 인터페이스)
- [x] 응답 후처리 (마크다운, 한국어 등)
- [x] 채팅 메시지 관리 (ChatMessage 클래스)
- [x] 스트리밍/비스트리밍 응답 지원

#### 3.3 구현된 기능
- [x] LLMClient: Claude API 통합, 스트리밍 지원, 재시도 로직
- [x] LLMService: 채팅 응답 생성, Tool call 처리, 대화 히스토리 관리
- [x] MMA System Prompt: 전문적인 MMA 어시스턴트 역할 정의
- [x] Tool 인터페이스: MCP Tool 연동을 위한 구조 정의
- [x] 에러 처리: LLMError 클래스 및 예외 처리
- [x] 글로벌 인스턴스: get_llm_client(), get_llm_service() 팩토리 함수

---

### Phase 4: 실시간 WebSocket 구현 (2-3일) ✅ 완료

#### 4.1 WebSocket 연결 관리
- [x] **WebSocket 엔드포인트** - `/ws/chat`
  ```python
  # Query: ?token={jwt_token}&session_id={session_id}
  # JWT 토큰 검증 후 연결 허용
  ```
- [x] 연결 상태 관리 (연결/해제) - ConnectionManager 클래스
- [x] 사용자별 연결 세션 관리 - 다중 연결 지원
- [x] 연결 끊어짐 처리 및 재연결 로직

#### 4.2 실시간 메시지 처리
- [x] **메시지 수신 처리**
  ```python
  # Client -> Server: {"type": "message", "content": str, "session_id": str}
  ```
- [x] **LLM 스트리밍 응답**
  ```python
  # Server -> Client: {"type": "response_chunk", "content": str, "message_id": str}
  # Server -> Client: {"type": "typing", "is_typing": bool}
  ```
- [x] 메시지 DB 저장 (비동기) - 사용자/어시스턴트 메시지 모두 저장
- [x] 에러 처리 및 클라이언트 알림

#### 4.3 타이핑 상태 관리
- [x] 타이핑 시작/종료 이벤트 처리
- [x] LLM 응답 생성 중 타이핑 상태 표시
- [x] 스트리밍 응답과 동기화된 타이핑 상태

#### 4.4 구현된 기능
- [x] ConnectionManager: WebSocket 연결 및 메시지 라우팅 관리
- [x] JWT 기반 WebSocket 인증
- [x] 실시간 LLM 스트리밍 응답
- [x] 세션 기반 대화 관리
- [x] 다중 연결 지원 (한 사용자가 여러 탭에서 접속 가능)
- [x] 에러 처리 및 재연결 로직
- [x] WebSocket 통계 및 헬스체크 엔드포인트
- [x] 메인 FastAPI 애플리케이션 통합 (`src/main_api.py`)

---

### Phase 5: 시스템 통합 및 최적화 (1-2일)

#### 5.1 기존 FastAPI 통합
- [ ] 기존 MMA 데이터 API와 라우터 통합
- [ ] 공통 미들웨어 설정 (CORS, 인증, 로깅)
- [ ] 데이터베이스 연결 풀 최적화

#### 5.2 성능 최적화
- [ ] Redis 캐싱 전략 (사용자 세션, 자주 조회되는 MMA 데이터)
- [ ] 데이터베이스 쿼리 최적화
- [ ] LLM API 응답 캐싱 (동일 질문 처리)

#### 5.3 보안 강화
- [ ] Rate Limiting (API 호출 제한)
- [ ] Input Validation (XSS, Injection 방지)
- [ ] CORS 정책 설정
- [ ] 환경변수 보안 관리

---

## 📁 프로젝트 구조 확장

```
src/
├── api/                    # 기존 API (MMA 데이터)
├── chat/                   # 새로운 채팅 관련 모듈
│   ├── models.py          # Chat 관련 SQLAlchemy 모델
│   ├── schemas.py         # Pydantic 스키마
│   ├── services.py        # 채팅 비즈니스 로직
│   ├── websocket.py       # WebSocket 핸들러
│   └── routes.py          # 채팅 API 라우터
├── auth/                   # 인증 관련 모듈
│   ├── jwt_handler.py     # JWT 토큰 처리
│   ├── dependencies.py    # 인증 의존성
│   └── models.py          # 사용자 모델
├── llm/                    # LLM 통합 모듈
│   ├── client.py          # LLM API 클라이언트
│   ├── tools.py           # MMA 데이터 조회 도구
│   ├── prompts.py         # System prompts
│   └── streaming.py       # 스트리밍 응답 처리
├── database/               # 기존 데이터베이스 (확장)
└── core/                   # 설정 및 공통 모듈
    ├── config.py          # 환경설정 (확장)
    ├── security.py        # 보안 관련
    └── dependencies.py    # 공통 의존성
```

---

## 🔧 환경 설정 확장

### 추가 환경 변수
```bash
# LLM API
OPENAI_API_KEY=your_openai_key
# 또는
CLAUDE_API_KEY=your_claude_key

# JWT 설정 (NextAuth.js와 동일)
NEXTAUTH_SECRET=your_nextauth_secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# Redis (채팅 세션 관리)
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=your_redis_password

# CORS 설정
FRONTEND_URL=http://localhost:3000
```

---

## 🧪 테스트 계획

### API 테스트
- [ ] 인증 미들웨어 테스트
- [ ] 채팅 API 엔드포인트 테스트
- [ ] WebSocket 연결 및 메시지 테스트
- [ ] LLM Tool 함수 테스트

### 통합 테스트
- [ ] 프론트엔드-백엔드 연동 테스트
- [ ] 실시간 채팅 플로우 테스트
- [ ] MMA 데이터 조회 정확성 테스트

---

## 🚀 배포 준비

### Docker 설정
- [ ] 기존 docker-compose.yml 확장
- [ ] 환경별 설정 분리 (dev, prod)
- [ ] Redis 컨테이너 추가

### 모니터링
- [ ] API 응답 시간 모니터링
- [ ] LLM API 사용량 추적
- [ ] WebSocket 연결 상태 모니터링
- [ ] 에러 로깅 및 알림

---

## 📝 예상 개발 일정

**총 예상 기간**: 7-10일  
**우선순위**: 인증 → 채팅 세션 → LLM 통합 → WebSocket → 최적화

### Week 1
- [ ] Phase 1: 기본 인증 및 사용자 관리
- [ ] Phase 2: 채팅 세션 관리  
- [ ] Phase 3: LLM 통합 및 Tool 구현

### Week 2  
- [ ] Phase 4: 실시간 WebSocket 구현
- [ ] Phase 5: 시스템 통합 및 최적화
- [ ] 프론트엔드 연동 테스트

---

**참고**: MMA 데이터 조회는 LLM Tool로 처리하므로 별도 API 엔드포인트 불필요  
**중요**: 기존 MMA 데이터 수집 FastAPI와 통합하여 하나의 서비스로 구성