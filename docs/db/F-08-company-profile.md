# F-08 회사 프로필 관리 DB 스키마 (확정본)

## 개요

F-08 회사 프로필 관리에서 사용하는 테이블 설계입니다.
모든 테이블은 Soft Delete (`deleted_at`) 및 감사 필드 (`created_at`, `updated_at`)를 포함합니다.

---

## 테이블 목록

1. `companies` - 회사 프로필
2. `company_members` - 회사 멤버십
3. `performances` - 수행 실적
4. `certifications` - 보유 인증

---

## 1. companies

회사 프로필 정보를 저장합니다.

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 회사 고유 ID |
| business_number | VARCHAR(10) | NOT NULL, UNIQUE | 사업자등록번호 (10자리 숫자) |
| name | VARCHAR(200) | NOT NULL | 회사명 |
| ceo_name | VARCHAR(100) | NOT NULL | 대표자명 |
| address | TEXT | NULL | 주소 |
| phone | VARCHAR(20) | NULL | 전화번호 |
| industry | VARCHAR(100) | NULL | 업종 |
| scale | VARCHAR(50) | NULL | 기업 규모 (startup/small/medium/large) |
| description | TEXT | NULL | 회사 소개 |
| deleted_at | TIMESTAMP WITH TIME ZONE | NULL | 소프트 삭제 시각 |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | 생성 시각 |
| updated_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | 수정 시각 |

**인덱스**
```sql
CREATE UNIQUE INDEX idx_companies_business_number ON companies(business_number)
  WHERE deleted_at IS NULL;
CREATE INDEX idx_companies_deleted_at ON companies(deleted_at);
```

---

## 2. company_members

회사와 사용자의 멤버십 관계를 저장합니다.

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 멤버십 고유 ID |
| company_id | UUID | NOT NULL, FK → companies.id | 회사 ID |
| user_id | UUID | NOT NULL, FK → users.id | 사용자 ID |
| role | VARCHAR(20) | NOT NULL | 역할 (owner/admin/member) |
| invited_at | TIMESTAMP WITH TIME ZONE | NULL | 초대 시각 |
| joined_at | TIMESTAMP WITH TIME ZONE | NULL | 가입 시각 |
| deleted_at | TIMESTAMP WITH TIME ZONE | NULL | 소프트 삭제 시각 |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | 생성 시각 |
| updated_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | 수정 시각 |

**인덱스**
```sql
CREATE UNIQUE INDEX idx_company_members_company_user ON company_members(company_id, user_id)
  WHERE deleted_at IS NULL;
CREATE INDEX idx_company_members_user_id ON company_members(user_id)
  WHERE deleted_at IS NULL;
CREATE INDEX idx_company_members_company_id ON company_members(company_id)
  WHERE deleted_at IS NULL;
```

**역할 정의**
- `owner`: 최초 등록자. 1명만 가능. 역할 변경 불가.
- `admin`: 회사 관리자. 멤버 초대/수정 가능.
- `member`: 일반 멤버. 조회만 가능.

---

## 3. performances

회사의 수행 실적을 저장합니다.

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 실적 고유 ID |
| company_id | UUID | NOT NULL, FK → companies.id | 회사 ID |
| project_name | VARCHAR(200) | NOT NULL | 프로젝트명 |
| client_name | VARCHAR(200) | NOT NULL | 발주처명 |
| client_type | VARCHAR(20) | NOT NULL | 발주처 유형 (public/private) |
| contract_amount | BIGINT | NOT NULL | 계약금액 (원) |
| start_date | DATE | NOT NULL | 시작일 |
| end_date | DATE | NOT NULL | 종료일 |
| status | VARCHAR(20) | NOT NULL | 상태 (ongoing/completed) |
| description | TEXT | NULL | 실적 설명 |
| is_representative | BOOLEAN | NOT NULL, DEFAULT false | 대표 실적 여부 |
| document_url | TEXT | NULL | 증빙 문서 URL |
| deleted_at | TIMESTAMP WITH TIME ZONE | NULL | 소프트 삭제 시각 |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | 생성 시각 |
| updated_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | 수정 시각 |

**제약 조건**
- 회사당 `is_representative = true`인 실적은 최대 3개

**인덱스**
```sql
CREATE INDEX idx_performances_company_id ON performances(company_id)
  WHERE deleted_at IS NULL;
CREATE INDEX idx_performances_company_representative ON performances(company_id, is_representative)
  WHERE deleted_at IS NULL;
CREATE INDEX idx_performances_status ON performances(company_id, status)
  WHERE deleted_at IS NULL;
CREATE INDEX idx_performances_contract_amount ON performances(company_id, contract_amount DESC)
  WHERE deleted_at IS NULL;
```

---

## 4. certifications

회사의 보유 인증을 저장합니다.

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 인증 고유 ID |
| company_id | UUID | NOT NULL, FK → companies.id | 회사 ID |
| name | VARCHAR(200) | NOT NULL | 인증 명칭 |
| issuer | VARCHAR(200) | NOT NULL | 발급 기관 |
| cert_number | VARCHAR(100) | NOT NULL | 인증 번호 |
| issued_date | DATE | NOT NULL | 발급일 |
| expiry_date | DATE | NULL | 만료일 (없으면 영구) |
| document_url | TEXT | NULL | 증빙 문서 URL |
| deleted_at | TIMESTAMP WITH TIME ZONE | NULL | 소프트 삭제 시각 |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | 생성 시각 |
| updated_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | 수정 시각 |

**인덱스**
```sql
CREATE INDEX idx_certifications_company_id ON certifications(company_id)
  WHERE deleted_at IS NULL;
CREATE INDEX idx_certifications_expiry_date ON certifications(company_id, expiry_date ASC NULLS LAST)
  WHERE deleted_at IS NULL;
```

---

## 5. users 테이블 변경 사항

기존 `users` 테이블에 다음 컬럼을 추가합니다.

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| company_id | UUID | NULL, FK → companies.id | 소속 회사 ID (미소속 시 NULL) |

```sql
ALTER TABLE users ADD COLUMN company_id UUID REFERENCES companies(id) ON DELETE SET NULL;
CREATE INDEX idx_users_company_id ON users(company_id) WHERE company_id IS NOT NULL;
```

---

## 관계 다이어그램

```
users (1) ─── (N) company_members (N) ─── (1) companies
                                                   │
                                                   ├── (N) performances
                                                   └── (N) certifications
```

---

## 사업자등록번호 체크섬 알고리즘

10자리 숫자 중 앞 9자리로 마지막 자리(체크 디지트)를 검증합니다.

```python
weights = [1, 3, 7, 1, 3, 7, 1, 3, 5]
total = sum(w * d for w, d in zip(weights, digits[:9]))
total += (5 * digits[8]) // 10
checksum = (10 - (total % 10)) % 10
# checksum == digits[9] 이어야 유효
```
