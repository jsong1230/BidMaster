# F-05 제안서 편집기 — 테스트 명세

## 참조

- **설계서**: docs/specs/F-05-proposal-editor/design.md
- **인수조건**: docs/project/features.md #F-05
- **기존 테스트**: backend/tests/f03/test_proposal_service.py

---

## 1. 단위 테스트

### 1.1 TipTap 에디터 컴포넌트

| 대상 | 시나리오 | 입력 | 예상 결과 |
|------|----------|------|-----------|
| `TipTapEditor` | 초기 로드 | Markdown 콘텐츠 | HTML로 렌더링됨 |
| `TipTapEditor` | 텍스트 입력 | "새로운 텍스트" | content 상태 업데이트 |
| `TipTapEditor` | 빈 문서 | null | placeholder 표시 |
| `TipTapEditor` | 이미지 삽입 | 이미지 파일 | base64 또는 URL로 삽입 |
| `TipTapEditor` | 표 삽입 | 3x3 테이블 | 테이블 노드 생성 |
| `TipTapEditor` | 서식 적용 | 볼드, 이탤릭 | 스타일 적용됨 |
| `TipTapEditor` | 링크 삽입 | URL 입력 | href 속성 포함됨 |
| `TipTapEditor` | Undo/Redo | Ctrl+Z / Ctrl+Y | 이력 관리 동작 |

### 1.2 EditorToolbar

| 대상 | 시나리오 | 입력 | 예상 결과 |
|------|----------|------|-----------|
| `EditorToolbar` | 볼드 버튼 클릭 | 선택 텍스트 있음 | active 상태 토글 |
| `EditorToolbar` | 비활성 상태 | 포커스 없음 | 모든 버튼 비활성화 |
| `EditorToolbar` | 텍스트 정렬 | 왼쪽/가운데/오른쪽 | 정렬 변경됨 |
| `EditorToolbar` | 표 메뉴 | 표 내부 클릭 | 표 관련 메뉴 활성화 |

### 1.3 AutoSaveIndicator

| 대상 | 시나리오 | 입력 | 예상 결과 |
|------|----------|------|-----------|
| `AutoSaveIndicator` | 편집 시작 | 텍스트 입력 | "편집 중..." 표시 |
| `AutoSaveIndicator` | 30초 경과 | 변경사항 있음 | "저장 중..." → "저장됨" |
| `AutoSaveIndicator` | 저장 실패 | 네트워크 에러 | "저장 실패" + 재시도 버튼 |
| `AutoSaveIndicator` | 수동 저장 | Ctrl+S | 즉시 저장 실행 |

### 1.4 EvaluationPanel

| 대상 | 시나리오 | 입력 | 예상 결과 |
|------|----------|------|-----------|
| `EvaluationPanel` | 체크박스 토글 | 항목 클릭 | 달성률 업데이트 |
| `EvaluationPanel` | 전체 선택 | "전체 체크" 클릭 | 100% 달성 |
| `EvaluationPanel` | 부분 선택 | 3/5 체크 | 60% 달성 |
| `EvaluationPanel` | 섹션별 필터 | 섹션 선택 | 해당 섹션 항목만 표시 |

### 1.5 SectionNavigator

| 대상 | 시나리오 | 입력 | 예상 결과 |
|------|----------|------|-----------|
| `SectionNavigator` | 섹션 클릭 | "사업 개요" | 해당 섹션으로 스크롤 |
| `SectionNavigator` | 활성 섹션 | 스크롤 중 | 현재 섹션 하이라이트 |
| `SectionNavigator` | 진행률 | 섹션 완료 | 체크마크 표시 |

### 1.6 커스텀 훅

| 대상 | 시나리오 | 입력 | 예상 결과 |
|------|----------|------|-----------|
| `useAutoSave` | 30초 debounce | 변경사항 | saveCallback 호출 |
| `useAutoSave` | 중간 변경 | 추가 입력 | 타이머 리셋 |
| `useAutoSave` | 언마운트 | 컴포넌트 제거 | pending 변경사항 저장 |
| `useWordCount` | 텍스트 변경 | 한국어 + 영어 | 정확한 단어 수 |
| `useEvaluationProgress` | 체크리스트 변경 | 항목 토글 | 달성률 재계산 |

