# F-05 제안서 편집기 — 기술 설계서

## 1. 참조

- **인수조건**: docs/project/features.md #F-05
- **시스템 설계**: docs/system/system-design.md
- **ERD**: docs/system/erd.md
- **API 컨벤션**: docs/system/api-conventions.md
- **디자인 시스템**: docs/system/design-system.md
- **의존 기능**: F-03 (제안서 AI 초안 생성) — 완료

---

## 2. 아키텍처 결정

### 결정 1: 리치텍스트 에디터 선택

- **선택지**:
  - A) **TipTap** — ProseMirror 기반, 모듈화된 아키텍처, Next.js 호환성 우수
  - B) Lexical — Meta 개발, 경량화, 페이스북 레거시
  - C) Slate — 완전 커스터마이징, 학습 곡선 높음
  - D) Quill — 레거시, 유지보수 이슈

- **결정**: **TipTap (Option A)**

- **근거**:
  1. **Next.js 14 호환성**: App Router와 완벽하게 호환, SSR 이슈 없음
  2. **모듈화**: 필요한 기능만 추가 가능 (번들 크기 최적화)
  3. **한국어 지원**: IME 입력 문제 없음
  4. **표/이미지 지원**: Table, Image 확장 기본 제공
  5. **협업 준비**: Y.js 통합으로 F-11 팀 협업 확장 가능
  6. **마크다운 호환**: Markdown 확장으로 기존 F-03 콘텐츠 그대로 활용

### 결정 2: 자동 저장 전략

- **선택지**:
  - A) Debounce 30초 + 수동 저장 버튼
  - B) Debounce 5초 + 백그라운드 자동 저장
  - C) Throttle 10초 + 변경 감지

- **결정**: **Option A — Debounce 30초 + 수동 저장**

- **근거**:
  1. 인수조건에 명시된 30초 기준 준수
  2. 불필요한 API 호출 최소화
  3. 사용자에게 "저장됨" 상태 명확히 표시
  4. 수동 저장으로 즉시 저장 가능

### 결정 3: 콘텐츠 포맷

- **선택지**:
  - A) Markdown 유지 (기존 F-03 방식)
  - B) HTML로 전환 (리치텍스트 표현)
  - C) JSON (ProseMirror Document)

- **결정**: **HTML 우선, Markdown 역호환**

- **근거**:
  1. 리치텍스트 표현력 확보 (표, 이미지, 서식)
  2. 기존 Markdown 콘텐츠는 TipTap이 자동 변환
  3. DB `content` 컬럼이 TEXT 타입으로 충분
  4. 다운로드 시 HTML → DOCX/PDF 변환 용이

### 결정 4: 버전 관리 전략

- **선택지**:
  - A) 수동 스냅샷 (사용자가 "버전 저장" 클릭)
  - B) 자동 스냅샷 (N회 편집마다)
  - C) 시간 기반 스냅샷 (1시간마다)

- **결정**: **Option A — 수동 스냅샷 + 자동 버전 증가**

- **근거**:
  1. F-03에서 이미 `proposal_versions` 테이블 존재
  2. 사용자가 의미 있는 버전만 저장 (혼란 방지)
  3. 버전 복원 API 이미 구현됨

---

## 3. API 설계

### 3.1 기존 API (F-03) 재사용

| API | Method | 용도 | 상태 |
|-----|--------|------|------|
| `/api/v1/proposals/{id}` | GET | 제안서 상세 조회 | 구현됨 |
| `/api/v1/proposals/{id}` | PATCH | 제안서 기본 정보 수정 | 구현됨 |
| `/api/v1/proposals/{id}/sections/{key}` | PATCH | 섹션 내용 수정 | 구현됨 |
| `/api/v1/proposals/{id}/sections/{key}/regenerate` | POST | 섹션 AI 재생성 | 구현됨 |
| `/api/v1/proposals/{id}/versions` | POST | 버전 스냅샷 생성 | 구현됨 |
| `/api/v1/proposals/{id}/versions/{n}/restore` | POST | 버전 복원 | 구현됨 |

### 3.2 신규 API (F-05 추가)

#### PATCH /api/v1/proposals/{id}/auto-save

- **목적**: 자동 저장 (debounce)
- **인증**: 필요 (JWT)
- **Request Body**:
  ```json
  {
    "sections": [
      {
        "sectionKey": "overview",
        "content": "<p>HTML 콘텐츠...</p>",
        "wordCount": 520
      }
    ]
  }
  ```
