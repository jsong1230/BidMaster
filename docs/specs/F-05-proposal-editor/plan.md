# F-05 제안서 편집기 — 구현 계획서

## 참조
- 설계서: docs/specs/F-05-proposal-editor/design.md
- 인수조건: docs/project/features.md #F-05
- 테스트 명세: docs/specs/F-05-proposal-editor/test-spec.md
- 의존 기능: F-03 (제안서 AI 초안 생성) — ✅ 완료

---

## 태스크 목록

### Phase 1: 백엔드 구현

#### 1.1 DB 스키마 + 마이그레이션
- [ ] [backend] proposal_sections.metadata JSONB 필드 확장 (format, editCount 추가)
- [ ] [backend] proposals.evaluation_checklist JSONB 필드 검증 (이미 존재)
- [ ] [backend] 마이그레이션 스크립트 작성 (alembic revision)
- [ ] [backend] 마이그레이션 실행 및 검증

#### 1.2 서비스 로직 구현
- [ ] [backend] ProposalService.auto_save_section() 메서드 구현
  - word_count 재계산 로직 (HTML → 텍스트 추출)
  - metadata 업데이트 (lastEditedBy, editCount, lastEditAt, format)
- [ ] [backend] ProposalService.validate_proposal() 메서드 구현
  - 필수 섹션 비어있는지 검증
  - 페이지 제한 초과 검증 (word_count 기준)
  - 평가 항목 체크율 검증
- [ ] [backend] ProposalService.update_evaluation_checklist() 메서드 구현
  - 달성률 계산 (checked/total * 100)
- [ ] [backend] 단위 테스트 작성 (test_spec.md 참조)

#### 1.3 API 라우트 구현
- [ ] [backend] PATCH /api/v1/proposals/{id}/auto-save 엔드포인트 구현
- [ ] [backend] POST /api/v1/proposals/{id}/validate 엔드포인트 구현
- [ ] [backend] PATCH /api/v1/proposals/{id}/evaluation-checklist 엔드포인트 구현
- [ ] [backend] Pydantic 스키마 작성 (AutoSaveRequest, ValidationResponse, ChecklistUpdateRequest)
- [ ] [backend] API 통합 테스트 작성

#### 1.4 API 스펙 문서 작성
- [ ] [backend] docs/api/F-05-proposal-editor.md 작성
  - 신규 3개 엔드포인트 스펙
  - 기존 F-03 API 재사용 안내

#### 1.5 DB 스키마 문서 작성
- [ ] [backend] docs/db/F-05-proposal-editor.md 작성
  - proposals.evaluation_checklist 구조
  - proposal_sections.metadata 구조

---

### Phase 2: 프론트엔드 구현

#### 2.1 타입 정의 + API 클라이언트
- [ ] [frontend] frontend/src/types/proposal.ts 타입 확장
  - AutoSaveRequest, ValidationResponse, ChecklistUpdateRequest 타입 추가
  - EvaluationChecklist 타입 정의
- [ ] [frontend] frontend/src/lib/api/proposal.ts API 함수 추가
  - autoSaveProposal()
  - validateProposal()
  - updateEvaluationChecklist()

#### 2.2 의존성 설치
- [ ] [frontend] TipTap 관련 패키지 설치
  ```bash
  npm install @tiptap/react @tiptap/starter-kit @tiptap/extension-table @tiptap/extension-image @tiptap/extension-link @tiptap/extension-text-align @tiptap/extension-underline @tiptap/extension-highlight @tiptap/extension-placeholder @tiptap/extension-markdown
  ```

#### 2.3 TipTap 설정
- [ ] [frontend] frontend/src/lib/tiptap/extensions.ts 작성
  - 필수 확장 구성 (StarterKit, Table, Image, Link, TextAlign, Underline, Highlight, Placeholder, Markdown)
  - 한국어 IME 호환성 확인
- [ ] [frontend] frontend/src/lib/tiptap/utils.ts 작성
  - HTML → 텍스트 추출 함수 (word count용)
  - 텍스트 → 단어 수 계산 (한국어 + 영어)

#### 2.4 편집기 컴포넌트 구현
- [ ] [frontend] frontend/src/components/proposals/editor/TipTapEditor.tsx 구현
  - TipTap 인스턴스 관리
  - onChange 콜백
  - readOnly 모드 지원
