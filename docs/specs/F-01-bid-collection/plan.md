# F-01 공고 자동 수집 및 매칭 -- 구현 계획서

## 참조
- 설계서: docs/specs/F-01-bid-collection/design.md
- 인수조건: docs/project/features.md #F-01
- 테스트 명세: docs/specs/F-01-bid-collection/test-spec.md

---

## 태스크 목록

### Phase 1: 백엔드 구현

#### T1: 모델 및 DB 마이그레이션
- [ ] [backend] `backend/src/models/bid.py` — Bid 모델 (bids 테이블)
- [ ] [backend] `backend/src/models/bid_attachment.py` — BidAttachment 모델 (bid_attachments 테이블)
- [ ] [backend] `backend/src/models/user_bid_match.py` — UserBidMatch 모델 (user_bid_matches 테이블)
- [ ] [backend] `backend/src/models/__init__.py` — Bid, BidAttachment, UserBidMatch import 추가
- [ ] [backend] Alembic 마이그레이션 파일 생성 (bids, bid_attachments, user_bid_matches 신규 테이블 + 인덱스)

| 태스크 | 설명 | 파일 |
|--------|------|------|
| T1-1 | Bid SQLAlchemy 모델 | backend/src/models/bid.py |
| T1-2 | BidAttachment SQLAlchemy 모델 | backend/src/models/bid_attachment.py |
| T1-3 | UserBidMatch SQLAlchemy 모델 | backend/src/models/user_bid_match.py |
| T1-4 | 모델 __init__ 등록 | backend/src/models/__init__.py |
| T1-5 | Alembic 마이그레이션 파일 | backend/alembic/versions/xxxx_add_bids_tables.py |

#### T2: Pydantic 스키마
- [ ] [backend] `backend/src/schemas/bid.py` — BidListItem, BidDetail, BidListResponse, BidQuery 스키마
- [ ] [backend] `backend/src/schemas/bid_match.py` — UserBidMatchResponse, MatchedBidListItem, MatchedBidListResponse 스키마

| 태스크 | 설명 | 파일 |
|--------|------|------|
| T2-1 | 공고 관련 Pydantic 스키마 | backend/src/schemas/bid.py |
| T2-2 | 매칭 관련 Pydantic 스키마 | backend/src/schemas/bid_match.py |

#### T3: 공고 수집 서비스
- [ ] [backend] `backend/src/services/bid_collector_service.py` — BidCollectorService 구현
  - `collect_bids()` — 수집 메인 플로우
  - `_fetch_from_api()` — 공공데이터포털 나라장터 API 호출 (getBidPblancListInfoServc)
  - `_retry_with_backoff()` — 지수 백오프 재시도 (2s, 4s, 8s, 최대 3회)
  - `_save_bid()` — API 응답 Bid 모델 변환 및 저장
  - `_save_attachments()` — 첨부파일 정보 저장
  - `_is_duplicate()` — bid_number 기준 중복 확인

| 태스크 | 설명 | 파일 |
|--------|------|------|
| T3-1 | BidCollectorService 구현 | backend/src/services/bid_collector_service.py |

#### T4: 첨부파일 파싱 서비스
- [ ] [backend] `backend/src/services/bid_parser_service.py` — BidParserService 구현
  - `parse_attachment()` — 파싱 메인 플로우 (다운로드 → 파서 선택 → 텍스트 추출)
  - `_download_file()` — 파일 다운로드 (임시 경로 반환)
  - `_parse_pdf()` — PDF 텍스트 추출 (pdfplumber)
  - `_parse_hwp()` — HWP 텍스트 추출 (pyhwp, graceful degradation)
  - `parse_all_for_bid()` — 공고 전체 첨부파일 파싱

| 태스크 | 설명 | 파일 |
|--------|------|------|
| T4-1 | BidParserService 구현 | backend/src/services/bid_parser_service.py |

