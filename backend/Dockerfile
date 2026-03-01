# syntax=docker/dockerfile:1
FROM python:3.12-alpine AS builder

WORKDIR /app

# 의존성 설치를 위한 시스템 패키지
RUN apk add --no-cache gcc musl-dev postgresql-dev

# 의존성 파일 복사
COPY pyproject.toml ./

# 의존성 설치 (캐시 마운트 활용)
RUN --mount=type=cache,target=/root/.cache/pip pip install --no-cache-dir -e ".[dev]"

# 소스 코드 복사
COPY . .

# 비동기 엔진 캐시 디렉토리 생성
RUN mkdir -p /app/.cache

# 런타임 스테이지
FROM python:3.12-alpine

WORKDIR /app

# 런타임 의존성
RUN apk add --no-cache postgresql-client

# 빌더 스테이지에서 Python 환경 복사
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app

# 비동기 엔진 캐시 디렉토리 생성
RUN mkdir -p /app/.cache

# 비루트 사용자 생성
RUN addgroup -g 1000 appuser && adduser -D -u 1000 -G appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# 포트 노출
EXPOSE 8000

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# 개발 모드 진입점
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
