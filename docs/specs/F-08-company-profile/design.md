# F-08 회사 프로필 관리 — 변경 설계서

## 1. 참조
- 인수조건: docs/project/features.md #F-08
- 시스템 분석: docs/system/system-analysis.md
- ERD: docs/system/erd.md (companies, company_members, certifications, performances)
- API 컨벤션: docs/system/api-conventions.md
- 인증 설계: docs/specs/F-07-auth/design.md

---

## 2. 변경 범위

- **변경 유형**: 신규 추가
- **영향 받는 모듈**:
  - User 모델 (company_id FK 활성화, company relationship 추가)
  - 인증 토큰 (companyId 클레임 갱신)
  - API 라우터 (companies 라우터 등록)
  - 모델 __init__.py (신규 모델 등록)

---

## 3. 영향 분석

### 기존 API 변경

| API | 현재 | 변경 후 | 하위 호환성 |
|-----|------|---------|-------------|
| GET /api/v1/auth/me | company_id: null 반환 | company_id: UUID 반환 | O (nullable 유지) |
| POST /api/v1/auth/login | JWT에 companyId: null | JWT에 companyId: UUID | O (nullable 유지) |

### 기존 DB 변경

| 테이블 | 변경 내용 | 마이그레이션 전략 |
|--------|----------|------------------|
| users | company_id FK 제약조건 활성화 (companies 테이블 생성 후) | companies 테이블 먼저 생성 후 FK 제약조건 추가 |

### 기존 모델 변경

| 파일 | 변경 내용 |
|------|----------|
| backend/src/models/user.py | company relationship 추가 |
| backend/src/models/__init__.py | Company, CompanyMember, Certification, Performance 모델 등록 |
| backend/src/api/v1/router.py | companies 라우터 포함 |

### 사이드 이펙트
- users.company_id FK가 companies 테이블 존재를 전제하므로, Alembic 마이그레이션 순서 주의 (companies 먼저)
- 회사 등록 시 company_members에 owner로 자동 추가되므로, 사용자의 company_id도 함께 갱신 필요
- Access Token의 companyId 클레임은 회사 등록 후 재로그인 또는 토큰 갱신 시 반영됨

---

## 4. 아키텍처 결정

### 결정 1: 사업자등록번호 검증 전략
- **선택지**: A) 국세청 API 실시간 검증 / B) 형식 검증만 (MVP)
- **결정**: B) 형식 검증만 (정규식 + 체크섬)
- **근거**:
  - MVP 단계에서 외부 API 의존성 최소화
  - 사업자등록번호 10자리 형식 + 체크섬 검증으로 기본 유효성 확보
  - 추후 국세청 API 연동 시 서비스 레이어만 변경하면 됨

### 결정 2: 임베딩 생성 시점
- **선택지**: A) 저장 시 동기 생성 / B) 저장 후 비동기 생성 / C) nullable 스텁 (MVP)
- **결정**: C) nullable 스텁
- **근거**:
  - MVP에서는 임베딩 컬럼을 nullable로 유지
  - F-01 공고 매칭 기능 구현 시 임베딩 생성 로직 연동
  - 회사 프로필 저장/수정 시 embedding_status 대신 단순 NULL 체크로 처리

### 결정 3: 파일 업로드 전략
- **선택지**: A) S3 / B) 로컬 파일시스템 (MVP) / C) 파일 메타데이터만 저장
- **결정**: C) 파일 메타데이터만 저장 (MVP)
- **근거**:
  - MVP에서는 document_url 필드에 URL 문자열만 저장
  - 실제 파일 업로드는 api-conventions.md 9절의 파일 업로드 API 구현 시 연동
  - certifications.document_url, performances.document_url 모두 동일 전략

### 결정 4: 회사-사용자 관계 모델
- **선택지**: A) users.company_id FK만 사용 / B) company_members 중간 테이블 + users.company_id
- **결정**: B) company_members 중간 테이블 + users.company_id
- **근거**:
  - company_members로 다중 역할(owner, admin, member) 관리
  - users.company_id는 빠른 조회용 (정규화 vs 성능 트레이드오프)
  - 회사 등록 시 company_members에 owner로 추가하고, users.company_id도 갱신

### 결정 5: 대표 실적 지정 방식
- **선택지**: A) is_representative 불리언 (다수 가능) / B) 단일 대표 실적만 허용
- **결정**: A) is_representative 불리언 (다수 가능)
- **근거**:
  - 제안서 생성 시 여러 대표 실적을 우선 활용할 수 있어야 함
  - 대표 실적 수 제한은 비즈니스 규칙으로 서비스 레이어에서 처리 (최대 5개)

