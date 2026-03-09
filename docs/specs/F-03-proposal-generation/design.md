# F-03 제안서 AI 초안 생성 -- 변경 설계서

## 1. 참조
- 인수조건: docs/project/features.md #F-03
- ERD: docs/system/erd.md (proposals, proposal_sections, proposal_versions)
- API 컨벤션: docs/system/api-conventions.md (SSE 스트리밍 섹션 8)
- 공고 설계: docs/specs/F-01-bid-collection/design.md
- 회사 프로필: backend/src/services/company_service.py

---

## 2. 변경 범위

- **변경 유형**: 신규 추가 + 기존 스텁 교체
- **영향 받는 모듈**:
  - proposals.py (스텁 -> 실제 API 구현)
  - models/__init__.py (Proposal, ProposalSection, ProposalVersion 등록)
  - config.py (Claude API 설정 추가)
  - api/v1/router.py (변경 없음, proposals 라우터 이미 등록됨)

---

## 3. 영향 분석

### 기존 API 변경

| API | 현재 | 변경 후 | 하위 호환성 |
|-----|------|---------|-------------|
| GET /proposals | 스텁 (빈 목록) | 실제 목록 조회 | 호환 (응답 구조 동일) |
| GET /proposals/{id} | 스텁 | 실제 상세 조회 | 호환 |
| POST /proposals | 스텁 | 실제 제안서 생성 | 호환 |

### 기존 DB 변경

| 테이블 | 변경 내용 | 마이그레이션 전략 |
|--------|----------|------------------|
| proposals | 신규 생성 | 신규 마이그레이션 |
| proposal_sections | 신규 생성 | 신규 마이그레이션 |
| proposal_versions | 신규 생성 | 신규 마이그레이션 |

### 사이드 이펙트
- bids 테이블: 읽기 전용 참조 (공고 정보 + 첨부파일 추출 텍스트)
- bid_attachments 테이블: 읽기 전용 참조 (extracted_text를 프롬프트에 포함)
- companies 테이블: 읽기 전용 참조 (회사 프로필)
- performances 테이블: 읽기 전용 참조 (관련 실적 자동 포함)
- certifications 테이블: 읽기 전용 참조 (보유 인증 자동 포함)
- NotificationService: 제안서 생성 완료 알림 호출 (스텁, F-10에서 구현)

---

## 4. 아키텍처 결정

### 결정 1: AI 모델 선택
- **선택지**: A) Claude claude-sonnet-4-6 / B) GPT-4o / C) 로컬 LLM
- **결정**: A) Claude claude-sonnet-4-6
- **근거**:
  - features.md에서 Claude API 사용 명시
  - config.py에 anthropic_api_key 이미 설정됨
  - 한국어 제안서 생성에 우수한 성능
  - 스트리밍 API 지원 (SSE 요구사항 충족)

### 결정 2: 스트리밍 방식
- **선택지**: A) SSE (Server-Sent Events) / B) WebSocket / C) 폴링
- **결정**: A) SSE
- **근거**:
  - api-conventions.md 섹션 8에서 SSE 컨벤션 이미 정의됨
  - 단방향 스트리밍으로 충분 (서버 -> 클라이언트)
  - Claude API의 스트리밍 응답과 자연스럽게 연결
  - FastAPI StreamingResponse로 구현 용이

### 결정 3: 섹션 생성 전략
- **선택지**: A) 전체 한 번에 생성 / B) 섹션별 개별 API 호출 / C) 순차 섹션 생성 (파이프라인)
- **결정**: C) 순차 섹션 생성 (파이프라인)
- **근거**:
  - 섹션별 독립 생성 인수조건 충족
  - 섹션 완료 시마다 SSE 이벤트 발행 -> 실시간 UX
  - 한 번에 전체 생성보다 토큰 제어가 용이
  - 섹션 간 컨텍스트 전달 가능 (이전 섹션 요약 포함)

