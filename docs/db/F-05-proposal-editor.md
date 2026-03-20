# F-05 제안서 편집기 DB 스키마 문서

## 개요

제안서 편집기 기능을 위한 데이터베이스 스키마입니다. 기존 제안서(`Proposal`) 및 제안서 섹션(`ProposalSection`) 테이블을 활용하며, 추가적인 테이블 생성 없이 기존 스키마를 확장하여 사용합니다.

---

## 테이블 구조

### 1. proposals (제안서 테이블)

제안서 기본 정보를 저장하는 테이블입니다. F-05에서는 `word_count`, `page_count`, `evaluation_checklist` 필드를 주로 사용합니다.

**컬럼:**

| 컬럼명 | 타입 | 설명 | F-05 관련 |
|--------|------|------|----------|
| id | UUID | 제안서 ID (PK) | 조회용 |
| user_id | UUID | 사용자 ID (FK) | 소유자 확인 |
| bid_id | UUID | 입찰 공고 ID (FK) | 관련 공고 |
| company_id | UUID | 회사 ID (FK) | 회사 정보 |
| title | VARCHAR(300) | 제안서 제목 | - |
| status | VARCHAR(20) | 상태 (`draft`, `generating`, `ready`, `submitted`) | - |
| version | INTEGER | 버전 번호 | - |
| evaluation_checklist | JSONB | 평가 항목 체크리스트 | **F-05 주요 사용** |
| page_count | INTEGER | 페이지 수 | **F-05 자동 계산** |
| word_count | INTEGER | 단어 수 | **F-05 자동 계산** |
| generated_at | TIMESTAMP | AI 생성 완료 시각 | - |
| submitted_at | TIMESTAMP | 제출 시각 | - |
| created_at | TIMESTAMP | 생성 시각 | - |
| updated_at | TIMESTAMP | 수정 시각 | **F-05 자동 업데이트** |
| deleted_at | TIMESTAMP | 삭제 시각 (Soft Delete) | - |

**제약사항:**

```sql
-- FK 제약
ALTER TABLE proposals
ADD CONSTRAINT fk_proposals_user_id
FOREIGN KEY (user_id) REFERENCES users(id);

ALTER TABLE proposals
ADD CONSTRAINT fk_proposals_bid_id
FOREIGN KEY (bid_id) REFERENCES bids(id);

ALTER TABLE proposals
ADD CONSTRAINT fk_proposals_company_id
FOREIGN KEY (company_id) REFERENCES companies(id);

-- 인덱스
CREATE INDEX idx_proposals_user_id ON proposals(user_id);
CREATE INDEX idx_proposals_bid_id ON proposals(bid_id);
CREATE INDEX idx_proposals_status ON proposals(status);
CREATE INDEX idx_proposals_deleted_at ON proposals(deleted_at);
```

---

### 2. proposal_sections (제안서 섹션 테이블)

제안서의 각 섹션별 콘텐츠를 저장하는 테이블입니다. F-05의 핵심 테이블입니다.

**컬럼:**

| 컬럼명 | 타입 | 설명 | F-05 관련 |
|--------|------|------|----------|
| id | UUID | 섹션 ID (PK) | - |
| proposal_id | UUID | 제안서 ID (FK) | **F-05 주요 사용** |
| section_key | VARCHAR(50) | 섹션 키 | **F-05 주요 사용** |
| title | VARCHAR(200) | 섹션 제목 | - |
| content | TEXT | 섹션 콘텐츠 (HTML) | **F-05 주요 사용** |
| order | INTEGER | 섹션 순서 | - |
| is_ai_generated | BOOLEAN | AI 생성 여부 | - |
| word_count | INTEGER | 섹션 단어 수 | **F-05 자동 계산** |
| section_metadata | JSONB | 섹션 메타데이터 | **F-05 주요 사용** |
| created_at | TIMESTAMP | 생성 시각 | - |
| updated_at | TIMESTAMP | 수정 시각 | **F-05 자동 업데이트** |

**제약사항:**

```sql
-- FK 제약
ALTER TABLE proposal_sections
ADD CONSTRAINT fk_proposal_sections_proposal_id
FOREIGN KEY (proposal_id) REFERENCES proposals(id)
ON DELETE CASCADE;

-- UNIQUE 제약 (제안서별 섹션 키)
CREATE UNIQUE INDEX idx_proposal_sections_proposal_key
ON proposal_sections(proposal_id, section_key);

-- 인덱스
CREATE INDEX idx_proposal_sections_proposal_id ON proposal_sections(proposal_id);
```

