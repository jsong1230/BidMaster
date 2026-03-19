# F-03 제안서 AI 초안 생성 -- UI 명세서

## 참조
- 설계서: docs/specs/F-03-proposal-generation/design.md
- 네비게이션: docs/system/navigation.md
- 디자인 시스템: docs/system/design-system.md

---

## 1. 페이지 구성

| 경로 | 페이지명 | 설명 |
|------|----------|------|
| `/proposals` | 제안서 목록 | 사용자의 제안서 목록 조회 |
| `/proposals/new?bidId={id}` | 제안서 생성 | 공고 선택 → 제안서 생성 |
| `/proposals/{id}` | 제안서 상세 | 제안서 내용 조회 및 편집 |
| `/proposals/{id}/generate` | 제안서 생성 진행 | SSE 스트리밍 진행 상황 |

---

## 2. 제안서 목록 페이지 (`/proposals`)

### 레이아웃
```
┌─────────────────────────────────────────────────────────────┐
│ [사이드바]  │  제안서 관리                    [+ 새 제안서] │
│             │──────────────────────────────────────────────│
│             │  [상태 필터: 전체 | 생성중 | 완료 | 제출완료] │
│             │──────────────────────────────────────────────│
│             │  ┌────────────────────────────────────────┐ │
│             │  │ 📄 제안서 제목                          │ │
│             │  │ 공고명: xxx 공고                        │ │
│             │  │ 상태: ✅완료 | 6섹션 | 4,500자          │ │
│             │  │ 2026-03-08 생성                         │ │
│             │  └────────────────────────────────────────┘ │
│             │  ┌────────────────────────────────────────┐ │
│             │  │ 📄 또 다른 제안서...                    │ │
│             │  └────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 컴포넌트
- `ProposalListPage`: 메인 페이지 컴포넌트
- `ProposalCard`: 개별 제안서 카드
- `StatusFilter`: 상태 필터 탭
- `EmptyState`: 제안서 없을 때 표시

### 상태 표시
| status | 라벨 | 색상 | 아이콘 |
|--------|------|------|--------|
| draft | 초안 | gray | 📝 |
| generating | 생성중 | blue | ⏳ |
| ready | 완료 | green | ✅ |
| submitted | 제출완료 | purple | 📤 |

---

## 3. 제안서 생성 페이지 (`/proposals/new`)

### 시나리오 A: bidId 파라미터 있음
```
┌─────────────────────────────────────────────────────────────┐
│ 제안서 생성                                                  │
│─────────────────────────────────────────────────────────────│
│                                                              │
│ 선택된 공고                                                  │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 📋 2026년 정보시스템 고도화 사업                         │ │
│ │ 발주기관: OO부처 | 예산: 5억원 | 마감: D-7              │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                              │
│ 제안서 제목 (선택)                                           │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ [자동 생성됨]                                           │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                              │
│ 생성할 섹션 선택                                             │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ ☑ 사업 개요   ☑ 기술 제안   ☑ 수행 방법론              │ │
│ │ ☑ 추진 일정   ☑ 조직 구성   ☑ 예산                     │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                              │
│ 추가 지시사항 (선택)                                         │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ [특별히 강조하고 싶은 내용을 입력하세요...]              │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                              │
│                                    [취소] [제안서 생성하기] │
└─────────────────────────────────────────────────────────────┘
```

### 시나리오 B: bidId 없음 → 공고 선택 모달
```
┌─────────────────────────────────────────────────────────────┐
│ 공고 선택                                         [X 닫기] │
│─────────────────────────────────────────────────────────────│
│ 🔍 [공고명 또는 기관명으로 검색...]                          │
│─────────────────────────────────────────────────────────────│
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 📋 공고명 A                          [선택]             │ │
│ │ 발주기관 | 예산 | 마감 D-3                              │ │
│ ├────────────────────────────────────────────────────────┤ │
│ │ 📋 공고명 B                          [선택]             │ │
│ │ 발주기관 | 예산 | 마감 D-7                              │ │
│ └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 컴포넌트
- `ProposalCreatePage`: 메인 생성 페이지
- `BidSelectModal`: 공고 선택 모달
- `SectionSelector`: 섹션 다중 선택
- `CustomInstructionsInput`: 추가 지시사항 입력

---

## 4. 제안서 생성 진행 페이지 (`/proposals/{id}/generate`)

### SSE 스트리밍 진행 UI
```
┌─────────────────────────────────────────────────────────────┐
│ 제안서 생성 중...                                            │
│─────────────────────────────────────────────────────────────│
│                                                              │
│         ╭───────────────────────────────────────╮          │
│         │                                       │          │
│         │           🤖 AI가 제안서를            │          │
│         │           작성하고 있습니다           │          │
│         │                                       │          │
│         │         [████████░░░░░░░░] 50%        │          │
│         │                                       │          │
│         ╰───────────────────────────────────────╯          │
│                                                              │
│ 진행 상황                                                    │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ ✅ 사업 개요 (520자)                                   │ │
│ │ ✅ 기술 제안 (680자)                                   │ │
│ │ ✅ 수행 방법론 (750자)                                 │ │
│ │ ⏳ 추진 일정 생성 중...                                │ │
│ │ ⏳ 조직 구성 대기 중                                   │ │
│ │ ⏳ 예산 대기 중                                        │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                              │
│                            [생성 취소]                       │
└─────────────────────────────────────────────────────────────┘
```

