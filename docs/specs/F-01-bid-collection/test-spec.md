# F-01 공고 자동 수집 및 매칭 -- 테스트 명세

## 참조
- 설계서: docs/specs/F-01-bid-collection/design.md
- 인수조건: docs/project/features.md #F-01

---

## 단위 테스트

### BidCollectorService

| 대상 | 시나리오 | 입력 | 예상 결과 |
|------|----------|------|-----------|
| collect_bids | 신규 공고 3건 수집 성공 | API 응답 mock (3건) | CollectionResult(new_count=3) |
| collect_bids | 중복 공고 필터링 | API 응답 mock (5건 중 2건 기존) | CollectionResult(new_count=3) |
| collect_bids | API 응답 빈 목록 | API 응답 mock (0건) | CollectionResult(new_count=0) |
| _fetch_from_api | 정상 응답 파싱 | mock JSON 응답 | 공고 dict 리스트 반환 |
| _fetch_from_api | 페이지네이션 처리 | totalCount=250, numOfRows=100 | 3페이지 순회, 250건 반환 |
| _retry_with_backoff | 1회 실패 후 성공 | 1차 TimeoutError, 2차 성공 | 정상 결과 반환 |
| _retry_with_backoff | 2회 실패 후 성공 | 1-2차 TimeoutError, 3차 성공 | 정상 결과 반환 |
| _retry_with_backoff | 3회 모두 실패 | 3차 모두 TimeoutError | CollectionError 발생 |
| _retry_with_backoff | 지수 백오프 대기 시간 | 3회 실패 | 대기 시간: 2s, 4s, 8s (근사) |
| _save_bid | API 응답 -> Bid 변환 | 공공데이터포털 응답 dict | Bid 객체 (필드 매핑 정확) |
| _save_bid | 필수 필드 누락 | title 없는 응답 | ValidationError |
| _save_attachments | 첨부파일 2건 저장 | 첨부파일 정보 리스트 | BidAttachment 2건 생성 |
| _is_duplicate | 기존 공고번호 | 이미 존재하는 bid_number | True |
| _is_duplicate | 신규 공고번호 | 존재하지 않는 bid_number | False |

### BidParserService

| 대상 | 시나리오 | 입력 | 예상 결과 |
|------|----------|------|-----------|
| parse_attachment | PDF 파싱 성공 | PDF 파일 경로 | 추출된 텍스트 문자열 |
| parse_attachment | HWP 파싱 성공 | HWP 파일 경로 (pyhwp 설치됨) | 추출된 텍스트 문자열 |
| parse_attachment | HWP 파싱 건너뜀 | HWP 파일 경로 (pyhwp 미설치) | None 반환, 경고 로그 |
| parse_attachment | 지원하지 않는 파일 타입 | XLSX 파일 | None 반환, 정보 로그 |
| _parse_pdf | 빈 PDF | 빈 PDF 파일 | 빈 문자열 |
| _parse_pdf | 다중 페이지 PDF | 3페이지 PDF | 전체 페이지 텍스트 결합 |
| _parse_pdf | 깨진 PDF | 손상된 PDF 파일 | None 반환 (예외 catch) |
| _download_file | 다운로드 성공 | 유효한 URL | 임시 파일 경로 |
| _download_file | 다운로드 실패 (404) | 존재하지 않는 URL | None 반환 |
| _download_file | 다운로드 타임아웃 | 느린 서버 URL | None 반환 |
| parse_all_for_bid | 3건 중 2건 파싱 성공 | 3개 첨부파일 (1개 HWP, pyhwp 미설치) | 반환값 2 |

### BidMatchService