### 결정 4: 프롬프트 템플릿 관리
- **선택지**: A) 코드 내 하드코딩 / B) DB 저장 / C) 파일 기반 Jinja2 템플릿
- **결정**: C) 파일 기반 Jinja2 템플릿
- **근거**:
  - 프롬프트 변경 시 코드 변경 불필요
  - Jinja2는 features.md 기술 고려사항에 명시됨
  - 섹션별 개별 템플릿 파일로 관리 용이
  - 템플릿 변수로 공고/회사 데이터 주입

### 결정 5: 제안서 다운로드 (Word/PDF)
- **선택지**: A) 실시간 변환 / B) 사전 생성 후 캐시
- **결정**: A) 실시간 변환
- **근거**:
  - 편집 후 최신 내용 반영 필요
  - python-docx, reportlab은 빠른 생성 가능 (10초 이내 AC 충족)
  - 캐시 무효화 복잡성 회피

---

## 5. API 설계

### 5.1 POST /api/v1/proposals
제안서 생성 (AI 초안 생성 트리거)

- **목적**: 특정 공고에 대한 제안서 생성 시작
- **인증**: 필요 (Bearer Token)
- **Request Body**:
```json
{
  "bidId": "uuid",
  "title": "제안서 제목 (선택, 미입력 시 공고명 기반 자동 생성)",
  "sections": ["overview", "technical", "methodology", "schedule", "organization", "budget"],
  "customInstructions": "추가 지시사항 (선택)"
}
```
- **Response** (201 Created):
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "bidId": "uuid",
    "title": "2026년 정보시스템 고도화 사업 제안서",
    "status": "generating",
    "sections": ["overview", "technical", "methodology", "schedule", "organization", "budget"],
    "createdAt": "2026-03-08T10:00:00Z"
  }
}
```
- **비즈니스 규칙**:
  - 사용자 소속 회사 프로필이 등록되어 있어야 함
  - 공고가 존재하고 상태가 open이어야 함
  - sections 미지정 시 기본 6개 섹션 전체 생성
  - 동일 공고에 대해 여러 제안서 생성 가능 (버전 관리)
- **에러 케이스**:
  | 코드 | HTTP Status | 상황 |
  |------|-------------|------|
  | AUTH_002 | 401 | 인증 토큰 없음 |
  | BID_001 | 404 | 공고를 찾을 수 없음 |
  | BID_002 | 400 | 공고가 이미 마감됨 |
  | COMPANY_001 | 404 | 소속 회사 없음 |
  | RATE_LIMIT_002 | 429 | AI 생성 요청 한도 초과 |

### 5.2 GET /api/v1/proposals/{id}/generate/stream
AI 제안서 생성 SSE 스트리밍

- **목적**: 제안서 AI 생성 진행 상황을 실시간으로 전달
- **인증**: 필요 (Bearer Token, query parameter로 전달)
- **요청 헤더**: `Accept: text/event-stream`
- **Query Parameters**:
  | Parameter | Type | 설명 |
  |-----------|------|------|
  | token | string | Bearer Token (SSE는 헤더 전달 불가하므로) |
- **SSE 이벤트**:

  **시작 이벤트**
  ```
  event: start
  data: {"proposalId": "uuid", "totalSections": 6, "message": "제안서 생성을 시작합니다."}
  ```

  **진행 상황 이벤트**
  ```
  event: progress
  data: {"sectionKey": "overview", "percent": 17, "message": "사업 개요 섹션 생성 중..."}
  ```

  **섹션 완료 이벤트**
  ```
  event: section
  data: {"sectionKey": "overview", "title": "사업 개요", "content": "# 사업 개요\n\n...", "wordCount": 520, "order": 1}
  ```

  **전체 완료 이벤트**
  ```
  event: complete
  data: {"proposalId": "uuid", "totalSections": 6, "totalWordCount": 4500, "generatedAt": "2026-03-08T10:03:00Z"}
  ```

  **에러 이벤트**
  ```
  event: error
  data: {"code": "PROPOSAL_003", "message": "제안서 생성 중 오류가 발생했습니다."}
  ```

- **에러 케이스**:
  | 코드 | HTTP Status | 상황 |
  |------|-------------|------|
  | PROPOSAL_001 | 404 | 제안서를 찾을 수 없음 |
  | PROPOSAL_002 | 403 | 제안서 소유자가 아님 |
  | PROPOSAL_004 | 504 | AI 생성 시간 초과 (3분) |

### 5.3 POST /api/v1/proposals/{id}/sections/{sectionKey}/regenerate
개별 섹션 재생성

- **목적**: 특정 섹션만 AI로 재생성
- **인증**: 필요 (Bearer Token)
- **Request Body**:
```json
{
  "customInstructions": "더 구체적인 수행 방법론을 포함해주세요"
}
```
- **Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "sectionKey": "methodology",
    "title": "수행 방법론",
    "content": "# 수행 방법론\n\n...",
    "wordCount": 680,
    "isAiGenerated": true,
    "updatedAt": "2026-03-08T10:10:00Z"
  }
}
```
- **에러 케이스**:
  | 코드 | HTTP Status | 상황 |
  |------|-------------|------|
  | PROPOSAL_001 | 404 | 제안서를 찾을 수 없음 |
  | PROPOSAL_002 | 403 | 제안서 소유자가 아님 |
  | PROPOSAL_006 | 404 | 섹션을 찾을 수 없음 |