---

## F-05 관련 데이터 구조

### evaluation_checklist (JSONB)

제안서의 평가 항목 체크리스트를 저장합니다.

**구조:**

```json
{
  "technical_capability": {
    "checked": true,
    "weight": 30
  },
  "price_competitiveness": {
    "checked": true,
    "weight": 25
  },
  "past_performance": {
    "checked": false,
    "weight": 20
  },
  "project_schedule": {
    "checked": true,
    "weight": 15
  },
  "organization": {
    "checked": false,
    "weight": 10
  }
}
```

**필드:**

| 키 | 타입 | 필수 | 설명 |
|----|------|------|------|
| * | object | Y | 평가 항목 (키 이름은 자유롭게 지정) |
| *.checked | boolean | Y | 체크 여부 |
| *.weight | number | Y | 가중치 (0-100) |

**GDB 인덱스 (선택사항):**

```sql
CREATE INDEX idx_proposals_evaluation_checklist
ON proposals USING GIN(evaluation_checklist);
```

---

### section_metadata (JSONB)

섹션별 메타데이터를 저장합니다. 편집 이력 추적에 사용됩니다.

**구조:**

```json
{
  "lastEditedBy": "550e8400-e29b-41d4-a716-446655440000",
  "editCount": 5,
  "lastEditAt": "2026-03-20T10:30:00Z",
  "format": "html"
}
```

**필드:**

| 키 | 타입 | 필수 | 설명 |
|----|------|------|------|
| lastEditedBy | string | Y | 마지막 편집자 사용자 ID |
| editCount | number | Y | 편집 횟수 |
| lastEditAt | string | Y | 마지막 편집 시각 (ISO 8601) |
| format | string | Y | 콘텐츠 포맷 (현재는 `html`) |

---

## 섹션 정의 (SECTION_DEFINITIONS)

데이터베이스에 저장되지 않고 코드 상수로 관리됩니다.

```python
SECTION_DEFINITIONS = {
    "overview": {"title": "사업 개요", "order": 1},
    "technical": {"title": "기술 제안", "order": 2},
    "price": {"title": "가격 제안", "order": 3},
    "schedule": {"title": "추진 일정", "order": 4},
    "organization": {"title": "조직 구성", "order": 5},
    "past_performance": {"title": "수행 실적", "order": 6},
}
```

| 섹션 키 | 섹션 명 | 순서 | 필수 여부 |
|---------|---------|------|-----------|
| overview | 사업 개요 | 1 | Y |
| technical | 기술 제안 | 2 | Y |
| price | 가격 제안 | 3 | N |
| schedule | 추진 일정 | 4 | N |
| organization | 조직 구성 | 5 | N |
| past_performance | 수행 실적 | 6 | N |

---

## F-05 동작 방식

### 1. 섹션 자동 저장 (auto_save_sections)

1. **요청 수신**: 여러 섹션의 업데이트 요청 수신
2. **검증**:
   - 제안서 존재 확인
   - 섹션 키 유효성 확인
   - 소유자 권한 확인
3. **업데이트**:
   - 각 섹션의 `content`, `is_ai_generated`, `updated_at` 업데이트
   - `section_metadata` 자동 업데이트 (`editCount` 증가, `lastEditAt` 설정)
4. **계산**:
   - 각 섹션의 `word_count` 재계산
   - 제안서의 총 `word_count` 계산
   - `page_count` 계산 (`word_count // 2000`)
5. **저장**: DB에 변경사항 커밋

### 2. 제안서 검증 (validate_proposal)

1. **제안서 조회**: 모든 섹션 포함하여 조회
2. **필수 섹션 검증**:
   - `overview`, `technical` 섹션이 비어있는지 확인
3. **페이지 제한 검증**:
   - 총 단어 수 기반 예상 페이지 수 계산
   - `pageLimit`이 제공되면 초과 여부 확인
4. **평가 항목 달성률 검증**:
   - `evaluation_checklist`에서 달성률 계산
   - 50% 미만이면 경고 추가 (비차단)
5. **결과 반환**: `isValid`, `warnings`, `stats` 반환

### 3. 평가 체크리스트 업데이트 (update_evaluation_checklist)

