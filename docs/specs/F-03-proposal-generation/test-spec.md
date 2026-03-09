# F-03 제안서 AI 초안 생성 -- 테스트 명세

## 참조
- 설계서: docs/specs/F-03-proposal-generation/design.md
- 인수조건: docs/project/features.md #F-03

---

## 단위 테스트

### ProposalService

| 대상 | 시나리오 | 입력 | 예상 결과 |
|------|----------|------|-----------|
| create_proposal | 정상 생성 | 유효한 bid_id, user_id (회사 소속) | proposals 레코드 생성, status='generating', 6개 빈 sections 생성 |
| create_proposal | 소속 회사 없음 | company_id가 없는 user_id | COMPANY_001 (404) 예외 |
| create_proposal | 존재하지 않는 공고 | 잘못된 bid_id | BID_001 (404) 예외 |
| create_proposal | 마감된 공고 | status='closed'인 bid_id | BID_002 (400) 예외 |
| create_proposal | 제목 미입력 시 자동 생성 | title=None | 공고명 기반 제목 자동 생성 확인 |
| create_proposal | 섹션 일부만 지정 | sections=["overview", "technical"] | 2개 sections만 생성 |
| get_proposal | 정상 조회 | 유효한 proposal_id, 소유자 user_id | proposal + sections 반환 |
| get_proposal | 소유자 아님 | 다른 user_id | PROPOSAL_002 (403) 예외 |
| get_proposal | 존재하지 않는 제안서 | 잘못된 proposal_id | PROPOSAL_001 (404) 예외 |
| get_proposal | Soft Delete된 제안서 | deleted_at 설정된 proposal | PROPOSAL_001 (404) 예외 |
| list_proposals | 빈 목록 | 제안서 없는 사용자 | items=[], total=0 |
| list_proposals | 필터 적용 (status) | status='ready' | ready 상태만 반환 |
| list_proposals | 필터 적용 (bidId) | 특정 bid_id | 해당 공고 제안서만 반환 |
| list_proposals | 페이지네이션 | page=2, pageSize=10, total=25 | 10건 반환, totalPages=3 |
| update_proposal_status | 정상 갱신 | status='ready' | status 변경 확인 |
| save_section_content | 정상 저장 | section_key='overview', content='...' | content 갱신, updated_at 갱신 |
| finalize_proposal | 정상 완료 | 모든 섹션 생성 완료된 proposal | status='ready', word_count 계산, generated_at 설정, 버전 스냅샷 생성 |
| create_version_snapshot | 정상 스냅샷 | 유효한 proposal | version_number 증가, snapshot JSONB에 전체 섹션 저장 |

### ProposalGeneratorService

| 대상 | 시나리오 | 입력 | 예상 결과 |
|------|----------|------|-----------|
| _build_bid_context | 공고 + 첨부파일 | bid + 2개 attachments (1개 파싱 완료) | title, description, attachment_texts(1건) 포함 dict |
| _build_bid_context | 첨부파일 없는 공고 | bid만 | attachment_texts=[] |
| _build_company_context | 회사 + 실적 + 인증 | company, 5개 performances, 3개 certifications | 정리된 dict |
| _build_company_context | 실적/인증 없음 | company만 | performances=[], certifications=[] |
| _select_relevant_performances | 관련 실적 선별 | 10개 performances, bid 정보 | 대표 실적 우선, 키워드 유사 실적 포함, 최대 10건 |
| _select_relevant_performances | 대표 실적만 있음 | 3개 대표 실적 | 3건 반환 (대표 우선) |
| _render_prompt | overview 섹션 | bid_context, company_context | 유효한 프롬프트 문자열 (공고 정보 + 회사 정보 포함) |
| _render_prompt | custom_instructions 포함 | 추가 지시사항 있음 | 프롬프트에 custom_instructions 포함 |
| _render_prompt | previous_sections 포함 | 이전 2개 섹션 | 프롬프트에 이전 섹션 요약 포함 |
| _generate_section | 정상 생성 (Mock) | Claude API Mock | 유효한 Markdown 텍스트 반환 |
| _generate_section | API 타임아웃 | 30초 초과 Mock | PROPOSAL_004 예외 |
| _generate_section | API 에러 | 500 응답 Mock | PROPOSAL_003 예외 |
| regenerate_section | 정상 재생성 | 유효한 proposal_id, section_key | 섹션 내용 갱신, is_ai_generated=True |
| regenerate_section | 존재하지 않는 섹션 | 잘못된 section_key | PROPOSAL_006 (404) 예외 |

