# F-08 회사 프로필 관리 — 테스트 명세

## 참조
- 설계서: docs/specs/F-08-company-profile/design.md
- 인수조건: docs/project/features.md #F-08
- ERD: docs/system/erd.md
- API 컨벤션: docs/system/api-conventions.md

---

## 1. 단위 테스트

### 1.1 사업자등록번호 검증 (utils/validators.py)

| ID | 대상 | 시나리오 | 입력 | 예상 결과 |
|----|------|----------|------|-----------|
| UT-01 | validate_business_number | 유효한 사업자등록번호 | "1234567890" (유효 체크섬) | True |
| UT-02 | validate_business_number | 10자리 미만 | "12345678" | ValidationError(COMPANY_003) |
| UT-03 | validate_business_number | 10자리 초과 | "12345678901" | ValidationError(COMPANY_003) |
| UT-04 | validate_business_number | 숫자가 아닌 문자 포함 | "123456789a" | ValidationError(COMPANY_003) |
| UT-05 | validate_business_number | 빈 문자열 | "" | ValidationError(COMPANY_003) |
| UT-06 | validate_business_number | 체크섬 불일치 | "1234567891" (잘못된 체크섬) | ValidationError(COMPANY_003) |
| UT-07 | validate_business_number | 모두 0 | "0000000000" | ValidationError(COMPANY_003) |

### 1.2 CompanyService - 회사 등록

| ID | 대상 | 시나리오 | 입력 | 예상 결과 |
|----|------|----------|------|-----------|
| UT-10 | create_company | 정상 등록 | 유효한 회사 정보 + 미소속 사용자 | Company 생성, CompanyMember(owner) 생성, users.company_id 갱신 |
| UT-11 | create_company | 중복 사업자등록번호 | 이미 등록된 business_number | AppException(COMPANY_002, 409) |
| UT-12 | create_company | 이미 소속된 사용자 | company_id가 NOT NULL인 사용자 | AppException(COMPANY_004, 409) |
| UT-13 | create_company | 잘못된 사업자등록번호 | 체크섬 불일치 번호 | AppException(COMPANY_003, 400) |
| UT-14 | create_company | scale enum 검증 | scale="invalid" | ValidationError |
| UT-15 | create_company | 필수 필드 누락 (name) | name 없음 | ValidationError(VALIDATION_002) |

### 1.3 CompanyService - 회사 조회

| ID | 대상 | 시나리오 | 입력 | 예상 결과 |
|----|------|----------|------|-----------|
| UT-20 | get_my_company | 소속 회사 존재 | company_id가 있는 사용자 | Company 정보 + 집계(memberCount, performanceCount, certificationCount) |
| UT-21 | get_my_company | 소속 회사 없음 | company_id가 NULL인 사용자 | AppException(COMPANY_001, 404) |
| UT-22 | get_my_company | 삭제된 회사 | deleted_at이 NOT NULL인 회사 | AppException(COMPANY_001, 404) |

### 1.4 CompanyService - 회사 수정

| ID | 대상 | 시나리오 | 입력 | 예상 결과 |
|----|------|----------|------|-----------|
| UT-30 | update_company | 정상 수정 (owner) | owner + 유효한 수정 데이터 | Company 갱신, updatedAt 갱신 |
| UT-31 | update_company | 정상 수정 (admin) | admin + 유효한 수정 데이터 | Company 갱신 |
| UT-32 | update_company | 권한 없음 (member) | member 역할 사용자 | AppException(PERMISSION_001, 403) |
| UT-33 | update_company | businessNumber 수정 시도 | 요청에 businessNumber 포함 | businessNumber 무시 (변경 안 됨) |
| UT-34 | update_company | 존재하지 않는 회사 | 잘못된 company_id | AppException(COMPANY_001, 404) |

### 1.5 CompanyService - 수행 실적

