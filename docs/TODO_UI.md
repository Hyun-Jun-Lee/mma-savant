# MMA Savant 프론트엔드 개발 계획

## 📋 프로젝트 개요
MMA Savant 챗봇 서비스의 React 기반 프론트엔드 개발 계획서

**백엔드**: FastAPI  
**프론트엔드**: Next.js 14 + TypeScript  
**인증**: NextAuth.js (Google OAuth)  
**스타일링**: Tailwind CSS + Shadcn/ui  

---

## 🛠️ 기술 스택

### Frontend Core
- **Next.js 14** (App Router)
- **TypeScript**
- **React 18**
- **Tailwind CSS**
- **Shadcn/ui** (컴포넌트 라이브러리)

### Authentication
- **NextAuth.js v5** (Auth.js)
- **Google OAuth 2.0**
- **JWT 토큰 관리**
- **세션 관리**

### State Management
- **Zustand** (가벼운 상태 관리)
- **React Query/TanStack Query** (서버 상태 관리)

### Real-time Communication
- **Socket.io Client**
- **WebSocket** (실시간 채팅)
- **Server-Sent Events** (스트리밍 응답)

### UI/UX
- **Framer Motion** (애니메이션)
- **React Hook Form** (폼 관리)
- **Zod** (유효성 검사)
- **Lucide React** (아이콘)

---

## 📁 프로젝트 구조

```
mma-savant/
├── frontend/                   # 프론트엔드 Next.js 프로젝트
│   ├── src/
│   │   ├── app/                # Next.js App Router
│   │   │   ├── (auth)/
│   │   │   │   ├── login/
│   │   │   │   └── signup/
│   │   │   ├── chat/
│   │   │   ├── profile/
│   │   │   ├── layout.tsx
│   │   │   └── page.tsx
│   │   ├── components/         # UI 컴포넌트
│   │   │   ├── ui/             # Shadcn/ui 컴포넌트
│   │   │   ├── auth/
│   │   │   │   ├── LoginForm.tsx
│   │   │   │   ├── GoogleLoginButton.tsx
│   │   │   │   └── AuthGuard.tsx
│   │   │   ├── chat/
│   │   │   │   ├── ChatContainer.tsx
│   │   │   │   ├── MessageList.tsx
│   │   │   │   ├── MessageInput.tsx
│   │   │   │   ├── MessageBubble.tsx
│   │   │   │   └── TypingIndicator.tsx
│   │   │   ├── layout/
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   └── Footer.tsx
│   │   │   └── common/
│   │   │       ├── Loading.tsx
│   │   │       ├── ErrorBoundary.tsx
│   │   │       └── Modal.tsx
│   │   ├── lib/                # 유틸리티 및 설정
│   │   │   ├── auth.ts         # NextAuth 설정
│   │   │   ├── api.ts          # API 클라이언트
│   │   │   ├── socket.ts       # Socket.io 설정
│   │   │   ├── utils.ts        # 공통 유틸리티
│   │   │   └── validations.ts  # Zod 스키마
│   │   ├── hooks/              # 커스텀 훅
│   │   │   ├── useAuth.ts
│   │   │   ├── useChat.ts
│   │   │   ├── useSocket.ts
│   │   │   └── useLocalStorage.ts
│   │   ├── store/              # Zustand 스토어
│   │   │   ├── authStore.ts
│   │   │   ├── chatStore.ts
│   │   │   └── uiStore.ts
│   │   └── types/              # TypeScript 타입 정의
│   │       ├── auth.ts
│   │       ├── chat.ts
│   │       └── api.ts
│   ├── public/
│   ├── .env.local
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── package.json
│   └── README.md
├── src/                        # 백엔드 FastAPI (기존)
├── docs/                       # 문서 (기존)
└── ...                         # 기타 프로젝트 파일들
```

---

## 🎯 개발 단계별 TODO

### Phase 1: 프로젝트 설정 및 기본 구조 (1-2일) ✅ 완료
- [x] frontend/ 디렉토리에 Next.js 14 프로젝트 초기화
- [x] TypeScript 설정
- [x] Tailwind CSS + Shadcn/ui 설정
- [x] frontend/src/ 하위 폴더 구조 생성
- [x] ESLint, Prettier 설정
- [x] 기본 레이아웃 컴포넌트 구현 (MMA Savant 홈페이지)

### Phase 2: 인증 시스템 구현 (2-3일) ✅ 완료
- [x] NextAuth.js 설정
  - [x] Google OAuth 설정
  - [x] JWT 토큰 관리
  - [x] 세션 관리