---

## 5. API 설계

### 5.1 POST /api/v1/companies
회사 등록

- **목적**: 신규 회사 프로필 생성 및 등록자를 owner로 설정
- **인증**: 필요 (Bearer Token)
- **Request Body**:
```json
{
  "businessNumber": "1234567890",
  "name": "주식회사 비드마스터",
  "ceoName": "홍길동",
  "address": "서울특별시 강남구 테헤란로 123",
  "phone": "02-1234-5678",
  "industry": "소프트웨어 개발업",
  "scale": "small",
  "description": "AI 기반 입찰 자동화 솔루션 기업"
}
```
- **유효성 검사**:
  - businessNumber: 필수, 10자리 숫자, 사업자등록번호 체크섬 검증
  - name: 필수, 1~200자
  - scale: 선택, enum (small, medium, large)
  - industry: 선택, 1~100자
- **Response** (201 Created):
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "businessNumber": "1234567890",
    "name": "주식회사 비드마스터",
    "ceoName": "홍길동",
    "address": "서울특별시 강남구 테헤란로 123",
    "phone": "02-1234-5678",
    "industry": "소프트웨어 개발업",
    "scale": "small",
    "description": "AI 기반 입찰 자동화 솔루션 기업",
    "createdAt": "2026-03-02T10:00:00Z"
  }
}
```
- **비즈니스 규칙**:
  - 등록자는 company_members에 owner 역할로 자동 추가
  - 등록자의 users.company_id를 생성된 회사 ID로 갱신
  - 이미 회사에 소속된 사용자는 등록 불가
- **에러 케이스**:
  | 코드 | HTTP Status | 상황 |
  |------|-------------|------|
  | COMPANY_002 | 409 | 이미 등록된 사업자등록번호 |
  | COMPANY_003 | 400 | 사업자등록번호 형식/체크섬 검증 실패 |
  | COMPANY_004 | 409 | 사용자가 이미 회사에 소속됨 |
  | VALIDATION_001 | 400 | 입력값 유효성 실패 |

### 5.2 GET /api/v1/companies/my
내 회사 조회

- **목적**: 현재 로그인 사용자의 소속 회사 정보 조회
- **인증**: 필요 (Bearer Token)
- **Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "businessNumber": "1234567890",
    "name": "주식회사 비드마스터",
    "ceoName": "홍길동",
    "address": "서울특별시 강남구 테헤란로 123",
    "phone": "02-1234-5678",
    "industry": "소프트웨어 개발업",
    "scale": "small",
    "description": "AI 기반 입찰 자동화 솔루션 기업",
    "memberCount": 3,
    "performanceCount": 12,
    "certificationCount": 5,
    "createdAt": "2026-03-02T10:00:00Z",
    "updatedAt": "2026-03-02T10:00:00Z"
  }
}
```
- **에러 케이스**:
  | 코드 | HTTP Status | 상황 |
  |------|-------------|------|
  | COMPANY_001 | 404 | 소속 회사 없음 (company_id가 NULL) |

### 5.3 PUT /api/v1/companies/{id}
회사 정보 수정

- **목적**: 회사 기본 정보 수정
- **인증**: 필요 (Bearer Token)
- **권한**: owner 또는 admin만 수정 가능
- **Request Body**:
```json
{
  "name": "주식회사 비드마스터",
  "ceoName": "김길동",
  "address": "서울특별시 서초구 서초대로 456",
  "phone": "02-9876-5432",
  "industry": "소프트웨어 개발업",
  "scale": "medium",
  "description": "AI 기반 입찰 자동화 솔루션 기업 (업데이트)"
}
```
- **유효성 검사**:
  - businessNumber는 수정 불가 (변경 필요 시 관리자 문의)
  - name: 필수, 1~200자
  - scale: 선택, enum (small, medium, large)