| ID | 대상 | 시나리오 | 입력 | 예상 결과 |
|----|------|----------|------|-----------|
| UT-40 | create_performance | 정상 등록 | 유효한 실적 데이터 + 멤버 사용자 | Performance 생성 |
| UT-41 | create_performance | 대표 실적으로 등록 | isRepresentative=true, 기존 대표 3개 | Performance 생성 (is_representative=true) |
| UT-42 | create_performance | 대표 실적 초과 | isRepresentative=true, 기존 대표 5개 | AppException(COMPANY_005, 400) |
| UT-43 | create_performance | 비멤버 등록 시도 | 해당 회사 멤버가 아닌 사용자 | AppException(PERMISSION_001, 403) |
| UT-44 | create_performance | end_date < start_date | startDate: 2025-12-31, endDate: 2025-01-01 | ValidationError |
| UT-45 | create_performance | 계약 금액 0 이하 | contractAmount: -100 | ValidationError |
| UT-46 | update_performance | 정상 수정 (owner) | owner + 유효 데이터 | Performance 갱신 |
| UT-47 | update_performance | 권한 없음 (member) | member 역할 사용자 | AppException(PERMISSION_001, 403) |
| UT-48 | update_performance | 존재하지 않는 실적 | 잘못된 perfId | AppException(COMPANY_006, 404) |
| UT-49 | update_performance | 삭제된 실적 수정 | deleted_at NOT NULL인 실적 | AppException(COMPANY_006, 404) |
| UT-50 | delete_performance | 정상 삭제 | owner + 존재하는 실적 | deleted_at 갱신 (Soft Delete) |
| UT-51 | delete_performance | 대표 실적 삭제 | is_representative=true인 실적 | 삭제 성공, is_representative 해제 |
| UT-52 | set_representative | 대표 지정 | isRepresentative=true, 기존 대표 4개 | is_representative=true 갱신 |
| UT-53 | set_representative | 대표 해제 | isRepresentative=false | is_representative=false 갱신 |
| UT-54 | set_representative | 대표 초과 | isRepresentative=true, 기존 대표 5개 | AppException(COMPANY_005, 400) |

### 1.6 CompanyService - 보유 인증

| ID | 대상 | 시나리오 | 입력 | 예상 결과 |
|----|------|----------|------|-----------|
| UT-60 | create_certification | 정상 등록 | 유효한 인증 데이터 + 멤버 사용자 | Certification 생성 |
| UT-61 | create_certification | 비멤버 등록 시도 | 해당 회사 멤버 아님 | AppException(PERMISSION_001, 403) |
| UT-62 | create_certification | expiryDate < issuedDate | issuedDate: 2027, expiryDate: 2024 | ValidationError |
| UT-63 | update_certification | 정상 수정 | owner + 유효 데이터 | Certification 갱신 |
| UT-64 | update_certification | 권한 없음 (member) | member 역할 사용자 | AppException(PERMISSION_001, 403) |
| UT-65 | update_certification | 존재하지 않는 인증 | 잘못된 certId | AppException(COMPANY_007, 404) |
| UT-66 | delete_certification | 정상 삭제 | owner + 존재하는 인증 | deleted_at 갱신 |

### 1.7 CompanyService - 멤버 관리

| ID | 대상 | 시나리오 | 입력 | 예상 결과 |
|----|------|----------|------|-----------|
| UT-70 | invite_member | 정상 초대 (owner) | owner + 미소속 대상 이메일 | CompanyMember 생성, users.company_id 갱신 |
| UT-71 | invite_member | 정상 초대 (admin) | admin + 미소속 대상 이메일 | CompanyMember 생성 |
| UT-72 | invite_member | 권한 없음 (member) | member 역할 사용자 | AppException(PERMISSION_003, 403) |
| UT-73 | invite_member | 존재하지 않는 이메일 | 미등록 이메일 | AppException(COMPANY_008, 404) |
| UT-74 | invite_member | 이미 멤버인 사용자 | 해당 회사 기존 멤버 이메일 | AppException(COMPANY_009, 409) |
| UT-75 | invite_member | 다른 회사 소속 사용자 | 다른 회사 멤버 이메일 | AppException(COMPANY_010, 409) |
| UT-76 | invite_member | owner 역할 지정 시도 | role="owner" | ValidationError (admin, member만 가능) |