### 1.7 editorStore (Zustand)

| 대상 | 시나리오 | 입력 | 예상 결과 |
|------|----------|------|-----------|
| `editorStore` | 섹션 변경 | sectionKey 업데이트 | activeSection 변경 |
| `editorStore` | 저장 상태 | saving = true | isSaving 플래그 설정 |
| `editorStore` | 에러 발생 | 에러 메시지 | error 상태 설정 |

---

## 2. 통합 테스트

### 2.1 API 통합

| API | 시나리오 | 입력 | 예상 결과 |
|-----|----------|------|-----------|
| `GET /proposals/{id}` | 편집기 로드 | 제안서 ID | 섹션별 content 반환 |
| `PATCH /proposals/{id}/sections/{key}` | 섹션 저장 | HTML content | wordCount 업데이트, updatedAt 갱신 |
| `PATCH /proposals/{id}` | 체크리스트 저장 | evaluationChecklist | 저장됨 |
| `POST /proposals/{id}/sections/{key}/regenerate` | AI 재생성 | customInstructions | 새 content 반환 |
| `POST /proposals/{id}/validate` | 제출 전 검증 | - | 검증 결과 + 경고 목록 |
| `POST /proposals/{id}/versions` | 버전 저장 | - | 새 버전 번호 반환 |
| `POST /proposals/{id}/versions/{n}/restore` | 버전 복원 | 버전 번호 | 섹션 내용 복원됨 |

### 2.2 자동 저장 플로우

| 시나리오 | 단계 | 예상 결과 |
|----------|------|-----------|
| 정상 저장 | 1) 편집 → 2) 30초 대기 → 3) API 호출 → 4) 응답 | "저장됨" 표시 |
| 네트워크 실패 | 1) 편집 → 2) 30초 대기 → 3) API 실패 → 4) 재시도 | "저장 실패" + 재시도 버튼 |
| 연속 편집 | 1) 편집 → 2) 15초 후 추가 편집 → 3) 타이머 리셋 | 30초 다시 카운트 |
| 페이지 이탈 | 1) 편집 → 2) beforeunload → 3) 강제 저장 | 변경사항 저장됨 |

### 2.3 AI 재생성 플로우

| 시나리오 | 단계 | 예상 결과 |
|----------|------|-----------|
| 정상 재생성 | 1) 모달 열기 → 2) 지시사항 입력 → 3) API 호출 → 4) 완료 | 새 콘텐츠로 교체 |
| 빈 지시사항 | 1) 모달 열기 → 2) 지시사항 없음 → 3) API 호출 | 기본 프롬프트로 재생성 |
| 재생성 취소 | 1) 모달 열기 → 2) 취소 클릭 | 기존 콘텐츠 유지 |
| 에러 발생 | 1) API 호출 → 2) GLM 에러 | 에러 토스트 표시 |

### 2.4 검증 플로우

| 시나리오 | 조건 | 예상 결과 |
|----------|------|-----------|
| 모든 검증 통과 | 필수 항목 기재, 페이지 제한 내 | 성공, 제출 가능 |
| 필수 항목 누락 | overview 섹션 비어있음 | 경고: "사업 개요를 입력하세요" |
| 페이지 초과 | 15페이지 (제한 10페이지) | 경고: "페이지 제한을 초과했습니다" |
| 평가 항목 미달성 | 50% 미만 체크 | 경고: "평가 항목을 더 확인하세요" |

---

## 3. 경계 조건 / 에러 케이스

### 3.1 입력 검증

| 케이스 | 입력 | 예상 결과 |
|--------|------|-----------|
| 빈 제안서 | sections = [] | 빈 에디터 + placeholder |
| 매우 긴 섹션 | 50,000자 | 가상 스크롤링 활성화 |
| 특수 문자 | `<script>alert(1)</script>` | XSS 방지, 텍스트로 표시 |
| 이미지 크기 초과 | 20MB 이미지 | "최대 10MB까지 업로드 가능" 에러 |
| 지원하지 않는 파일 | .gif 파일 | "지원하지 않는 형식입니다" 에러 |

### 3.2 API 에러

