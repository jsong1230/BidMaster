# syntax=docker/dockerfile:1
FROM node:22.13-alpine AS builder

WORKDIR /app

# 의존성 파일 복사
COPY package*.json ./

# 의존성 설치 (캐시 마운트 활용)
RUN --mount=type=cache,target=/root/.npm npm ci --prefer-offline

# 소스 코드 복사
COPY . .

# 빌드
RUN npm run build

# 런타임 스테이지
FROM node:22.13-alpine

WORKDIR /app

# 의존성 파일 복사
COPY package*.json ./

# 의존성 설치 (캐시 마운트 활용)
RUN --mount=type=cache,target=/root/.npm npm ci --prefer-offline --omit=dev

# 빌더 스테이지에서 .next 복사
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/next.config.js ./

# 비루트 사용자 생성
RUN addgroup -g 1000 appuser && adduser -D -u 1000 -G appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# 포트 노출
EXPOSE 3000

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

# 개발 모드 진입점
CMD ["npm", "run", "dev"]