#### T5: 매칭 분석 서비스 + 알림 스텁
- [ ] [backend] `backend/src/services/bid_match_service.py` — BidMatchService 구현
  - `analyze_match()` — 단일 공고-사용자 매칭 분석
  - `analyze_new_bids_for_all_users()` — 신규 공고 전체 사용자 매칭
  - `_build_company_text()` — 회사 프로필 텍스트 생성 (TF-IDF 입력)
  - `_build_bid_text()` — 공고 텍스트 생성 (TF-IDF 입력)
  - `_calculate_tfidf_similarity()` — TF-IDF 코사인 유사도 계산 (scikit-learn)
  - `_score_to_recommendation()` — 점수 → 추천 등급 변환 (70+: recommended, 40~69: neutral, 0~39: not_recommended)
  - `_notify_high_score_matches()` — 70점 이상 알림 발송 (NotificationService 호출)
- [ ] [backend] `backend/src/services/notification_service.py` — NotificationService 스텁 구현
  - `send_bid_match_notification()` — 로그만 기록
  - `send_admin_alert()` — 로그만 기록

| 태스크 | 설명 | 파일 |
|--------|------|------|
| T5-1 | BidMatchService 구현 | backend/src/services/bid_match_service.py |
| T5-2 | NotificationService 스텁 구현 | backend/src/services/notification_service.py |

#### T6: APScheduler 통합 + API 라우터
- [ ] [backend] `backend/src/services/scheduler.py` — APScheduler 설정 및 scheduled_collect_bids() 작업 함수
  - Redis 기반 동시 실행 방지 (SETNX, TTL 600s)
  - 수집 → 파싱 → 매칭 순차 파이프라인
- [ ] [backend] `backend/src/api/v1/bids.py` — 공고 API 엔드포인트 구현
  - GET /api/v1/bids — 공고 목록 조회 (필터, 페이지네이션)
  - GET /api/v1/bids/matched — 사용자 매칭 공고 목록 조회
  - GET /api/v1/bids/{id} — 공고 상세 조회
  - GET /api/v1/bids/{id}/matches — 공고별 매칭 결과 조회 (lazy evaluation)
  - POST /api/v1/bids/collect — 수동 수집 트리거 (owner 전용)
- [ ] [backend] `backend/src/config.py` — NARA_API_KEY, scheduler_enabled 등 설정 추가
- [ ] [backend] `backend/src/main.py` — APScheduler lifespan 통합
- [ ] [backend] `backend/src/api/v1/router.py` — bids 라우터 include 추가
- [ ] [backend] `requirements.txt` — apscheduler, httpx, scikit-learn, pdfplumber, pyhwp 의존성 추가

| 태스크 | 설명 | 파일 |
|--------|------|------|
| T6-1 | APScheduler 스케줄러 모듈 | backend/src/services/scheduler.py |
| T6-2 | 공고 API 엔드포인트 | backend/src/api/v1/bids.py |
| T6-3 | config.py 설정 추가 | backend/src/config.py |
| T6-4 | main.py lifespan 통합 | backend/src/main.py |
| T6-5 | router.py 라우터 등록 | backend/src/api/v1/router.py |
| T6-6 | requirements.txt 의존성 | backend/requirements.txt |
| T6-7 | 백엔드 API 스펙 문서 작성 | docs/api/F-01-bid-collection.md |
| T6-8 | 백엔드 DB 스키마 문서 작성 | docs/db/F-01-bid-collection.md |

---

### Phase 2: 프론트엔드 구현

#### T7: 타입 정의 + API 클라이언트
- [ ] [frontend] `frontend/src/types/bid.ts` — Bid, BidDetail, BidAttachment, BidListResponse 타입 정의
- [ ] [frontend] `frontend/src/types/bid-match.ts` — UserBidMatch, MatchedBidListResponse 타입 정의
- [ ] [frontend] `frontend/src/lib/api/bids.ts` — 공고 API 클라이언트 함수
  - `getBids(params)` — 공고 목록 조회
  - `getBid(id)` — 공고 상세 조회
  - `getBidMatches(bidId)` — 공고별 매칭 결과 조회
  - `getMatchedBids(params)` — 매칭 공고 목록 조회
  - `triggerCollect()` — 수동 수집 트리거

| 태스크 | 설명 | 파일 |
|--------|------|------|
| T7-1 | 공고 TypeScript 타입 정의 | frontend/src/types/bid.ts |
| T7-2 | 매칭 TypeScript 타입 정의 | frontend/src/types/bid-match.ts |
| T7-3 | 공고 API 클라이언트 | frontend/src/lib/api/bids.ts |

