# BidMaster (비드마스터)

## 프로젝트
AI 기반 공공 입찰 제안서 자동화 SaaS

## 기술 스택
- Backend: FastAPI (Python 3.12)
- Frontend: Next.js 14 (App Router) + TypeScript + Tailwind CSS
- DB: PostgreSQL + Redis

## 디렉토리
- `frontend/` — Next.js 프론트엔드
- `backend/` — FastAPI 백엔드
- `docs/` — 프로젝트 문서

## 실행
- 개발:
  - Frontend: `cd frontend && npm run dev`
  - Backend: `cd backend && uvicorn src.main:app --reload`
- 테스트:
  - Frontend: `cd frontend && npm test`
  - Backend: `cd backend && pytest`
- 빌드:
  - Frontend: `cd frontend && npm run build`

## 프로젝트 관리
- 방식: file