- [ ] [frontend] frontend/src/components/proposals/editor/EditorToolbar.tsx 구현
  - 서식 버튼 (볼드, 이탤릭, 밑줄, 하이라이트)
  - 텍스트 정렬 버튼
  - 표/이미지/링크 메뉴
  - 현재 상태에 따른 활성/비활성 처리
- [ ] [frontend] frontend/src/components/proposals/editor/TableMenu.tsx 구현
  - 표 삽입/삭제/병합 기능
- [ ] [frontend] frontend/src/components/proposals/editor/ImageUploader.tsx 구현
  - 파일 업로드 (최대 10MB)
  - 파일 타입 검증
  - 미리보기
- [ ] [frontend] frontend/src/components/proposals/editor/SectionEditor.tsx 구현
  - TipTapEditor 래핑
  - 섹션별 편집 관리
  - wordCount 표시

#### 2.5 상태 관리 컴포넌트 구현
- [ ] [frontend] frontend/src/components/proposals/editor/AutoSaveIndicator.tsx 구현
  - "편집 중..." / "저장 중..." / "저장됨" / "저장 실패" 상태
  - 저장 실패 시 재시도 버튼
- [ ] [frontend] frontend/src/components/proposals/hooks/useAutoSave.ts 구현
  - 30초 debounce 로직
  - 페이지 이탈 시 강제 저장 (beforeunload)
  - 언마운트 시 pending 변경사항 저장
- [ ] [frontend] frontend/src/components/proposals/hooks/useDebounce.ts 구현
  - 일반용 debounce 훅
- [ ] [frontend] frontend/src/components/proposals/hooks/useWordCount.ts 구현
  - HTML → 단어 수 계산
  - 한국어 최적화

#### 2.6 사이드바 컴포넌트 구현
- [ ] [frontend] frontend/src/components/proposals/sidebar/EvaluationPanel.tsx 구현
  - 평가 기준 체크리스트 표시
  - 체크박스 토글
  - 달성률 프로그레스바
  - API PATCH /evaluation-checklist 호출
- [ ] [frontend] frontend/src/components/proposals/sidebar/SectionNavigator.tsx 구현
  - 섹션 목록 표시
  - 클릭 시 해당 섹션으로 스크롤
  - 현재 섹션 하이라이트
  - 완료 섹션 체크마크
- [ ] [frontend] frontend/src/components/proposals/sidebar/VersionHistory.tsx 구현
  - 버전 목록 표시 (F-03 기능 재사용)
  - 버전 복원 기능

#### 2.7 메인 컨테이너 구현
- [ ] [frontend] frontend/src/stores/editorStore.ts 작성 (Zustand)
  - activeSection 상태
  - isSaving 플래그
  - error 상태
- [ ] [frontend] frontend/src/components/proposals/editor/ProposalEditor.tsx 구현
  - 전체 편집기 레이아웃
  - 섹션 간 이동 관리
  - 자동 저장 조율
  - 사이드바와 에디터 통합
- [ ] [frontend] frontend/src/components/proposals/modals/ValidationModal.tsx 구현
  - 검증 경고 표시
  - 필수 항목 누락 경고
  - 페이지 초과 경고
  - "그대로 제출" / "편집 계속" 버튼

#### 2.8 페이지 통합
- [ ] [frontend] frontend/src/components/proposals/ProposalDetailPage.tsx 수정
  - 읽기 전용 → 편집 모드로 변경
  - ProposalEditor 컴포넌트 통합
  - 제출 버튼에 검증 로직 연결

#### 2.9 단위 테스트 작성
- [ ] [frontend] TipTapEditor 컴포넌트 테스트 (test_spec.md 참조)
- [ ] [frontend] EditorToolbar 컴포넌트 테스트
- [ ] [frontend] AutoSaveIndicator 컴포넌트 테스트
- [ ] [frontend] EvaluationPanel 컴포넌트 테스트
- [ ] [frontend] useAutoSave 훅 테스트
- [ ] [frontend] editorStore 테스트

---

### Phase 3: 검증

#### 3.1 통합 테스트 실행
- [ ] [shared] 백엔드 단위 테스트 실행 (pytest tests/f05)
- [ ] [shared] 프론트엔드 단위 테스트 실행 (npm test -- --testPathPattern="proposals/editor")
- [ ] [shared] API 통합 테스트 실행

#### 3.2 E2E 테스트 작성 및 실행
- [ ] [shared] frontend/tests/proposals/editor.spec.ts 작성
  - 제안서 편집 및 저장 플로우
  - AI 재생성 플로우
  - 검증 플로우
