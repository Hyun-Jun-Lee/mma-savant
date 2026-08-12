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

## Production CD

릴리스는 기존처럼 `main` 브랜치에서 `vX.Y.Z` 형식의 git tag를 push하면 시작된다.
CD는 직전 semver tag와 현재 tag의 변경 파일을 비교해서 필요한 컴포넌트만 빌드/배포한다.

| 변경 범위 | 빌드 이미지 | 운영 반영 |
|-----------|-------------|-----------|
| `frontend/**` | `web:<tag>` | API/Web blue-green 배포, API는 기존 운영 버전 재사용 |
| `src/api/**`, `src/llm/**` 등 API 런타임 | `api:<tag>` | API/Web blue-green 배포, Web은 기존 운영 버전 재사용 |
| `src/data_collector/**` | `flow:<tag>` | `flow_serve` 컨테이너만 recreate |
| 공용 모델/DB 계층 | `api:<tag>`, `flow:<tag>` | API/Web 배포와 `flow_serve` recreate |

운영 서버에는 현재 배포된 컴포넌트 버전이 각각 기록된다.

```bash
cat ~/mma-savant/.deployed-api-version
cat ~/mma-savant/.deployed-web-version
cat ~/mma-savant/.deployed-flow-version
```

수동으로 API/Web을 배포해야 할 때는 버전을 독립적으로 넘길 수 있다.

```bash
./scripts/deploy-blue-green.sh \
  --api-version v0.18.0 \
  --web-version v0.17.3 \
  --release-version v0.18.0 \
  --registry ghcr.io/hyun-jun-lee/mma-savant
```

수동으로 Prefect `flow_serve`만 갱신해야 할 때는 Flow 이미지 버전을 지정한다.

```bash
./scripts/restart-flow-serve.sh \
  --flow-version v0.18.0 \
  --registry ghcr.io/hyun-jun-lee/mma-savant
```