| 코드 | 상황 | 클라이언트 처리 |
|------|------|-----------------|
| 401 | 토큰 만료 | 로그인 페이지 리다이렉트 |
| 403 | 권한 없음 | "편집 권한이 없습니다" 토스트 |
| 404 | 제안서 없음 | "제안서를 찾을 수 없습니다" + 목록으로 |
| 409 | 동시 편집 충돌 | "다른 사용자가 편집 중입니다" 경고 |
| 429 | AI 요청 한도 | "재생성 요청 한도를 초과했습니다" |
| 500 | 서버 에러 | "일시적인 오류입니다. 잠시 후 다시 시도하세요" |
| 504 | AI 타임아웃 | "AI 생성 시간이 초과되었습니다" |

### 3.3 네트워크 이슈

| 케이스 | 시나리오 | 처리 |
|--------|----------|------|
| 오프라인 | 편집 중 네트워크 끊김 | "오프라인 상태입니다" 표시, 로컬 저장 |
| 느린 연결 | API 응답 10초+ | 로딩 스피너 + 취소 버튼 |
| 연결 복구 | 오프라인 → 온라인 | 자동 동기화 시도 |

### 3.4 브라우저 이슈

| 케이스 | 시나리오 | 처리 |
|--------|----------|------|
| 페이지 새로고침 | 저장되지 않은 변경사항 | beforeunload 경고 |
| 뒤로가기 | 편집 중 이탈 | 변경사항 저장 확인 |
| 탭 닫기 | 저장되지 않음 | beforeunload 경고 |
| 세션 만료 | 1시간+ 비활성 | 세션 갱신 또는 재로그인 |

---

## 4. 성능 테스트

### 4.1 로딩 성능

| 시나리오 | 조건 | 기준 |
|----------|------|------|
| 초기 로드 | 제안서 6개 섹션 | < 1초 |
| 섹션 전환 | 클릭 → 렌더 | < 200ms |
| 대용량 섹션 | 5,000자 | < 500ms |
| 이미지 로드 | 10개 이미지 | < 2초 |

### 4.2 편집 성능

| 시나리오 | 조건 | 기준 |
|----------|------|------|
| 타이핑 | 연속 입력 | 지연 없음 (< 16ms) |
| 서식 변경 | 볼드/이탤릭 | 즉시 적용 |
| 표 편집 | 10x10 셀 | < 100ms |
| 자동 저장 | API 호출 | 백그라운드, UI 블로킹 없음 |

### 4.3 메모리

| 시나리오 | 조건 | 기준 |
|----------|------|------|
| 초기 메모리 | 편집기 로드 | < 50MB |
| 장시간 편집 | 1시간 사용 | < 200MB |
| 메모리 누수 | 섹션 전환 100회 | 증가 없음 |

---

## 5. E2E 테스트 (Playwright)

### 5.1 기본 편집 플로우

```typescript
test('제안서 편집 및 저장', async ({ page }) => {
  // 1. 제안서 상세 페이지 진입
  await page.goto('/proposals/123');

  // 2. 섹션 편집
  await page.click('[data-testid="section-overview"]');
  await page.type('.tiptap', '새로운 내용입니다.');

  // 3. 자동 저장 대기
  await page.waitForSelector('[data-testid="save-indicator"]:has-text("저장됨")', {
    timeout: 35000
  });

  // 4. 페이지 새로고침 후 확인
  await page.reload();
  await expect(page.locator('.tiptap')).toContainText('새로운 내용입니다.');
});
```

### 5.2 AI 재생성 플로우

```typescript
test('섹션 AI 재생성', async ({ page }) => {
  await page.goto('/proposals/123');

  // 1. 재생성 버튼 클릭
  await page.click('[data-testid="regenerate-button"]');

  // 2. 모달에서 지시사항 입력
  await page.fill('[data-testid="custom-instructions"]', '더 구체적인 기술 제안을 포함해주세요');
  await page.click('button:has-text("재생성")');

  // 3. 로딩 상태 확인
  await expect(page.locator('[data-testid="regenerating"]')).toBeVisible();

  // 4. 완료 확인
  await page.waitForSelector('[data-testid="regenerate-complete"]', { timeout: 60000 });
});
```

### 5.3 검증 플로우

