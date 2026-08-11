# MMA Savant — Frontend

MMA/UFC 데이터 분석 플랫폼의 프론트엔드 애플리케이션.
대시보드를 통한 통계 시각화, AI 채팅 기반 데이터 분석, 선수/이벤트 상세 정보를 제공한다.

## 주요 기능

- **대시보드** — 홈, Overview, Striking, Grappling 탭별 통계 차트 및 리더보드
- **AI 채팅** — WebSocket 기반 실시간 MMA 데이터 분석 대화 (토큰 스트리밍, 시각화 자동 생성)
- **선수 상세** — 전적, 스탯, 경기 히스토리
- **이벤트 상세** — 대회 정보, 경기 결과
- **인증** — 일반 로그인/회원가입, OAuth (NextAuth)
- **프로필** — 사용자 정보 및 사용량 관리
- **관리자 설정** — 시스템 설정 (AdminGuard)

## 페이지 구조

| 경로 | 페이지 | 인증 |
|------|--------|------|
| `/` | 대시보드 (홈) | 불필요 |
| `/chat` | AI 채팅 | 필요 |
| `/fighters/[id]` | 선수 상세 | 불필요 |
| `/events/[id]` | 이벤트 상세 | 불필요 |
| `/auth/signin` | 로그인 | - |
| `/auth/signup` | 회원가입 | - |
| `/profile` | 프로필 | 필요 |
| `/settings` | 관리자 설정 | 관리자 전용 |

## 프로젝트 구조

```
src/
├── app/                  # Next.js App Router 페이지
│   ├── page.tsx          # 대시보드 (홈)
│   ├── layout.tsx        # 루트 레이아웃
│   ├── error.tsx         # 글로벌 에러 바운더리
│   ├── global-error.tsx  # 루트 레이아웃 에러 바운더리
│   ├── auth/             # 로그인/회원가입
│   ├── chat/             # AI 채팅
│   ├── fighters/[id]/    # 선수 상세
│   ├── events/[id]/      # 이벤트 상세
│   ├── profile/          # 프로필
│   └── settings/         # 관리자 설정
├── components/
│   ├── ui/               # shadcn/ui 기반 공통 UI 컴포넌트
│   ├── layout/           # GlobalNav 등 레이아웃
│   ├── dashboard/        # 대시보드 차트 및 카드
│   ├── chat/             # 채팅 UI (메시지, 입력, 사이드바)
│   ├── fighter/          # 선수 상세 컴포넌트
│   ├── event/            # 이벤트 상세 컴포넌트
│   ├── visualization/    # Recharts 기반 차트 컴포넌트
│   ├── auth/             # AuthGuard, 로그인/회원가입 폼
│   ├── admin/            # AdminGuard, 설정 컴포넌트
│   ├── profile/          # 프로필 컴포넌트
│   ├── providers/        # SessionProvider
│   └── common/           # 공통 컴포넌트
├── hooks/                # 커스텀 훅 (useSocket, useUser 등)
├── services/             # API 서비스 계층 (dashboardApi, chatApi 등)
├── lib/                  # 유틸리티 (api 클라이언트, realSocket, toast)
├── store/                # Zustand 상태 관리
├── types/                # TypeScript 타입 정의
└── config/               # 환경변수 설정
```