- **Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "businessNumber": "1234567890",
    "name": "주식회사 비드마스터",
    "ceoName": "김길동",
    "address": "서울특별시 서초구 서초대로 456",
    "phone": "02-9876-5432",
    "industry": "소프트웨어 개발업",
    "scale": "medium",
    "description": "AI 기반 입찰 자동화 솔루션 기업 (업데이트)",
    "updatedAt": "2026-03-02T11:00:00Z"
  }
}
```
- **에러 케이스**:
  | 코드 | HTTP Status | 상황 |
  |------|-------------|------|
  | COMPANY_001 | 404 | 회사를 찾을 수 없음 |
  | PERMISSION_001 | 403 | 수정 권한 없음 |
  | VALIDATION_001 | 400 | 입력값 유효성 실패 |

### 5.4 POST /api/v1/companies/{id}/performances
수행 실적 등록

- **목적**: 과거 사업 수행 실적 등록
- **인증**: 필요 (Bearer Token)
- **권한**: 해당 회사 멤버 (owner, admin, member)
- **Request Body**:
```json
{
  "projectName": "공공데이터 포털 고도화 사업",
  "clientName": "행정안전부",
  "clientType": "public",
  "contractAmount": 500000000,
  "startDate": "2024-01-15",
  "endDate": "2024-12-31",
  "status": "completed",
  "description": "공공데이터 포털 UI/UX 개선 및 API 고도화",
  "isRepresentative": false,
  "documentUrl": null
}
```
- **유효성 검사**:
  - projectName: 필수, 1~300자
  - clientName: 필수, 1~200자
  - clientType: 선택, enum (public, private)
  - contractAmount: 필수, 양수
  - startDate: 필수, YYYY-MM-DD
  - endDate: 필수, YYYY-MM-DD, startDate 이후
  - status: 필수, enum (completed, ongoing)
  - isRepresentative: 선택, boolean (기본 false)
  - isRepresentative=true 시 기존 대표 실적 수 확인 (최대 5개)
- **Response** (201 Created):
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "companyId": "uuid",
    "projectName": "공공데이터 포털 고도화 사업",
    "clientName": "행정안전부",
    "clientType": "public",
    "contractAmount": 500000000,
    "startDate": "2024-01-15",
    "endDate": "2024-12-31",
    "status": "completed",
    "description": "공공데이터 포털 UI/UX 개선 및 API 고도화",
    "isRepresentative": false,
    "documentUrl": null,
    "createdAt": "2026-03-02T10:00:00Z"
  }
}
```
- **에러 케이스**:
  | 코드 | HTTP Status | 상황 |
  |------|-------------|------|
  | COMPANY_001 | 404 | 회사를 찾을 수 없음 |
  | PERMISSION_001 | 403 | 해당 회사 멤버가 아님 |
  | VALIDATION_001 | 400 | 입력값 유효성 실패 |
  | COMPANY_005 | 400 | 대표 실적 최대 개수 초과 (5개) |

### 5.5 GET /api/v1/companies/{id}/performances
수행 실적 목록 조회

- **목적**: 회사의 수행 실적 목록 조회 (페이지네이션)
- **인증**: 필요 (Bearer Token)
- **권한**: 해당 회사 멤버
- **Query Parameters**:
  | Parameter | Type | Default | 설명 |
  |-----------|------|---------|------|
  | page | int | 1 | 페이지 번호 |
  | pageSize | int | 20 | 페이지당 항목 수 (최대 100) |
  | status | string | | 필터: completed, ongoing |
  | isRepresentative | boolean | | 필터: 대표 실적 여부 |
  | sortBy | string | createdAt | 정렬 필드 (createdAt, contractAmount, startDate) |
  | sortOrder | string | desc | 정렬 방향 (asc, desc) |
- **Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "projectName": "공공데이터 포털 고도화 사업",
        "clientName": "행정안전부",
        "clientType": "public",
        "contractAmount": 500000000,
        "startDate": "2024-01-15",
        "endDate": "2024-12-31",
        "status": "completed",
        "isRepresentative": true,
        "createdAt": "2026-03-02T10:00:00Z"
      }
    ]
  },
  "meta": {
    "page": 1,
    "pageSize": 20,
    "total": 12,
    "totalPages": 1
  }
}
```

### 5.6 PUT /api/v1/companies/{id}/performances/{perfId}
수행 실적 수정

- **목적**: 기존 수행 실적 정보 수정
- **인증**: 필요 (Bearer Token)
- **권한**: 해당 회사 owner 또는 admin
- **Request Body**: 5.4와 동일 구조
- **Response** (200 OK): 5.4의 Response와 동일 구조 (updatedAt 포함)
- **에러 케이스**:
  | 코드 | HTTP Status | 상황 |
  |------|-------------|------|
  | COMPANY_001 | 404 | 회사를 찾을 수 없음 |
  | COMPANY_006 | 404 | 수행 실적을 찾을 수 없음 |
  | PERMISSION_001 | 403 | 수정 권한 없음 |
  | COMPANY_005 | 400 | 대표 실적 최대 개수 초과 |

### 5.7 DELETE /api/v1/companies/{id}/performances/{perfId}
수행 실적 삭제 (Soft Delete)

- **목적**: 수행 실적 소프트 삭제
- **인증**: 필요 (Bearer Token)
- **권한**: 해당 회사 owner 또는 admin
- **Response** (200 OK):
```json
{
  "success": true,
  "data": null
}
```
- **에러 케이스**:
  | 코드 | HTTP Status | 상황 |
  |------|-------------|------|
  | COMPANY_001 | 404 | 회사를 찾을 수 없음 |
  | COMPANY_006 | 404 | 수행 실적을 찾을 수 없음 |
  | PERMISSION_001 | 403 | 삭제 권한 없음 |

### 5.8 PATCH /api/v1/companies/{id}/performances/{perfId}/representative
대표 실적 지정/해제

- **목적**: 특정 실적의 대표 여부 토글
- **인증**: 필요 (Bearer Token)
- **권한**: 해당 회사 owner 또는 admin
- **Request Body**:
```json
{
  "isRepresentative": true
}
```
- **비즈니스 규칙**:
  - isRepresentative=true 지정 시 기존 대표 실적 수 확인 (최대 5개)
  - isRepresentative=false 해제 시 제한 없음
- **Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "projectName": "공공데이터 포털 고도화 사업",
    "isRepresentative": true,
    "updatedAt": "2026-03-02T11:00:00Z"
  }
}
```
- **에러 케이스**:
  | 코드 | HTTP Status | 상황 |
  |------|-------------|------|
  | COMPANY_006 | 404 | 수행 실적을 찾을 수 없음 |
  | PERMISSION_001 | 403 | 지정 권한 없음 |
  | COMPANY_005 | 400 | 대표 실적 최대 개수 초과 |

