# F-03 제안서 AI 초안 생성 API 스펙

## 개요

공고 분석 + 회사 프로필 기반으로 AI가 섹션별 제안서를 자동 생성하는 API입니다.

**Base URL**: `/api/v1/proposals`

---

## 공통 응답 포맷

```json
{
  "success": true,
  "data": { ... },
  "meta": { ... }
}
```

에러 응답:
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "에러 메시지"
  }
}
```

---

## 에러 코드

| 코드 | HTTP | 설명 |
|------|------|------|
| AUTH_002 | 401 | 인증 토큰이 필요합니다 |
| BID_001 | 404 | 공고를 찾을 수 없습니다 |
| BID_002 | 400 | 공고가 이미 마감되었습니다 |
| COMPANY_001 | 404 | 회사를 찾을 수 없습니다 (미소속 사용자) |
| PROPOSAL_001 | 404 | 제안서를 찾을 수 없습니다 |
| PROPOSAL_002 | 403 | 제안서 접근 권한이 없습니다 |
| PROPOSAL_003 | 500 | 제안서 생성 중 오류가 발생했습니다 |
| PROPOSAL_004 | 504 | AI 생성 시간이 초과되었습니다 |
| PROPOSAL_006 | 404 | 섹션을 찾을 수 없습니다 |
| PROPOSAL_007 | 400 | 제안서가 이미 생성 중입니다 |
| RATE_LIMIT_002 | 429 | AI 생성 요청 한도를 초과했습니다 |
| VALIDATION_001 | 400 | 입력값 유효성 실패 |

---

## 엔드포인트

### 1. 제안서 생성

```
POST /api/v1/proposals
```

**인증**: Bearer Token 필수

**요청 본문**:

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| bidId | UUID | Y | 공고 ID |
| title | string | N | 제안서 제목 (미입력 시 공고명 기반 자동 생성) |
| sections | string[] | N | 생성할 섹션 키 목록 (기본: 전체 6개) |
| customInstructions | string | N | 추가 지시사항 (최대 10000자) |

**sections 유효 값**:
- `overview` (사업 개요)
- `technical` (기술 제안)
- `methodology` (수행 방법론)
- `schedule` (추진 일정)
- `organization` (조직 구성)
- `budget` (예산)

**요청 예시**:
```json
{
  "bidId": "550e8400-e29b-41d4-a716-446655440000",
  "title": "2026년 정보시스템 고도화 사업 제안서",
  "sections": ["overview", "technical", "methodology", "schedule", "organization", "budget"],
  "customInstructions": "클라우드 네이티브 아키텍처를 강조해주세요"
}
```

**성공 응답** (201 Created):
```json
{
  "success": true,
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "bidId": "550e8400-e29b-41d4-a716-446655440000",
    "title": "2026년 정보시스템 고도화 사업 제안서",
    "status": "generating",
    "sections": ["overview", "technical", "methodology", "schedule", "organization", "budget"],
    "createdAt": "2026-03-08T10:00:00+00:00"
  }
}
```

**에러 응답**:
- `401 AUTH_002`: 인증 토큰 없음
- `400 BID_002`: 공고 마감
- `404 BID_001`: 공고 없음
- `404 COMPANY_001`: 회사 미소속
- `429 RATE_LIMIT_002`: 생성 한도 초과

---

### 2. 제안서 AI 생성 SSE 스트리밍

```
GET /api/v1/proposals/{proposal_id}/generate/stream
```

**인증**: Query Parameter로 토큰 전달 (SSE 특성상 헤더 불가)

**쿼리 파라미터**:

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| token | string | Y | Bearer Token |

**요청 헤더**:
```
Accept: text/event-stream
```

**SSE 이벤트 타입**:

| Event | 설명 | 발생 횟수 |
|-------|------|-----------|
| start | 생성 시작 | 1회 |
| progress | 진행 상황 | 섹션 수만큼 |
| section | 섹션 생성 완료 | 섹션 수만큼 |
| complete | 전체 완료 | 1회 |
| error | 오류 발생 | 0~1회 |

**이벤트 상세**:

시작:
```
event: start
data: {"proposalId": "uuid", "totalSections": 6, "message": "제안서 생성을 시작합니다."}
```

진행:
```
event: progress
data: {"sectionKey": "overview", "percent": 17, "message": "사업 개요 섹션 생성 중..."}
```

섹션 완료:
```
event: section
data: {"sectionKey": "overview", "title": "사업 개요", "content": "# 사업 개요\n\n본 제안서는...", "wordCount": 520, "order": 1}
```

전체 완료:
```
event: complete
data: {"proposalId": "uuid", "totalSections": 6, "totalWordCount": 4500, "generatedAt": "2026-03-08T10:03:00+00:00"}
```

오류:
```
event: error
data: {"code": "PROPOSAL_004", "message": "AI 생성 시간이 초과되었습니다."}
```

**에러 응답**:
- `404 PROPOSAL_001`: 제안서 없음
- `403 PROPOSAL_002`: 소유자 아님

**클라이언트 연결 예시**:
```typescript
const eventSource = new EventSource(
  `/api/v1/proposals/${proposalId}/generate/stream?token=${accessToken}`
);