### ProposalExportService

| 대상 | 시나리오 | 입력 | 예상 결과 |
|------|----------|------|-----------|
| export_docx | 정상 DOCX 생성 | proposal + 6개 sections | 유효한 DOCX 바이너리 (크기 > 0) |
| export_docx | 빈 섹션 포함 | 일부 섹션 content=None | 빈 섹션은 건너뛰고 생성 |
| export_pdf | 정상 PDF 생성 | proposal + 6개 sections | 유효한 PDF 바이너리 (%PDF- 매직바이트) |
| export_pdf | 한글 포함 | 한국어 내용 | 깨짐 없이 렌더링 |

---

## 통합 테스트

### API 통합 테스트

| API | 시나리오 | 입력 | 예상 결과 |
|-----|----------|------|-----------|
| POST /proposals | 정상 제안서 생성 | 유효한 bidId, 인증 토큰 | 201, proposalId 반환, status='generating' |
| POST /proposals | 인증 없이 요청 | 토큰 없음 | 401, AUTH_002 |
| POST /proposals | 잘못된 bidId | 존재하지 않는 UUID | 404, BID_001 |
| POST /proposals | 마감된 공고 | status='closed'인 bid | 400, BID_002 |
| POST /proposals | 회사 미소속 사용자 | company_id=None인 user | 404, COMPANY_001 |
| GET /proposals/{id}/generate/stream | SSE 스트리밍 정상 | 유효한 proposal_id, token | text/event-stream 응답, start -> progress -> section(6건) -> complete |
| GET /proposals/{id}/generate/stream | 존재하지 않는 제안서 | 잘못된 id | 404, PROPOSAL_001 |
| GET /proposals/{id}/generate/stream | 소유자 아닌 사용자 | 다른 사용자 토큰 | 403, PROPOSAL_002 |
| POST /proposals/{id}/sections/{key}/regenerate | 정상 재생성 | overview 섹션, custom_instructions | 200, 갱신된 content |
| POST /proposals/{id}/sections/{key}/regenerate | 존재하지 않는 섹션 | 잘못된 section_key | 404, PROPOSAL_006 |
| GET /proposals | 목록 조회 | page=1, pageSize=10 | 200, items + meta |
| GET /proposals | status 필터 | status=ready | 200, ready 상태만 |
| GET /proposals/{id} | 상세 조회 | 유효한 proposal_id | 200, proposal + sections |
| GET /proposals/{id}/download | DOCX 다운로드 | format=docx | 200, Content-Type: application/vnd.openxmlformats... |
| GET /proposals/{id}/download | PDF 다운로드 | format=pdf | 200, Content-Type: application/pdf |
| GET /proposals/{id}/download | 소유자 아님 | 다른 사용자 토큰 | 403, PROPOSAL_002 |

### SSE 스트리밍 상세 테스트