1. **요청 수신**: 체크리스트 업데이트 요청 수신
2. **병합**: 기존 체크리스트와 새 체크리스트 병합
3. **달성률 계산**:
   ```
   달성률 = (체크된 항목 가중치 합 / 전체 가중치) * 100
   ```
4. **저장**: `evaluation_checklist` 업데이트 및 `updated_at` 설정

---

## 워드 카운트 계산 로직

```python
def calculate_word_count(content: str) -> int:
    if not content:
        return 0

    # HTML 태그 제거
    text = re.sub(r"<[^>]+>", "", content)
    text = text.strip()

    if not text:
        return 0

    # 한글 글자 수 + 영어 단어 수
    korean_chars = len(re.findall(r"[가-힣]", text))
    english_words = len(re.findall(r"[a-zA-Z]+", text))

    return korean_chars + english_words
```

**예시:**
- `"<p>안녕하세요 테스트입니다</p>"` → 11
- `"<p>Hello World</p>"` → 2
- `"<p>Hello 안녕하세요</p>"` → 6

---

## 페이지 수 계산 로직

```python
page_count = max(1, total_word_count // 2000)
```

- 2000자당 1페이지로 계산
- 최소 1페이지

---

## 검증 규칙

### 차단 경고 (isValid = False)

1. **필수 섹션 누락**:
   - `overview` 또는 `technical` 섹션이 비어있음
   - 타입: `required_field`

2. **페이지 제한 초과**:
   - `estimated_pages > page_limit`
   - 타입: `page_limit`

### 비차단 경고 (isValid = True)

1. **평가 항목 달성률 낮음**:
   - `achievement_rate < 50`
   - 타입: `evaluation_incomplete`

---

## 성능 최적화

### 인덱스

```sql
-- 자주 조회되는 컬럼에 인덱스
CREATE INDEX idx_proposals_user_id_status ON proposals(user_id, status);
CREATE INDEX idx_proposals_updated_at ON proposals(updated_at DESC);

-- JSONB 필드에 GIN 인덱스 (선택사항)
CREATE INDEX idx_proposals_evaluation_checklist
ON proposals USING GIN(evaluation_checklist);
```

### N+1 쿼리 방지

```python
# 섹션 포함하여 제안서 조회 (preload)
stmt = select(Proposal).options(
    selectinload(Proposal.sections),
    selectinload(Proposal.versions),
)
```

### 페이지네이션

```sql
-- 목록 조회 시 페이지네이션 필수
SELECT * FROM proposals
WHERE user_id = :user_id AND deleted_at IS NULL
ORDER BY updated_at DESC
LIMIT :page_size OFFSET :offset
```

---

## 마이그레이션

Prisma 마이그레이션 생성:

```bash
npx prisma migrate dev --name f05_proposal_editor
```

---

## 캐싱 전략

현재는 캐싱 전략이 없습니다. 향후 Redis를 활용한 캐싱을 고려할 수 있습니다:

- 섹션 콘텐츠 캐싱
- 제안서 검증 결과 캐싱 (짧은 TTL)
- 평가 체크리스트 캐싱

---

## 백업 및 복구

### 버전 관리

제안서 버전은 `proposal_versions` 테이블에 저장됩니다.

```sql
SELECT * FROM proposal_versions
WHERE proposal_id = :proposal_id
ORDER BY version_number DESC;
```

### 복원

```sql
-- 버전 복원 시 새 버전 생성 후 스냅샷 복원
INSERT INTO proposal_versions (proposal_id, version_number, snapshot, created_by)
VALUES (:proposal_id, :next_version, :snapshot, :user_id);
```

---

## 테스트 데이터

### 테스트용 제안서

```sql
INSERT INTO proposals (id, user_id, bid_id, title, status, version, word_count, page_count)
VALUES (
    '550e8400-e29b-41d4-a716-446655440000',
    '660e8400-e29b-41d4-a716-446655440001',
    '770e8400-e29b-41d4-a716-446655440002',
    '테스트 제안서',
    'draft',
    1,
    1250,
    1
);
```

### 테스트용 섹션

```sql
INSERT INTO proposal_sections (id, proposal_id, section_key, title, content, order, word_count)
VALUES
('880e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440000', 'overview', '사업 개요', '<p>내용</p>', 1, 50),
('990e8400-e29b-41d4-a716-446655440004', '550e8400-e29b-41d4-a716-446655440000', 'technical', '기술 제안', '<p>기술 내용</p>', 2, 100);
```
