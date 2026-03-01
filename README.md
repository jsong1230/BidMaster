# BidMaster (비드마스터)

AI 기반 공공 입찰 제안서 자동화 SaaS

## 기술 스택

### Backend
- FastAPI 0.115.0 (Python 3.12)
- SQLAlchemy 2.0.36 (비동기 ORM)
- Alembic 1.14.0 (데이터베이스 마이그레이션)
- PostgreSQL 16.6
- Redis 7.4
- Anthropic Claude AI

### Frontend
- Next.js 14.2.0 (App Router)
- React 18.3.0
- TypeScript 5.6.0
- Tailwind CSS 3.4.0
- TanStack React Query 5.62.0
- Zustand 5.0.0 (상태 관리)

## 디렉토리 구조

```
BidMaster/
├── backend/                 # FastAPI 백엔드
│   ├── src/
│   │   ├── api/            # API 라우터
│   │   ├── models/         # 데이터베이스 모델
│   │   ├── schemas/        # Pydantic 스키마
│   │   ├── services/       # 비즈니스 로직
│   │   ├── core/           # 코어 모듈 (보안 등)
│   │   ├── main.py         # FastAPI 앱 진입점
│   │   └── config.py       # 설정 관리
│   ├── tests/              # 테스트
│   ├── alembic/            # 데이터베이스 마이그레이션
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/               # Next.js 프론트엔드
│   ├── src/
│   │   ├── app/           # App Router 페이지
│   │   ├── components/    # React 컴포넌트
│   │   ├── lib/           # 유틸리티, API 클라이언트
│   │   └── types/         # TypeScript 타입
│   ├── public/
│   ├── Dockerfile
│   └── package.json
├── docs/                  # 프로젝트 문서
├── docker-compose.yml
└── CLAUDE.md
```

## 실행 방법

### Docker Compose (권장)

```bash
# 전체 서비스 기동 (DB, Redis, Backend, Frontend)
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 서비스 중지
docker-compose down
```

### 로컬 개발

#### Backend

```bash
cd backend

# 가상환경 생성 및 활성화
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 또는
.venv\Scripts\activate     # Windows

# 의존성 설치
pip install -e ".[dev]"

# 데이터베이스 마이그레이션
alembic upgrade head

# 개발 서버 실행
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

## 환경 변수

### Backend (.env)

```bash
# 애플리케이션
APP_NAME=BidMaster API
DEBUG=true

# 데이터베이스
DATABASE_URL=postgresql+asyncpg://bidmaster:bidmaster@localhost:5432/bidmaster

# Redis
REDIS_URL=redis://localhost:6379/0

# 보안
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Anthropic Claude
ANTHROPIC_API_KEY=your-anthropic-api-key
```

### Frontend (.env.local)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## 테스트

### Backend

```bash
cd backend
pytest
```

### Frontend

```bash
cd frontend
npm test
```

## API 문서

백엔드 서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 라이선스

Copyright (c) 2026 BidMaster. All rights reserved.