| 시나리오 | 검증 항목 | 예상 결과 |
|----------|-----------|-----------|
| 정상 6섹션 생성 | 이벤트 순서 | start(1) -> progress(6) -> section(6) -> complete(1) |
| 정상 6섹션 생성 | progress percent | 17, 33, 50, 67, 83, 100 (순차 증가) |
| 정상 6섹션 생성 | section 이벤트 데이터 | sectionKey, title, content(비어있지 않음), wordCount > 0 |
| 정상 6섹션 생성 | complete 이벤트 데이터 | totalSections=6, totalWordCount > 0, generatedAt |
| 3분 내 완료 (AC-03) | 전체 생성 시간 | 180초 이내 |
| 중간 섹션 실패 | 에러 이벤트 | error 이벤트 발행, 이전 완료 섹션은 DB에 저장됨 |
| 클라이언트 연결 끊김 | 생성 중단 | GeneratorExit 처리, 부분 저장된 섹션 유지 |

---

## 경계 조건 / 에러 케이스

### 입력 검증
- bidId가 UUID 형식이 아닌 경우 -> 422 Unprocessable Entity
- sections에 유효하지 않은 section_key 포함 -> 400 VALIDATION_001
- sections 빈 배열 -> 400 VALIDATION_001
- customInstructions가 10000자 초과 -> 400 VALIDATION_003
- format 파라미터에 docx/pdf 외의 값 -> 400 VALIDATION_001

### AI 생성 관련
- Claude API 키 미설정 (anthropic_api_key='') -> 500 PROPOSAL_003
- Claude API Rate Limit -> 429 RATE_LIMIT_002
- Claude API 응답이 빈 문자열 -> 재시도 1회 후 PROPOSAL_003
- 전체 생성 시간 3분 초과 -> SSE error 이벤트 (PROPOSAL_004)
- 섹션당 30초 초과 -> 해당 섹션 건너뛰고 다음 섹션 진행

### 데이터 관련
- 공고에 첨부파일이 없는 경우 -> 첨부파일 없이 기본 정보만으로 생성
- 첨부파일 텍스트 추출 실패 (extracted_text=NULL) -> 해당 첨부파일 건너뜀
- 회사에 실적/인증이 없는 경우 -> 실적/인증 없이 생성 (프롬프트에서 해당 섹션 생략)
- 동일 공고에 이미 generating 상태 제안서 존재 -> PROPOSAL_007 (400)

### 동시성
- 동일 제안서에 대한 동시 generate/stream 요청 -> 먼저 도착한 요청만 처리, 후속 요청은 PROPOSAL_007
- 생성 중 섹션 재생성 요청 -> PROPOSAL_007 (generating 상태에서 재생성 불가)

---

## 회귀 테스트

| 기존 기능 | 영향 여부 | 검증 방법 |
|-----------|-----------|-----------|
| F-01 공고 목록 조회 (GET /bids) | 영향 없음 (읽기 전용 참조) | 기존 bids API 테스트 재실행 |
| F-01 공고 상세 조회 (GET /bids/{id}) | 영향 없음 | 기존 테스트 재실행 |
| F-07 인증 (GET /auth/*) | 영향 없음 | 로그인/토큰 갱신 테스트 |
| F-08 회사 프로필 (GET /companies/*) | 영향 없음 (읽기 전용 참조) | 회사 CRUD 테스트 재실행 |
| models/__init__.py 변경 | Alembic 마이그레이션 | 기존 모델 import 정상 확인, 기존 테이블 영향 없음 |
| config.py 변경 | 새 설정 필드 추가 | 기존 설정 로드 정상, 기본값으로 기존 동작 영향 없음 |

---

## 성능 테스트 기준

| 항목 | 기준 | 근거 |
|------|------|------|
| 10페이지 제안서 생성 시간 | 3분 이내 | AC-03 |
| DOCX 다운로드 응답 시간 | 10초 이내 | AC-05 |
| PDF 다운로드 응답 시간 | 10초 이내 | AC-05 |
| 제안서 목록 조회 응답 시간 | 500ms 이내 | 일반 API 기준 |
| 제안서 상세 조회 응답 시간 | 1초 이내 | 섹션 데이터 포함 |
| 평가 항목 반영률 | 90% 이상 | AC-04 |