### 5.9 POST /api/v1/companies/{id}/certifications
보유 인증 등록

- **목적**: 회사 보유 인증/자격 등록
- **인증**: 필요 (Bearer Token)
- **권한**: 해당 회사 멤버
- **Request Body**:
```json
{
  "name": "GS인증 1등급",
  "issuer": "한국정보통신기술협회(TTA)",
  "certNumber": "GS-2024-0123",
  "issuedDate": "2024-06-15",
  "expiryDate": "2027-06-14",
  "documentUrl": null
}
```
- **유효성 검사**:
  - name: 필수, 1~200자
  - issuer: 선택, 1~200자
  - certNumber: 선택, 1~100자
  - issuedDate: 선택, YYYY-MM-DD
  - expiryDate: 선택, YYYY-MM-DD, issuedDate 이후
- **Response** (201 Created):
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "companyId": "uuid",
    "name": "GS인증 1등급",
    "issuer": "한국정보통신기술협회(TTA)",
    "certNumber": "GS-2024-0123",
    "issuedDate": "2024-06-15",
    "expiryDate": "2027-06-14",
    "documentUrl": null,
    "createdAt": "2026-03-02T10:00:00Z"
  }
}
```
- **에러 케이스**:
  | 코드 | HTTP Status | 상황 |
  |------|-------------|------|
  | COMPANY_001 | 404 | 회사를 찾을 수 없음 |
  | PERMISSION_001 | 403 | 해당 회사 멤버가 아님 |
  | VALIDATION_001 | 400 | 입력값 유효성 실패 |

### 5.10 GET /api/v1/companies/{id}/certifications
보유 인증 목록 조회

- **목적**: 회사의 보유 인증 목록 조회 (페이지네이션)
- **인증**: 필요 (Bearer Token)
- **권한**: 해당 회사 멤버
- **Query Parameters**:
  | Parameter | Type | Default | 설명 |
  |-----------|------|---------|------|
  | page | int | 1 | 페이지 번호 |
  | pageSize | int | 20 | 페이지당 항목 수 (최대 100) |
  | sortBy | string | createdAt | 정렬 필드 (createdAt, expiryDate, name) |
  | sortOrder | string | desc | 정렬 방향 (asc, desc) |
- **Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "name": "GS인증 1등급",
        "issuer": "한국정보통신기술협회(TTA)",
        "certNumber": "GS-2024-0123",
        "issuedDate": "2024-06-15",
        "expiryDate": "2027-06-14",
        "documentUrl": null,
        "isExpired": false,
        "createdAt": "2026-03-02T10:00:00Z"
      }
    ]
  },
  "meta": {
    "page": 1,
    "pageSize": 20,
    "total": 5,
    "totalPages": 1
  }
}
```

### 5.11 PUT /api/v1/companies/{id}/certifications/{certId}
보유 인증 수정

- **목적**: 기존 인증 정보 수정
- **인증**: 필요 (Bearer Token)
- **권한**: 해당 회사 owner 또는 admin
- **Request Body**: 5.9와 동일 구조
- **Response** (200 OK): 5.9의 Response와 동일 구조 (updatedAt 포함)
- **에러 케이스**:
  | 코드 | HTTP Status | 상황 |
  |------|-------------|------|
  | COMPANY_001 | 404 | 회사를 찾을 수 없음 |
  | COMPANY_007 | 404 | 인증 정보를 찾을 수 없음 |
  | PERMISSION_001 | 403 | 수정 권한 없음 |

