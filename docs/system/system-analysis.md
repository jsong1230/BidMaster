# 시스템 분석 (BidMaster)

## 1. 프로젝트 개요

**BidMaster**는 AI 기반 공공 입찰 제안서 자동화 SaaS입니다.

### 비즈니스 목표
- 공공 입찰 공고 자동 수집 및 매칭
- AI 기반 제안서 자동 생성
- 낙찰 가능성 분석 및 투찰 전략 제안
- 입찰 파이프라인 대시보드 제공

### 핵심 가치
- 제안서 작성 시간 80% 단축
- 낙찰률 향상 (데이터 기반 전략)
- 매칭 공고 자동 발견

---

## 2. 기술 스택 분석

### Backend (FastAPI)
| 구성요소 | 기술 | 상태 |
|----------|------|------|
| Framework | FastAPI (Python 3.12) | ✅ 스캐폴딩 완료 |
| Database | PostgreSQL + pgvector | ⚠️ 설정만 완료, 스키마 없음 |
| Cache | Redis | ⚠️ 설정만 완료 |
| Auth | JWT (python-jose, bcrypt) | ⚠️ 유틸리티만 존재 |
| AI | Anthropic Claude | ⚠️ 설정만 존재 |

### Frontend (Next.js 14)
| 구성요소 | 기술 | 상태 |
|----------|------|------|
| Framework | Next.js 14 (App Router) | ✅ 스캐폴딩 완료 |
| Styling | Tailwind CSS | ✅ 설정 완료 |
| Font | Inter (Google Fonts) | ✅ 적용 |

### 인프라
- Docker: 미설정
- CI/CD: 미설정
- 배포: 미설정

---

## 3. 현재 코드 구조

### Backend 구조
```
backend/
├── src/
│   ├── api/
│   │   ├── deps.py          # DB/Redis 의존성
│   │   └── v1/
│   │       ├── router.py    # API 라우터 통합
│   │       ├── auth.py      # 인증 API (스텁)
│   │       └── proposals.py # 제안서 API (스텁)
│   ├── core/
│   │   └── security.py      # JWT/비밀번호 유틸리티
│   ├── models/              # SQLAlchemy 모델 (비어있음)
│   ├── schemas/             # Pydantic 스키마 (비어있음)
│   ├── services/            # 비즈니스 로직 (비어있음)
│   ├── config.py            # 설정 관리
│   └── main.py              # FastAPI 앱 진입점
├── alembic/                 # DB 마이그레이션 (설정만)
└── tests/                   # 테스트 (비어있음)
```

### Frontend 구조
```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx       # 루트 레이아웃
│   │   ├── page.tsx         # 홈페이지
│   │   └── globals.css      # 글로벌 스타일
│   └── lib/
│       └── api-client.ts    # API 클라이언트 (기본)
└── tailwind.config.ts       # Tailwind 설정
```

---

## 4. API 엔드포인트 (현재)

| Method | Path | 설명 | 상태 |
|--------|------|------|------|
| GET | / | 루트 | ✅ 구현 |
| GET | /health | 헬스체크 | ✅ 구현 |
| POST | /api/v1/auth/login | 로그인 | ⚠️ 스텁 |
| POST | /api/v1/auth/register | 회원가입 | ⚠️ 스텁 |
| POST | /api/v1/auth/logout | 로그아웃 | ⚠️ 스텁 |
| GET | /api/v1/proposals | 제안서 목록 | ⚠️ 스텁 |
| GET | /api/v1/proposals/{id} | 제안서 상세 | ⚠️ 스텁 |
| POST | /api/v1/proposals | 제안서 생성 | ⚠️ 스텁 |

---

## 5. 데이터베이스 스키마 (현재)

**현재 상태**: 마이그레이션 없음, 테이블 없음

### 필요한 엔티티 (features.md 기반)
1. **users** - 사용자 계정
2. **companies** - 회사 프로필
3. **certifications** - 보유 인증
4. **performances** - 수행 실적
5. **bids** - 공고 정보
6. **bid_attachments** - 공고 첨부파일
7. **proposals** - 제안서
8. **proposal_sections** - 제안서 섹션
9. **notifications** - 알림
10. **subscriptions** - 구독 정보

---

## 6. 보안 현황

### 구현된 것
- JWT 토큰 생성/검증 유틸리티
- 비밀번호 해싱 (bcrypt)
- CORS 설정 (localhost:3000)

### 미구현
- 실제 인증 로직
- 토큰 블랙리스트 (Redis)
- 카카오 OAuth
- RBAC (역할 기반 접근 제어)

---

## 7. 분석 결론

### 현재 상태
- **프로젝트 단계**: 초기 스캐폴딩 (M0 시작 전)
- **구현률**: ~5% (기본 구조만)
- **기능 상태**: 모든 기능 대기 (⏳)

### 우선 작업 필요
1. **데이터베이스 스키마 설계** (ERD)
2. **인증 시스템 구현** (F-07)
3. **프로필 관리 구현** (F-08)

### 설계 필요 사항
- ERD (엔티티 관계도)
- 디자인 시스템 (색상, 타이포, 컴포넌트)
- API 컨벤션 (응답 포맷, 에러 코드)
- 내비게이션 구조 (화면 흐름)
- 레이아웃 와이어프레임