### 완료 화면
```
┌─────────────────────────────────────────────────────────────┐
│ ✅ 제안서 생성 완료!                                         │
│─────────────────────────────────────────────────────────────│
│                                                              │
│         ╭───────────────────────────────────────╮          │
│         │           🎉                           │          │
│         │                                       │          │
│         │     제안서가 성공적으로 생성되었습니다  │          │
│         │                                       │          │
│         │     총 6개 섹션 | 4,500자             │          │
│         ╰───────────────────────────────────────╯          │
│                                                              │
│           [제안서 보기]    [다운로드]                        │
└─────────────────────────────────────────────────────────────┘
```

### 컴포넌트
- `ProposalGeneratePage`: SSE 연결 + 진행 상황
- `GenerationProgress`: 프로그레스 바 + 상태
- `SectionProgressList`: 섹션별 진행 상황
- `GenerationComplete`: 완료 화면

### SSE 이벤트 처리
```typescript
// 이벤트 타입
type SSEEvent =
  | { event: 'start'; data: { proposalId: string; totalSections: number } }
  | { event: 'progress'; data: { sectionKey: string; percent: number } }
  | { event: 'section'; data: { sectionKey: string; title: string; content: string; wordCount: number } }
  | { event: 'complete'; data: { totalSections: number; totalWordCount: number } }
  | { event: 'error'; data: { code: string; message: string } };
```

---

## 5. 제안서 상세 페이지 (`/proposals/{id}`)

### 레이아웃
```
┌─────────────────────────────────────────────────────────────┐
│ [사이드바]  │  📄 2026년 정보시스템 고도화 사업 제안서       │
│             │  상태: ✅완료 | v1 | 12p | 4,500자            │
│             │──────────────────────────────────────────────│
│             │  [다운로드 ▼] [섹션 재생성] [버전 관리]       │
│             │──────────────────────────────────────────────│
│             │                                                 │
│             │  ┌─ 섹션 네비게이션 ────┐  ┌─ 본문 ─────────┐│
│             │  │ 1. 사업 개요      ▶ │  │                ││
│             │  │ 2. 기술 제안      ▶ │  │ # 사업 개요    ││
│             │  │ 3. 수행 방법론    ▶ │  │                ││
│             │  │ 4. 추진 일정      ▶ │  │ 사업의 배경... ││
│             │  │ 5. 조직 구성      ▶ │  │                ││
│             │  │ 6. 예산          ▶ │  │ ## 목표        ││
│             │  └────────────────────┘  │ ...            ││
│             │                          │                ││
│             │                          └────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 섹션 상세 (확장 시)
```
┌─────────────────────────────────────────────────────────────┐
│ 1. 사업 개요                                     [AI 재생성]│
│─────────────────────────────────────────────────────────────│
│ # 사업 개요                                                  │
│                                                              │
│ ## 1. 사업의 배경 및 필요성                                  │
│                                                              │
│ 최근 디지털 전환이 가속화됨에 따라...                        │
│                                                              │
│ ## 2. 사업 목표                                              │
│                                                              │
│ 본 사업의 주요 목표는 다음과 같습니다...                      │
│                                                              │
│ ...                                                          │
│                                                              │
│ ──────────────────────────────────────────────────────────  │
│ AI 생성됨 | 520자 | 2026-03-08 10:01                        │
└─────────────────────────────────────────────────────────────┘
```

### 컴포넌트
- `ProposalDetailPage`: 메인 상세 페이지
- `ProposalHeader`: 제목, 상태, 액션 버튼
- `SectionNavigation`: 섹션 네비게이션 (클릭 시 스크롤)
- `ProposalSection`: 개별 섹션 내용 표시
- `DownloadButton`: DOCX/PDF 다운로드
- `RegenerateModal`: 섹션 재생성 모달

---

## 6. 다운로드 기능

### 다운로드 드롭다운
```
┌─────────────────────┐
│ [다운로드 ▼]        │
│─────────────────────│
│ 📄 Word (.docx)     │
│ 📄 PDF (.pdf)       │
└─────────────────────┘
```

### 다운로드 진행 중
```
┌─────────────────────────────┐
│ ⏳ 파일 생성 중...          │
│ [████████████░░░░░░] 65%    │
└─────────────────────────────┘
```

---

## 7. 섹션 재생성 모달

```
┌─────────────────────────────────────────────────────────────┐
│ 섹션 재생성                                       [X 닫기] │
│─────────────────────────────────────────────────────────────│
│                                                              │
│ 대상 섹션: 수행 방법론                                       │
│                                                              │
│ 추가 지시사항                                                │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 예: Agile 방법론을 더 구체적으로 설명해주세요           │ │
│ │                                                       │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                              │
│                              [취소] [재생성하기]             │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. 상태 관리 (Zustand)