### 5.12 DELETE /api/v1/companies/{id}/certifications/{certId}
보유 인증 삭제 (Soft Delete)

- **목적**: 인증 정보 소프트 삭제
- **인증**: 필요 (Bearer Token)
- **권한**: 해당 회사 owner 또는 admin
- **Response** (200 OK):
```json
{
  "success": true,
  "data": null
}
```
- **에러 케이스**:
  | 코드 | HTTP Status | 상황 |
  |------|-------------|------|
  | COMPANY_001 | 404 | 회사를 찾을 수 없음 |
  | COMPANY_007 | 404 | 인증 정보를 찾을 수 없음 |
  | PERMISSION_001 | 403 | 삭제 권한 없음 |

### 5.13 POST /api/v1/companies/{id}/members
멤버 초대

- **목적**: 이메일로 회사 멤버 초대
- **인증**: 필요 (Bearer Token)
- **권한**: owner 또는 admin만 초대 가능
- **Request Body**:
```json
{
  "email": "member@example.com",
  "role": "member"
}
```
- **유효성 검사**:
  - email: 필수, 유효한 이메일 형식
  - role: 필수, enum (admin, member) - owner 지정 불가
- **비즈니스 규칙**:
  - 초대 대상 사용자가 이미 다른 회사에 소속된 경우 에러
  - 초대 대상 사용자가 이미 해당 회사 멤버인 경우 에러
  - company_members에 invited_at 기록, joined_at은 NULL (초대 수락 후 갱신)
  - 초대 대상 사용자의 users.company_id 갱신 및 joined_at 기록 (MVP에서는 즉시 가입 처리)
- **Response** (201 Created):
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "companyId": "uuid",
    "userId": "uuid",
    "email": "member@example.com",
    "name": "김멤버",
    "role": "member",
    "invitedAt": "2026-03-02T10:00:00Z",
    "joinedAt": "2026-03-02T10:00:00Z"
  }
}
```
- **에러 케이스**:
  | 코드 | HTTP Status | 상황 |
  |------|-------------|------|
  | COMPANY_001 | 404 | 회사를 찾을 수 없음 |
  | PERMISSION_003 | 403 | 팀원 초대 권한 없음 |
  | COMPANY_008 | 404 | 초대 대상 사용자를 찾을 수 없음 |
  | COMPANY_009 | 409 | 이미 해당 회사 멤버임 |
  | COMPANY_010 | 409 | 대상 사용자가 이미 다른 회사에 소속됨 |

### 5.14 GET /api/v1/companies/{id}/members
멤버 목록 조회

- **목적**: 회사 멤버 목록 조회
- **인증**: 필요 (Bearer Token)
- **권한**: 해당 회사 멤버
- **Query Parameters**:
  | Parameter | Type | Default | 설명 |
  |-----------|------|---------|------|
  | page | int | 1 | 페이지 번호 |
  | pageSize | int | 20 | 페이지당 항목 수 (최대 100) |
- **Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "userId": "uuid",
        "email": "owner@example.com",
        "name": "홍길동",
        "role": "owner",
        "joinedAt": "2026-03-01T10:00:00Z"
      },
      {
        "id": "uuid",
        "userId": "uuid",
        "email": "member@example.com",
        "name": "김멤버",
        "role": "member",
        "joinedAt": "2026-03-02T10:00:00Z"
      }
    ]
  },
  "meta": {
    "page": 1,
    "pageSize": 20,
    "total": 2,
    "totalPages": 1
  }
}
```

---

## 6. DB 설계

ERD (docs/system/erd.md)에 정의된 테이블 구조를 그대로 사용합니다.

### 6.1 companies 테이블

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 회사 고유 ID |
| business_number | VARCHAR(10) | UK, NOT NULL | 사업자등록번호 |
| name | VARCHAR(200) | NOT NULL | 회사명 |
| ceo_name | VARCHAR(100) | | 대표자명 |
| address | VARCHAR(500) | | 주소 |
| phone | VARCHAR(20) | | 대표 전화번호 |
| industry | VARCHAR(100) | | 업종 |
| scale | VARCHAR(20) | | 기업 규모 (small, medium, large) |
| description | TEXT | | 회사 소개 |
| profile_embedding | vector(1536) | | 프로필 임베딩 (nullable, MVP 스텁) |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 생성 시간 |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 수정 시간 |
| deleted_at | TIMESTAMP | | 삭제 시간 (Soft Delete) |