- [ ] [shared] E2E 테스트 실행 (npx playwright test)

#### 3.3 회귀 테스트
- [ ] [shared] F-03 기능 테스트 실행 (기존 기능 보호)
  - 제안서 목록 조회
  - 제안서 생성 (SSE)
  - 섹션 재생성 API
  - 버전 관리
  - 다운로드 (PDF/DOCX)

#### 3.4 Quality Gate 검증
- [ ] [shared] 보안 검증 (XSS 방지, 파일 업로드 검증)
- [ ] [shared] 성능 검증 (로딩 < 1초, 타이핑 지연 < 16ms)
- [ ] [shared] 코드 리뷰 (타입 안전성, 에러 처리)
- [ ] [shared] 문서 리뷰 (API 스펙, DB 스펙 완전성)

#### 3.5 M2 마일스톤 완료 확인
- [ ] [shared] M2 기능 전체 완료 확인 (F-03, F-05, F-06, F-10)
- [ ] [shared] M2 통합 테스트 실행
- [ ] [shared] M2 릴리스 준비

---

## 태스크 의존성

```
Phase 1 (백엔드)
  ├─ 1.1 DB 스키마 ──▶ 1.2 서비스 로직 ──▶ 1.3 API 라우트 ──▶ 1.4 API 스펙 ──▶ 1.5 DB 스펙
  └─ (병렬 가능)

Phase 2 (프론트엔드)
  ├─ 2.1 타입 + API 클라이언트 ──▶ 2.2 의존성 설치 ──▶ 2.3 TipTap 설정
  ├─ 2.3 TipTap 설정 ──▶ 2.4 편집기 컴포넌트
  ├─ 2.4 편집기 컴포넌트 ──▶ 2.5 상태 관리 컴포넌트
  ├─ 2.5 상태 관리 컴포넌트 ──▶ 2.6 사이드바 컴포넌트
  ├─ 2.6 사이드바 컴포넌트 ──▶ 2.7 메인 컨테이너
  ├─ 2.7 메인 컨테이너 ──▶ 2.8 페이지 통합
  └─ 2.8 페이지 통합 ──▶ 2.9 단위 테스트

Phase 1 ──▶ Phase 2 (백엔드 API 완료 후 프론트엔드 연결)
Phase 1 + Phase 2 ──▶ Phase 3 (통합 테스트)
```

---

## 병렬 실행 판단

- **Agent Team 권장**: Yes
- **근거**:
  1. 백엔드와 프론트엔드는 독립적인 작업 영역
  2. Phase 1 (백엔드) API 라우트 완료 후 프론트엔드 연결 가능
  3. UI 컴포넌트 개발과 동시에 API 스펙 문서화 가능
  4. 프론트엔드 단위 테스트는 API 모킹으로 병렬 진행 가능

**권장 작업 분할**:
- **backend-dev**: Phase 1 전체 (1.1 ~ 1.5)
- **frontend-dev**: Phase 2 전체 (2.1 ~ 2.9)
- **병합 시점**: Phase 2.8 (페이지 통합) 이후 Phase 3 통합 테스트

---

## 마일스톤 영향

- **현재 마일스톤**: M2
- **M2 기능 상태**:
  - F-03: ✅ 완료
  - F-05: 🔄 진행중 (본 기능)
  - F-06: ✅ 완료
  - F-10: ✅ 완료
- **F-05 완료 후**: M2 마일스톤 100% 완료 → M3 (결제 및 구독 관리)로 진행 가능

---

## 위험 요소 및 완화 대책

| 위험 요소 | 영향 | 완화 대책 |
|----------|------|----------|
| TipTap 한국어 IME 이슈 | 사용자 경험 저하 | TipTap Markdown 확장으로 호환성 확보, 테스트 주도 개발 |
| 자동 저장 네트워크 실패 | 데이터 손실 | 로컬 스토리지 백업 + 재시도 로직 + beforeunload 강제 저장 |
| 대용량 문서 성능 | 렌더링 지연 | 가상 스크롤링, 섹션 지연 로딩, 이미지 Lazy Loading |
| F-03 기능 회귀 | 기존 기능 파손 | 회귀 테스트 전면 실행, 기존 API 호환성 검증 |

---

## 변경 이력

| 날짜 | 변경 내용 | 이유 |
|------|----------|------|
| 2026-03-20 | 초기 계획서 작성 | F-05 개발 시작 |
