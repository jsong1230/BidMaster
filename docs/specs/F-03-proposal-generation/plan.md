# F-03 제안서 AI 초안 생성 -- 구현 계획서

## 참조
- 설계서: docs/specs/F-03-proposal-generation/design.md
- UI 명세서: docs/specs/F-03-proposal-generation/ui-spec.md
- 인수조건: docs/project/features.md #F-03
- 테스트 명세: docs/specs/F-03-proposal-generation/test-spec.md

---

## 구현 상태 확인

### 백엔드 (완료)
| 모듈 | 파일 | 상태 | 비고 |
|------|------|------|------|
| Models | models/proposal.py, proposal_section.py, proposal_version.py | ✅ | |
| Schemas | schemas/proposal.py | ✅ | |
| Services | services/proposal_service.py | ✅ | |
| Services | services/proposal_generator_service.py | ✅ | GLM API 사용 |
| Services | services/proposal_export_service.py | ✅ | |
| API | api/v1/proposals.py | ✅ | SSE 스트리밍 |
| Templates | templates/prompts/*.j2 | ✅ | |
| Tests | tests/test_f03_proposal.py | ✅ | |

### 프론트엔드 (미구현)
| 모듈 | 파일 | 상태 | 비고 |
|------|------|------|------|
| Types | types/proposal.ts | ❌ | |
| API Client | lib/api/proposal.ts | ❌ | |
| Store | stores/proposalStore.ts | ❌ | |
| Pages | app/(main)/(proposals)/proposals/page.tsx | ❌ | 목록 |
| Pages | app/(main)/(proposals)/proposals/new/page.tsx | ❌ | 생성 |
| Pages | app/(main)/(proposals)/proposals/[id]/page.tsx | ❌ | 상세 |
| Pages | app/(main)/(proposals)/proposals/[id]/generate/page.tsx | ❌ | SSE |
| Components | components/proposals/*.tsx | ❌ | |

---

## 구현 범위

이번 구현은 **프론트엔드 전체**입니다. 백엔드는 이미 완료되어 있으므로 건드리지 않습니다.

---

## 태스크

### T-01: 타입 및 API 클라이언트
**담당**: frontend-dev
**산출물**:
- `frontend/src/types/proposal.ts` - 타입 정의
- `frontend/src/lib/api/proposal.ts` - API 클라이언트

**인수조건**:
- [ ] Proposal, ProposalDetail, ProposalSection 타입 정의
- [ ] SSE 연결 함수 구현 (EventSource)
- [ ] 목록/상세/생성/다운로드/재생성 API 함수

### T-02: Zustand 스토어
**담당**: frontend-dev
**산출물**:
- `frontend/src/stores/proposalStore.ts`

**인수조건**:
- [ ] 목록/상세/필터 상태 관리
- [ ] SSE 연결/해제 액션
- [ ] 생성 진행 상황 상태 관리

### T-03: 제안서 목록 페이지
**담당**: frontend-dev
**산출물**:
- `frontend/src/app/(main)/(proposals)/proposals/page.tsx`
- `frontend/src/components/proposals/ProposalCard.tsx`
- `frontend/src/components/proposals/ProposalListPage.tsx`

**인수조건**:
- [ ] 제안서 목록 조회 및 표시
- [ ] 상태 필터 동작
- [ ] 빈 상태 표시
- [ ] 새 제안서 생성 버튼

### T-04: 제안서 생성 페이지
**담당**: frontend-dev
**산출물**:
- `frontend/src/app/(main)/(proposals)/proposals/new/page.tsx`
- `frontend/src/components/proposals/ProposalCreatePage.tsx`
- `frontend/src/components/proposals/BidSelectModal.tsx`
- `frontend/src/components/proposals/SectionSelector.tsx`

**인수조건**:
- [ ] bidId 파라미터 있으면 해당 공고 자동 선택
- [ ] bidId 없으면 공고 선택 모달 표시
- [ ] 섹션 다중 선택 UI
- [ ] 추가 지시사항 입력
- [ ] 생성 요청 → 생성 진행 페이지로 이동

### T-05: 제안서 생성 진행 페이지 (SSE)
**담당**: frontend-dev
**산출물**:
- `frontend/src/app/(main)/(proposals)/proposals/[id]/generate/page.tsx`
- `frontend/src/components/proposals/ProposalGeneratePage.tsx`
- `frontend/src/components/proposals/GenerationProgress.tsx`
- `frontend/src/components/proposals/SectionProgressList.tsx`

**인수조건**:
- [ ] SSE 연결 (/proposals/{id}/generate/stream)
- [ ] start → progress → section → complete 이벤트 처리
- [ ] 프로그레스 바 실시간 업데이트
- [ ] 섹션별 진행 상황 표시
- [ ] 에러 이벤트 처리
- [ ] 완료 시 상세 페이지로 이동

### T-06: 제안서 상세 페이지
**담당**: frontend-dev
**산출물**:
- `frontend/src/app/(main)/(proposals)/proposals/[id]/page.tsx`
- `frontend/src/components/proposals/ProposalDetailPage.tsx`
- `frontend/src/components/proposals/ProposalHeader.tsx`
- `frontend/src/components/proposals/SectionNavigation.tsx`
- `frontend/src/components/proposals/ProposalSection.tsx`
- `frontend/src/components/proposals/DownloadButton.tsx`
- `frontend/src/components/proposals/RegenerateModal.tsx`

**인수조건**:
- [ ] 제안서 상세 정보 표시
- [ ] 섹션 네비게이션 (클릭 시 스크롤)
- [ ] 섹션 내용 마크다운 렌더링
- [ ] DOCX/PDF 다운로드
- [ ] 섹션 재생성 모달

### T-07: 통합 및 검증
**담당**: frontend-dev
**산출물**:
- 빌드 성공 확인
- 라우트 연결 확인

**인수조건**:
- [ ] `npm run build` 성공
- [ ] /proposals, /proposals/new, /proposals/[id], /proposals/[id]/generate 라우트 동작
- [ ] 네비게이션 메뉴에 제안서 링크 추가

---

## 의존성

```
T-01 ─┐
      ├─→ T-02 ─→ T-03, T-04, T-05, T-06 ─→ T-07
T-01 ─┘
```

T-01과 T-02는 병렬 가능, 나머지는 순차 진행.

---

## 파일 생성 목록

```
frontend/src/
├── app/(main)/(proposals)/
│   ├── proposals/
│   │   ├── page.tsx
│   │   ├── new/page.tsx
│   │   └── [id]/
│   │       ├── page.tsx
│   │       └── generate/page.tsx
│   └── layout.tsx (기존 또는 수정)
├── components/proposals/
│   ├── ProposalCard.tsx
│   ├── ProposalListPage.tsx
│   ├── ProposalCreatePage.tsx
│   ├── ProposalDetailPage.tsx
│   ├── ProposalGeneratePage.tsx
│   ├── SectionNavigation.tsx
│   ├── ProposalSection.tsx
│   ├── RegenerateModal.tsx
│   ├── BidSelectModal.tsx
│   ├── SectionSelector.tsx
│   ├── GenerationProgress.tsx
│   ├── SectionProgressList.tsx
│   ├── ProposalHeader.tsx
│   └── DownloadButton.tsx
├── lib/api/proposal.ts
├── stores/proposalStore.ts
└── types/proposal.ts
```

---

## 실행 계획

1. **T-01**: 타입 + API 클라이언트 구현
2. **T-02**: Zustand 스토어 구현
3. **T-03**: 목록 페이지
4. **T-04**: 생성 페이지
5. **T-05**: SSE 진행 페이지
6. **T-06**: 상세 페이지
7. **T-07**: 빌드 검증

---

## 비고

- 백엔드는 GLM API 사용 (Claude API 사용 불가 제약)
- SSE 인증은 query parameter로 token 전달
- 마크다운 렌더링은 react-markdown 사용 (이미 프로젝트에 있음)