| 대상 | 시나리오 | 입력 | 예상 결과 |
|------|----------|------|-----------|
| analyze_match | 높은 적합도 매칭 | 업종 일치 회사 + 유사 공고 | total_score >= 70, recommendation="recommended" |
| analyze_match | 낮은 적합도 매칭 | 업종 불일치 회사 + 공고 | total_score < 40, recommendation="not_recommended" |
| analyze_match | 보통 적합도 매칭 | 부분 일치 회사 + 공고 | 40 <= total_score < 70, recommendation="neutral" |
| analyze_match | 회사 프로필 없음 | company_id=None인 사용자 | AppException(COMPANY_001) |
| analyze_match | 공고 없음 | 존재하지 않는 bid_id | AppException(BID_001) |
| analyze_match | 기존 매칭 결과 있음 | 이미 매칭된 user+bid | 기존 결과 갱신 (upsert) |
| _build_company_text | 풀 프로필 | 회사 + 실적 3건 + 인증 2건 | 결합된 텍스트 (모든 정보 포함) |
| _build_company_text | 최소 프로필 | 회사 기본 정보만 (실적/인증 없음) | 업종 + 설명만 포함된 텍스트 |
| _build_bid_text | 첨부파일 포함 공고 | 공고 + 첨부파일 2건 (1건 파싱됨) | 공고 텍스트 + 파싱 텍스트 |
| _build_bid_text | 첨부파일 없는 공고 | 공고만 (첨부파일 없음) | 공고 제목 + 설명만 |
| _calculate_tfidf_similarity | 동일 텍스트 | 같은 텍스트 2개 | 1.0 (또는 근사) |
| _calculate_tfidf_similarity | 완전히 다른 텍스트 | 관련 없는 텍스트 2개 | 0.0에 가까운 값 |
| _calculate_tfidf_similarity | 빈 텍스트 | 빈 문자열 + 일반 텍스트 | 0.0 |
| _score_to_recommendation | 점수 85 | total_score=85 | ("recommended", "높은 적합도...") |
| _score_to_recommendation | 점수 55 | total_score=55 | ("neutral", "보통 적합도...") |
| _score_to_recommendation | 점수 25 | total_score=25 | ("not_recommended", "낮은 적합도...") |
| analyze_new_bids_for_all_users | 신규 공고 2건, 사용자 3명 | bid_ids 2개, 회사 보유 사용자 3명 | 6개 매칭 결과 생성 |
| analyze_new_bids_for_all_users | 회사 없는 사용자 제외 | 사용자 5명 중 3명만 회사 있음 | 3명 * 공고 수만 매칭 |
| _notify_high_score_matches | 70점 이상 매칭 2건 | 매칭 결과 리스트 | NotificationService.send 2회 호출 |

### NotificationService (스텁)

| 대상 | 시나리오 | 입력 | 예상 결과 |
|------|----------|------|-----------|
| send_bid_match_notification | 알림 전송 스텁 | user_id, bid_id, score=85 | 로그 기록 확인 (예외 없음) |
| send_admin_alert | 관리자 알림 스텁 | "수집 실패" 메시지 | 경고 로그 기록 확인 |

---

## 통합 테스트

### API 엔드포인트

| API | 시나리오 | 입력 | 예상 결과 |
|-----|----------|------|-----------|
| GET /api/v1/bids | 공고 목록 조회 (기본) | 인증 토큰 | 200, items 배열, meta 포함 |
| GET /api/v1/bids | 페이지네이션 | page=2, pageSize=10 | 200, meta.page=2, meta.pageSize=10 |
| GET /api/v1/bids | status 필터 | status=open | 200, 모든 items의 status="open" |
| GET /api/v1/bids | keyword 검색 | keyword=정보시스템 | 200, 제목/기관에 키워드 포함 |
| GET /api/v1/bids | region 필터 | region=서울 | 200, 모든 items의 region="서울" |
| GET /api/v1/bids | budget 범위 필터 | minBudget=100000000, maxBudget=500000000 | 200, 예산 범위 내 공고 |
| GET /api/v1/bids | 날짜 범위 필터 | startDate=2026-03-01, endDate=2026-03-31 | 200, 해당 기간 공고 |
| GET /api/v1/bids | 정렬 | sortBy=budget, sortOrder=desc | 200, budget 내림차순 |
| GET /api/v1/bids | 인증 없음 | 토큰 없음 | 401, AUTH_002 |
| GET /api/v1/bids/{id} | 공고 상세 조회 | 존재하는 bid_id | 200, 공고 상세 + attachments |
| GET /api/v1/bids/{id} | 존재하지 않는 공고 | 없는 bid_id | 404, BID_001 |
| GET /api/v1/bids/{id}/matches | 매칭 결과 조회 (기존 결과) | 매칭 분석된 bid_id | 200, 매칭 점수 포함 |
| GET /api/v1/bids/{id}/matches | 매칭 결과 조회 (신규 분석) | 미분석 bid_id | 200, 새로 분석된 매칭 결과 |
| GET /api/v1/bids/{id}/matches | 회사 미등록 사용자 | company_id=NULL인 사용자 | 404, COMPANY_001 |
| GET /api/v1/bids/matched | 매칭 공고 목록 | 인증 토큰, 회사 등록 사용자 | 200, totalScore 내림차순 |
| GET /api/v1/bids/matched | 점수 필터 | minScore=70 | 200, 모든 totalScore >= 70 |
| GET /api/v1/bids/matched | 추천 필터 | recommendation=recommended | 200, 모든 recommendation="recommended" |
| POST /api/v1/bids/collect | 수동 수집 (관리자) | owner 역할 토큰 | 202, 수집 시작 메시지 |
| POST /api/v1/bids/collect | 수동 수집 (권한 없음) | member 역할 토큰 | 403, PERMISSION_001 |
| POST /api/v1/bids/collect | 수집 이미 진행 중 | 잠금 상태에서 요청 | 409, BID_004 |