eventSource.addEventListener('start', (e) => {
  const data = JSON.parse(e.data);
  showStartMessage(data.message);
});

eventSource.addEventListener('progress', (e) => {
  const data = JSON.parse(e.data);
  updateProgressBar(data.percent, data.message);
});

eventSource.addEventListener('section', (e) => {
  const data = JSON.parse(e.data);
  renderSection(data);
});

eventSource.addEventListener('complete', (e) => {
  const data = JSON.parse(e.data);
  showCompletionNotice(data);
  eventSource.close();
});

eventSource.addEventListener('error', (e) => {
  if (e.data) {
    const data = JSON.parse(e.data);
    showError(data.message);
  }
  eventSource.close();
});
```

---

### 3. 개별 섹션 재생성

```
POST /api/v1/proposals/{proposal_id}/sections/{section_key}/regenerate
```

**인증**: Bearer Token 필수

**경로 파라미터**:
- `proposal_id` (UUID): 제안서 ID
- `section_key` (string): 섹션 키 (overview, technical, methodology, schedule, organization, budget)

**요청 본문**:

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| customInstructions | string | N | 재생성 지시사항 |

**요청 예시**:
```json
{
  "customInstructions": "더 구체적인 수행 방법론을 포함하고 애자일 방법론을 강조해주세요"
}
```

**성공 응답** (200 OK):
```json
{
  "success": true,
  "data": {
    "sectionKey": "methodology",
    "title": "수행 방법론",
    "content": "# 수행 방법론\n\n## 1. 애자일 기반 수행 체계\n\n...",
    "wordCount": 680,
    "isAiGenerated": true,
    "updatedAt": "2026-03-08T10:10:00+00:00"
  }
}
```

**에러 응답**:
- `401 AUTH_002`: 인증 토큰 없음
- `403 PROPOSAL_002`: 소유자 아님
- `404 PROPOSAL_001`: 제안서 없음
- `404 PROPOSAL_006`: 섹션 없음
- `400 PROPOSAL_007`: 현재 생성 중 (status='generating')

---

### 4. 제안서 목록 조회

```
GET /api/v1/proposals
```

**인증**: Bearer Token 필수

**쿼리 파라미터**:

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| page | int | 1 | 페이지 번호 |
| pageSize | int | 20 | 페이지 크기 (최대 100) |
| status | string | - | 필터: draft/generating/ready/submitted |
| bidId | UUID | - | 특정 공고의 제안서 필터 |
| sortBy | string | updatedAt | 정렬: updatedAt/createdAt/title |
| sortOrder | string | desc | 정렬 방향: asc/desc |

**성공 응답** (200 OK):
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
        "generatedAt": "2026-03-08T10:03:00+00:00",
        "createdAt": "2026-03-08T10:00:00+00:00",
        "updatedAt": "2026-03-08T10:03:00+00:00"
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

---

### 5. 제안서 상세 조회

```
GET /api/v1/proposals/{proposal_id}
```

**인증**: Bearer Token 필수

**성공 응답** (200 OK):
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
      "technical": {"items": ["기술 이해도", "수행 방법론"], "score": 85},
      "price": {"items": ["가격 적정성"], "score": 20}
    },
    "pageCount": 12,
    "wordCount": 4500,
    "sections": [
      {
        "id": "section-uuid",
        "sectionKey": "overview",
        "title": "사업 개요",
        "order": 1,
        "content": "# 사업 개요\n\n...",
        "wordCount": 520,
        "isAiGenerated": true,
        "metadata": {
          "referencedPerformances": ["perf-uuid-1", "perf-uuid-2"]
        },
        "updatedAt": "2026-03-08T10:01:00+00:00"
      },
      {
        "id": "section-uuid-2",
        "sectionKey": "technical",
        "title": "기술 제안",
        "order": 2,
        "content": "# 기술 제안\n\n...",
        "wordCount": 850,
        "isAiGenerated": true,
        "metadata": {},
        "updatedAt": "2026-03-08T10:01:30+00:00"
      }
    ],
    "generatedAt": "2026-03-08T10:03:00+00:00",
    "createdAt": "2026-03-08T10:00:00+00:00",
    "updatedAt": "2026-03-08T10:03:00+00:00"
  }
}
```

