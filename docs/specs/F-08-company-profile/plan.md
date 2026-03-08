# F-08 회사 프로필 관리 — 구현 계획서

## 참조
- 설계서: docs/specs/F-08-company-profile/design.md
- 테스트 명세: docs/specs/F-08-company-profile/test-spec.md
- UI 설계서: docs/specs/F-08-company-profile/ui-spec.md
- ERD: docs/system/erd.md
- API 컨벤션: docs/system/api-conventions.md

---

## 태스크 목록

### [BE] 백엔드 태스크

#### T1: DB 모델 및 마이그레이션

- [ ] T1.1: Company 모델 정의 (backend/src/models/company.py)
  - 컬럼: id, business_number, name, ceo_name, address, phone, industry, scale, description, profile_embedding, created_at, updated_at, deleted_at
  - Check Constraint: chk_companies_scale (small, medium, large)
  - Soft Delete 지원 (deleted_at)
  - Relationship: users (back_populates="company"), members, certifications, performances
- [ ] T1.2: CompanyMember 모델 정의 (backend/src/models/company_member.py)
  - 컬럼: id, company_id, user_id, role, invited_at, joined_at, created_at, updated_at
  - Unique Constraint: (company_id, user_id)
  - Check Constraint: chk_company_members_role (owner, admin, member)
  - FK: company_id -> companies.id, user_id -> users.id
- [ ] T1.3: Certification 모델 정의 (backend/src/models/certification.py)
  - 컬럼: id, company_id, name, issuer, cert_number, issued_date, expiry_date, document_url, created_at, updated_at, deleted_at
  - Check Constraint: chk_certifications_expiry (expiry_date >= issued_date)
  - Soft Delete 지원 (deleted_at)
  - FK: company_id -> companies.id
- [ ] T1.4: Performance 모델 정의 (backend/src/models/performance.py)
  - 컬럼: id, company_id, project_name, client_name, client_type, contract_amount, start_date, end_date, status, description, is_representative, document_url, embedding, created_at, updated_at, deleted_at
  - Check Constraints: chk_performances_status, chk_performances_client_type, chk_performances_dates, chk_performances_amount
  - Soft Delete 지원 (deleted_at)
  - FK: company_id -> companies.id
- [ ] T1.5: Alembic 마이그레이션 생성 (backend/alembic/versions/002_create_company_tables.py)
  - companies 테이블 먼저 생성 (users.company_id FK 의존)
  - company_members, certifications, performances 테이블 생성
  - 인덱스: idx_companies_business_number, idx_company_members_unique, idx_company_members_user, idx_performances_company, idx_performances_representative, idx_certifications_company
  - users.company_id FK 제약조건 활성화 (companies 테이블 생성 후)
- [ ] T1.6: models/__init__.py 업데이트
  - Company, CompanyMember, Certification, Performance 모델 import 추가

#### T2: 스키마 정의

- [ ] T2.1: 회사 요청/응답 스키마 (backend/src/schemas/company.py)
  - CompanyCreateRequest: businessNumber, name, ceoName, address, phone, industry, scale, description
  - CompanyUpdateRequest: name, ceoName, address, phone, industry, scale, description (businessNumber 제외)
  - CompanyResponse: id, businessNumber, name, ceoName, address, phone, industry, scale, description, createdAt, updatedAt
  - CompanyDetailResponse: CompanyResponse + memberCount, performanceCount, certificationCount
- [ ] T2.2: 수행 실적 요청/응답 스키마 (backend/src/schemas/performance.py)
  - PerformanceCreateRequest: projectName, clientName, clientType, contractAmount, startDate, endDate, status, description, isRepresentative, documentUrl
  - PerformanceUpdateRequest: 동일 구조
  - PerformanceResponse: id, companyId, projectName, clientName, clientType, contractAmount, startDate, endDate, status, description, isRepresentative, documentUrl, createdAt, updatedAt
  - PerformanceListResponse: items, meta (page, pageSize, total, totalPages)
  - RepresentativeUpdateRequest: isRepresentative
