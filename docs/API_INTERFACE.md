# API Reference

MMA Savant Backend API 명세서

**Version**: 1.0.0

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [User Management](#user-management)
4. [Chat Session](#chat-session)
5. [WebSocket](#websocket)
6. [Admin API](#admin-api)
7. [Error Responses](#error-responses)
8. [Schemas](#schemas)

---

## Overview

### Base Information

| Item | Value |
|------|-------|
| Protocol | HTTP/1.1, WebSocket |
| Content-Type | `application/json` |
| Authentication | Bearer Token (JWT) |
| Charset | UTF-8 |

### Authentication Header

인증이 필요한 엔드포인트는 다음 헤더를 포함해야 합니다:

```
Authorization: Bearer <jwt_token>
```

### Common Response Format

**Success Response**
```json
{
  "data": { ... },
  "message": "Success"
}
```

**Error Response**
```json
{
  "detail": "Error message description"
}
```

---

## Authentication

인증 관련 API. Google OAuth 토큰을 FastAPI JWT 토큰으로 교환합니다.

### POST /api/auth/google-token

Google OAuth 토큰을 FastAPI용 JWT 토큰으로 교환

**Authentication**: Not Required

**Request Body**

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `google_token` | string | ✓ | Google OAuth 토큰 |
| `email` | string | ✓ | 사용자 이메일 |
| `name` | string | ✓ | 사용자 이름 |
| `picture` | string | | 프로필 이미지 URL |

**Request Example**
```json
{
  "google_token": "ya29.a0AfH6SMBx...",
  "email": "user@example.com",
  "name": "John Doe",
  "picture": "https://lh3.googleusercontent.com/..."
}
```

**Response** `200 OK`

| Field | Type | Description |
|-------|------|-------------|
| `access_token` | string | FastAPI JWT 토큰 |
| `token_type` | string | 토큰 타입 (항상 "bearer") |
| `expires_in` | integer | 토큰 만료 시간 (초, 86400 = 24시간) |

**Response Example**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

**Errors**

| Status | Code | Description |
|--------|------|-------------|
| 500 | Internal Server Error | JWT secret not configured |
| 500 | Internal Server Error | Failed to create JWT token |

---

## User Management

사용자 프로필 관리 API. NextAuth.js OAuth 사용자를 지원합니다.

### GET /api/user/profile

현재 로그인한 사용자의 프로필 조회

**Authentication**: Required

**Response** `200 OK`

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | 사용자 ID |
| `email` | string | 이메일 |
| `name` | string | 사용자 이름 |
| `picture` | string | 프로필 이미지 URL |
| `username` | string | 사용자명 (레거시) |
| `total_requests` | integer | 총 요청 횟수 |
| `daily_requests` | integer | 오늘 요청 횟수 |
| `remaining_requests` | integer | 오늘 남은 요청 횟수 |
| `is_active` | boolean | 활성화 상태 |
| `created_at` | datetime | 생성 일시 |
| `updated_at` | datetime | 수정 일시 |

**Response Example**
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "John Doe",
  "picture": "https://lh3.googleusercontent.com/...",
  "username": null,
  "total_requests": 42,
  "daily_requests": 5,
  "remaining_requests": 95,
  "is_active": true,
  "created_at": "2024-01-15T09:30:00",
  "updated_at": "2024-01-15T10:00:00"
}
```

**Errors**

| Status | Code | Description |
|--------|------|-------------|
| 401 | Unauthorized | 인증 토큰 없음 또는 만료 |
| 404 | Not Found | 사용자를 찾을 수 없음 |
| 500 | Internal Server Error | 데이터베이스 오류 |

---

### PUT /api/user/profile

현재 로그인한 사용자의 프로필 업데이트

**Authentication**: Required

**Request Body**

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `name` | string | | 변경할 이름 |
| `picture` | string | | 변경할 프로필 이미지 URL |

**Request Example**
```json
{
  "name": "Jane Doe",
  "picture": "https://example.com/new-avatar.jpg"
}
```

**Response** `200 OK`

[UserProfileResponse](#userprofileresponse) 스키마 참조

**Errors**

| Status | Code | Description |
|--------|------|-------------|
| 400 | Bad Request | 유효성 검사 실패 |
| 401 | Unauthorized | 인증 실패 |
| 404 | Not Found | 사용자를 찾을 수 없음 |
| 500 | Internal Server Error | 데이터베이스 오류 |

---

### GET /api/user/profile/{user_id}

특정 사용자 프로필 조회 (관리자용 또는 자신의 프로필)

**Authentication**: Required

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | integer | 조회할 사용자 ID |

**Response** `200 OK`

[UserProfileResponse](#userprofileresponse) 스키마 참조

**Errors**

| Status | Code | Description |
|--------|------|-------------|
| 400 | Bad Request | 잘못된 user_id |
| 401 | Unauthorized | 인증 실패 |
| 404 | Not Found | 사용자를 찾을 수 없음 |

---

### POST /api/user/increment-usage

사용자 요청 횟수 증가 (API 호출 시 자동 증가)

**Authentication**: Required

**Response** `200 OK`

```json
{
  "success": true,
  "message": "Usage updated successfully",
  "usage": {
    "total_requests": 43,
    "daily_requests": 5,
    "remaining_requests": 95
  }
}
```

**Response (Failure)**
```json
{
  "success": false,
  "message": "Usage update failed: <error_message>"
}
```

---

### GET /api/user/check-auth

인증 상태 확인 (토큰 검증)

**Authentication**: Required

**Response** `200 OK`

```json
{
  "authenticated": true,
  "user_id": 1,
  "email": "user@example.com",
  "name": "John Doe",
  "token_valid": true
}
```

**Errors**

| Status | Code | Description |
|--------|------|-------------|
| 401 | Unauthorized | 토큰 없음, 만료, 또는 유효하지 않음 |

---

### GET /api/user/me

현재 사용자 정보 조회 (GET /api/user/profile 의 별칭)

**Authentication**: Required

**Response** `200 OK`

[UserProfileResponse](#userprofileresponse) 스키마 참조

---

## Chat Session

채팅 세션 관리 API. 대화 세션의 CRUD 및 메시지 히스토리를 관리합니다.

### POST /api/chat/session

새 채팅 세션 생성

**Authentication**: Required

**Request Body**

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `title` | string | | 세션 제목 (선택) |

**Request Example**
```json
{
  "title": "UFC 300 분석"
}
```

**Response** `200 OK`

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | 세션 ID |
| `user_id` | integer | 사용자 ID |
| `title` | string | 세션 제목 |
| `last_message_at` | datetime | 마지막 메시지 시간 |
| `created_at` | datetime | 생성 일시 |
| `updated_at` | datetime | 수정 일시 |

**Response Example**
```json
{
  "id": 123,
  "user_id": 1,
  "title": "UFC 300 분석",
  "last_message_at": null,
  "created_at": "2024-01-15T10:00:00",
  "updated_at": "2024-01-15T10:00:00"
}
```

**Errors**

| Status | Code | Description |
|--------|------|-------------|
| 401 | Unauthorized | 인증 실패 |
| 500 | Internal Server Error | 세션 생성 실패 |

---

### GET /api/chat/sessions

사용자의 채팅 세션 목록 조회

**Authentication**: Required

**Query Parameters**

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `limit` | integer | 20 | 1-100 | 조회할 세션 수 |
| `offset` | integer | 0 | 0+ | 건너뛸 세션 수 |

**Response** `200 OK`

| Field | Type | Description |
|-------|------|-------------|
| `sessions` | array | 세션 목록 ([ChatSessionResponse](#chatsessionresponse)[]) |
| `total_sessions` | integer | 총 세션 수 |

**Response Example**
```json
{
  "sessions": [
    {
      "id": 123,
      "user_id": 1,
      "title": "UFC 300 분석",
      "last_message_at": "2024-01-15T10:30:00",
      "created_at": "2024-01-15T10:00:00",
      "updated_at": "2024-01-15T10:30:00"
    }
  ],
  "total_sessions": 1
}
```

**Errors**

| Status | Code | Description |
|--------|------|-------------|
| 401 | Unauthorized | 인증 실패 |
| 500 | Internal Server Error | 세션 목록 조회 실패 |

---

### GET /api/chat/session/{conversation_id}

특정 채팅 세션 조회

**Authentication**: Required

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `conversation_id` | integer | 세션 ID |

**Response** `200 OK`

[ChatSessionResponse](#chatsessionresponse) 스키마 참조

**Errors**

| Status | Code | Description |
|--------|------|-------------|
| 401 | Unauthorized | 인증 실패 |
| 404 | Not Found | 세션을 찾을 수 없음 |
| 500 | Internal Server Error | 세션 조회 실패 |

---

### DELETE /api/chat/session/{conversation_id}

채팅 세션 삭제

**Authentication**: Required

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `conversation_id` | integer | 삭제할 세션 ID |

**Response** `200 OK`

```json
{
  "success": true,
  "message": "Session deleted successfully"
}
```

**Errors**

| Status | Code | Description |
|--------|------|-------------|
| 401 | Unauthorized | 인증 실패 |
| 404 | Not Found | 세션을 찾을 수 없음 |
| 500 | Internal Server Error | 세션 삭제 실패 |

---

### PUT /api/chat/session/{conversation_id}/title

채팅 세션 제목 업데이트

**Authentication**: Required

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `conversation_id` | integer | 세션 ID |

**Query Parameters**

| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| `title` | string | ✓ | 새 제목 |

**Response** `200 OK`

[ChatSessionResponse](#chatsessionresponse) 스키마 참조

**Errors**

| Status | Code | Description |
|--------|------|-------------|
| 400 | Bad Request | 제목이 비어있음 |
| 401 | Unauthorized | 인증 실패 |
| 404 | Not Found | 세션을 찾을 수 없음 |
| 500 | Internal Server Error | 제목 업데이트 실패 |

---

### GET /api/chat/history

채팅 히스토리 조회

**Authentication**: Required

**Query Parameters**

| Parameter | Type | Required | Default | Range | Description |
|-----------|------|:--------:|---------|-------|-------------|
| `conversation_id` | integer | ✓ | - | - | 세션 ID |
| `limit` | integer | | 50 | 1-200 | 조회할 메시지 수 |
| `offset` | integer | | 0 | 0+ | 건너뛸 메시지 수 |

**Response** `200 OK`

| Field | Type | Description |
|-------|------|-------------|
| `conversation_id` | integer | 세션 ID |
| `messages` | array | 메시지 목록 ([ChatMessageResponse](#chatmessageresponse)[]) |
| `total_messages` | integer | 총 메시지 수 |
| `has_more` | boolean | 추가 메시지 존재 여부 |

**Response Example**
```json
{
  "conversation_id": 123,
  "messages": [
    {
      "id": "msg_abc123",
      "content": "UFC 300 메인 이벤트는 누가 이길까요?",
      "role": "user",
      "timestamp": "2024-01-15T10:00:00",
      "conversation_id": 123,
      "tool_results": null
    },
    {
      "id": "msg_def456",
      "content": "UFC 300 메인 이벤트 분석 결과입니다...",
      "role": "assistant",
      "timestamp": "2024-01-15T10:00:05",
      "conversation_id": 123,
      "tool_results": [
        {
          "tool": "sql_query",
          "result": { ... }
        }
      ]
    }
  ],
  "total_messages": 2,
  "has_more": false
}
```

**Errors**

| Status | Code | Description |
|--------|------|-------------|
| 401 | Unauthorized | 인증 실패 |
| 404 | Not Found | 세션을 찾을 수 없음 |
| 500 | Internal Server Error | 히스토리 조회 실패 |

---

### POST /api/chat/message

채팅 메시지 저장 (백업용)

> **Note**: 실제 채팅은 WebSocket을 통해 처리되고, 이 API는 메시지 백업 저장용입니다.

**Authentication**: Required

**Request Body**

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `content` | string | ✓ | 메시지 내용 |
| `role` | string | ✓ | 역할 ("user" 또는 "assistant") |
| `conversation_id` | integer | ✓ | 세션 ID |
| `tool_results` | array | | 도구 실행 결과 |

**Request Example**
```json
{
  "content": "UFC 300 메인 이벤트 분석해줘",
  "role": "user",
  "conversation_id": 123,
  "tool_results": null
}
```

**Response** `200 OK`

[ChatMessageResponse](#chatmessageresponse) 스키마 참조

**Errors**

| Status | Code | Description |
|--------|------|-------------|
| 401 | Unauthorized | 인증 실패 |
| 403 | Forbidden | 세션 접근 권한 없음 |
| 404 | Not Found | 세션을 찾을 수 없음 |
| 500 | Internal Server Error | 메시지 저장 실패 |

---

### GET /api/chat/session/{conversation_id}/validate

세션 접근 권한 확인

**Authentication**: Required

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `conversation_id` | integer | 확인할 세션 ID |

**Response** `200 OK`

```json
{
  "conversation_id": 123,
  "has_access": true,
  "user_id": 1
}
```

**Errors**

| Status | Code | Description |
|--------|------|-------------|
| 401 | Unauthorized | 인증 실패 |
| 500 | Internal Server Error | 권한 확인 실패 |

---

## WebSocket

실시간 채팅을 위한 WebSocket API

### WS /ws/chat

채팅을 위한 WebSocket 엔드포인트

**Connection URL**
```
ws://localhost:8000/ws/chat?token={jwt_token}&conversation_id={conversation_id}
```

**Query Parameters**

| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| `token` | string | ✓ | JWT 인증 토큰 |
| `conversation_id` | integer | | 세션 ID (없으면 새 세션) |

**Connection Flow**

1. 클라이언트가 WebSocket 연결 요청
2. 서버가 토큰 검증
3. 연결 성공 시 `connection_established` 메시지 전송
4. 메시지 송수신 시작

---

### Client → Server Messages

#### Message (채팅 메시지)

```json
{
  "type": "message",
  "content": "UFC 300 메인 이벤트 분석해줘",
  "conversation_id": 123
}
```

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `type` | string | ✓ | "message" |
| `content` | string | ✓ | 메시지 내용 |
| `conversation_id` | integer | | 세션 ID |

---

#### Ping (연결 상태 확인)

```json
{
  "type": "ping"
}
```

---

#### Typing (타이핑 상태)

```json
{
  "type": "typing",
  "is_typing": true
}
```

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `type` | string | ✓ | "typing" |
| `is_typing` | boolean | ✓ | 타이핑 중 여부 |

---

### Server → Client Messages

#### connection_established (연결 성공)

```json
{
  "type": "connection_established",
  "connection_id": "conn_abc123",
  "user_id": 1,
  "conversation_id": 123,
  "timestamp": "2024-01-15T10:00:00+09:00",
  "message": "연결이 성공적으로 설정되었습니다."
}
```

---

#### stream_start (스트리밍 시작)

```json
{
  "type": "stream_start",
  "message_id": "msg_abc123",
  "timestamp": "2024-01-15T10:00:00+09:00"
}
```

---

#### stream_chunk (스트리밍 청크)

```json
{
  "type": "stream_chunk",
  "content": "UFC 300 메인 이벤트는",
  "message_id": "msg_abc123"
}
```

---

#### stream_end (스트리밍 종료)

```json
{
  "type": "stream_end",
  "message_id": "msg_abc123",
  "full_content": "UFC 300 메인 이벤트는 Alex Pereira vs Jamahal Hill 입니다...",
  "tool_results": [
    {
      "tool": "sql_query",
      "result": { ... }
    }
  ],
  "timestamp": "2024-01-15T10:00:05+09:00"
}
```

---

#### thinking_start / thinking_end (추론 상태)

```json
{
  "type": "thinking_start",
  "phase": "understand_and_collect",
  "timestamp": "2024-01-15T10:00:00+09:00"
}
```

```json
{
  "type": "thinking_end",
  "phase": "understand_and_collect",
  "timestamp": "2024-01-15T10:00:02+09:00"
}
```

| Phase | Description |
|-------|-------------|
| `understand_and_collect` | Phase 1: ReAct 에이전트로 데이터 수집 |
| `process_and_visualize` | Phase 2: LLM으로 응답 생성 |

---

#### tool_execution (도구 실행)

```json
{
  "type": "tool_execution",
  "tool_name": "sql_query",
  "status": "executing",
  "timestamp": "2024-01-15T10:00:01+09:00"
}
```

---

#### pong (Ping 응답)

```json
{
  "type": "pong",
  "timestamp": "2024-01-15T10:00:00+09:00"
}
```

---

#### typing_echo (타이핑 상태 에코)

```json
{
  "type": "typing_echo",
  "is_typing": true,
  "timestamp": "2024-01-15T10:00:00+09:00"
}
```

---

#### error (에러)

```json
{
  "type": "error",
  "error": "Invalid JSON format",
  "timestamp": "2024-01-15T10:00:00+09:00"
}
```

---

### WebSocket Close Codes

| Code | Reason |
|------|--------|
| 4001 | Token required / Authentication failed |
| 1000 | Normal closure |
| 1001 | Going away |

---

### GET /ws/stats

WebSocket 연결 통계 조회

**Authentication**: Not Required

**Response** `200 OK`

```json
{
  "total_connections": 5,
  "connections_by_user": {
    "1": 2,
    "2": 3
  },
  "active_conversations": [123, 456]
}
```

---

### GET /ws/health

WebSocket 서비스 상태 확인

**Authentication**: Not Required

**Response** `200 OK`

```json
{
  "status": "healthy",
  "service": "websocket",
  "stats": {
    "total_connections": 5
  },
  "timestamp": "2024-01-15T10:00:00+09:00"
}
```

---

## Admin API

관리자 전용 API. `is_admin: true` 권한이 있는 사용자만 접근 가능합니다.

### GET /api/admin/users

전체 사용자 목록 조회 (페이지네이션)

**Authentication**: Required (Admin Only)

**Query Parameters**

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `page` | integer | 1 | 1+ | 페이지 번호 |
| `page_size` | integer | 20 | 1-100 | 페이지 크기 |
| `search` | string | | | 이름/이메일 검색 |

**Response** `200 OK`

| Field | Type | Description |
|-------|------|-------------|
| `users` | array | 사용자 목록 ([UserAdminResponse](#useradminresponse)[]) |
| `total_users` | integer | 전체 사용자 수 |
| `page` | integer | 현재 페이지 |
| `page_size` | integer | 페이지 크기 |
| `total_pages` | integer | 전체 페이지 수 |

**Response Example**
```json
{
  "users": [
    {
      "id": 1,
      "email": "user@example.com",
      "name": "John Doe",
      "picture": "https://lh3.googleusercontent.com/...",
      "is_admin": false,
      "total_requests": 150,
      "daily_requests": 10,
      "daily_request_limit": 100,
      "last_request_date": "2024-01-15T10:00:00",
      "is_active": true,
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-15T10:00:00"
    }
  ],
  "total_users": 50,
  "page": 1,
  "page_size": 20,
  "total_pages": 3
}
```

**Errors**

| Status | Code | Description |
|--------|------|-------------|
| 401 | Unauthorized | 인증 토큰 없음 또는 만료 |
| 403 | Forbidden | 관리자 권한 필요 |
| 500 | Internal Server Error | 서버 오류 |

---

### GET /api/admin/users/{user_id}

특정 사용자 상세 조회

**Authentication**: Required (Admin Only)

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | integer | 조회할 사용자 ID |

**Response** `200 OK`

[UserAdminResponse](#useradminresponse) 스키마 참조

**Errors**

| Status | Code | Description |
|--------|------|-------------|
| 401 | Unauthorized | 인증 실패 |
| 403 | Forbidden | 관리자 권한 필요 |
| 404 | Not Found | 사용자를 찾을 수 없음 |

---

### PUT /api/admin/users/{user_id}/limit

사용자 일일 요청 제한 수정

**Authentication**: Required (Admin Only)

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | integer | 수정할 사용자 ID |

**Request Body**

| Field | Type | Required | Range | Description |
|-------|------|:--------:|-------|-------------|
| `daily_request_limit` | integer | ✓ | 0-10000 | 일일 요청 제한 수 |

**Request Example**
```json
{
  "daily_request_limit": 200
}
```

**Response** `200 OK`

[UserAdminResponse](#useradminresponse) 스키마 참조

**Errors**

| Status | Code | Description |
|--------|------|-------------|
| 400 | Bad Request | 유효하지 않은 제한 값 (0-10000 범위) |
| 401 | Unauthorized | 인증 실패 |
| 403 | Forbidden | 관리자 권한 필요 |
| 404 | Not Found | 사용자를 찾을 수 없음 |

---

### PUT /api/admin/users/{user_id}/admin

사용자 관리자 권한 수정

**Authentication**: Required (Admin Only)

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | integer | 수정할 사용자 ID |

**Request Body**

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `is_admin` | boolean | ✓ | 관리자 권한 여부 |

**Request Example**
```json
{
  "is_admin": true
}
```

**Response** `200 OK`

[UserAdminResponse](#useradminresponse) 스키마 참조

**Errors**

| Status | Code | Description |
|--------|------|-------------|
| 401 | Unauthorized | 인증 실패 |
| 403 | Forbidden | 관리자 권한 필요 |
| 403 | Forbidden | 자기 자신의 권한은 수정할 수 없음 |
| 404 | Not Found | 사용자를 찾을 수 없음 |

---

### PUT /api/admin/users/{user_id}/status

사용자 활성화/비활성화

**Authentication**: Required (Admin Only)

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | integer | 수정할 사용자 ID |

**Request Body**

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `is_active` | boolean | ✓ | 활성화 상태 |

**Request Example**
```json
{
  "is_active": false
}
```

**Response** `200 OK`

[UserAdminResponse](#useradminresponse) 스키마 참조

**Errors**

| Status | Code | Description |
|--------|------|-------------|
| 401 | Unauthorized | 인증 실패 |
| 403 | Forbidden | 관리자 권한 필요 |
| 403 | Forbidden | 자기 자신을 비활성화할 수 없음 |
| 404 | Not Found | 사용자를 찾을 수 없음 |

---

### GET /api/admin/stats/overview

시스템 통계 조회

**Authentication**: Required (Admin Only)

**Response** `200 OK`

| Field | Type | Description |
|-------|------|-------------|
| `total_users` | integer | 전체 사용자 수 |
| `active_users` | integer | 활성 사용자 수 |
| `admin_users` | integer | 관리자 수 |
| `total_requests_today` | integer | 오늘 전체 요청 수 |
| `total_conversations` | integer | 전체 대화 세션 수 |

**Response Example**
```json
{
  "total_users": 150,
  "active_users": 142,
  "admin_users": 3,
  "total_requests_today": 1250,
  "total_conversations": 5830
}
```

**Errors**

| Status | Code | Description |
|--------|------|-------------|
| 401 | Unauthorized | 인증 실패 |
| 403 | Forbidden | 관리자 권한 필요 |
| 500 | Internal Server Error | 통계 조회 실패 |

---

## Error Responses

### Standard Error Format

모든 에러는 다음 형식으로 반환됩니다:

```json
{
  "detail": "Error message description"
}
```

### HTTP Status Codes

| Status | Name | Description |
|--------|------|-------------|
| 400 | Bad Request | 잘못된 요청 파라미터 |
| 401 | Unauthorized | 인증 필요 또는 토큰 만료 |
| 403 | Forbidden | 접근 권한 없음 |
| 404 | Not Found | 리소스를 찾을 수 없음 |
| 500 | Internal Server Error | 서버 내부 오류 |

### Authentication Errors

| Status | Detail | Description |
|--------|--------|-------------|
| 401 | Authorization header required | 인증 헤더 누락 |
| 401 | Token has expired | 토큰 만료 |
| 401 | Could not validate credentials | 토큰 검증 실패 |
| 401 | User not found | 사용자 없음 |
| 401 | Inactive user | 비활성화된 사용자 |

---

## Schemas

### UserProfileResponse

```typescript
interface UserProfileResponse {
  id: number;                    // 사용자 ID
  email?: string;                // 이메일
  name?: string;                 // 사용자 이름
  picture?: string;              // 프로필 이미지 URL
  username?: string;             // 사용자명 (레거시)
  total_requests: number;        // 총 요청 횟수
  daily_requests: number;        // 오늘 요청 횟수
  daily_request_limit: number;   // 일일 요청 제한
  remaining_requests: number;    // 오늘 남은 요청 횟수 (daily_limit - daily_requests)
  is_active: boolean;            // 활성화 상태
  is_admin: boolean;             // 관리자 여부
  created_at: string;            // 생성 일시 (ISO 8601)
  updated_at?: string;           // 수정 일시 (ISO 8601)
}
```

---

### UserAdminResponse

```typescript
interface UserAdminResponse {
  id: number;                       // 사용자 ID
  email?: string;                   // 이메일
  name?: string;                    // 사용자 이름
  picture?: string;                 // 프로필 이미지 URL
  is_admin: boolean;                // 관리자 여부
  total_requests: number;           // 총 요청 횟수
  daily_requests: number;           // 오늘 요청 횟수
  daily_request_limit: number;      // 일일 요청 제한
  last_request_date?: string;       // 마지막 요청 일시 (ISO 8601)
  is_active: boolean;               // 활성화 상태
  created_at: string;               // 생성 일시 (ISO 8601)
  updated_at?: string;              // 수정 일시 (ISO 8601)
}
```

---

### UserListResponse

```typescript
interface UserListResponse {
  users: UserAdminResponse[];  // 사용자 목록
  total_users: number;         // 전체 사용자 수
  page: number;                // 현재 페이지
  page_size: number;           // 페이지 크기
  total_pages: number;         // 전체 페이지 수
}
```

---

### UserLimitUpdate

```typescript
interface UserLimitUpdate {
  daily_request_limit: number;  // 일일 요청 제한 (0-10000)
}
```

---

### UserAdminStatusUpdate

```typescript
interface UserAdminStatusUpdate {
  is_admin: boolean;  // 관리자 권한 여부
}
```

---

### UserActiveStatusUpdate

```typescript
interface UserActiveStatusUpdate {
  is_active: boolean;  // 활성화 상태
}
```

---

### AdminStatsResponse

```typescript
interface AdminStatsResponse {
  total_users: number;           // 전체 사용자 수
  active_users: number;          // 활성 사용자 수
  admin_users: number;           // 관리자 수
  total_requests_today: number;  // 오늘 전체 요청 수
  total_conversations: number;   // 전체 대화 세션 수
}
```

---

### ChatSessionResponse

```typescript
interface ChatSessionResponse {
  id: number;                   // 세션 ID
  user_id: number;              // 사용자 ID
  title?: string;               // 세션 제목
  last_message_at?: string;     // 마지막 메시지 시간 (ISO 8601)
  created_at: string;           // 생성 일시
  updated_at: string;           // 수정 일시
}
```

---

### ChatMessageResponse

```typescript
interface ChatMessageResponse {
  id: string;                   // 메시지 ID (UUID)
  content: string;              // 메시지 내용
  role: "user" | "assistant";   // 역할
  timestamp: string;            // 생성 시간 (ISO 8601)
  conversation_id: number;      // 세션 ID
  tool_results?: ToolResult[];  // 도구 실행 결과
}
```

---

### ToolResult

```typescript
interface ToolResult {
  tool: string;          // 도구 이름 (e.g., "sql_query")
  result: any;           // 도구 실행 결과
  error?: string;        // 에러 메시지 (실패 시)
}
```

---

### JWTTokenResponse

```typescript
interface JWTTokenResponse {
  access_token: string;  // JWT 토큰
  token_type: "bearer";  // 토큰 타입
  expires_in: number;    // 만료 시간 (초)
}
```

---

### TokenData (Internal)

JWT 토큰 페이로드 구조:

```typescript
interface TokenData {
  sub: string;           // 사용자 ID 또는 이메일
  email?: string;        // 이메일
  name?: string;         // 이름
  picture?: string;      // 프로필 이미지
  iat?: number;          // 발급 시간 (Unix timestamp)
  exp?: number;          // 만료 시간 (Unix timestamp)
}
```

---

## Appendix

### Rate Limiting

사용자별 일일 요청 제한이 적용됩니다.

**기본 설정**

| 항목 | 값 | 설명 |
|------|-----|------|
| 기본 일일 제한 | 100 | 신규 사용자 기본값 |
| 최소 제한 | 0 | 요청 차단 |
| 최대 제한 | 10000 | 관리자가 설정 가능한 최대값 |
| 리셋 시간 | 00:00 KST | 매일 자정 (한국 시간) |

**Rate Limit 확인**

`GET /api/user/profile` 응답에서 확인:

```json
{
  "daily_requests": 42,
  "daily_request_limit": 100,
  "remaining_requests": 58
}
```

**Rate Limit 초과 시**

WebSocket 메시지 전송 시 제한 초과하면 다음 에러 반환:

```json
{
  "type": "error",
  "error": "rate_limit_exceeded",
  "remaining": 0,
  "reset_at": "2024-01-16T00:00:00+09:00",
  "message": "일일 요청 제한을 초과했습니다. 2024-01-16T00:00:00+09:00에 초기화됩니다."
}
```

**관리자 제한 수정**

관리자는 `PUT /api/admin/users/{user_id}/limit` API로 사용자별 제한을 수정할 수 있습니다.

### CORS Configuration

```python
allowed_origins = [
  "http://localhost:3000",
  "https://your-production-domain.com"
]
```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|:--------:|
| `NEXTAUTH_SECRET` | JWT 서명 시크릿 (NextAuth와 공유) | ✓ |
| `TOKEN_ALGORITHM` | JWT 알고리즘 (기본: HS256) | |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 토큰 만료 시간 (분) | |

---

*Last Updated: 2024-01*