#### T8: 상태 관리 (Zustand 스토어)
- [ ] [frontend] `frontend/src/store/bid-store.ts` — 공고 목록/필터/선택 상태 관리
  - bids, totalCount, currentPage, filters 상태
  - fetchBids, setFilter, resetFilter 액션
- [ ] [frontend] `frontend/src/store/matched-bid-store.ts` — 매칭 공고 상태 관리
  - matchedBids, fetchMatchedBids 액션

| 태스크 | 설명 | 파일 |
|--------|------|------|
| T8-1 | 공고 Zustand 스토어 | frontend/src/store/bid-store.ts |
| T8-2 | 매칭 공고 Zustand 스토어 | frontend/src/store/matched-bid-store.ts |

#### T9: UI 컴포넌트 + 페이지 통합
- [ ] [frontend] `frontend/src/components/bids/BidCard.tsx` — 공고 카드 컴포넌트 (목록 아이템)
- [ ] [frontend] `frontend/src/components/bids/BidFilterBar.tsx` — 필터 바 (상태, 키워드, 지역, 분류, 예산 범위)
- [ ] [frontend] `frontend/src/components/bids/BidMatchBadge.tsx` — 매칭 점수 + 추천 등급 배지
- [ ] [frontend] `frontend/src/components/bids/BidAttachmentList.tsx` — 첨부파일 목록
- [ ] [frontend] `frontend/src/app/(dashboard)/bids/page.tsx` — 공고 목록 페이지
- [ ] [frontend] `frontend/src/app/(dashboard)/bids/[id]/page.tsx` — 공고 상세 페이지 (첨부파일, 매칭 결과 포함)
- [ ] [frontend] `frontend/src/app/(dashboard)/bids/matched/page.tsx` — 매칭 공고 목록 페이지 (점수 높은 순)

| 태스크 | 설명 | 파일 |
|--------|------|------|
| T9-1 | BidCard 컴포넌트 | frontend/src/components/bids/BidCard.tsx |
| T9-2 | BidFilterBar 컴포넌트 | frontend/src/components/bids/BidFilterBar.tsx |
| T9-3 | BidMatchBadge 컴포넌트 | frontend/src/components/bids/BidMatchBadge.tsx |
| T9-4 | BidAttachmentList 컴포넌트 | frontend/src/components/bids/BidAttachmentList.tsx |
| T9-5 | 공고 목록 페이지 | frontend/src/app/(dashboard)/bids/page.tsx |
| T9-6 | 공고 상세 페이지 | frontend/src/app/(dashboard)/bids/[id]/page.tsx |
| T9-7 | 매칭 공고 목록 페이지 | frontend/src/app/(dashboard)/bids/matched/page.tsx |

---

### Phase 3: 검증
- [ ] [shared] 통합 테스트 실행 (pytest: 공고 수집 API, 매칭 API)
- [ ] [shared] quality-gate 검증 (보안, 성능, 코드 리뷰)

---

## 태스크 의존성

```
T1 (모델/마이그레이션)
  └─▶ T2 (스키마)
        └─▶ T3 (수집 서비스)
              └─▶ T4 (파싱 서비스)
                    └─▶ T5 (매칭 서비스 + 알림 스텁)
                          └─▶ T6 (스케줄러 + API 라우터)
                                └─▶ Phase 3 (검증)

T7 (타입 + API 클라이언트) ─▶ T8 (스토어) ─▶ T9 (컴포넌트 + 페이지)
                                                      └─▶ Phase 3 (검증)

Phase 1 (T6 완료) ──▶ Phase 2 시작 가능 (API 계약 확정 후)
Phase 1 + Phase 2 ──▶ Phase 3
```

---

## 병렬 실행 판단

- Agent Team 권장: Yes
- 근거:
  - 백엔드(T1~T6)와 프론트엔드(T7~T9)는 API 계약(스키마)이 design.md에 확정되어 있으므로 독립적으로 개발 가능
  - 프론트엔드는 mock API 또는 타입 정의를 먼저 작성하고 백엔드 완료 후 연동 검증
  - 백엔드는 DB 마이그레이션부터 순차 진행 (T1 → T2 → T3 → T4 → T5 → T6)
  - 프론트엔드는 타입/스토어/컴포넌트 순으로 독립 진행 (T7 → T8 → T9)
  - Phase 3 통합 검증은 양쪽 완료 후 진행