```typescript
// stores/proposalStore.ts
interface ProposalState {
  // 목록
  proposals: Proposal[];
  isLoading: boolean;
  filters: { status?: string; bidId?: string };

  // 상세
  currentProposal: ProposalDetail | null;
  sections: ProposalSection[];

  // 생성 진행
  isGenerating: boolean;
  generationProgress: GenerationProgress | null;

  // 액션
  fetchProposals: (filters?: Filters) => Promise<void>;
  fetchProposal: (id: string) => Promise<void>;
  createProposal: (data: CreateProposalRequest) => Promise<Proposal>;
  connectGenerationStream: (proposalId: string) => void;
  disconnectGenerationStream: () => void;
  regenerateSection: (proposalId: string, sectionKey: string, instructions?: string) => Promise<void>;
  downloadProposal: (proposalId: string, format: 'docx' | 'pdf') => Promise<void>;
}
```

---

## 9. API 클라이언트

```typescript
// lib/api/proposal.ts
export const proposalApi = {
  // 목록/상세
  list: (params: ListParams) => api.get('/proposals', { params }),
  get: (id: string) => api.get(`/proposals/${id}`),

  // 생성
  create: (data: CreateProposalRequest) => api.post('/proposals', data),

  // SSE 스트리밍
  connectGenerateStream: (proposalId: string, token: string) =>
    new EventSource(`${API_URL}/proposals/${proposalId}/generate/stream?token=${token}`),

  // 섹션 재생성
  regenerateSection: (proposalId: string, sectionKey: string, data: RegenerateRequest) =>
    api.post(`/proposals/${proposalId}/sections/${sectionKey}/regenerate`, data),

  // 다운로드
  download: (proposalId: string, format: 'docx' | 'pdf') =>
    api.get(`/proposals/${proposalId}/download`, { params: { format }, responseType: 'blob' }),
};
```

---

## 10. 타입 정의

```typescript
// types/proposal.ts
export type ProposalStatus = 'draft' | 'generating' | 'ready' | 'submitted';

export interface Proposal {
  id: string;
  bidId: string;
  bidTitle: string | null;
  title: string;
  status: ProposalStatus;
  version: number;
  pageCount: number;
  wordCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface ProposalDetail extends Proposal {
  companyId: string;
  evaluationChecklist: Record<string, unknown>;
  sections: ProposalSection[];
  generatedAt: string | null;
}

export interface ProposalSection {
  id: string;
  sectionKey: SectionKey;
  title: string;
  order: number;
  content: string | null;
  wordCount: number;
  isAiGenerated: boolean;
  metadata: Record<string, unknown>;
  updatedAt: string;
}

export type SectionKey = 'overview' | 'technical' | 'methodology' | 'schedule' | 'organization' | 'budget';

export const SECTION_LABELS: Record<SectionKey, string> = {
  overview: '사업 개요',
  technical: '기술 제안',
  methodology: '수행 방법론',
  schedule: '추진 일정',
  organization: '조직 구성',
  budget: '예산',
};
```

---

## 11. 에러 처리

| 에러 코드 | 상황 | UI 처리 |
|-----------|------|---------|
| AUTH_002 | 미인증 | 로그인 페이지로 리다이렉트 |
| BID_001 | 공고 없음 | "공고를 찾을 수 없습니다" 알림 |
| BID_002 | 공고 마감 | "이미 마감된 공고입니다" 알림 |
| COMPANY_001 | 회사 미등록 | 회사 프로필 등록 유도 모달 |
| PROPOSAL_003 | AI 생성 오류 | "생성 중 오류가 발생했습니다" + 재시도 버튼 |
| PROPOSAL_004 | 타임아웃 | "생성 시간이 초과되었습니다" + 재시도 버튼 |

---

## 12. 파일 구조

```
frontend/src/
├── app/(main)/
│   └── (proposals)/
│       ├── proposals/
│       │   ├── page.tsx              # 목록
│       │   ├── new/
│       │   │   └── page.tsx          # 생성
│       │   └── [id]/
│       │       ├── page.tsx          # 상세
│       │       └── generate/
│       │           └── page.tsx      # SSE 진행
│       └── layout.tsx
├── components/proposals/
│   ├── ProposalCard.tsx
│   ├── ProposalListPage.tsx
│   ├── ProposalCreatePage.tsx
│   ├── ProposalDetailPage.tsx
│   ├── ProposalGeneratePage.tsx
│   ├── SectionNavigation.tsx
│   ├── ProposalSection.tsx
│   ├── RegenerateModal.tsx
│   └── BidSelectModal.tsx
├── lib/api/
│   └── proposal.ts
├── stores/
│   └── proposalStore.ts
└── types/
    └── proposal.ts
```