**Check Constraints**:
```sql
ALTER TABLE companies
    ADD CONSTRAINT chk_companies_scale
    CHECK (scale IS NULL OR scale IN ('small', 'medium', 'large'));
```

### 6.2 company_members 테이블

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 멤버십 ID |
| company_id | UUID | FK -> companies.id, NOT NULL | 회사 ID |
| user_id | UUID | FK -> users.id, NOT NULL | 사용자 ID |
| role | VARCHAR(20) | NOT NULL | 역할 (owner, admin, member) |
| invited_at | TIMESTAMP | | 초대 시간 |
| joined_at | TIMESTAMP | | 가입 시간 |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 생성 시간 |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 수정 시간 |

**Unique Constraint**: (company_id, user_id)

**Check Constraints**:
```sql
ALTER TABLE company_members
    ADD CONSTRAINT chk_company_members_role
    CHECK (role IN ('owner', 'admin', 'member'));
```

### 6.3 certifications 테이블

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 인증 ID |
| company_id | UUID | FK -> companies.id, NOT NULL | 회사 ID |
| name | VARCHAR(200) | NOT NULL | 인증명 |
| issuer | VARCHAR(200) | | 발급 기관 |
| cert_number | VARCHAR(100) | | 인증 번호 |
| issued_date | DATE | | 발급일 |
| expiry_date | DATE | | 만료일 |
| document_url | VARCHAR(500) | | 인증서 파일 URL |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 생성 시간 |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 수정 시간 |
| deleted_at | TIMESTAMP | | 삭제 시간 (Soft Delete) |

**Check Constraints**:
```sql
ALTER TABLE certifications
    ADD CONSTRAINT chk_certifications_expiry
    CHECK (expiry_date IS NULL OR issued_date IS NULL OR expiry_date >= issued_date);
```

### 6.4 performances 테이블

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 실적 ID |
| company_id | UUID | FK -> companies.id, NOT NULL | 회사 ID |
| project_name | VARCHAR(300) | NOT NULL | 사업명 |
| client_name | VARCHAR(200) | NOT NULL | 발주처명 |
| client_type | VARCHAR(50) | | 발주처 유형 (public, private) |
| contract_amount | DECIMAL(15,0) | NOT NULL | 계약 금액 |
| start_date | DATE | NOT NULL | 착수일 |
| end_date | DATE | NOT NULL | 완료일 |
| status | VARCHAR(20) | NOT NULL | 상태 (completed, ongoing) |
| description | TEXT | | 사업 내용 |
| is_representative | BOOLEAN | DEFAULT FALSE | 대표 실적 여부 |
| document_url | VARCHAR(500) | | 실적증명서 URL |
| embedding | vector(1536) | | 실적 임베딩 (nullable, MVP 스텁) |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 생성 시간 |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 수정 시간 |
| deleted_at | TIMESTAMP | | 삭제 시간 (Soft Delete) |

**Check Constraints**:
```sql
ALTER TABLE performances
    ADD CONSTRAINT chk_performances_status
    CHECK (status IN ('completed', 'ongoing'));

ALTER TABLE performances
    ADD CONSTRAINT chk_performances_client_type
    CHECK (client_type IS NULL OR client_type IN ('public', 'private'));

ALTER TABLE performances
    ADD CONSTRAINT chk_performances_dates
    CHECK (end_date >= start_date);

ALTER TABLE performances
    ADD CONSTRAINT chk_performances_amount
    CHECK (contract_amount > 0);
```

---

## 7. 시퀀스 흐름

### 7.1 회사 등록

```
사용자 -> Frontend -> POST /companies -> CompanyService -> DB
    |                                          |
    |  1. 회사 정보 입력                        |
    | ---------------------------------------->|
    |                                          | 2. 사업자등록번호 형식/체크섬 검증
    |                                          | 3. 사업자등록번호 중복 확인
    |                                          | 4. 사용자 기존 소속 회사 확인
    |                                          | 5. companies 테이블에 회사 생성
    |                                          | 6. company_members에 owner로 추가
    |                                          |    (invited_at = NOW, joined_at = NOW)
    |                                          | 7. users.company_id 갱신
    |                                          | 8. commit
    |  <---------------------------------------|
    |  9. 회사 정보 반환                         |
```

### 7.2 수행 실적 등록

```
사용자 -> Frontend -> POST /companies/{id}/performances -> CompanyService -> DB
    |                                                           |
    |  1. 실적 정보 입력                                         |
    | -------------------------------------------------------->|
    |                                                           | 2. 회사 존재 확인 (deleted_at IS NULL)
    |                                                           | 3. 사용자 멤버십 확인
    |                                                           | 4. isRepresentative=true면 기존 대표 실적 수 확인
    |                                                           | 5. performances 테이블에 실적 생성
    |                                                           | 6. commit
    |  <--------------------------------------------------------|
    |  7. 실적 정보 반환                                          |
```

