FROM node:20-alpine

WORKDIR /app

# 의존성 파일 복사
COPY package.json package-lock.json* ./

# 의존성 설치
RUN npm ci

# 소스 코드 복사
COPY . .

# 환경변수 설정
ENV NODE_ENV=development
ENV NEXT_TELEMETRY_DISABLED=1

# 포트 노출
EXPOSE 3000