- [ ] T2.3: 보유 인증 요청/응답 스키마 (backend/src/schemas/certification.py)
  - CertificationCreateRequest: name, issuer, certNumber, issuedDate, expiryDate, documentUrl
  - CertificationUpdateRequest: 동일 구조
  - CertificationResponse: id, companyId, name, issuer, certNumber, issuedDate, expiryDate, documentUrl, isExpired, createdAt, updatedAt
  - CertificationListResponse: items, meta
- [ ] T2.4: 멤버 요청/응답 스키마 (backend/src/schemas/member.py)
  - MemberInviteRequest: email, role (admin, member only)
  - MemberResponse: id, companyId, userId, email, name, role, invitedAt, joinedAt
  - MemberListResponse: items, meta

#### T3: 서비스 레이어

- [ ] T3.1: CompanyService (backend/src/services/company_service.py)
  - create_company(user_id, data) — 사업자등록번호 형식/체크섬 검증, 중복 확인, 기존 소속 확인, companies 생성, company_members(owner) 생성, users.company_id 갱신
  - get_my_company(user_id) — company_id 조회, deleted_at IS NULL 필터, 집계(memberCount, performanceCount, certificationCount)
  - update_company(company_id, user_id, data) — owner/admin 권한 확인, businessNumber 수정 불가, 기본 정보 갱신
- [ ] T3.2: PerformanceService (backend/src/services/performance_service.py)
  - create_performance(company_id, user_id, data) — 멤버 권한 확인, isRepresentative=true 시 대표 실적 수 확인(최대 5개), 실적 생성
  - list_performances(company_id, user_id, filters, pagination) — 멤버 권한 확인, status/isRepresentative 필터, 정렬, 페이지네이션
  - update_performance(company_id, perf_id, user_id, data) — owner/admin 권한 확인, 실적 존재/소프트딜리트 확인, 갱신
  - delete_performance(company_id, perf_id, user_id) — owner/admin 권한 확인, Soft Delete (deleted_at 갱신)
  - set_representative(company_id, perf_id, user_id, is_representative) — owner/admin 권한 확인, 대표 실적 수 제한 확인, is_representative 갱신
- [ ] T3.3: CertificationService (backend/src/services/certification_service.py)
  - create_certification(company_id, user_id, data) — 멤버 권한 확인, 인증 생성
  - list_certifications(company_id, user_id, pagination) — 멤버 권한 확인, 정렬, 페이지네이션, isExpired 계산
  - update_certification(company_id, cert_id, user_id, data) — owner/admin 권한 확인, 인증 존재 확인, 갱신
  - delete_certification(company_id, cert_id, user_id) — owner/admin 권한 확인, Soft Delete
- [ ] T3.4: CompanyMemberService (backend/src/services/company_member_service.py)
  - invite_member(company_id, inviter_id, email, role) — owner/admin 권한 확인, 대상 사용자 이메일 조회, 기존 소속/멤버 여부 확인, company_members 생성, users.company_id 갱신(MVP 즉시 가입)
  - list_members(company_id, user_id, pagination) — 멤버 권한 확인, 멤버 목록 반환

#### T4: API 엔드포인트 (backend/src/api/v1/companies.py)

- [ ] T4.1: POST /api/v1/companies — 회사 등록 (201 Created)
- [ ] T4.2: GET /api/v1/companies/my — 내 회사 조회 (200 OK)
- [ ] T4.3: PUT /api/v1/companies/{id} — 회사 정보 수정 (200 OK)
- [ ] T4.4: POST /api/v1/companies/{id}/performances — 수행 실적 등록 (201 Created)
- [ ] T4.5: GET /api/v1/companies/{id}/performances — 수행 실적 목록 조회 (200 OK)
  - Query: page, pageSize, status, isRepresentative, sortBy, sortOrder