- **Response**:
  ```json
  {
    "success": true,
    "data": {
      "savedAt": "2026-03-20T10:30:00Z",
      "wordCount": 520
    }
  }
  ```
- **에러 케이스**:

  | 코드 | 상황 |
  |------|------|
  | PROPOSAL_001 | 제안서를 찾을 수 없음 |
  | PERMISSION_002 | 리소스 소유자가 아님 |

#### POST /api/v1/proposals/{id}/validate

- **목적**: 제출 전 검증 (필수 항목, 분량 제한)
- **인증**: 필요 (JWT)
- **Request Body**:
  ```json
  {
    "pageLimit": 30
  }
  ```
- **Response**:
  ```json
  {
    "success": true,
    "data": {
      "isValid": false,
      "warnings": [
        {
          "type": "required_field",
          "section": "technical",
          "message": "기술 제안 섹션이 비어 있습니다."
        },
        {
          "type": "page_limit",
          "current": 35,
          "limit": 30,
          "message": "페이지 제한을 초과했습니다. (현재 35페이지 / 제한 30페이지)"
        }
      ],
      "stats": {
        "totalWordCount": 8500,
        "estimatedPages": 35,
        "sectionStats": [
          { "sectionKey": "overview", "wordCount": 1200, "isEmpty": false },
          { "sectionKey": "technical", "wordCount": 0, "isEmpty": true }
        ]
      }
    }
  }
  ```

#### PATCH /api/v1/proposals/{id}/evaluation-checklist

- **목적**: 평가 기준 체크리스트 업데이트
- **인증**: 필요 (JWT)
- **Request Body**:
  ```json
  {
    "checklist": {
      "technical_capability": { "checked": true, "weight": 30 },
      "price_competitiveness": { "checked": true, "weight": 25 },
      "past_performance": { "checked": false, "weight": 20 },
      "project_schedule": { "checked": true, "weight": 15 },
      "organization": { "checked": false, "weight": 10 }
    }
  }
  ```
- **Response**:
  ```json
  {
    "success": true,
    "data": {
      "checklist": { ... },
      "achievementRate": 70,
      "updatedAt": "2026-03-20T10:30:00Z"
    }
  }
  ```

---

## 4. DB 설계

### 4.1 기존 테이블 재사용

#### proposals (변경 없음)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| evaluation_checklist | JSONB | 평가 항목 체크리스트 (F-05에서 활용) |

#### proposal_sections (변경 없음)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| content | TEXT | 섹션 내용 (Markdown → HTML 저장 가능) |
| metadata | JSONB | 섹션 메타데이터 (편집 이력 등) |

#### proposal_versions (변경 없음)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| snapshot | JSONB | 전체 섹션 스냅샷 |

### 4.2 신규 컬럼 (선택적)

**섹션 편집 메타데이터 확장** (metadata JSONB 내부):

```json
{
  "lastEditedBy": "user-uuid",
  "editCount": 5,
  "lastEditAt": "2026-03-20T10:30:00Z",
  "format": "html"
}
```

---

## 5. 시퀀스 흐름

### 5.1 편집기 로드

```
사용자 → Frontend (제안서 상세 페이지)
    → API GET /proposals/{id}
    → DB proposals + proposal_sections 조회
    → Frontend (TipTap 에디터 초기화)
    → 각 섹션 content를 TipTap 에디터로 렌더링
```

### 5.2 섹션 편집 및 자동 저장

```
사용자 (섹션 편집)
    → TipTap onChange 트리거
    → debounce 30초 타이머 시작
    → (30초 경과)
    → API PATCH /proposals/{id}/auto-save
    → DB proposal_sections 업데이트
    → Frontend "저장됨" 토스트 표시
```

### 5.3 AI 재생성

```
사용자 (재생성 버튼 클릭)
    → Modal (커스텀 지시사항 입력)
    → API POST /proposals/{id}/sections/{key}/regenerate
    → AI Service (GLM API 호출)
    → DB 섹션 업데이트
    → Frontend (새 콘텐츠로 에디터 갱신)
```

### 5.4 평가 기준 체크