### 수집 파이프라인 통합

| 시나리오 | 전제 조건 | 예상 결과 |
|----------|----------|-----------|
| 전체 수집 플로우 | API mock 응답 5건, PDF 첨부 2건 | bids 5건 저장, attachments 2건 저장, extracted_text 채워짐 |
| 수집 + 매칭 플로우 | 신규 공고 3건, 회사 등록 사용자 2명 | user_bid_matches 6건 생성 |
| 수집 + 매칭 + 알림 | 매칭 결과 중 70점 이상 2건 | NotificationService 2회 호출, is_notified=True |

---

## 경계 조건 / 에러 케이스

### 수집 관련
- 공공데이터포털 API가 500 응답 반환 시: 지수 백오프 재시도 3회, 모두 실패 시 관리자 알림
- 공공데이터포털 API가 빈 결과 반환 시: CollectionResult(new_count=0), 에러 아님
- API 응답에 필수 필드(bidNtceNo) 누락 시: 해당 건 건너뛰고 로그 기록
- API Key 미설정 시: 수집 시작 전 설정 검증, 로그 경고 + 스킵
- 수집 중 DB 커넥션 에러: 트랜잭션 롤백, 관리자 알림
- 동시 수집 요청 시: Redis 잠금으로 두 번째 요청 거부 (BID_004)

### 파싱 관련
- PDF가 0바이트 파일인 경우: 빈 문자열 반환
- PDF가 이미지 전용 (OCR 필요) 경우: 빈 문자열 반환 (MVP에서 OCR 미지원)
- HWP 파일인데 pyhwp 미설치: None 반환, 로그 경고 (graceful degradation)
- 파일 다운로드 URL 만료: None 반환, 로그 기록
- 파싱 중 메모리 초과: 예외 catch, 해당 파일 건너뜀

### 매칭 관련
- 회사 설명이 빈 문자열인 경우: 업종만으로 매칭 (점수 낮을 수 있음)
- 공고에 첨부파일 텍스트가 없는 경우: 제목 + 설명만으로 매칭
- 둘 다 빈 텍스트인 경우: total_score=0
- 동일 사용자-공고 매칭이 이미 존재: upsert (갱신)
- 사용자의 회사가 soft-deleted 상태: 매칭 대상에서 제외
- TF-IDF 벡터가 0인 경우 (용어 겹침 없음): 유사도 0, total_score=0

### API 관련
- pageSize > 100 요청 시: 100으로 제한
- page < 1 요청 시: 1로 보정
- 잘못된 sortBy 값: VALIDATION_001 (400)
- 잘못된 status 값: VALIDATION_001 (400)
- UUID 형식이 아닌 bid_id: 422 (FastAPI 자동 처리)

---

## 회귀 테스트

| 기존 기능 | 영향 여부 | 검증 방법 |
|-----------|-----------|-----------|
| F-07 인증 | 영향 없음 | 기존 auth 테스트 실행 확인 |
| F-08 회사 프로필 | 읽기 전용 참조 | 회사 프로필 CRUD 테스트 실행, 매칭이 회사 데이터를 변경하지 않음 확인 |
| Settings | nara_api_key 추가 | 기존 설정 필드 기본값 유지, 신규 필드 optional |
| main.py lifespan | APScheduler 추가 | scheduler_enabled=False로 테스트 시 스케줄러 비활성화 확인 |
| API 라우터 | bids 라우터 추가 | 기존 /auth, /proposals 라우터 정상 동작 확인 |