### 7.3 대표 실적 지정

```
사용자 -> Frontend -> PATCH /companies/{id}/performances/{perfId}/representative -> CompanyService -> DB
    |                                                                                     |
    |  1. 대표 실적 지정 요청                                                               |
    | ----------------------------------------------------------------------------------->|
    |                                                                                     | 2. 실적 존재 확인
    |                                                                                     | 3. 사용자 권한 확인 (owner/admin)
    |                                                                                     | 4. isRepresentative=true면
    |                                                                                     |    기존 대표 실적 수 확인 (최대 5개)
    |                                                                                     | 5. performances.is_representative 갱신
    |                                                                                     | 6. commit
    |  <----------------------------------------------------------------------------------|
    |  7. 갱신된 실적 정보 반환                                                               |
```

### 7.4 보유 인증 등록

```
사용자 -> Frontend -> POST /companies/{id}/certifications -> CompanyService -> DB
    |                                                             |
    |  1. 인증 정보 입력                                           |
    | ---------------------------------------------------------->|
    |                                                             | 2. 회사 존재 확인
    |                                                             | 3. 사용자 멤버십 확인
    |                                                             | 4. certifications 테이블에 인증 생성
    |                                                             | 5. commit
    |  <---------------------------------------------------------|
    |  6. 인증 정보 반환                                            |
```

### 7.5 멤버 초대

```
사용자 -> Frontend -> POST /companies/{id}/members -> CompanyService -> DB
    |                                                       |
    |  1. 이메일 + 역할 입력                                  |
    | ----------------------------------------------------->|
    |                                                       | 2. 회사 존재 확인
    |                                                       | 3. 초대자 권한 확인 (owner/admin)
    |                                                       | 4. 대상 사용자 이메일로 조회
    |                                                       | 5. 대상 사용자 기존 소속 회사 확인
    |                                                       | 6. 기존 멤버 여부 확인
    |                                                       | 7. company_members에 추가
    |                                                       | 8. users.company_id 갱신 (즉시 가입, MVP)
    |                                                       | 9. commit
    |  <----------------------------------------------------|
    |  10. 멤버 정보 반환                                     |
```

---

## 8. 영향 범위

### 8.1 수정 필요 파일

| 파일 | 변경 내용 |
|------|----------|
| backend/src/models/user.py | company relationship 추가 (`company = relationship("Company", back_populates="users")`) |
| backend/src/models/__init__.py | Company, CompanyMember, Certification, Performance 모델 import 추가 |
| backend/src/api/v1/router.py | `companies.router` include 추가 |

### 8.2 신규 생성 파일

| 파일 | 설명 |
|------|------|
| backend/src/models/company.py | Company 모델 |
| backend/src/models/company_member.py | CompanyMember 모델 |
| backend/src/models/certification.py | Certification 모델 |
| backend/src/models/performance.py | Performance 모델 |
| backend/src/schemas/company.py | 회사 관련 Pydantic 스키마 |
| backend/src/schemas/performance.py | 수행 실적 관련 스키마 |
| backend/src/schemas/certification.py | 보유 인증 관련 스키마 |
| backend/src/schemas/member.py | 멤버 관련 스키마 |
| backend/src/services/company_service.py | 회사 비즈니스 로직 |
| backend/src/api/v1/companies.py | 회사 프로필 API 엔드포인트 |
| backend/src/utils/validators.py | 사업자등록번호 체크섬 검증 유틸리티 |
| backend/alembic/versions/xxx_create_company_tables.py | 마이그레이션 (companies, company_members, certifications, performances) |

---

## 9. 보안 설계

### 9.1 권한 체계

| 리소스 | owner | admin | member |
|--------|-------|-------|--------|
| 회사 정보 수정 | O | O | X |
| 수행 실적 등록 | O | O | O |
| 수행 실적 수정/삭제 | O | O | X |
| 대표 실적 지정 | O | O | X |
| 인증 등록 | O | O | O |
| 인증 수정/삭제 | O | O | X |
| 멤버 초대 | O | O | X |
| 멤버 목록 조회 | O | O | O |
| 실적/인증 목록 조회 | O | O | O |

### 9.2 권한 검증 흐름