```typescript
test('제출 전 검증', async ({ page }) => {
  await page.goto('/proposals/123');

  // 1. 일부 섹션 비우기
  await page.click('[data-testid="section-overview"]');
  await page.fill('.tiptap', '');

  // 2. 제출 버튼 클릭
  await page.click('button:has-text("제출하기")');

  // 3. 검증 경고 확인
  await expect(page.locator('[data-testid="validation-warning"]')).toContainText('사업 개요를 입력하세요');
});
```

---

## 6. 백엔드 단위 테스트

### 6.1 ProposalService 확장

| 테스트 케이스 | 입력 | 예상 결과 |
|---------------|------|-----------|
| `test_auto_save_section` | 섹션 HTML 업데이트 | word_count 재계산, updated_at 갱신 |
| `test_validate_required_sections` | overview 누락 | ValidationError |
| `test_validate_page_limit` | 15페이지 (제한 10) | ValidationError |
| `test_update_evaluation_checklist` | 체크리스트 업데이트 | 저장됨, 달성률 계산 |
| `test_create_version_on_major_change` | 버전 저장 | version_number 증가 |
| `test_restore_version` | 버전 2로 복원 | 섹션 내용 복원, version = 3 |

### 6.2 검증 로직

```python
class TestProposalValidation:
    """제안서 검증 테스트"""

    async def test_validate_empty_required_section(self, db_session):
        """필수 섹션 비어있을 때 검증 실패"""
        proposal = await create_proposal_with_empty_section(db_session, "overview")

        service = ProposalService(db_session)
        result = await service.validate_proposal(proposal.id, user_id)

        assert result["isValid"] is False
        assert any(w["code"] == "REQUIRED_SECTION_EMPTY" for w in result["warnings"])

    async def test_validate_page_limit_exceeded(self, db_session):
        """페이지 제한 초과 시 검증 실패"""
        proposal = await create_proposal_with_pages(db_session, pages=15, limit=10)

        service = ProposalService(db_session)
        result = await service.validate_proposal(proposal.id, user_id)

        assert result["isValid"] is False
        assert any(w["code"] == "PAGE_LIMIT_EXCEEDED" for w in result["warnings"])

    async def test_validate_success(self, db_session):
        """모든 검증 통과"""
        proposal = await create_valid_proposal(db_session)

        service = ProposalService(db_session)
        result = await service.validate_proposal(proposal.id, user_id)

        assert result["isValid"] is True
        assert len(result["warnings"]) == 0
```

---

## 7. 접근성 테스트

| 항목 | 도구 | 기준 |
|------|------|------|
| 키보드 네비게이션 | 수동 테스트 | Tab 순서 논리적, 단축키 동작 |
| 스크린 리더 | NVDA/VoiceOver | 섹션 헤딩 읽힘, 상태 변경 안내 |
| 색상 대비 | axe-core | WCAG 2.1 AA 준수 |
| 포커스 표시 | 수동 테스트 | 2px 테두리 명확 |

---

## 8. 회귀 테스트 (F-03 기능 보호)

| 기존 기능 | 영향 여부 | 검증 방법 |
|-----------|-----------|-----------|
| 제안서 목록 조회 | 없음 | 기존 테스트 실행 |
| 제안서 생성 (SSE) | 없음 | 기존 테스트 실행 |
| 섹션 재생성 API | 호환성 유지 | Markdown → HTML 변환 확인 |
| 버전 관리 | 확장 | 기존 API 동작 확인 |
| 다운로드 (PDF/DOCX) | 확인 필요 | HTML 콘텐츠 변환 테스트 |

---

## 9. 테스트 커버리지 목표

| 계층 | 목표 |
|------|------|
| 프론트엔드 컴포넌트 | 80% |
| 프론트엔드 훅 | 90% |
| 백엔드 서비스 | 85% |
| API 통합 | 100% (모든 엔드포인트) |
| E2E | 핵심 플로우 5개 |

---

## 10. 테스트 실행 명령

```bash
# 프론트엔드 단위 테스트
cd frontend && npm test -- --coverage --testPathPattern="proposals/editor"

# 백엔드 단위 테스트
cd backend && pytest tests/f05 -v --cov=src/services

# E2E 테스트
cd frontend && npx playwright test tests/proposals/editor.spec.ts
```

---

## 변경 이력

| 날짜 | 변경 내용 | 이유 |
|------|----------|------|
| 2026-03-20 | 초기 테스트 명세 작성 | F-05 개발 시작 |