- [ ] T4.6: PUT /api/v1/companies/{id}/performances/{perfId} — 수행 실적 수정 (200 OK)
- [ ] T4.7: DELETE /api/v1/companies/{id}/performances/{perfId} — 수행 실적 삭제 (200 OK)
- [ ] T4.8: PATCH /api/v1/companies/{id}/performances/{perfId}/representative — 대표 실적 지정/해제 (200 OK)
- [ ] T4.9: POST /api/v1/companies/{id}/certifications — 보유 인증 등록 (201 Created)
- [ ] T4.10: GET /api/v1/companies/{id}/certifications — 보유 인증 목록 조회 (200 OK)
  - Query: page, pageSize, sortBy, sortOrder
- [ ] T4.11: PUT /api/v1/companies/{id}/certifications/{certId} — 보유 인증 수정 (200 OK)
- [ ] T4.12: DELETE /api/v1/companies/{id}/certifications/{certId} — 보유 인증 삭제 (200 OK)
- [ ] T4.13: POST /api/v1/companies/{id}/members — 멤버 초대 (201 Created)
- [ ] T4.14: GET /api/v1/companies/{id}/members — 멤버 목록 조회 (200 OK)
  - Query: page, pageSize

#### T5: 권한 미들웨어

- [ ] T5.1: 회사 소속 확인 의존성 (backend/src/api/deps.py 확장)
  - get_company_member(company_id, current_user) — company_members에서 (company_id, user_id) 조회, 미소속 시 PERMISSION_001(403)
- [ ] T5.2: 역할 기반 접근 제어 팩토리 (backend/src/api/deps.py 확장)
  - require_role(required_roles: list[str]) — 현재 사용자 역할 확인, 미충족 시 PERMISSION_001(403)
  - owner/admin 전용 엔드포인트에 Depends(require_role(["owner", "admin"])) 적용

#### T6: 기존 파일 수정 + 검증 유틸리티

- [ ] T6.1: User 모델 수정 (backend/src/models/user.py)
  - company = relationship("Company", back_populates="users") 추가
- [ ] T6.2: API 라우터 등록 (backend/src/api/v1/router.py)
  - companies.router include 추가
- [ ] T6.3: 사업자등록번호 검증 유틸리티 (backend/src/utils/validators.py)
  - validate_business_number(number: str) -> bool — 10자리 숫자 형식, 체크섬 알고리즘 (가중치 [1,3,7,1,3,7,1,3,5]) 구현

---

### [FE] 프론트엔드 태스크

#### T7: API 클라이언트

- [ ] T7.1: company API 클라이언트 (frontend/src/lib/api/company-api.ts)
  - createCompany(data: CompanyCreateRequest)
  - getMyCompany()
  - updateCompany(id, data: CompanyUpdateRequest)
  - createPerformance(companyId, data: PerformanceCreateRequest)
  - listPerformances(companyId, params)
  - updatePerformance(companyId, perfId, data)
  - deletePerformance(companyId, perfId)
  - setRepresentative(companyId, perfId, isRepresentative)
  - createCertification(companyId, data: CertificationCreateRequest)
  - listCertifications(companyId, params)
  - updateCertification(companyId, certId, data)
  - deleteCertification(companyId, certId)
  - inviteMember(companyId, data: MemberInviteRequest)
  - listMembers(companyId, params)

#### T8: 상태 관리

- [ ] T8.1: company store (frontend/src/stores/company-store.ts)
  - State: company, isLoading, currentUserRole
  - Actions: fetchMyCompany, createCompany, updateCompany
- [ ] T8.2: performance store (frontend/src/stores/performance-store.ts)
  - State: performances, isLoading, isSlideOverOpen, editingPerformance, deletingPerformanceId, representativeCount, filterStatus
  - Actions: fetchPerformances, createPerformance, updatePerformance, deletePerformance, setRepresentative
- [ ] T8.3: certification store (frontend/src/stores/certification-store.ts)
  - State: certifications, isLoading, isModalOpen, editingCert, deletingCertId
  - Actions: fetchCertifications, createCertification, updateCertification, deleteCertification