### 1.8 CompanyService - 권한 검증 유틸리티

| ID | 대상 | 시나리오 | 입력 | 예상 결과 |
|----|------|----------|------|-----------|
| UT-80 | verify_company_membership | 멤버인 경우 | 유효한 (company_id, user_id) | CompanyMember 반환 |
| UT-81 | verify_company_membership | 비멤버인 경우 | 매칭 안 되는 (company_id, user_id) | AppException(PERMISSION_001, 403) |
| UT-82 | verify_company_membership | 역할 제한 (owner만) | member 역할 + required_roles=["owner"] | AppException(PERMISSION_001, 403) |
| UT-83 | verify_company_membership | 역할 제한 통과 | owner 역할 + required_roles=["owner", "admin"] | CompanyMember 반환 |

---

## 2. 통합 테스트

### 2.1 회사 등록 API

| ID | API | 시나리오 | 입력 | 예상 결과 |
|----|-----|----------|------|-----------|
| IT-01 | POST /api/v1/companies | 정상 회사 등록 | 유효 데이터 + 인증 토큰 | 201, company 생성, company_members owner 추가, users.company_id 갱신 |
| IT-02 | POST /api/v1/companies | 미인증 요청 | 토큰 없음 | 401, AUTH_002 |
| IT-03 | POST /api/v1/companies | 중복 사업자등록번호 | 이미 등록된 번호 | 409, COMPANY_002 |
| IT-04 | POST /api/v1/companies | 잘못된 사업자등록번호 형식 | "1234" | 400, COMPANY_003 |
| IT-05 | POST /api/v1/companies | 이미 소속된 사용자 | company_id NOT NULL | 409, COMPANY_004 |
| IT-06 | POST /api/v1/companies | 필수 필드 누락 | businessNumber 없음 | 400, VALIDATION_001 |

### 2.2 내 회사 조회 API

| ID | API | 시나리오 | 입력 | 예상 결과 |
|----|-----|----------|------|-----------|
| IT-10 | GET /api/v1/companies/my | 소속 회사 조회 | 회사 소속 사용자 | 200, 회사 정보 + 집계 |
| IT-11 | GET /api/v1/companies/my | 미소속 사용자 | company_id NULL | 404, COMPANY_001 |
| IT-12 | GET /api/v1/companies/my | 미인증 요청 | 토큰 없음 | 401, AUTH_002 |

### 2.3 회사 수정 API

| ID | API | 시나리오 | 입력 | 예상 결과 |
|----|-----|----------|------|-----------|
| IT-20 | PUT /api/v1/companies/{id} | owner가 수정 | owner 토큰 + 유효 데이터 | 200, 수정된 데이터 |
| IT-21 | PUT /api/v1/companies/{id} | admin이 수정 | admin 토큰 + 유효 데이터 | 200 |
| IT-22 | PUT /api/v1/companies/{id} | member가 수정 | member 토큰 | 403, PERMISSION_001 |
| IT-23 | PUT /api/v1/companies/{id} | 다른 회사 수정 시도 | 다른 회사 ID | 403, PERMISSION_001 |
| IT-24 | PUT /api/v1/companies/{id} | 존재하지 않는 회사 | 잘못된 UUID | 404, COMPANY_001 |

### 2.4 수행 실적 API