```python
async def verify_company_membership(
    user_id: UUID,
    company_id: UUID,
    required_roles: list[str] | None = None
) -> CompanyMember:
    """
    1. company_members에서 (company_id, user_id) 조회
    2. 존재하지 않으면 PERMISSION_001 (403)
    3. required_roles가 지정된 경우 역할 확인
    4. 해당 역할이 아니면 PERMISSION_001 (403)
    """
```

### 9.3 리소스 접근 제어
- 모든 /companies/{id}/* 엔드포인트는 해당 회사 멤버만 접근 가능
- URL의 {id}와 사용자의 소속 회사 ID 일치 여부 확인
- 소속 회사가 아닌 다른 회사의 리소스 접근 시 PERMISSION_001 (403)

### 9.4 사업자등록번호 검증
```python
def validate_business_number(number: str) -> bool:
    """
    사업자등록번호 형식 검증 (10자리 숫자 + 체크섬)

    체크섬 알고리즘:
    - 가중치: [1, 3, 7, 1, 3, 7, 1, 3, 5]
    - 각 자리 * 가중치 합산
    - 9번째 자리(index 8): (가중치 * 자리수) / 10의 몫도 더함
    - (10 - (합산 % 10)) % 10 == 마지막 자리
    """
```

---

## 10. 성능 설계

### 10.1 인덱스 계획

```sql
-- companies 테이블
CREATE INDEX idx_companies_business_number ON companies(business_number) WHERE deleted_at IS NULL;

-- company_members 테이블
CREATE UNIQUE INDEX idx_company_members_unique ON company_members(company_id, user_id);
CREATE INDEX idx_company_members_user ON company_members(user_id);

-- performances 테이블
CREATE INDEX idx_performances_company ON performances(company_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_performances_representative ON performances(company_id, is_representative)
    WHERE deleted_at IS NULL AND is_representative = TRUE;

-- certifications 테이블
CREATE INDEX idx_certifications_company ON certifications(company_id) WHERE deleted_at IS NULL;

-- 임베딩 검색 (추후 F-01 연동 시 활성화)
-- CREATE INDEX idx_companies_profile_embedding ON companies
--     USING ivfflat (profile_embedding vector_cosine_ops) WITH (lists = 100);
-- CREATE INDEX idx_performances_embedding ON performances
--     USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

### 10.2 캐싱 전략

MVP에서는 별도 캐싱 불필요. 추후 다음 전략 적용 가능:

```
# 회사 프로필 캐시 (추후)
company:{company_id} -> {company_data} (TTL: 10분)

# 회사 프로필 변경 시 캐시 무효화
invalidate: company:{company_id}
```

### 10.3 페이지네이션 성능

- performances, certifications 목록은 company_id로 필터링 후 페이지네이션
- company_id 인덱스가 있으므로 빠른 필터링 가능
- 정렬 필드(created_at, contract_amount)에 대한 추가 복합 인덱스는 데이터량 증가 시 고려

---

## 11. 에러 코드 요약

### 기존 에러 코드 (api-conventions.md)

| 코드 | HTTP Status | 메시지 |
|------|-------------|--------|
| COMPANY_001 | 404 | 회사를 찾을 수 없습니다. |
| COMPANY_002 | 409 | 이미 등록된 사업자등록번호입니다. |
| COMPANY_003 | 400 | 사업자등록번호 검증 실패 |
| COMPANY_004 | 409 | 회사 프로필이 이미 존재합니다. |

### 신규 에러 코드 (F-08 추가)

| 코드 | HTTP Status | 메시지 |
|------|-------------|--------|
| COMPANY_005 | 400 | 대표 실적은 최대 5개까지 지정할 수 있습니다. |
| COMPANY_006 | 404 | 수행 실적을 찾을 수 없습니다. |
| COMPANY_007 | 404 | 인증 정보를 찾을 수 없습니다. |
| COMPANY_008 | 404 | 초대 대상 사용자를 찾을 수 없습니다. |
| COMPANY_009 | 409 | 이미 해당 회사의 멤버입니다. |
| COMPANY_010 | 409 | 대상 사용자가 이미 다른 회사에 소속되어 있습니다. |

### 기존 공통 에러 코드 (재사용)

| 코드 | HTTP Status | 메시지 |
|------|-------------|--------|
| PERMISSION_001 | 403 | 접근 권한이 없습니다. |
| PERMISSION_003 | 403 | 팀원 초대 권한이 없습니다. |
| VALIDATION_001 | 400 | 입력값이 유효하지 않습니다. |
| AUTH_002 | 401 | 인증 토큰이 필요합니다. |

---

## 변경 이력

| 날짜 | 변경 내용 | 이유 |
|------|----------|------|
| 2026-03-02 | 초기 변경 설계 | F-08 기능 구현 시작 |