- [x] 인증 관련 컴포넌트
  - [x] 로그인 페이지 구현
  - [x] GoogleLoginButton 컴포넌트
  - [x] LogoutButton 컴포넌트
  - [x] UserProfile 컴포넌트
  - [x] AuthGuard 컴포넌트 (보호된 라우트)
- [x] 인증 상태 관리 (Zustand)
- [x] 로그인/로그아웃 플로우 구현

### Phase 3: 채팅 UI 구현 (3-4일) ✅ 완료
- [x] 채팅 기본 컴포넌트
  - [x] ChatContainer (메인 채팅 컨테이너)
  - [x] MessageList (메시지 목록)
  - [x] MessageBubble (개별 메시지)
  - [x] MessageInput (메시지 입력)
  - [x] 빈 상태 UI 및 예시 질문
- [x] 채팅 상태 관리 (Zustand)
- [x] 메시지 스크롤 관리
- [x] 반응형 디자인 적용

### Phase 4: 실시간 통신 구현 (2-3일) ✅ 완료
- [x] Socket.io 클라이언트 설정 (Mock WebSocket 구현)
- [x] 실시간 메시지 송수신
- [x] 스트리밍 응답 처리 (단어별 스트리밍 시뮬레이션)
- [x] 연결 상태 관리 및 재연결 로직
- [x] 타이핑 상태 실시간 동기화

### Phase 5: FastAPI 연동 (2일)
- [ ] API 클라이언트 구성
- [ ] 인증 토큰 헤더 자동 첨부
- [ ] API 에러 처리
- [ ] 데이터 캐싱 전략 (React Query)
- [ ] 로딩 상태 관리

### Phase 6: 고급 기능 구현 (3-4일)
- [ ] 사용자 프로필 관리
- [ ] 채팅 히스토리 저장/불러오기
- [ ] 다크/라이트 테마 토글
- [ ] 메시지 검색 기능
- [ ] 파일 업로드 (이미지, 문서)
- [ ] 모바일 반응형 최적화

### Phase 7: 성능 최적화 및 배포 준비 (2-3일)
- [ ] 코드 스플리팅 최적화
- [ ] 이미지 최적화
- [ ] SEO 메타 태그 설정
- [ ] PWA 설정 (선택사항)
- [ ] 에러 바운더리 구현
- [ ] 로딩 스켈레톤 UI
- [ ] 배포 설정 (Vercel/Netlify)

---

## 🔧 주요 컴포넌트 상세 계획

### 1. 인증 컴포넌트

#### GoogleLoginButton.tsx
```typescript
// Google OAuth 로그인 버튼
- signIn from next-auth/react 사용
- 로딩 상태 표시
- 에러 처리
- 커스텀 스타일링
```

#### AuthGuard.tsx
```typescript
// 보호된 라우트 컴포넌트
- 세션 상태 확인
- 로그인되지 않은 경우 리다이렉트
- 로딩 스피너 표시
```

### 2. 채팅 컴포넌트

#### ChatContainer.tsx
```typescript
// 메인 채팅 컨테이너
- 메시지 목록과 입력창 포함
- 실시간 연결 상태 표시
- 스크롤 위치 관리
```

#### MessageBubble.tsx
```typescript
// 개별 메시지 표시
- 사용자/AI 메시지 구분
- 마크다운 렌더링
- 시간 표시
- 애니메이션 효과
```

#### MessageInput.tsx
```typescript
// 메시지 입력 컴포넌트
- 멀티라인 텍스트 입력
- Enter/Shift+Enter 처리
- 전송 버튼 상태 관리
- 글자수 제한
```

### 3. 레이아웃 컴포넌트

#### Header.tsx
```typescript
// 헤더 컴포넌트
- 로고 및 제목
- 사용자 프로필 드롭다운
- 테마 토글 버튼
- 로그아웃 버튼
```

#### Sidebar.tsx
```typescript
// 사이드바 컴포넌트 (선택사항)
- 채팅 히스토리
- 새 채팅 시작 버튼
- 설정 메뉴
```

---

## 🎨 디자인 시스템

### 컬러 팔레트
```css
/* Primary Colors */
--primary: #dc2626 (MMA 레드)
--primary-dark: #991b1b
--primary-light: #fee2e2

/* Neutral Colors */
--background: #ffffff
--surface: #f9fafb
--border: #e5e7eb
--text-primary: #111827
--text-secondary: #6b7280

/* Status Colors */
--success: #10b981
--warning: #f59e0b
--error: #ef4444
--info: #3b82f6
```

### 타이포그래피
```css
/* Heading */
h1: text-3xl font-bold
h2: text-2xl font-semibold
h3: text-xl font-medium

/* Body */
body: text-base
small: text-sm
caption: text-xs
```