| ID | API | 시나리오 | 입력 | 예상 결과 |
|----|-----|----------|------|-----------|
| IT-30 | POST /companies/{id}/performances | 정상 실적 등록 | member 토큰 + 유효 데이터 | 201, Performance 생성 |
| IT-31 | POST /companies/{id}/performances | 대표 실적으로 등록 | isRepresentative=true | 201, is_representative=true |
| IT-32 | POST /companies/{id}/performances | 대표 실적 초과 | 이미 5개 대표 + isRepresentative=true | 400, COMPANY_005 |
| IT-33 | POST /companies/{id}/performances | 비멤버 | 다른 회사 멤버 토큰 | 403, PERMISSION_001 |
| IT-34 | GET /companies/{id}/performances | 목록 조회 | page=1, pageSize=10 | 200, items + meta |
| IT-35 | GET /companies/{id}/performances | 대표 실적 필터 | isRepresentative=true | 200, 대표 실적만 반환 |
| IT-36 | GET /companies/{id}/performances | 상태 필터 | status=completed | 200, 완료 실적만 반환 |
| IT-37 | GET /companies/{id}/performances | 정렬 | sortBy=contractAmount&sortOrder=desc | 200, 금액 내림차순 |
| IT-38 | PUT /companies/{id}/performances/{perfId} | owner가 수정 | owner 토큰 + 유효 데이터 | 200 |
| IT-39 | PUT /companies/{id}/performances/{perfId} | member가 수정 | member 토큰 | 403, PERMISSION_001 |
| IT-40 | DELETE /companies/{id}/performances/{perfId} | 정상 삭제 | owner 토큰 | 200, data: null |
| IT-41 | DELETE /companies/{id}/performances/{perfId} | 존재하지 않는 실적 | 잘못된 perfId | 404, COMPANY_006 |
| IT-42 | PATCH /companies/{id}/performances/{perfId}/representative | 대표 지정 | isRepresentative=true | 200 |
| IT-43 | PATCH /companies/{id}/performances/{perfId}/representative | 대표 해제 | isRepresentative=false | 200 |

### 2.5 보유 인증 API

| ID | API | 시나리오 | 입력 | 예상 결과 |
|----|-----|----------|------|-----------|
| IT-50 | POST /companies/{id}/certifications | 정상 인증 등록 | member 토큰 + 유효 데이터 | 201, Certification 생성 |
| IT-51 | POST /companies/{id}/certifications | 비멤버 | 다른 회사 멤버 토큰 | 403, PERMISSION_001 |
| IT-52 | GET /companies/{id}/certifications | 목록 조회 | page=1 | 200, items + meta |
| IT-53 | GET /companies/{id}/certifications | 정렬 | sortBy=expiryDate&sortOrder=asc | 200, 만료일 오름차순 |
| IT-54 | PUT /companies/{id}/certifications/{certId} | owner가 수정 | owner 토큰 + 유효 데이터 | 200 |
| IT-55 | PUT /companies/{id}/certifications/{certId} | member가 수정 | member 토큰 | 403, PERMISSION_001 |
| IT-56 | DELETE /companies/{id}/certifications/{certId} | 정상 삭제 | owner 토큰 | 200, data: null |
| IT-57 | DELETE /companies/{id}/certifications/{certId} | 존재하지 않는 인증 | 잘못된 certId | 404, COMPANY_007 |

### 2.6 멤버 관리 API

| ID | API | 시나리오 | 입력 | 예상 결과 |
|----|-----|----------|------|-----------|
| IT-60 | POST /companies/{id}/members | owner가 멤버 초대 | owner 토큰 + 유효 이메일 | 201, CompanyMember 생성 |
| IT-61 | POST /companies/{id}/members | admin이 멤버 초대 | admin 토큰 + 유효 이메일 | 201 |
| IT-62 | POST /companies/{id}/members | member가 초대 시도 | member 토큰 | 403, PERMISSION_003 |
| IT-63 | POST /companies/{id}/members | 존재하지 않는 이메일 | 미등록 이메일 | 404, COMPANY_008 |
| IT-64 | POST /companies/{id}/members | 이미 멤버인 사용자 | 기존 멤버 이메일 | 409, COMPANY_009 |
| IT-65 | POST /companies/{id}/members | 다른 회사 소속 사용자 | 다른 회사 멤버 이메일 | 409, COMPANY_010 |
| IT-66 | GET /companies/{id}/members | 멤버 목록 조회 | member 토큰 | 200, items + meta |
| IT-67 | GET /companies/{id}/members | 비멤버 조회 | 다른 회사 멤버 토큰 | 403, PERMISSION_001 |

