# F-03 제안서 AI 초안 생성 DB 스키마

## 개요

제안서 AI 초안 생성 기능에 필요한 DB 테이블 스키마입니다. ERD(docs/system/erd.md)에 정의된 proposals, proposal_sections, proposal_versions 테이블을 구현합니다.

---

## 신규 테이블

### 1. proposals

제안서 메타 정보를 저장합니다.

```sql
CREATE TABLE proposals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    bid_id UUID NOT NULL REFERENCES bids(id) ON DELETE RESTRICT,
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE SET NULL,
    title VARCHAR(300) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    version INTEGER NOT NULL DEFAULT 1,
    evaluation_checklist JSONB,
    page_count INTEGER DEFAULT 0,
    word_count INTEGER DEFAULT 0,
    generated_at TIMESTAMP WITH TIME ZONE,
    submitted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT chk_proposals_status
        CHECK (status IN ('draft', 'generating', 'ready', 'submitted'))
);
```

**컬럼 상세**:

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 제안서 고유 ID |
| user_id | UUID | FK -> users.id, NOT NULL, ON DELETE RESTRICT | 작성자 ID |
| bid_id | UUID | FK -> bids.id, NOT NULL, ON DELETE RESTRICT | 대상 공고 ID |
| company_id | UUID | FK -> companies.id, NOT NULL, ON DELETE SET NULL | 소속 회사 ID |
| title | VARCHAR(300) | NOT NULL | 제안서 제목 |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'draft' | 상태 (draft, generating, ready, submitted) |
| version | INTEGER | NOT NULL, DEFAULT 1 | 현재 버전 번호 |
| evaluation_checklist | JSONB | | 평가 항목 체크리스트 (공고 평가 기준 기반) |
| page_count | INTEGER | DEFAULT 0 | 추정 페이지 수 |
| word_count | INTEGER | DEFAULT 0 | 총 글자 수 |
| generated_at | TIMESTAMPTZ | | AI 생성 완료 시간 |
| submitted_at | TIMESTAMPTZ | | 제출 시간 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 생성 시간 |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 수정 시간 |
| deleted_at | TIMESTAMPTZ | | 삭제 시간 (Soft Delete) |

**evaluation_checklist JSONB 구조 예시**:
```json
{
  "technical": {
    "weight": 80,
    "items": [
      {"name": "기술 이해도", "weight": 20, "achieved": true},
      {"name": "수행 방법론", "weight": 30, "achieved": true},
      {"name": "품질 관리", "weight": 15, "achieved": false},
      {"name": "일정 계획", "weight": 15, "achieved": true}
    ],
    "score": 65
  },
  "price": {
    "weight": 20,
    "items": [
      {"name": "가격 적정성", "weight": 20, "achieved": true}
    ],
    "score": 20
  }
}
```

---

### 2. proposal_sections

제안서 섹션 내용을 저장합니다.

```sql
CREATE TABLE proposal_sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
    section_key VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    "order" INTEGER NOT NULL,
    content TEXT,
    metadata JSONB,
    is_ai_generated BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_proposal_sections_key UNIQUE (proposal_id, section_key)
);
```

**컬럼 상세**:

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 섹션 고유 ID |
| proposal_id | UUID | FK -> proposals.id, NOT NULL, ON DELETE CASCADE | 소속 제안서 ID |
| section_key | VARCHAR(50) | NOT NULL | 섹션 식별 키 |
| title | VARCHAR(200) | NOT NULL | 섹션 제목 (표시용) |
| order | INTEGER | NOT NULL | 섹션 정렬 순서 |
| content | TEXT | | 섹션 본문 (Markdown) |
| metadata | JSONB | | 부가 정보 (참조된 실적 ID 등) |
| is_ai_generated | BOOLEAN | DEFAULT TRUE | AI 생성 여부 (사용자 편집 시 FALSE) |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 생성 시간 |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 수정 시간 |

**section_key 정의**:

| section_key | title | order | 설명 |
|-------------|-------|-------|------|
| overview | 사업 개요 | 1 | 사업 이해, 목표, 기대 효과 |
| technical | 기술 제안 | 2 | 기술적 접근 방법, 아키텍처 |
| methodology | 수행 방법론 | 3 | 수행 체계, 품질 관리 |
| schedule | 추진 일정 | 4 | WBS, 마일스톤, 단계별 일정 |
| organization | 조직 구성 | 5 | 투입 인력, 조직도 |
| budget | 예산 | 6 | 비용 산출 내역 |