### 스페이싱
```css
/* Spacing Scale (Tailwind) */
xs: 0.25rem (4px)
sm: 0.5rem (8px)
md: 1rem (16px)
lg: 1.5rem (24px)
xl: 2rem (32px)
2xl: 3rem (48px)
```

---

## 🔌 API 연동 계획

### FastAPI 엔드포인트 연동
```typescript
// 예상 API 엔드포인트
POST /api/auth/login          // 로그인
POST /api/auth/logout         // 로그아웃
GET  /api/user/profile        // 사용자 프로필
PUT  /api/user/profile        // 프로필 업데이트
POST /api/chat/message        // 메시지 전송
GET  /api/chat/history        // 채팅 히스토리
POST /api/chat/new            // 새 채팅 생성
```

### WebSocket 연결
```typescript
// Socket.io 이벤트
connect / disconnect          // 연결 관리
message                       // 메시지 송수신
typing / stop_typing          // 타이핑 상태
error                         // 에러 처리
```

---

## 📱 반응형 디자인

### 브레이크포인트
```css
/* Tailwind 브레이크포인트 */
sm: 640px   // 모바일
md: 768px   // 태블릿
lg: 1024px  // 데스크톱
xl: 1280px  // 대형 데스크톱
```

### 모바일 최적화
- [ ] 터치 친화적 UI 크기
- [ ] 가로/세로 모드 대응
- [ ] 모바일 키보드 대응
- [ ] 스와이프 제스처 (선택사항)

---

## 🚀 성능 최적화

### 최적화 기법
- [ ] **코드 스플리팅**: 페이지별 청크 분할
- [ ] **지연 로딩**: 이미지 및 컴포넌트 lazy loading
- [ ] **메모이제이션**: React.memo, useMemo, useCallback
- [ ] **번들 최적화**: next/bundle-analyzer 사용
- [ ] **이미지 최적화**: next/image 컴포넌트 활용

### 캐싱 전략
- [ ] **API 캐싱**: React Query로 서버 상태 캐싱
- [ ] **Static Generation**: 정적 페이지 pre-render
- [ ] **브라우저 캐싱**: 적절한 Cache-Control 헤더

---

## 🔒 보안 고려사항

### 인증 보안
- [ ] HTTPS 강제 사용
- [ ] JWT 토큰 만료 처리
- [ ] Refresh Token 로직
- [ ] CSRF 보호

### 입력 검증
- [ ] XSS 방지 (DOMPurify)
- [ ] 입력값 sanitization
- [ ] 파일 업로드 검증

---

## 🧪 테스트 계획

### 테스트 도구
- **Jest**: 단위 테스트
- **React Testing Library**: 컴포넌트 테스트
- **Cypress**: E2E 테스트

### 테스트 범위
- [ ] 인증 플로우 테스트
- [ ] 채팅 기능 테스트
- [ ] API 연동 테스트
- [ ] 반응형 디자인 테스트

---

## 📦 배포 계획

### 배포 플랫폼
- **Vercel** (추천): Next.js 최적화
- **Netlify**: 대안 플랫폼

### 환경 설정
```bash
# frontend/.env.local
NEXTAUTH_URL=https://mma-savant.vercel.app
NEXTAUTH_SECRET=your_secret_key
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
NEXT_PUBLIC_API_URL=http://localhost:8000  # FastAPI 백엔드 URL
```

### CI/CD
- [ ] GitHub Actions 설정
- [ ] 자동 빌드 및 배포
- [ ] 테스트 자동화
- [ ] 환경별 배포 (dev, staging, prod)

---

## 🎯 마일스톤

### Week 1 ✅ 완료
- [x] 프로젝트 설정 및 기본 구조
- [x] 인증 시스템 구현
- [x] 기본 채팅 UI 구현
- [x] 실시간 통신 구현 (Mock 기반)

### Week 2
- [ ] FastAPI 연동
- [ ] 고급 기능 구현

### Week 3
- [ ] 성능 최적화
- [ ] 테스트 작성
- [ ] 배포 준비 및 배포

---

## 📝 추가 검토 사항

### 향후 확장 계획
- [ ] **다국어 지원** (i18n)
- [ ] **음성 입력/출력**
- [ ] **모바일 앱** (React Native)
- [ ] **오프라인 모드** (PWA)
- [ ] **AI 음성 대화**

### 모니터링 및 분석
- [ ] **Google Analytics** 연동
- [ ] **Sentry** 에러 추적
- [ ] **성능 모니터링**
- [ ] **사용자 피드백** 수집

---

**예상 개발 기간**: 2-3주  
**예상 개발자**: 1명 (풀스택)  
**우선순위**: 인증 → 채팅 → 실시간 → 최적화