---

## 3. E2E 테스트 시나리오

### 3.1 회사 프로필 전체 흐름

| ID | 시나리오 | 단계 | 검증 사항 |
|----|----------|------|-----------|
| E2E-01 | 회사 등록 ~ 프로필 조회 | 1) 회원가입 2) 로그인 3) POST /companies 4) GET /companies/my | 회사 생성됨, 사용자 company_id 갱신, memberCount=1 |
| E2E-02 | 실적 등록 ~ 대표 지정 | 1) 회사 등록 2) POST /performances (3건) 3) PATCH representative (2건) 4) GET performances?isRepresentative=true | 2건 대표 실적 조회, is_representative=true |
| E2E-03 | 인증 등록 ~ 조회 | 1) 회사 등록 2) POST /certifications (2건) 3) GET /certifications | 2건 인증 조회 |
| E2E-04 | 멤버 초대 ~ 목록 | 1) 사용자A 회사 등록 2) 사용자B 회원가입 3) POST /members (사용자B 초대) 4) GET /members | memberCount=2, 사용자B의 company_id 갱신 |

### 3.2 권한 검증 흐름

| ID | 시나리오 | 단계 | 검증 사항 |
|----|----------|------|-----------|
| E2E-10 | member 권한 제한 | 1) 사용자A 회사 등록 (owner) 2) 사용자B 초대 (member) 3) 사용자B로 PUT /companies/{id} | 403, member는 회사 수정 불가 |
| E2E-11 | member 등록 가능 | 1) owner 회사 등록 2) member 초대 3) member로 POST /performances 4) member로 POST /certifications | 200, member는 실적/인증 등록 가능 |
| E2E-12 | 타회사 접근 차단 | 1) 사용자A 회사A 등록 2) 사용자B 회사B 등록 3) 사용자A로 GET /companies/{회사B ID}/performances | 403, 타회사 리소스 접근 차단 |

### 3.3 데이터 무결성 흐름

| ID | 시나리오 | 단계 | 검증 사항 |
|----|----------|------|-----------|
| E2E-20 | Soft Delete 동작 | 1) 실적 등록 2) DELETE /performances/{id} 3) GET /performances | 삭제된 실적 목록에 미노출, DB에 deleted_at 존재 |
| E2E-21 | 대표 실적 제한 | 1) 실적 6건 등록 2) 5건 대표 지정 (성공) 3) 6번째 대표 지정 (실패) | 400, COMPANY_005 |

---

## 4. 경계 조건 / 에러 케이스

### 4.1 입력값 경계

- 회사명 200자 최대 입력 (성공)
- 회사명 201자 입력 (실패, VALIDATION_003)
- 사업자등록번호 "0000000000" (실패, COMPANY_003)
- 계약 금액 0원 (실패, 양수만 허용)
- 계약 금액 999999999999999원 (DECIMAL(15,0) 최대값, 성공)
- 빈 description (성공, nullable)
- 매우 긴 description (TEXT 타입이므로 성공)

### 4.2 날짜 경계

- startDate == endDate (성공)
- startDate > endDate (실패, ValidationError)
- issuedDate만 존재, expiryDate NULL (성공)
- expiryDate만 존재, issuedDate NULL (성공)
- 과거 만료일의 인증 등록 (성공, isExpired=true로 표시)

### 4.3 동시성 / 충돌