**metadata JSONB 구조 예시**:
```json
{
  "referencedPerformances": ["perf-uuid-1", "perf-uuid-2"],
  "referencedCertifications": ["cert-uuid-1"],
  "generationModel": "claude-sonnet-4-6",
  "generationTokens": 2048,
  "customInstructions": "클라우드 네이티브 강조"
}
```

---

### 3. proposal_versions

제안서 버전 히스토리 스냅샷을 저장합니다.

```sql
CREATE TABLE proposal_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    snapshot JSONB NOT NULL,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

**컬럼 상세**:

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 버전 고유 ID |
| proposal_id | UUID | FK -> proposals.id, NOT NULL, ON DELETE CASCADE | 소속 제안서 ID |
| version_number | INTEGER | NOT NULL | 버전 번호 (1부터 순차) |
| snapshot | JSONB | NOT NULL | 전체 섹션 스냅샷 |
| created_by | UUID | FK -> users.id, NOT NULL, ON DELETE RESTRICT | 버전 생성자 ID |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 버전 생성 시간 |

**snapshot JSONB 구조**:
```json
{
  "title": "제안서 제목",
  "sections": [
    {
      "sectionKey": "overview",
      "title": "사업 개요",
      "order": 1,
      "content": "# 사업 개요\n\n...",
      "isAiGenerated": true
    }
  ],
  "wordCount": 4500,
  "pageCount": 12
}
```

---

## 인덱스

```sql
-- proposals 인덱스
CREATE INDEX idx_proposals_user ON proposals(user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_proposals_bid ON proposals(bid_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_proposals_status ON proposals(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_proposals_user_updated ON proposals(user_id, updated_at DESC)
    WHERE deleted_at IS NULL;

-- proposal_sections 인덱스
CREATE INDEX idx_proposal_sections_proposal ON proposal_sections(proposal_id);

-- proposal_versions 인덱스
CREATE INDEX idx_proposal_versions_proposal ON proposal_versions(proposal_id);
```

---

## 기존 테이블 변경

F-03에서 기존 테이블 스키마 변경은 없습니다. 다음 테이블은 읽기 전용으로 참조합니다:

| 테이블 | 참조 용도 |
|--------|-----------|
| users | 작성자 조회, 소속 회사 확인 |
| bids | 공고 정보 (제목, 설명, 평가 기준) |
| bid_attachments | 첨부파일 추출 텍스트 (RFP 내용) |
| companies | 회사 프로필 (이름, 업종, 규모, 설명) |
| performances | 수행 실적 (관련 실적 자동 참조) |
| certifications | 보유 인증 (인증 정보 포함) |

---

## Alembic 마이그레이션

### 마이그레이션 파일명 규칙
```
{timestamp}_f03_create_proposal_tables.py
```

### 마이그레이션 내용
```python
def upgrade():
    # 1. proposals 테이블 생성
    # 2. proposal_sections 테이블 생성
    # 3. proposal_versions 테이블 생성
    # 4. 인덱스 생성

def downgrade():
    # 역순 삭제
    # 1. proposal_versions 삭제
    # 2. proposal_sections 삭제
    # 3. proposals 삭제
```

---

## 데이터 무결성

### Foreign Key 전략

| FK | ON DELETE | 이유 |
|----|-----------|------|
| proposals.user_id -> users.id | RESTRICT | 사용자 삭제 시 제안서 보존 |
| proposals.bid_id -> bids.id | RESTRICT | 공고 삭제 시 제안서 보존 |
| proposals.company_id -> companies.id | SET NULL | 회사 삭제 시 제안서 유지 (회사 정보만 해제) |
| proposal_sections.proposal_id -> proposals.id | CASCADE | 제안서 삭제 시 섹션 동시 삭제 |
| proposal_versions.proposal_id -> proposals.id | CASCADE | 제안서 삭제 시 버전 동시 삭제 |
| proposal_versions.created_by -> users.id | RESTRICT | 사용자 삭제 시 버전 보존 |

### Soft Delete
- proposals 테이블만 Soft Delete 적용 (deleted_at)
- proposal_sections, proposal_versions는 CASCADE DELETE (proposals 삭제 시 자동)

---

## 변경 이력

| 날짜 | 변경 내용 | 이유 |
|------|----------|------|
| 2026-03-08 | 초기 스키마 설계 | F-03 기능 구현 시작 |