- [ ] T8.4: member store (frontend/src/stores/member-store.ts)
  - State: members, isLoading, isInviteModalOpen, removingMemberId, isInviting
  - Actions: fetchMembers, inviteMember

#### T9: 회사 프로필 페이지

- [ ] T9.1: 설정 > 회사 프로필 페이지 레이아웃 (frontend/src/app/(dashboard)/settings/company/page.tsx)
  - SettingsLayout 적용 (사이드바 + 메인 영역)
  - Breadcrumb (대시보드 > 설정 > 회사 프로필)
  - PageHeader (제목 + 설명)
  - TabNavigation (기본 정보 | 수행 실적 | 보유 인증 | 멤버 관리)
  - URL hash 기반 탭 전환 (#basic, #performance, #certification, #member)
  - 페이지 진입 시 GET /api/v1/companies/my 호출
- [ ] T9.2: 기본 정보 탭 (frontend/src/components/company/CompanyBasicInfoTab.tsx)
  - 미등록 상태: EmptyRegistrationState + CompanyRegistrationForm
  - 등록 완료 상태: RegisteredCompanyView (CompanyInfoCard + 수정 버튼)
  - 수정 모드: CompanyEditForm (inline 전환, 사업자등록번호 disabled)
  - 로딩 상태: 스켈레톤 UI (animate-pulse)
- [ ] T9.3: 수행 실적 탭 (frontend/src/components/company/PerformanceTab.tsx)
  - TabToolbar (실적 등록 버튼 + 상태 필터 컨트롤)
  - EmptyState (빈 상태 안내 + CTA)
  - PerformanceCardList (카드 2열 그리드, 모바일 1열)
  - PerformanceSlideOver (등록/수정 패널, 오른쪽 슬라이드인)
  - DeleteConfirmModal (삭제 확인)
- [ ] T9.4: 보유 인증 탭 (frontend/src/components/company/CertificationTab.tsx)
  - TabToolbar (인증 등록 버튼)
  - EmptyState (빈 상태 안내 + CTA)
  - CertificationTable (데스크톱 테이블, 모바일 카드형)
  - CertificationModal (등록/수정, max-width 560px)
  - DeleteConfirmModal (삭제 확인)
  - 만료 임박/만료됨 배지 표시 (30일 기준)
- [ ] T9.5: 멤버 관리 탭 (frontend/src/components/company/MemberTab.tsx)
  - TabToolbar (팀원 초대 버튼, owner/admin만 노출)
  - MemberTable (역할 배지, 권한별 액션 버튼)
  - InviteMemberModal (이메일 + 역할 선택)
  - RemoveMemberConfirmModal (제거 확인)
  - PermissionNotice (member 역할 시 읽기 전용 안내 배너)

#### T10: 공통 컴포넌트

- [ ] T10.1: 슬라이드오버 패널 (frontend/src/components/ui/SlideOverPanel.tsx)
  - 오른쪽 슬라이드인 애니메이션 (transform translateX, 300ms ease)
  - 배경 dimmed 오버레이
  - ESC 키 닫기 지원
  - 변경사항 있을 때 닫기 확인 다이얼로그
  - 모바일 전체 너비, 태블릿 480px, 데스크톱 520px
- [ ] T10.2: 사업자등록번호 입력 (frontend/src/components/ui/BusinessNumberInput.tsx)
  - 숫자 이외 입력 무시
  - 10자리 입력 시 000-00-00000 형식 디스플레이 (저장값은 숫자만)
  - 인라인 에러 메시지 표시 (COMPANY_002, COMPANY_003)
- [ ] T10.3: 금액 입력 (frontend/src/components/ui/AmountInput.tsx)
  - blur 시 천 단위 콤마 포맷 적용
  - 양수 값만 허용
- [ ] T10.4: 역할 배지 (frontend/src/components/ui/RoleBadge.tsx)
  - owner / admin / member 배지 스타일 분기
- [ ] T10.5: 대표 실적 배지 (frontend/src/components/ui/RepresentativeBadge.tsx)
  - 별 아이콘 + "대표 실적" 텍스트 (accent-500 색상)

#### T11: 네비게이션 업데이트

- [ ] T11.1: 사이드바에 "설정 > 회사 프로필" 진입점 확인 (frontend/src/components/layout/Sidebar.tsx)
  - /settings/company 경로 링크 확인 및 추가
- [ ] T11.2: 회원가입 후 회사 프로필 등록 가이드 (frontend/src/components/company/CompanyOnboardingBanner.tsx)
  - 대시보드 진입 시 company_id가 null이면 등록 안내 배너 노출
  - "/settings/company로 이동" CTA 버튼 포함

---

### [TEST] 테스트 태스크

#### T12: 백엔드 단위 테스트

- [ ] T12.1: 사업자등록번호 검증 테스트 (backend/tests/unit/test_validators.py)
  - UT-01~UT-07 (유효한 번호, 10자리 미만/초과, 숫자 아닌 문자, 빈 문자열, 체크섬 불일치, 모두 0)
- [ ] T12.2: CompanyService 단위 테스트 (backend/tests/unit/test_company_service.py)
  - UT-10~UT-15 (회사 등록), UT-20~UT-22 (회사 조회), UT-30~UT-34 (회사 수정)
- [ ] T12.3: PerformanceService 단위 테스트 (backend/tests/unit/test_performance_service.py)
  - UT-40~UT-54 (실적 등록, 수정, 삭제, 대표 지정/해제)
- [ ] T12.4: CertificationService 단위 테스트 (backend/tests/unit/test_certification_service.py)
  - UT-60~UT-66 (인증 등록, 수정, 삭제)
- [ ] T12.5: CompanyMemberService 단위 테스트 (backend/tests/unit/test_member_service.py)
  - UT-70~UT-76 (멤버 초대 권한, 중복, 다른 회사 소속)
- [ ] T12.6: 권한 검증 유틸리티 테스트 (backend/tests/unit/test_deps.py)
  - UT-80~UT-83 (멤버 확인, 비멤버, 역할 제한)

#### T13: 백엔드 통합 테스트

- [ ] T13.1: 회사 등록 API 테스트 (backend/tests/integration/test_company_api.py)
  - IT-01~IT-06 (정상 등록, 미인증, 중복, 형식 오류, 이미 소속, 필수 필드 누락)
- [ ] T13.2: 내 회사 조회/수정 API 테스트
  - IT-10~IT-12 (조회), IT-20~IT-24 (수정, 권한)
- [ ] T13.3: 수행 실적 API 테스트
  - IT-30~IT-43 (등록, 목록, 필터, 정렬, 수정, 삭제, 대표 지정)
- [ ] T13.4: 보유 인증 API 테스트
  - IT-50~IT-57 (등록, 목록, 정렬, 수정, 삭제)
- [ ] T13.5: 멤버 관리 API 테스트
  - IT-60~IT-67 (초대, 목록, 권한, 중복, 다른 회사 소속)

#### T14: E2E 테스트

- [ ] T14.1: 회사 등록 ~ 프로필 조회 플로우 (E2E-01)
- [ ] T14.2: 실적 등록 ~ 대표 지정 플로우 (E2E-02)
- [ ] T14.3: 인증 등록 ~ 조회 플로우 (E2E-03)
- [ ] T14.4: 멤버 초대 ~ 목록 플로우 (E2E-04)
- [ ] T14.5: 권한 검증 흐름 (E2E-10~E2E-12)
- [ ] T14.6: Soft Delete 및 대표 실적 제한 (E2E-20~E2E-21)

#### T15: 회귀 테스트

- [ ] T15.1: F-07 인증 기능 영향 검증
  - POST /auth/register, POST /auth/login, GET /auth/me, POST /auth/refresh, POST /auth/logout 정상 동작 확인
- [ ] T15.2: User 모델 변경 영향 검증
  - company relationship 추가 후 기존 User 조회/생성 정상 동작 확인

---

## 태스크 의존성

```
BE: T1 ──▶ T2 ──▶ T3 ──▶ T4 ──▶ T5 ──▶ T6
FE: T7 ──▶ T8 ──▶ T9 ──▶ T10 ──▶ T11
TEST: (BE 완료) T12 ──▶ T13 ──▶ T15
      (FE 완료) T14
```

---

## 병렬 실행 판단

- Agent Team 권장: Yes
- 근거: API 계약이 design.md에 명확히 정의되어 있어 BE와 FE를 독립적으로 진행 가능. FE는 MSW(Mock Service Worker) 또는 mock 데이터로 개발하고, BE 완료 후 실제 API로 교체.

### BE 내부 순서
1. T1 (DB 모델 + 마이그레이션) → T2 (스키마) → T3 (서비스) → T4 (API 엔드포인트) → T5 (권한 미들웨어) → T6 (기존 파일 수정 + 검증 유틸리티)
2. T6.3 (validators.py)은 T3과 병렬 시작 가능

### FE 내부 순서
1. T7 (API 클라이언트) → T8 (상태 관리) → T9 (페이지) → T10 (공통 컴포넌트) → T11 (네비게이션)
2. T10은 T9와 병렬 가능

---

## 의존성

### 외부 의존성
- 없음 (국세청 API 실시간 검증: MVP에서 형식/체크섬 검증으로 대체, 임베딩 생성: nullable 스텁, 파일 업로드: URL 문자열만 저장)

### 환경 변수
- 추가 필요 없음 (F-07 환경 변수 그대로 사용)

---

## 파일 생성 목록

### Backend 신규 파일

```
backend/
├── src/
│   ├── models/
│   │   ├── company.py
│   │   ├── company_member.py
│   │   ├── certification.py
│   │   └── performance.py
│   ├── schemas/
│   │   ├── company.py
│   │   ├── performance.py
│   │   ├── certification.py
│   │   └── member.py
│   ├── services/
│   │   ├── company_service.py
│   │   ├── performance_service.py
│   │   ├── certification_service.py
│   │   └── company_member_service.py
│   ├── api/
│   │   └── v1/
│   │       └── companies.py
│   └── utils/
│       └── validators.py
├── alembic/
│   └── versions/
│       └── 002_create_company_tables.py
└── tests/
    ├── unit/
    │   ├── test_validators.py
    │   ├── test_company_service.py
    │   ├── test_performance_service.py
    │   ├── test_certification_service.py
    │   └── test_member_service.py
    └── integration/
        └── test_company_api.py
```

### Backend 수정 파일

```
backend/
└── src/
    ├── models/
    │   ├── user.py             (company relationship 추가)
    │   └── __init__.py         (신규 모델 4개 import 추가)
    └── api/
        └── v1/
            └── router.py       (companies 라우터 등록)
```

### Frontend 신규 파일

```
frontend/
├── src/
│   ├── app/
│   │   └── (dashboard)/
│   │       └── settings/
│   │           └── company/
│   │               └── page.tsx
│   ├── components/
│   │   ├── company/
│   │   │   ├── CompanyBasicInfoTab.tsx
│   │   │   ├── PerformanceTab.tsx
│   │   │   ├── CertificationTab.tsx
│   │   │   ├── MemberTab.tsx
│   │   │   └── CompanyOnboardingBanner.tsx
│   │   └── ui/
│   │       ├── SlideOverPanel.tsx
│   │       ├── BusinessNumberInput.tsx
│   │       ├── AmountInput.tsx
│   │       ├── RoleBadge.tsx
│   │       └── RepresentativeBadge.tsx
│   ├── lib/
│   │   └── api/
│   │       └── company-api.ts
│   └── stores/
│       ├── company-store.ts
│       ├── performance-store.ts
│       ├── certification-store.ts
│       └── member-store.ts
└── tests/
    └── e2e/
        └── company.spec.ts
```

---

## 변경 이력

| 날짜 | 변경 내용 | 이유 |
|------|----------|------|
| 2026-03-02 | 초기 plan.md 작성 | F-08 구현 시작 |