### 5.4 GET /api/v1/proposals
제안서 목록 조회

- **목적**: 사용자의 제안서 목록 조회
- **인증**: 필요 (Bearer Token)
- **Query Parameters**:
  | Parameter | Type | Default | 설명 |
  |-----------|------|---------|------|
  | page | int | 1 | 페이지 번호 |
  | pageSize | int | 20 | 페이지당 항목 수 (최대 100) |
  | status | string | | 필터: draft, generating, ready, submitted |
  | bidId | uuid | | 특정 공고의 제안서만 |
  | sortBy | string | updatedAt | 정렬 필드 |
  | sortOrder | string | desc | 정렬 방향 |
- **Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "bidId": "uuid",
        "bidTitle": "2026년 정보시스템 고도화 사업",
        "title": "제안서 초안",
        "status": "ready",
        "version": 1,
        "sectionCount": 6,
        "wordCount": 4500,
        "generatedAt": "2026-03-08T10:03:00Z",
        "createdAt": "2026-03-08T10:00:00Z",
        "updatedAt": "2026-03-08T10:03:00Z"
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

### 5.5 GET /api/v1/proposals/{id}
제안서 상세 조회

- **목적**: 제안서 메타 정보 + 전체 섹션 내용 조회
- **인증**: 필요 (Bearer Token)
- **Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "bidId": "uuid",
    "companyId": "uuid",
    "title": "2026년 정보시스템 고도화 사업 제안서",
    "status": "ready",
    "version": 1,
    "evaluationChecklist": {
      "technical": {"items": [...], "score": 85},
      "price": {"items": [...], "score": 20}
    },
    "pageCount": 12,
    "wordCount": 4500,
    "sections": [
      {
        "id": "uuid",
        "sectionKey": "overview",
        "title": "사업 개요",
        "order": 1,
        "content": "# 사업 개요\n\n...",
        "wordCount": 520,
        "isAiGenerated": true,
        "metadata": {"referencedPerformances": ["uuid1", "uuid2"]},
        "updatedAt": "2026-03-08T10:01:00Z"
      }
    ],
    "generatedAt": "2026-03-08T10:03:00Z",
    "createdAt": "2026-03-08T10:00:00Z",
    "updatedAt": "2026-03-08T10:03:00Z"
  }
}
```

### 5.6 GET /api/v1/proposals/{id}/download
제안서 다운로드

- **목적**: 제안서를 Word 또는 PDF 파일로 다운로드
- **인증**: 필요 (Bearer Token)
- **Query Parameters**:
  | Parameter | Type | Default | 설명 |
  |-----------|------|---------|------|
  | format | string | docx | 다운로드 형식: docx, pdf |
- **Response** (200 OK): 파일 바이너리 (Content-Disposition 헤더)
- **에러 케이스**:
  | 코드 | HTTP Status | 상황 |
  |------|-------------|------|
  | PROPOSAL_001 | 404 | 제안서를 찾을 수 없음 |
  | PROPOSAL_002 | 403 | 제안서 소유자가 아님 |

---

## 6. DB 설계

ERD (docs/system/erd.md)에 정의된 테이블 구조를 기본으로 사용합니다.

### 6.1 proposals 테이블

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 제안서 ID |
| user_id | UUID | FK -> users.id, NOT NULL | 작성자 ID |
| bid_id | UUID | FK -> bids.id, NOT NULL | 공고 ID |
| company_id | UUID | FK -> companies.id, NOT NULL | 회사 ID |
| title | VARCHAR(300) | NOT NULL | 제안서 제목 |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'draft' | 상태 |
| version | INTEGER | NOT NULL, DEFAULT 1 | 버전 번호 |
| evaluation_checklist | JSONB | | 평가 항목 체크리스트 |
| page_count | INTEGER | DEFAULT 0 | 페이지 수 |
| word_count | INTEGER | DEFAULT 0 | 글자 수 |
| generated_at | TIMESTAMP | | AI 생성 완료 시간 |
| submitted_at | TIMESTAMP | | 제출 시간 |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 생성 시간 |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 수정 시간 |
| deleted_at | TIMESTAMP | | 삭제 시간 (Soft Delete) |

**Check Constraints**:
```sql
ALTER TABLE proposals
    ADD CONSTRAINT chk_proposals_status
    CHECK (status IN ('draft', 'generating', 'ready', 'submitted'));