```
사용자 (평가 패널에서 체크박스 토글)
    → API PATCH /proposals/{id}/evaluation-checklist
    → DB proposals.evaluation_checklist 업데이트
    → 달성률 계산 (checked/total * 100)
    → Frontend (달성률 프로그레스바 업데이트)
```

### 5.5 제출 전 검증

```
사용자 (제출 버튼 클릭)
    → API POST /proposals/{id}/validate
    → 검증 로직 실행
        ├─ 필수 섹션 비어있는지 확인
        ├─ 페이지 제한 초과 확인
        └─ 평가 항목 체크 확인
    → 경고 있으면 모달 표시
    → (확인 시) API POST /proposals/{id}/submit
```

---

## 6. 컴포넌트 구조

### 6.1 프론트엔드 디렉토리 구조

```
frontend/src/
├── components/
│   └── proposals/
│       ├── editor/
│       │   ├── ProposalEditor.tsx          # 메인 편집기 컨테이너
│       │   ├── SectionEditor.tsx           # 개별 섹션 에디터
│       │   ├── TipTapEditor.tsx            # TipTap 래퍼 컴포넌트
│       │   ├── EditorToolbar.tsx           # 서식 도구 모음
│       │   ├── TableMenu.tsx               # 표 삽입/편집 메뉴
│       │   ├── ImageUploader.tsx           # 이미지 업로드
│       │   └── AutoSaveIndicator.tsx       # 자동 저장 상태 표시
│       ├── sidebar/
│       │   ├── SectionNavigator.tsx        # 섹션 네비게이션
│       │   ├── EvaluationPanel.tsx         # 평가 기준 체크리스트
│       │   ├── VersionHistory.tsx          # 버전 히스토리
│       │   └── AIPanel.tsx                 # AI 재생성 패널
│       ├── modals/
│       │   ├── RegenerateModal.tsx         # 재생성 모달 (기존)
│       │   ├── ValidationModal.tsx         # 검증 경고 모달
│       │   └── VersionRestoreModal.tsx     # 버전 복원 모달
│       └── hooks/
│           ├── useAutoSave.ts              # 자동 저장 훅
│           ├── useDebounce.ts              # 디바운스 훅
│           └── useEditorState.ts           # 에디터 상태 관리
├── stores/
│   └── editorStore.ts                      # 편집기 상태 스토어
└── lib/
    └── tiptap/
        ├── extensions.ts                   # TipTap 확장 설정
        └── utils.ts                        # 에디터 유틸리티
```

### 6.2 핵심 컴포넌트 설계

#### ProposalEditor.tsx

```tsx
interface ProposalEditorProps {
  proposalId: string;
  initialData: ProposalDetail;
}

// 역할: 전체 편집기 레이아웃, 섹션 간 이동, 자동 저장 관리
```

#### SectionEditor.tsx

```tsx
interface SectionEditorProps {
  section: ProposalSection;
  onUpdate: (content: string) => void;
  onRegenerate: () => void;
}

// 역할: 개별 섹션 편집, TipTap 에디터 래핑
```

#### TipTapEditor.tsx

```tsx
interface TipTapEditorProps {
  content: string;
  onChange: (content: string) => void;
  placeholder?: string;
  readOnly?: boolean;
}

// 역할: TipTap 인스턴스 관리, 확장 로드
```

---

## 7. TipTap 확장 구성

### 7.1 필수 확장

```typescript
import StarterKit from '@tiptap/starter-kit';
import Table from '@tiptap/extension-table';
import TableRow from '@tiptap/extension-table-row';
import TableCell from '@tiptap/extension-table-cell';
import TableHeader from '@tiptap/extension-table-header';
import Image from '@tiptap/extension-image';
import Link from '@tiptap/extension-link';
import TextAlign from '@tiptap/extension-text-align';
import Underline from '@tiptap/extension-underline';
import TextStyle from '@tiptap/extension-text-style';
import Highlight from '@tiptap/extension-highlight';
import Placeholder from '@tiptap/extension-placeholder';
import Markdown from '@tiptap/extension-markdown';

const extensions = [
  StarterKit.configure({
    heading: { levels: [1, 2, 3] },
    bulletList: { keepMarks: true },
    orderedList: { keepMarks: true },
  }),
  Table.configure({ resizable: true }),
  TableRow,
  TableCell,
  TableHeader,
  Image.configure({ inline: true }),
  Link.configure({ openOnClick: false }),
  TextAlign.configure({ types: ['heading', 'paragraph'] }),
  Underline,
  Highlight,
  Placeholder.configure({ placeholder: '내용을 입력하세요...' }),
  Markdown, // 기존 Markdown 콘텐츠 호환
];
```