**에러 응답**:
- `401 AUTH_002`: 인증 토큰 없음
- `403 PROPOSAL_002`: 소유자 아님
- `404 PROPOSAL_001`: 제안서 없음

---

### 6. 제안서 다운로드

```
GET /api/v1/proposals/{proposal_id}/download
```

**인증**: Bearer Token 필수

**쿼리 파라미터**:

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| format | string | docx | 파일 형식: docx / pdf |

**성공 응답** (200 OK):
- Content-Type: `application/vnd.openxmlformats-officedocument.wordprocessingml.document` (docx)
- Content-Type: `application/pdf` (pdf)
- Content-Disposition: `attachment; filename="제안서_제목.docx"`

**에러 응답**:
- `401 AUTH_002`: 인증 토큰 없음
- `403 PROPOSAL_002`: 소유자 아님
- `404 PROPOSAL_001`: 제안서 없음
- `400 VALIDATION_001`: 잘못된 format 값

---

## 섹션 정의

| section_key | title | order | 포함 내용 |
|-------------|-------|-------|-----------|
| overview | 사업 개요 | 1 | 사업 배경, 목표, 기대 효과, 제안 범위 |
| technical | 기술 제안 | 2 | 기술적 접근 방법, 시스템 아키텍처, 핵심 기술 |
| methodology | 수행 방법론 | 3 | 수행 체계, 단계별 방법론, 품질 관리 |
| schedule | 추진 일정 | 4 | WBS, 마일스톤, 단계별 일정 |
| organization | 조직 구성 | 5 | PM/PL 구성, 투입 인력, 조직도 |
| budget | 예산 | 6 | 비용 산출, 인건비, 경비 내역 |

---

## Rate Limit

| 대상 | 제한 | 윈도우 |
|------|------|--------|
| AI 제안서 생성 (POST /proposals) | 10회 | 1시간 |
| 섹션 재생성 | 30회 | 1시간 |
| 일반 조회 API | 100회 | 1분 |

---

## AI 생성 성능 기준

| 항목 | 기준 |
|------|------|
| 10페이지 기준 전체 생성 시간 | 3분 이내 |
| 섹션당 생성 시간 | 30초 이내 |
| Word/PDF 다운로드 시간 | 10초 이내 |