```

### 6.2 proposal_sections 테이블

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 섹션 ID |
| proposal_id | UUID | FK -> proposals.id, NOT NULL | 제안서 ID |
| section_key | VARCHAR(50) | NOT NULL | 섹션 키 |
| title | VARCHAR(200) | NOT NULL | 섹션 제목 |
| order | INTEGER | NOT NULL | 순서 |
| content | TEXT | | 섹션 내용 (Markdown) |
| metadata | JSONB | | 섹션 메타데이터 |
| is_ai_generated | BOOLEAN | DEFAULT TRUE | AI 생성 여부 |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 생성 시간 |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 수정 시간 |

**Unique Constraint**: (proposal_id, section_key)

**section_key 정의**:

| section_key | title | order | 설명 |
|-------------|-------|-------|------|
| overview | 사업 개요 | 1 | 사업 이해 및 목표 |
| technical | 기술 제안 | 2 | 기술적 접근 방법 |
| methodology | 수행 방법론 | 3 | 수행 체계 및 방법론 |
| schedule | 추진 일정 | 4 | 단계별 일정 계획 |
| organization | 조직 구성 | 5 | 투입 인력 및 조직도 |
| budget | 예산 | 6 | 비용 산출 내역 |

### 6.3 proposal_versions 테이블

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 버전 ID |
| proposal_id | UUID | FK -> proposals.id, NOT NULL | 제안서 ID |
| version_number | INTEGER | NOT NULL | 버전 번호 |
| snapshot | JSONB | NOT NULL | 스냅샷 (전체 섹션) |
| created_by | UUID | FK -> users.id, NOT NULL | 생성자 ID |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 생성 시간 |

---

## 7. 서비스 설계

### 7.1 ProposalService -- 제안서 관리 서비스

**책임**: 제안서 CRUD 및 AI 생성 오케스트레이션

```python
class ProposalService:
    """제안서 관리 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_proposal(
        self, user_id: UUID, bid_id: UUID, data: dict
    ) -> Proposal:
        """
        제안서 생성 (메타 레코드)

        1. 사용자 소속 회사 조회
        2. 공고 존재 + open 상태 검증
        3. proposals 레코드 생성 (status='generating')
        4. 요청된 섹션별 proposal_sections 빈 레코드 생성
        Returns: Proposal 객체
        """

    async def get_proposal(self, proposal_id: UUID, user_id: UUID) -> Proposal:
        """
        제안서 상세 조회 (섹션 포함)

        - 소유자 검증
        - proposal + sections eager loading
        """

    async def list_proposals(
        self, user_id: UUID, filters: dict, page: int, page_size: int
    ) -> dict:
        """사용자의 제안서 목록 조회"""

    async def update_proposal_status(
        self, proposal_id: UUID, status: str
    ) -> None:
        """제안서 상태 갱신"""

    async def save_section_content(
        self, proposal_id: UUID, section_key: str, content: str, word_count: int
    ) -> ProposalSection:
        """섹션 내용 저장"""

    async def finalize_proposal(self, proposal_id: UUID) -> Proposal:
        """
        제안서 생성 완료 처리

        1. status -> 'ready'
        2. 총 글자수, 페이지수 계산
        3. generated_at 갱신
        4. 초기 버전 스냅샷 저장
        """

    async def create_version_snapshot(
        self, proposal_id: UUID, user_id: UUID
    ) -> ProposalVersion:
        """현재 상태의 버전 스냅샷 저장"""
```

### 7.2 ProposalGeneratorService -- AI 생성 서비스

**책임**: Claude API를 활용한 제안서 섹션별 AI 생성

```python
class ProposalGeneratorService:
    """제안서 AI 생성 서비스"""

    def __init__(self, db: AsyncSession, anthropic_client: AsyncAnthropic):
        self.db = db
        self.client = anthropic_client

    async def generate_proposal_stream(
        self, proposal_id: UUID
    ) -> AsyncGenerator[dict, None]:
        """
        제안서 AI 생성 스트리밍 메인 플로우

        1. proposal + bid + company + performances + certifications 조회
        2. 공고 컨텍스트 구성 (제목, 설명, 첨부파일 텍스트, 평가 기준)
        3. 회사 컨텍스트 구성 (프로필, 실적, 인증)
        4. 섹션 순서대로 반복:
           a. yield start/progress 이벤트
           b. _generate_section() 호출
           c. DB 저장
           d. yield section 이벤트
        5. 제안서 완료 처리
        6. yield complete 이벤트

        Yields: SSE 이벤트 dict (event_type, data)
        """

    async def _generate_section(
        self,
        section_key: str,
        bid_context: dict,
        company_context: dict,
        previous_sections: list[dict],
        custom_instructions: str | None = None,
    ) -> str:
        """
        단일 섹션 AI 생성

        1. Jinja2 템플릿에서 섹션별 프롬프트 렌더링
        2. Claude API 호출 (claude-sonnet-4-6)
        3. 응답 텍스트 반환
        """

    async def regenerate_section(
        self,
        proposal_id: UUID,
        section_key: str,
        custom_instructions: str | None = None,
    ) -> ProposalSection:
        """
        개별 섹션 재생성

        1. 기존 컨텍스트 재구성
        2. custom_instructions 반영
        3. Claude API 호출
        4. 섹션 내용 갱신
        """

    def _build_bid_context(
        self, bid: Bid, attachments: list[BidAttachment]
    ) -> dict:
        """
        공고 컨텍스트 구성

        Returns: {
            title, description, organization, budget,
            scoring_criteria, attachment_texts, deadline
        }
        """

    def _build_company_context(
        self, company: Any, performances: list, certifications: list
    ) -> dict:
        """
        회사 컨텍스트 구성

        - 대표 실적 우선 정렬 (is_representative=True)
        - 공고와 관련도 높은 실적 선별 (키워드 매칭)

        Returns: {
            name, industry, scale, description,
            performances: [{name, client, amount, description}],
            certifications: [{name, issuer}]
        }
        """

    def _select_relevant_performances(
        self, performances: list, bid_title: str, bid_description: str
    ) -> list:
        """
        공고와 관련도 높은 실적 선별 (AC-04)

        - 대표 실적 우선 포함
        - 키워드 유사도 기반 정렬
        - 최대 10건 선별
        """

    def _render_prompt(
        self,
        section_key: str,
        bid_context: dict,
        company_context: dict,
        previous_sections: list[dict],
        custom_instructions: str | None,
    ) -> str:
        """Jinja2 템플릿 렌더링"""
```

### 7.3 ProposalExportService -- 다운로드 서비스

**책임**: 제안서를 Word/PDF로 변환

```python
class ProposalExportService:
    """제안서 내보내기 서비스"""

    async def export_docx(self, proposal: Proposal, sections: list) -> bytes:
        """
        Word 파일 생성 (python-docx)

        - 표지 페이지 (제안서 제목, 회사명, 날짜)
        - 목차
        - 섹션별 내용 (Markdown -> DOCX 변환)
        Returns: DOCX 바이너리
        """

    async def export_pdf(self, proposal: Proposal, sections: list) -> bytes:
        """
        PDF 파일 생성 (reportlab)

        - Markdown -> PDF 변환
        - 한글 폰트 지원 (NanumGothic 등)
        Returns: PDF 바이너리
        """
```

---

## 8. 프롬프트 템플릿 설계

### 8.1 디렉토리 구조

```
backend/src/templates/prompts/
  base_system.j2          # 시스템 프롬프트 (공통)
  section_overview.j2     # 사업 개요 섹션
  section_technical.j2    # 기술 제안 섹션
  section_methodology.j2  # 수행 방법론 섹션
  section_schedule.j2     # 추진 일정 섹션
  section_organization.j2 # 조직 구성 섹션
  section_budget.j2       # 예산 섹션
```

### 8.2 시스템 프롬프트 (base_system.j2)

```
당신은 공공 입찰 제안서 작성 전문가입니다.
다음 공고에 대한 제안서를 작성합니다.

## 공고 정보
- 공고명: {{ bid.title }}
- 발주기관: {{ bid.organization }}
- 예산: {{ bid.budget | format_currency }}
- 평가 기준: {{ bid.scoring_criteria | tojson }}
- 마감일: {{ bid.deadline }}

## 공고 상세 내용
{{ bid.description }}

{% if bid.attachment_texts %}
## 제안요청서(RFP) 내용
{% for text in bid.attachment_texts %}
{{ text }}
{% endfor %}
{% endif %}

## 제안 회사 정보
- 회사명: {{ company.name }}
- 업종: {{ company.industry }}
- 규모: {{ company.scale }}
- 소개: {{ company.description }}

{% if company.performances %}
## 주요 수행 실적
{% for perf in company.performances %}
- {{ perf.project_name }} ({{ perf.client_name }}, {{ perf.contract_amount | format_currency }})
  {{ perf.description }}
{% endfor %}
{% endif %}

{% if company.certifications %}
## 보유 인증
{% for cert in company.certifications %}
- {{ cert.name }} ({{ cert.issuer }})
{% endfor %}
{% endif %}

## 작성 규칙
1. 한국어로 작성합니다.
2. 공공기관 제안서 형식에 맞춰 격식체를 사용합니다.
3. 회사의 실적과 인증을 적절히 참조합니다.
4. 평가 기준에 맞는 내용을 포함합니다.
5. Markdown 형식으로 작성합니다.
```

### 8.3 섹션 프롬프트 예시 (section_overview.j2)

```
{% include 'base_system.j2' %}

{% if previous_sections %}
## 이전 작성된 섹션
{% for section in previous_sections %}
### {{ section.title }}
{{ section.content | truncate(500) }}
{% endfor %}
{% endif %}

## 현재 작성할 섹션: 사업 개요

다음 항목을 포함하여 사업 개요 섹션을 작성해주세요:
1. 사업의 배경 및 필요성
2. 사업 목표
3. 기대 효과
4. 제안 범위

{{ custom_instructions or '' }}
```

---

## 9. 시퀀스 흐름

### 9.1 제안서 AI 생성 전체 흐름

```
사용자 -> Frontend -> POST /proposals -> ProposalService
    |                                        |
    |  1. 제안서 생성 요청                      |
    | -------------------------------------->|
    |                                        | 2. 사용자/회사/공고 검증
    |                                        | 3. proposals 레코드 생성 (status=generating)
    |                                        | 4. 빈 sections 레코드 생성
    |  <-------------------------------------|
    |  5. 201 응답 (proposalId)               |
    |                                        |
    |  6. SSE 연결                             |
    |  GET /proposals/{id}/generate/stream   |
    | -------------------------------------->|
    |                                        |
    |                                ProposalGeneratorService
    |                                        |
    |  event: start                          | 7. 컨텍스트 구성 (bid + company)
    |  <-------------------------------------|
    |                                        |
    |  event: progress (17%)                 | 8. section_overview.j2 렌더링
    |  <-------------------------------------|
    |                                        | 9. Claude API 호출 (스트리밍)
    |  event: section (overview)             | 10. DB 저장
    |  <-------------------------------------|
    |                                        |
    |  event: progress (33%)                 | 11. section_technical.j2 렌더링
    |  <-------------------------------------|
    |                                        | 12. Claude API 호출
    |  event: section (technical)            | 13. DB 저장
    |  <-------------------------------------|
    |                                        |
    |  ... (methodology, schedule, org, budget) ...
    |                                        |
    |  event: complete                       | 14. 제안서 완료 처리
    |  <-------------------------------------| 15. status -> ready
    |                                        | 16. 버전 스냅샷 저장
    |  SSE 연결 종료                           | 17. 알림 발송 (스텁)
```

### 9.2 개별 섹션 재생성 흐름

```
사용자 -> Frontend -> POST /proposals/{id}/sections/{key}/regenerate
    |                                        |
    | -------------------------------------->|
    |                          ProposalGeneratorService
    |                                        | 1. 기존 컨텍스트 재구성
    |                                        | 2. custom_instructions 반영
    |                                        | 3. Claude API 호출
    |                                        | 4. 섹션 내용 갱신
    |  <-------------------------------------|
    |  200 응답 (갱신된 섹션 내용)               |
```

---

## 10. 영향 범위

### 10.1 수정 필요 파일

| 파일 | 변경 내용 |
|------|----------|
| backend/src/api/v1/proposals.py | 스텁 -> 실제 API 구현 |
| backend/src/models/__init__.py | Proposal, ProposalSection, ProposalVersion import 추가 |
| backend/src/config.py | Claude API 관련 설정 추가 (모델명, 타임아웃, max_tokens) |

### 10.2 신규 생성 파일

| 파일 | 설명 |
|------|------|
| backend/src/models/proposal.py | Proposal 모델 |
| backend/src/models/proposal_section.py | ProposalSection 모델 |
| backend/src/models/proposal_version.py | ProposalVersion 모델 |
| backend/src/schemas/proposal.py | 제안서 관련 Pydantic 스키마 |
| backend/src/services/proposal_service.py | 제안서 관리 서비스 |
| backend/src/services/proposal_generator_service.py | AI 생성 서비스 |
| backend/src/services/proposal_export_service.py | 다운로드 서비스 |
| backend/src/templates/prompts/base_system.j2 | 공통 시스템 프롬프트 |
| backend/src/templates/prompts/section_overview.j2 | 사업 개요 프롬프트 |
| backend/src/templates/prompts/section_technical.j2 | 기술 제안 프롬프트 |
| backend/src/templates/prompts/section_methodology.j2 | 수행 방법론 프롬프트 |
| backend/src/templates/prompts/section_schedule.j2 | 추진 일정 프롬프트 |
| backend/src/templates/prompts/section_organization.j2 | 조직 구성 프롬프트 |
| backend/src/templates/prompts/section_budget.j2 | 예산 프롬프트 |

---

## 11. 성능 설계

### 11.1 인덱스 계획

```sql
-- 제안서 조회 (ERD 참조)
CREATE INDEX idx_proposals_user ON proposals(user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_proposals_bid ON proposals(bid_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_proposals_status ON proposals(status) WHERE deleted_at IS NULL;

-- 제안서 목록 페이지네이션 (복합 인덱스)
CREATE INDEX idx_proposals_user_updated ON proposals(user_id, updated_at DESC)
    WHERE deleted_at IS NULL;

-- 섹션 조회
CREATE INDEX idx_proposal_sections_proposal ON proposal_sections(proposal_id);
CREATE UNIQUE INDEX idx_proposal_sections_unique ON proposal_sections(proposal_id, section_key);

-- 버전 조회
CREATE INDEX idx_proposal_versions_proposal ON proposal_versions(proposal_id);
```

### 11.2 Claude API 최적화

| 설정 | 값 | 근거 |
|------|-----|------|
| 모델 | claude-sonnet-4-6 | 비용/성능 균형 |
| max_tokens | 4096 (섹션당) | 한 섹션 평균 500~1000단어 |
| 타임아웃 | 30초 (섹션당) | 6섹션 * 30초 = 최대 3분 (AC 충족) |
| 스트리밍 | true | SSE 실시간 전달 |

### 11.3 캐싱 전략

```
# AI 생성 Rate Limit (Redis)
proposal_gen:{user_id}:count -> {count} (TTL: 1시간)

# 프롬프트 템플릿 캐시 (메모리)
Jinja2 Environment(auto_reload=False)  # 프로덕션에서 파일 변경 감지 비활성화
```

---

## 12. 에러 코드 요약

### 기존 에러 코드 (api-conventions.md)

| 코드 | HTTP Status | 메시지 |
|------|-------------|--------|
| PROPOSAL_001 | 404 | 제안서를 찾을 수 없습니다. |
| PROPOSAL_002 | 403 | 제안서 생성 권한이 없습니다. |
| PROPOSAL_003 | 500 | 제안서 생성 중 오류가 발생했습니다. |
| PROPOSAL_004 | 504 | AI 생성 시간이 초과되었습니다. |
| PROPOSAL_005 | 404 | 제안서 버전을 찾을 수 없습니다. |

### 신규 에러 코드 (F-03 추가)

| 코드 | HTTP Status | 메시지 |
|------|-------------|--------|
| PROPOSAL_006 | 404 | 섹션을 찾을 수 없습니다. |
| PROPOSAL_007 | 400 | 제안서가 생성 중입니다. (중복 생성 방지) |
| PROPOSAL_008 | 400 | RFP 파싱에 실패했습니다. 수동 입력을 사용해주세요. |

---

## 13. 설정 변경

### backend/src/config.py 추가 필드

```python
class Settings(BaseSettings):
    # ... 기존 설정 ...

    # Claude API (F-03)
    anthropic_api_key: str = ""  # 이미 존재
    claude_model: str = "claude-sonnet-4-6"
    claude_max_tokens_per_section: int = 4096
    claude_timeout_seconds: int = 30  # 섹션당 타임아웃

    # 제안서 생성
    proposal_max_sections: int = 6
    proposal_generation_timeout: int = 180  # 전체 생성 타임아웃 (3분)
    proposal_rate_limit_per_hour: int = 10  # 시간당 생성 한도

    # 프롬프트 템플릿
    prompt_template_dir: str = "src/templates/prompts"
```

---

## 14. 의존성 추가

### requirements.txt 추가

```
anthropic>=0.39.0          # Claude API 클라이언트
jinja2>=3.1.0              # 프롬프트 템플릿
python-docx>=1.1.0         # Word 파일 생성
reportlab>=4.1.0           # PDF 파일 생성
markdown>=3.5.0            # Markdown 파싱 (DOCX/PDF 변환용)
```

---

## 변경 이력

| 날짜 | 변경 내용 | 이유 |
|------|----------|------|
| 2026-03-08 | 초기 변경 설계 | F-03 기능 구현 시작 |