---

## Mock 전략

### 공공데이터포털 API Mock

```python
# tests/fixtures/nara_api_responses.py

SAMPLE_BID_LIST_RESPONSE = {
    "response": {
        "header": {"resultCode": "00", "resultMsg": "NORMAL SERVICE."},
        "body": {
            "items": [
                {
                    "bidNtceNo": "20260308001",
                    "bidNtceOrd": "00",
                    "bidNtceNm": "2026년 정보시스템 고도화 사업",
                    "ntceInsttNm": "행정안전부",
                    "dminsttNm": "정보화전략과",
                    "presmptPrce": "500000000",
                    "bidNtceDt": "2026/03/08",
                    "bidClseDt": "2026/03/22 17:00:00",
                    "opengDt": "2026/03/23 10:00:00",
                    "ntceKindNm": "일반경쟁",
                    "cntrctMthdNm": "적격심사",
                }
            ],
            "numOfRows": 100,
            "pageNo": 1,
            "totalCount": 1,
        }
    }
}

EMPTY_BID_LIST_RESPONSE = {
    "response": {
        "header": {"resultCode": "00", "resultMsg": "NORMAL SERVICE."},
        "body": {"items": [], "numOfRows": 100, "pageNo": 1, "totalCount": 0}
    }
}
```

### HTTP 클라이언트 Mock

```python
# httpx.AsyncClient를 pytest-httpx 또는 respx로 mock
# 또는 의존성 주입으로 mock client 전달

class MockHttpClient:
    """테스트용 HTTP 클라이언트"""
    def __init__(self, responses: dict[str, Any]):
        self.responses = responses
        self.call_log = []

    async def get(self, url: str, **kwargs) -> MockResponse:
        self.call_log.append(("GET", url, kwargs))
        return MockResponse(self.responses.get(url, {}))
```

### 파일 파싱 Mock

```python
# 테스트용 PDF/HWP 파일 fixture
# tests/fixtures/files/sample.pdf — pdfplumber로 읽을 수 있는 테스트 PDF
# tests/fixtures/files/sample.hwp — pyhwp로 읽을 수 있는 테스트 HWP (선택적)

# BidParserService mock (통합 테스트 시)
class MockBidParserService:
    """파싱 서비스 mock"""
    async def parse_attachment(self, attachment):
        if attachment.file_type == "PDF":
            return "추출된 PDF 텍스트 내용"
        return None

    async def parse_all_for_bid(self, bid_id, attachments):
        return len([a for a in attachments if a.file_type == "PDF"])
```

### DB 테스트 전략

```python
# 패턴 1: 인메모리 저장소 (F-08 패턴 참조)
# — 단위 테스트에서 빠른 실행
# — BidCollectorService, BidMatchService에 인메모리 구현 제공

# 패턴 2: 실제 DB (통합 테스트)
# — pytest-asyncio + async session fixture
# — 테스트별 트랜잭션 롤백으로 격리

# 테스트 데이터 시드
async def seed_test_data(db: AsyncSession):
    """통합 테스트용 데이터 시드"""
    # 사용자 생성
    user = User(email="test@example.com", name="테스트", ...)
    # 회사 생성
    company = Company(business_number="1234567890", name="테스트회사", industry="소프트웨어", ...)
    # 실적 생성
    perf = Performance(company_id=company.id, project_name="테스트 사업", ...)
    # 인증 생성
    cert = Certification(company_id=company.id, name="GS인증", ...)
    # 공고 생성
    bid = Bid(bid_number="TEST-001", title="정보시스템 구축", ...)
```

---

## 테스트 파일 구조

```
backend/tests/
├── unit/
│   ├── test_bid_collector_service.py    # BidCollectorService 단위 테스트
│   ├── test_bid_parser_service.py       # BidParserService 단위 테스트
│   ├── test_bid_match_service.py        # BidMatchService 단위 테스트
│   └── test_notification_service.py     # NotificationService 스텁 테스트
├── integration/
│   ├── test_bids_api.py                 # 공고 API 통합 테스트
│   └── test_collection_pipeline.py      # 수집 파이프라인 통합 테스트
└── fixtures/
    ├── nara_api_responses.py            # API 응답 mock 데이터
    └── files/
        └── sample.pdf                   # 테스트용 PDF 파일
```