- 동시에 같은 사업자등록번호로 회사 등록 시도 (하나 성공, 하나 409)
- 동시에 같은 실적을 대표로 지정 (멱등 동작)
- 5개 대표 실적 상태에서 동시에 2개 추가 대표 지정 (하나 성공, 하나 400)

### 4.4 Soft Delete 관련

- 삭제된 회사의 실적/인증 조회 시 404
- 삭제된 실적의 수정 시도 시 404
- 삭제된 인증의 수정 시도 시 404

---

## 5. 회귀 테스트

### 5.1 F-07 인증 기능 영향 검증

| 기존 기능 | 영향 여부 | 검증 방법 |
|-----------|-----------|-----------|
| POST /auth/register | 영향 없음 | 회원가입 정상 동작, company_id=null |
| POST /auth/login | 영향 없음 | 로그인 정상 동작, JWT companyId 포함 |
| GET /auth/me | 영향 없음 | company_id 정상 반환 (null 또는 UUID) |
| POST /auth/refresh | 영향 없음 | 토큰 갱신 정상 동작 |
| POST /auth/logout | 영향 없음 | 로그아웃 정상 동작 |

### 5.2 User 모델 변경 영향

| 변경 사항 | 영향 여부 | 검증 방법 |
|-----------|-----------|-----------|
| user.py에 company relationship 추가 | 낮음 | 기존 User 조회/생성 정상 동작 확인 |
| company_id FK 활성화 | 낮음 | companies 테이블 생성 후 FK 정상 동작, 기존 NULL company_id 유지 |

### 5.3 라우터 변경 영향

| 변경 사항 | 영향 여부 | 검증 방법 |
|-----------|-----------|-----------|
| router.py에 companies 라우터 추가 | 없음 | 기존 /auth, /proposals 라우트 정상 동작 확인 |

---

## 6. 테스트 데이터 요구사항

### 6.1 테스트 픽스처

```python
# 테스트 사용자 (F-07 픽스처 재사용)
test_user_owner = {
    "email": "owner@test.com",
    "password": "TestP@ss123",
    "name": "테스트오너"
}

test_user_admin = {
    "email": "admin@test.com",
    "password": "TestP@ss123",
    "name": "테스트어드민"
}

test_user_member = {
    "email": "member@test.com",
    "password": "TestP@ss123",
    "name": "테스트멤버"
}

# 테스트 회사
test_company = {
    "businessNumber": "1234567890",  # 유효한 체크섬
    "name": "주식회사 테스트",
    "ceoName": "홍길동",
    "address": "서울특별시 강남구",
    "phone": "02-1234-5678",
    "industry": "소프트웨어 개발업",
    "scale": "small",
    "description": "테스트 회사"
}

# 테스트 수행 실적
test_performance = {
    "projectName": "테스트 프로젝트",
    "clientName": "테스트 발주처",
    "clientType": "public",
    "contractAmount": 100000000,
    "startDate": "2024-01-01",
    "endDate": "2024-12-31",
    "status": "completed",
    "description": "테스트 설명",
    "isRepresentative": False
}

# 테스트 보유 인증
test_certification = {
    "name": "GS인증 1등급",
    "issuer": "TTA",
    "certNumber": "GS-2024-0001",
    "issuedDate": "2024-01-01",
    "expiryDate": "2027-01-01"
}
```

### 6.2 테스트 환경 설정

- 테스트 DB: SQLite 인메모리 또는 별도 PostgreSQL 테스트 DB
- 각 테스트 케이스 전 DB 초기화 (트랜잭션 롤백 또는 테이블 초기화)
- 인증 토큰은 테스트 유틸리티로 직접 생성 (실제 로그인 불필요)

---

## 변경 이력

| 날짜 | 변경 내용 | 이유 |
|------|----------|------|
| 2026-03-02 | 초기 테스트 명세 작성 | F-08 기능 구현 시작 |