### 7.2 커스텀 확장 (선택)

- **CharacterCount**: 글자 수 실시간 카운트
- **WordCount**: 단어 수 카운트 (한국어 최적화)
- **SectionBreak**: 섹션 구분선

---

## 8. 성능 설계

### 8.1 에디터 최적화

| 항목 | 전략 |
|------|------|
| 초기 로딩 | 섹션별 지연 로딩 (Intersection Observer) |
| 대용량 문서 | Virtual Scrolling (섹션 10개 이상 시) |
| 이미지 | Lazy Loading + 압축 (WebP 변환) |
| 자동 저장 | Debounce 30초 + 네트워크 실패 시 재시도 |

### 8.2 인덱스 계획

기존 인덱스 충분 (F-03에서 이미 설정됨):

```sql
idx_proposals_user_updated (user_id, updated_at)
```

### 8.3 캐싱 전략

| 계층 | 전략 |
|------|------|
| 브라우저 | React Query로 캐싱 (staleTime: 30초) |
| CDN | 정적 리소스만 (에디터 에셋) |
| Redis | 미사용 (실시간성 중요) |

---

## 9. 영향 범위

### 9.1 수정 필요 파일

| 파일 | 변경 내용 |
|------|----------|
| `frontend/src/components/proposals/ProposalSection.tsx` | 읽기 전용 → 편집 가능으로 변경 |
| `frontend/src/components/proposals/ProposalDetailPage.tsx` | 편집기 레이아웃 적용 |
| `frontend/src/stores/proposalStore.ts` | 자동 저장 상태 추가 |
| `frontend/src/lib/api/proposal.ts` | auto-save, validate API 추가 |
| `frontend/src/types/proposal.ts` | 타입 확장 |
| `backend/src/api/v1/proposals.py` | auto-save, validate 엔드포인트 추가 |
| `backend/src/services/proposal_service.py` | 검증 로직 추가 |
| `backend/src/schemas/proposal.py` | 요청/응답 스키마 추가 |

### 9.2 신규 생성 파일

| 파일 | 설명 |
|------|------|
| `frontend/src/components/proposals/editor/*` | 편집기 컴포넌트 (8개) |
| `frontend/src/components/proposals/sidebar/*` | 사이드바 컴포넌트 (4개) |
| `frontend/src/components/proposals/hooks/*` | 커스텀 훅 (3개) |
| `frontend/src/stores/editorStore.ts` | 편집기 상태 스토어 |
| `frontend/src/lib/tiptap/*` | TipTap 설정 |

### 9.3 의존성 추가

```json
{
  "@tiptap/react": "^2.1.0",
  "@tiptap/starter-kit": "^2.1.0",
  "@tiptap/extension-table": "^2.1.0",
  "@tiptap/extension-image": "^2.1.0",
  "@tiptap/extension-link": "^2.1.0",
  "@tiptap/extension-text-align": "^2.1.0",
  "@tiptap/extension-underline": "^2.1.0",
  "@tiptap/extension-highlight": "^2.1.0",
  "@tiptap/extension-placeholder": "^2.1.0",
  "@tiptap/extension-markdown": "^2.1.0"
}
```

---

## 10. 보안 고려사항

### 10.1 XSS 방지

- TipTap은 기본적으로 HTML sanitize 수행
- 이미지 업로드 시 파일 타입 검증
- 외부 링크 `rel="noopener noreferrer"` 적용

### 10.2 권한 검증

- 모든 API에서 `user_id` 검증 (기존 로직 재사용)
- 회사 멤버만 편집 가능 (F-11 확장 시)

---

## 11. 접근성 (A11y)

| 항목 | 준수 방안 |
|------|----------|
| 키보드 네비게이션 | TipTap 기본 지원, 단축키 추가 |
| 스크린 리더 | ARIA 레이블, 섹션 헤딩 |
| 색상 대비 | WCAG 2.1 AA 준수 |
| 포커스 표시 | 2px 테두리 |

---

## 12. 변경 이력

| 날짜 | 변경 내용 | 이유 |
|------|----------|------|
| 2026-03-20 | 초기 설계 작성 | F-05 개발 시작 |
