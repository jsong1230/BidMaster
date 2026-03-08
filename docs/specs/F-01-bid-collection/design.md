# F-01 공고 자동 수집 및 매칭 -- 변경 설계서

## 1. 참조
- 인수조건: docs/project/features.md #F-01
- 시스템 분석: docs/system/system-analysis.md
- ERD: docs/system/erd.md (bids, bid_attachments, user_bid_matches)
- API 컨벤션: docs/system/api-conventions.md
- 회사 프로필 설계: docs/specs/F-08-company-profile/design.md

---

## 2. 변경 범위

- **변경 유형**: 신규 추가
- **영향 받는 모듈**:
  - Settings (NARA_API_KEY, 스케줄러 설정 추가)
  - FastAPI lifespan (APScheduler 통합)
  - 모델 __init__.py (Bid, BidAttachment, UserBidMatch 등록)
  - API 라우터 (bids 라우터 등록)

---

## 3. 영향 분석

### 기존 API 변경

| API | 현재 | 변경 후 | 하위 호환성 |
|-----|------|---------|-------------|
| (없음) | - | 신규 API 추가 | 해당 없음 |

### 기존 DB 변경

| 테이블 | 변경 내용 | 마이그레이션 전략 |
|--------|----------|------------------|
| (없음) | bids, bid_attachments, user_bid_matches 신규 생성 | 신규 마이그레이션 파일 |

### 기존 모델 변경

| 파일 | 변경 내용 |
|------|----------|
| backend/src/models/__init__.py | Bid, BidAttachment, UserBidMatch 모델 import 추가 |
| backend/src/api/v1/router.py | bids 라우터 include 추가 |
| backend/src/config.py | NARA_API_KEY 등 설정 추가 |
| backend/src/main.py | APScheduler lifespan 통합 |

### 사이드 이펙트
- companies 테이블의 profile_embedding 컬럼을 매칭에 활용 (현재 nullable, F-08에서 스텁 처리됨)
- MVP에서는 TF-IDF 키워드 기반 매칭을 사용하므로 profile_embedding 없이도 동작
- performances 테이블의 데이터를 매칭 역량 점수 산출에 참조
- certifications 테이블의 데이터를 매칭 역량 점수 산출에 참조
- AC-04 알림은 NotificationService 스텁으로 처리 (F-10에서 실제 구현)

---

## 4. 아키텍처 결정

### 결정 1: 나라장터 API 연동 방식
- **선택지**: A) 직접 스크래핑 / B) 공공데이터포털 Open API
- **결정**: B) 공공데이터포털 Open API
- **근거**:
  - 공식 API로 안정적 데이터 제공
  - 법적 리스크 없음
  - XML/JSON 구조화된 응답
  - API Key 기반 인증으로 관리 용이

### 결정 2: 스케줄러 기술
- **선택지**: A) Celery Beat / B) APScheduler / C) cron + 외부 호출
- **결정**: B) APScheduler
- **근거**:
  - 단일 프로세스, FastAPI lifespan에 통합 가능
  - 경량 (Celery 대비 인프라 불필요: 별도 broker, worker)
  - MVP 규모에 적합 (수집 주기 3회/일)
  - 추후 Celery로 전환 시 서비스 레이어만 변경

### 결정 3: 매칭 알고리즘
- **선택지**: A) pgvector 코사인 유사도 / B) TF-IDF 키워드 유사도 / C) 하이브리드
- **결정**: B) TF-IDF 키워드 유사도 (scikit-learn)
- **근거**:
  - MVP에서 임베딩 모델 의존성 제거 (OpenAI API 비용 절감)
  - scikit-learn만으로 구현 가능, 외부 API 호출 불필요
  - 회사 프로필 텍스트(업종, 설명, 실적, 인증) + 공고 텍스트로 유사도 산출
  - 추후 F-02 구현 시 pgvector 임베딩으로 고도화 가능

### 결정 4: 첨부파일 파싱 전략
- **선택지**: A) 파싱 즉시 실행 (동기) / B) 파싱 후처리 (비동기 태스크)
- **결정**: A) 파싱 즉시 실행 (동기, 수집 파이프라인 내)
- **근거**:
  - 수집 자체가 백그라운드 스케줄러에서 실행되므로 사용자 요청 차단 없음
  - 파싱 완료 후 매칭 분석 진행해야 하므로 순차 처리가 자연스러움
  - pyhwp ImportError 시 graceful degradation (HWP 파싱 건너뜀, 로그 기록)

### 결정 5: 재시도 전략
- **선택지**: A) 단순 재시도 / B) 지수 백오프 재시도
- **결정**: B) 지수 백오프 재시도 (AC-05 요구사항)
- **근거**:
  - 공공데이터포털 서버 부하 시 적절한 대기 시간 확보
  - 최대 3회 재시도 (2초, 4초, 8초 간격)
  - 3회 모두 실패 시 관리자 알림 (로그 + NotificationService 스텁)

---

## 5. API 설계

### 5.1 GET /api/v1/bids
공고 목록 조회

- **목적**: 수집된 공고 목록 조회 (페이지네이션, 필터링)
- **인증**: 필요 (Bearer Token)
- **Query Parameters**:
  | Parameter | Type | Default | 설명 |
  |-----------|------|---------|------|
  | page | int | 1 | 페이지 번호 |
  | pageSize | int | 20 | 페이지당 항목 수 (최대 100) |
  | status | string | | 필터: open, closed, awarded, cancelled |
  | keyword | string | | 제목/기관명 검색 |
  | region | string | | 지역 필터 |
  | category | string | | 분류 필터 |
  | bidType | string | | 입찰 유형 필터 (일반, 제한, 지명) |
  | minBudget | decimal | | 최소 추정가격 |
  | maxBudget | decimal | | 최대 추정가격 |
  | startDate | date | | 공고일 시작 |
  | endDate | date | | 공고일 종료 |
  | sortBy | string | deadline | 정렬 필드 (deadline, announcementDate, budget, createdAt) |
  | sortOrder | string | asc | 정렬 방향 (asc, desc) |
- **Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "bidNumber": "20260308-001",
        "title": "2026년 정보시스템 고도화 사업",
        "organization": "행정안전부",
        "region": "서울",
        "category": "용역",
        "bidType": "일반경쟁",
        "contractMethod": "적격심사",
        "budget": 500000000,
        "announcementDate": "2026-03-08",
        "deadline": "2026-03-22T17:00:00Z",
        "status": "open",
        "attachmentCount": 3,
        "crawledAt": "2026-03-08T06:00:00Z"
      }
    ]
  },
  "meta": {
    "page": 1,
    "pageSize": 20,
    "total": 150,
    "totalPages": 8
  }
}
```
- **에러 케이스**:
  | 코드 | HTTP Status | 상황 |
  |------|-------------|------|
  | AUTH_002 | 401 | 인증 토큰 없음 |
  | VALIDATION_001 | 400 | 잘못된 필터 값 |

### 5.2 GET /api/v1/bids/{id}
공고 상세 조회

- **목적**: 공고 상세 정보 + 첨부파일 목록 조회
- **인증**: 필요 (Bearer Token)
- **Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "bidNumber": "20260308-001",
    "title": "2026년 정보시스템 고도화 사업",
    "description": "행정안전부 내부 정보시스템 고도화...",
    "organization": "행정안전부",
    "region": "서울",
    "category": "용역",
    "bidType": "일반경쟁",
    "contractMethod": "적격심사",
    "budget": 500000000,
    "estimatedPrice": 450000000,
    "announcementDate": "2026-03-08",
    "deadline": "2026-03-22T17:00:00Z",
    "openDate": "2026-03-23T10:00:00Z",
    "status": "open",
    "scoringCriteria": {
      "technical": 80,
      "price": 20
    },
    "attachments": [
      {
        "id": "uuid",
        "filename": "제안요청서.pdf",
        "fileType": "PDF",
        "fileUrl": "https://nara.go.kr/files/...",
        "hasExtractedText": true
      },
      {
        "id": "uuid",
        "filename": "과업지시서.hwp",
        "fileType": "HWP",
        "fileUrl": "https://nara.go.kr/files/...",
        "hasExtractedText": false
      }
    ],
    "crawledAt": "2026-03-08T06:00:00Z",
    "createdAt": "2026-03-08T06:00:05Z"
  }
}
```
- **에러 케이스**:
  | 코드 | HTTP Status | 상황 |
  |------|-------------|------|
  | BID_001 | 404 | 공고를 찾을 수 없음 |

### 5.3 GET /api/v1/bids/{id}/matches
공고별 매칭 결과 조회

- **목적**: 특정 공고에 대한 현재 사용자의 매칭 분석 결과 조회
- **인증**: 필요 (Bearer Token)
- **비즈니스 규칙**:
  - 사용자의 소속 회사 프로필이 등록되어 있어야 함
  - 매칭 결과가 없으면 즉시 매칭 분석 실행 후 반환 (lazy evaluation)
- **Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "bidId": "uuid",
    "userId": "uuid",
    "suitabilityScore": 78.5,
    "competitionScore": 0,
    "capabilityScore": 0,
    "marketScore": 0,
    "totalScore": 78.5,
    "recommendation": "recommended",
    "recommendationReason": "회사 업종(소프트웨어 개발업)이 공고 분야와 높은 적합도를 보입니다. 유사 수행실적 3건이 확인됩니다.",
    "isNotified": true,
    "analyzedAt": "2026-03-08T06:05:00Z"
  }
}
```
- **비고**: MVP에서 competitionScore, marketScore는 0 (F-02에서 구현)
- **에러 케이스**:
  | 코드 | HTTP Status | 상황 |
  |------|-------------|------|
  | BID_001 | 404 | 공고를 찾을 수 없음 |
  | COMPANY_001 | 404 | 소속 회사 없음 (매칭 불가) |

### 5.4 GET /api/v1/bids/matched
사용자 매칭 공고 목록 조회

- **목적**: 현재 사용자에게 매칭된 공고 목록 (점수 높은 순)
- **인증**: 필요 (Bearer Token)
- **Query Parameters**:
  | Parameter | Type | Default | 설명 |
  |-----------|------|---------|------|
  | page | int | 1 | 페이지 번호 |
  | pageSize | int | 20 | 페이지당 항목 수 (최대 100) |
  | minScore | decimal | 0 | 최소 점수 필터 |
  | recommendation | string | | 필터: recommended, neutral, not_recommended |
  | sortBy | string | totalScore | 정렬 필드 (totalScore, analyzedAt, deadline) |
  | sortOrder | string | desc | 정렬 방향 |
- **Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "bid": {
          "id": "uuid",
          "bidNumber": "20260308-001",
          "title": "2026년 정보시스템 고도화 사업",
          "organization": "행정안전부",
          "budget": 500000000,
          "deadline": "2026-03-22T17:00:00Z",
          "status": "open"
        },
        "totalScore": 78.5,
        "recommendation": "recommended",
        "recommendationReason": "회사 업종이 공고 분야와 높은 적합도...",
        "analyzedAt": "2026-03-08T06:05:00Z"
      }
    ]
  },
  "meta": {
    "page": 1,
    "pageSize": 20,
    "total": 35,
    "totalPages": 2
  }
}
```
- **에러 케이스**:
  | 코드 | HTTP Status | 상황 |
  |------|-------------|------|
  | COMPANY_001 | 404 | 소속 회사 없음 |

### 5.5 POST /api/v1/bids/collect (관리자 전용)
수동 수집 트리거

- **목적**: 스케줄 외 수동으로 공고 수집 실행 (디버깅/관리 용도)
- **인증**: 필요 (Bearer Token)
- **권한**: owner 역할만 (MVP 관리자 대용)
- **Response** (202 Accepted):
```json
{
  "success": true,
  "data": {
    "message": "공고 수집이 시작되었습니다.",
    "triggeredAt": "2026-03-08T15:30:00Z"
  }
}
```
- **비즈니스 규칙**:
  - 백그라운드에서 수집 실행 (응답은 즉시 반환)
  - 동시에 여러 수집이 실행되지 않도록 잠금 (Redis SETNX)
- **에러 케이스**:
  | 코드 | HTTP Status | 상황 |
  |------|-------------|------|
  | PERMISSION_001 | 403 | 관리자 권한 없음 |
  | BID_004 | 409 | 수집이 이미 진행 중 |

---

## 6. DB 설계

ERD (docs/system/erd.md)에 정의된 테이블 구조를 기본으로 사용합니다.

### 6.1 bids 테이블

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 공고 ID |
| bid_number | VARCHAR(50) | UK, NOT NULL | 공고번호 (나라장터) |
| title | VARCHAR(500) | NOT NULL | 공고명 |
| description | TEXT | | 공고 요약 |
| organization | VARCHAR(200) | NOT NULL | 발주기관 |
| region | VARCHAR(100) | | 지역 |
| category | VARCHAR(100) | | 수요기관 분류 |
| bid_type | VARCHAR(50) | | 입찰 유형 (일반, 제한, 지명) |
| contract_method | VARCHAR(50) | | 계약 방식 (적격심사, 최저가, 혼합) |
| budget | DECIMAL(15,0) | | 추정가격 |
| announcement_date | DATE | | 공고일 |
| deadline | TIMESTAMP | NOT NULL | 마감일시 |
| open_date | TIMESTAMP | | 개찰일시 |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'open' | 상태 (open, closed, awarded, cancelled) |
| estimated_price | DECIMAL(15,0) | | 사전공고 추정가격 |
| content_embedding | vector(1536) | | 공고 내용 임베딩 (nullable, MVP에서 미사용) |
| match_score | DECIMAL(5,2) | | 전체 매칭 점수 (deprecated, user_bid_matches 사용) |
| scoring_criteria | JSONB | | 평가 기준 (파싱된 데이터) |
| crawled_at | TIMESTAMP | | 크롤링 시간 |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 생성 시간 |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 수정 시간 |

**Check Constraints**:
```sql
ALTER TABLE bids
    ADD CONSTRAINT chk_bids_status
    CHECK (status IN ('open', 'closed', 'awarded', 'cancelled'));
```

### 6.2 bid_attachments 테이블

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 첨부파일 ID |
| bid_id | UUID | FK -> bids.id, NOT NULL | 공고 ID |
| filename | VARCHAR(500) | NOT NULL | 파일명 |
| file_type | VARCHAR(50) | NOT NULL | 파일 타입 (PDF, HWP, DOC) |
| file_url | VARCHAR(1000) | NOT NULL | 파일 URL (원본 다운로드 링크) |
| extracted_text | TEXT | | 추출된 텍스트 |
| text_embedding | vector(1536) | | 텍스트 임베딩 (nullable, MVP에서 미사용) |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 생성 시간 |

### 6.3 user_bid_matches 테이블

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 매칭 ID |
| user_id | UUID | FK -> users.id, NOT NULL | 사용자 ID |
| bid_id | UUID | FK -> bids.id, NOT NULL | 공고 ID |
| suitability_score | DECIMAL(5,2) | | 적합도 점수 (TF-IDF 기반) |
| competition_score | DECIMAL(5,2) | DEFAULT 0 | 경쟁 강도 점수 (F-02에서 구현) |
| capability_score | DECIMAL(5,2) | DEFAULT 0 | 역량 점수 (F-02에서 구현) |
| market_score | DECIMAL(5,2) | DEFAULT 0 | 시장 환경 점수 (F-02에서 구현) |
| total_score | DECIMAL(5,2) | NOT NULL | 종합 점수 (0~100) |
| recommendation | VARCHAR(20) | | 추천 여부 (recommended, neutral, not_recommended) |
| recommendation_reason | TEXT | | 추천 사유 |
| is_notified | BOOLEAN | DEFAULT FALSE | 알림 발송 여부 |
| analyzed_at | TIMESTAMP | | 분석 시간 |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 생성 시간 |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 수정 시간 |

**Unique Constraint**: (user_id, bid_id)

**Check Constraints**:
```sql
ALTER TABLE user_bid_matches
    ADD CONSTRAINT chk_score_range
    CHECK (total_score >= 0 AND total_score <= 100);

ALTER TABLE user_bid_matches
    ADD CONSTRAINT chk_recommendation
    CHECK (recommendation IS NULL OR recommendation IN ('recommended', 'neutral', 'not_recommended'));
```

---

## 7. 서비스 설계

### 7.1 BidCollectorService -- 공고 수집 서비스

**책임**: 공공데이터포털 API에서 공고 데이터를 수집하여 DB에 저장

```python
class BidCollectorService:
    """공고 수집 서비스"""

    def __init__(self, db: AsyncSession, http_client: httpx.AsyncClient):
        self.db = db
        self.http_client = http_client

    async def collect_bids(self) -> CollectionResult:
        """
        공고 수집 메인 플로우

        1. 공공데이터포털 API 호출 (입찰공고목록 조회)
        2. 중복 공고 필터링 (bid_number 기준)
        3. 신규 공고 DB 저장
        4. 첨부파일 정보 저장
        5. 첨부파일 파싱 실행
        6. 매칭 분석 트리거
        Returns: CollectionResult(new_count, updated_count, failed_count, errors)
        """

    async def _fetch_from_api(self, page: int = 1, num_of_rows: int = 100) -> list[dict]:
        """
        공공데이터포털 나라장터 입찰공고 API 호출

        - URL: https://apis.data.go.kr/1230000/BidPublicInfoService04/getBidPblancListInfoServc
        - 파라미터:
          - ServiceKey: NARA_API_KEY
          - numOfRows: 페이지당 건수
          - pageNo: 페이지 번호
          - inqryDiv: 1 (입찰공고)
          - inqryBgnDt: 조회 시작일시 (yyyyMMddHHmm)
          - inqryEndDt: 조회 종료일시 (yyyyMMddHHmm)
          - type: json
        - 재시도: _retry_with_backoff 적용
        """

    async def _retry_with_backoff(
        self,
        func: Callable,
        max_retries: int = 3,
        base_delay: float = 2.0,
    ) -> Any:
        """
        지수 백오프 재시도 로직 (AC-05)

        - 1차: 2초 대기 후 재시도
        - 2차: 4초 대기 후 재시도
        - 3차: 8초 대기 후 재시도
        - 3회 모두 실패: CollectionError 발생 + 관리자 알림
        """

    async def _save_bid(self, bid_data: dict) -> Bid:
        """API 응답 -> Bid 모델 변환 및 저장"""

    async def _save_attachments(self, bid_id: UUID, attachments: list[dict]) -> list[BidAttachment]:
        """첨부파일 정보 저장"""

    async def _is_duplicate(self, bid_number: str) -> bool:
        """bid_number 기준 중복 확인"""
```

### 7.2 BidParserService -- 첨부파일 파싱 서비스

**책임**: 공고 첨부파일(PDF/HWP)에서 텍스트 추출

```python
class BidParserService:
    """첨부파일 파싱 서비스"""

    def __init__(self, http_client: httpx.AsyncClient):
        self.http_client = http_client

    async def parse_attachment(self, attachment: BidAttachment) -> str | None:
        """
        첨부파일 파싱 메인 플로우

        1. file_url에서 파일 다운로드 (임시 디렉토리)
        2. file_type에 따라 파서 선택
        3. 텍스트 추출
        4. attachment.extracted_text 갱신
        Returns: 추출된 텍스트 (실패 시 None)
        """

    async def _download_file(self, url: str) -> Path:
        """파일 다운로드 -> 임시 경로 반환"""

    def _parse_pdf(self, file_path: Path) -> str:
        """
        PDF 텍스트 추출 (pdfplumber)

        - 페이지별 텍스트 추출 후 결합
        - 테이블 데이터도 텍스트로 변환
        """

    def _parse_hwp(self, file_path: Path) -> str | None:
        """
        HWP 텍스트 추출 (pyhwp)

        - pyhwp 미설치 시 None 반환 (graceful degradation)
        - ImportError 발생 시 경고 로그 기록
        """

    async def parse_all_for_bid(self, bid_id: UUID, attachments: list[BidAttachment]) -> int:
        """
        공고의 모든 첨부파일 파싱

        Returns: 성공적으로 파싱된 파일 수
        """
```

### 7.3 BidMatchService -- 매칭 분석 서비스

**책임**: 회사 프로필과 공고 간 적합도 매칭 분석

```python
class BidMatchService:
    """매칭 분석 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze_match(self, user_id: UUID, bid_id: UUID) -> UserBidMatch:
        """
        단일 공고-사용자 매칭 분석

        1. 사용자 소속 회사 프로필 조회
        2. 회사 텍스트 생성 (업종 + 설명 + 실적 + 인증)
        3. 공고 텍스트 생성 (제목 + 설명 + 첨부파일 추출 텍스트)
        4. TF-IDF 유사도 계산
        5. 점수 산출 (0~100)
        6. 추천 등급 결정
        7. user_bid_matches 저장
        """

    async def analyze_new_bids_for_all_users(self, bid_ids: list[UUID]) -> int:
        """
        신규 공고에 대해 모든 회사 보유 사용자 매칭 분석

        - 회사 프로필이 등록된 사용자만 대상
        - 매칭 점수 70점 이상: is_notified=False로 저장 (알림 대상)
        Returns: 생성된 매칭 결과 수
        """

    def _build_company_text(self, company: Any, performances: list, certifications: list) -> str:
        """
        회사 프로필 텍스트 생성 (TF-IDF 입력용)

        포맷:
        - "업종: {industry}. 설명: {description}."
        - "실적: {project_name} ({client_name}, {contract_amount}원). ..." (반복)
        - "인증: {name} ({issuer}). ..." (반복)
        """

    def _build_bid_text(self, bid: Bid, attachments: list[BidAttachment]) -> str:
        """
        공고 텍스트 생성 (TF-IDF 입력용)

        포맷:
        - "공고: {title}. 기관: {organization}. 분류: {category}."
        - "설명: {description}"
        - "첨부파일 내용: {extracted_text}" (파싱된 텍스트만)
        """

    def _calculate_tfidf_similarity(self, text_a: str, text_b: str) -> float:
        """
        TF-IDF 코사인 유사도 계산 (scikit-learn)

        - TfidfVectorizer(max_features=5000, sublinear_tf=True)
        - cosine_similarity 사용
        Returns: 0.0 ~ 1.0 유사도
        """

    def _score_to_recommendation(self, score: float) -> tuple[str, str]:
        """
        점수 -> 추천 등급 + 사유 변환

        - 70~100: recommended, "높은 적합도..."
        - 40~69: neutral, "보통 적합도..."
        - 0~39: not_recommended, "낮은 적합도..."
        """

    async def _notify_high_score_matches(self, matches: list[UserBidMatch]) -> None:
        """
        매칭 점수 70점 이상 알림 발송 (AC-04)

        - NotificationService.send() 호출 (스텁)
        - is_notified = True로 갱신
        """
```

### 7.4 NotificationService (스텁)

```python
class NotificationService:
    """알림 서비스 (F-10에서 실제 구현, 현재 스텁)"""

    async def send_bid_match_notification(self, user_id: UUID, bid_id: UUID, score: float) -> None:
        """매칭 알림 발송 (스텁: 로그만 기록)"""
        logger.info(f"[알림 스텁] user={user_id}, bid={bid_id}, score={score}")

    async def send_admin_alert(self, message: str) -> None:
        """관리자 알림 발송 (스텁: 로그만 기록)"""
        logger.warning(f"[관리자 알림 스텁] {message}")
```

---

## 8. 공공데이터포털 API 연동 설계

### 8.1 API 정보

- **포털**: data.go.kr
- **서비스명**: 나라장터 입찰공고정보 (BidPublicInfoService04)
- **베이스 URL**: `https://apis.data.go.kr/1230000/BidPublicInfoService04`
- **인증**: API Key (ServiceKey 파라미터)
- **환경변수**: `NARA_API_KEY`

### 8.2 사용 엔드포인트

#### getBidPblancListInfoServc (입찰공고 목록 조회)

| 파라미터 | 필수 | 설명 |
|----------|------|------|
| ServiceKey | Y | API 인증 키 |
| numOfRows | N | 한 페이지 결과 수 (기본 10, 최대 999) |
| pageNo | N | 페이지 번호 |
| inqryDiv | N | 조회 구분 (1: 입찰공고) |
| inqryBgnDt | N | 조회 시작일시 (yyyyMMddHHmm) |
| inqryEndDt | N | 조회 종료일시 (yyyyMMddHHmm) |
| type | N | 응답 타입 (json) |

### 8.3 API 응답 매핑

| API 필드 | DB 컬럼 | 변환 |
|----------|---------|------|
| bidNtceNo + bidNtceOrd | bid_number | 결합 ({bidNtceNo}-{bidNtceOrd}) |
| bidNtceNm | title | 직접 매핑 |
| ntceInsttNm | organization | 직접 매핑 |
| dminsttNm | category | 직접 매핑 (수요기관) |
| presmptPrce | budget | 숫자 변환 |
| bidNtceDt | announcement_date | 날짜 변환 |
| bidClseDt | deadline | 일시 변환 |
| opengDt | open_date | 일시 변환 |
| bidNtceDtlUrl | (참조 URL) | 상세 페이지 URL |
| ntceKindNm | bid_type | 직접 매핑 |
| cntrctMthdNm | contract_method | 직접 매핑 |
| bidNtceUrl | (첨부파일 목록) | 별도 파싱 |

### 8.4 수집 주기

- **스케줄**: 매일 06:00, 12:00, 18:00 (KST)
- **조회 범위**: 이전 수집 시점 ~ 현재 시점
- **초기 수집**: 최근 7일치 (첫 실행 시)

---

## 9. APScheduler 통합 설계

### 9.1 FastAPI Lifespan 통합

```python
# backend/src/main.py 변경

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 라이프사이클 관리"""
    # 스케줄러 시작
    scheduler = AsyncIOScheduler(timezone="Asia/Seoul")
    scheduler.add_job(
        scheduled_collect_bids,
        CronTrigger(hour="6,12,18", minute=0, timezone="Asia/Seoul"),
        id="bid_collection",
        name="공고 자동 수집",
        replace_existing=True,
    )
    scheduler.start()
    app.state.scheduler = scheduler

    yield

    # 종료 시 정리
    scheduler.shutdown(wait=False)
    await close_redis()
```

### 9.2 스케줄러 작업 함수

```python
async def scheduled_collect_bids():
    """스케줄러에서 호출하는 수집 함수"""
    async with AsyncSessionLocal() as db:
        async with httpx.AsyncClient(timeout=30.0) as client:
            collector = BidCollectorService(db, client)
            parser = BidParserService(client)
            matcher = BidMatchService(db)

            # 1. 공고 수집
            result = await collector.collect_bids()

            # 2. 신규 공고 첨부파일 파싱
            for bid_id in result.new_bid_ids:
                attachments = await collector.get_attachments(bid_id)
                await parser.parse_all_for_bid(bid_id, attachments)

            # 3. 매칭 분석
            await matcher.analyze_new_bids_for_all_users(result.new_bid_ids)

            await db.commit()
```

### 9.3 동시 실행 방지

```python
# Redis 기반 분산 잠금 (단일 인스턴스에서도 안전)
COLLECTION_LOCK_KEY = "bid_collection:lock"
COLLECTION_LOCK_TTL = 600  # 10분

async def acquire_collection_lock(redis: Redis) -> bool:
    """수집 잠금 획득"""
    return await redis.set(COLLECTION_LOCK_KEY, "1", nx=True, ex=COLLECTION_LOCK_TTL)

async def release_collection_lock(redis: Redis) -> None:
    """수집 잠금 해제"""
    await redis.delete(COLLECTION_LOCK_KEY)
```

---

## 10. 시퀀스 흐름

### 10.1 스케줄러 기반 자동 수집

```
APScheduler (06:00/12:00/18:00)
    |
    | 1. scheduled_collect_bids() 호출
    |
    v
BidCollectorService
    | 2. Redis 잠금 획득
    | 3. 공공데이터포털 API 호출 (페이지네이션)
    |    |- 실패 시: 지수 백오프 재시도 (2s, 4s, 8s)
    |    |- 3회 실패: 관리자 알림 + 중단
    | 4. bid_number 기준 중복 필터링
    | 5. 신규 공고 bids 테이블 저장
    | 6. 첨부파일 정보 bid_attachments 저장
    |
    v
BidParserService
    | 7. 첨부파일 다운로드 (file_url)
    | 8. PDF: pdfplumber 파싱
    | 9. HWP: pyhwp 파싱 (ImportError시 건너뜀)
    | 10. extracted_text 갱신
    |
    v
BidMatchService
    | 11. 회사 프로필 보유 사용자 목록 조회
    | 12. 각 사용자별 회사 텍스트 생성
    | 13. 공고 텍스트 생성
    | 14. TF-IDF 코사인 유사도 계산
    | 15. 점수 산출 (유사도 * 100)
    | 16. 추천 등급 결정
    | 17. user_bid_matches 저장
    | 18. 70점 이상: NotificationService 호출 (스텁)
    |
    v
Redis 잠금 해제
```

### 10.2 사용자 공고 상세 + 매칭 조회

```
사용자 -> Frontend -> GET /bids/{id} -> BidsAPI -> DB
    |                                        |
    |  1. 공고 상세 요청                       |
    | -------------------------------------->|
    |                                        | 2. bids + bid_attachments 조회
    |  <-------------------------------------|
    |  3. 공고 상세 반환                        |
    |                                        |
    |        GET /bids/{id}/matches           |
    | -------------------------------------->|
    |                                        | 4. user_bid_matches 조회
    |                                        | 5. 결과 없으면 -> BidMatchService.analyze_match()
    |                                        | 6. 매칭 결과 반환
    |  <-------------------------------------|
```

---

## 11. 영향 범위

### 11.1 수정 필요 파일

| 파일 | 변경 내용 |
|------|----------|
| backend/src/models/__init__.py | Bid, BidAttachment, UserBidMatch 모델 import 추가 |
| backend/src/api/v1/router.py | bids 라우터 include 추가 |
| backend/src/config.py | NARA_API_KEY, 스케줄러 설정 추가 |
| backend/src/main.py | APScheduler lifespan 통합 |

### 11.2 신규 생성 파일

| 파일 | 설명 |
|------|------|
| backend/src/models/bid.py | Bid 모델 |
| backend/src/models/bid_attachment.py | BidAttachment 모델 |
| backend/src/models/user_bid_match.py | UserBidMatch 모델 |
| backend/src/schemas/bid.py | 공고 관련 Pydantic 스키마 |
| backend/src/schemas/bid_match.py | 매칭 관련 스키마 |
| backend/src/services/bid_collector_service.py | 공고 수집 서비스 |
| backend/src/services/bid_parser_service.py | 첨부파일 파싱 서비스 |
| backend/src/services/bid_match_service.py | 매칭 분석 서비스 |
| backend/src/services/notification_service.py | 알림 서비스 (스텁) |
| backend/src/services/scheduler.py | APScheduler 설정 및 작업 함수 |
| backend/src/api/v1/bids.py | 공고 API 엔드포인트 |

---

## 12. 성능 설계

### 12.1 인덱스 계획

```sql
-- 공고 검색 인덱스 (ERD 참조)
CREATE INDEX idx_bids_bid_number ON bids(bid_number);
CREATE INDEX idx_bids_status ON bids(status);
CREATE INDEX idx_bids_deadline ON bids(deadline);
CREATE INDEX idx_bids_organization ON bids(organization);
CREATE INDEX idx_bids_category ON bids(category);

-- 공고 목록 페이지네이션 (복합 인덱스)
CREATE INDEX idx_bids_status_deadline ON bids(status, deadline ASC);

-- 첨부파일 조회
CREATE INDEX idx_bid_attachments_bid ON bid_attachments(bid_id);

-- 매칭 결과 조회
CREATE INDEX idx_user_bid_matches_user_score ON user_bid_matches(user_id, total_score DESC);
CREATE INDEX idx_user_bid_matches_bid ON user_bid_matches(bid_id);

-- 매칭 유니크 제약
CREATE UNIQUE INDEX idx_user_bid_matches_unique ON user_bid_matches(user_id, bid_id);
```

### 12.2 캐싱 전략

MVP에서 별도 캐싱 불필요. 추후 적용 가능한 전략:

```
# 수집 잠금 (Redis, 즉시 적용)
bid_collection:lock -> "1" (TTL: 600s)

# 공고 목록 캐시 (추후)
bids:list:{hash(query_params)} -> {response} (TTL: 5분)

# 매칭 결과 캐시 (추후)
bid_match:{user_id}:{bid_id} -> {match_data} (TTL: 1시간)
```

### 12.3 수집 성능 고려사항

- 공공데이터포털 API 호출 시 numOfRows=100으로 설정 (최대 999)
- 페이지네이션으로 전체 데이터 순회
- 한 번의 수집 사이클에서 중복 제외 신규 공고만 처리
- 첨부파일 파싱은 동기 처리이나 스케줄러 백그라운드에서 실행되므로 사용자 영향 없음

---

## 13. 에러 코드 요약

### 기존 에러 코드 (api-conventions.md)

| 코드 | HTTP Status | 메시지 |
|------|-------------|--------|
| BID_001 | 404 | 공고를 찾을 수 없습니다. |
| BID_002 | 400 | 공고가 이미 마감되었습니다. |
| BID_003 | 422 | 첨부파일 파싱에 실패했습니다. |

### 신규 에러 코드 (F-01 추가)

| 코드 | HTTP Status | 메시지 |
|------|-------------|--------|
| BID_004 | 409 | 공고 수집이 이미 진행 중입니다. |
| BID_005 | 502 | 공공데이터포털 API 연동에 실패했습니다. |
| BID_006 | 500 | 매칭 분석 중 오류가 발생했습니다. |

### 기존 공통 에러 코드 (재사용)

| 코드 | HTTP Status | 메시지 |
|------|-------------|--------|
| COMPANY_001 | 404 | 회사를 찾을 수 없습니다. (매칭 시) |
| PERMISSION_001 | 403 | 접근 권한이 없습니다. |
| AUTH_002 | 401 | 인증 토큰이 필요합니다. |
| SERVER_002 | 502 | 외부 서비스 연동 실패 |

---

## 14. 설정 변경

### backend/src/config.py 추가 필드

```python
class Settings(BaseSettings):
    # ... 기존 설정 ...

    # 나라장터 API
    nara_api_key: str = ""  # 환경변수: NARA_API_KEY
    nara_api_base_url: str = "https://apis.data.go.kr/1230000/BidPublicInfoService04"

    # 스케줄러
    scheduler_enabled: bool = True  # 테스트 시 비활성화
    collection_schedule_hours: str = "6,12,18"  # KST 수집 시각

    # 수집 설정
    collection_retry_max: int = 3
    collection_retry_base_delay: float = 2.0
    collection_page_size: int = 100
    collection_initial_days: int = 7  # 초기 수집 범위 (일)
```

---

## 15. 의존성 추가

### requirements.txt 추가

```
apscheduler>=3.10.0        # 스케줄러
httpx>=0.25.0              # 비동기 HTTP 클라이언트
scikit-learn>=1.3.0        # TF-IDF 매칭
pdfplumber>=0.10.0         # PDF 파싱
pyhwp>=0.6.0               # HWP 파싱 (선택적)
```

### pyhwp 선택적 의존성 처리

```python
try:
    import hwp5
    HWP_AVAILABLE = True
except ImportError:
    HWP_AVAILABLE = False
    logger.warning("pyhwp가 설치되지 않았습니다. HWP 파싱이 비활성화됩니다.")
```

---

## 변경 이력

| 날짜 | 변경 내용 | 이유 |
|------|----------|------|
| 2026-03-08 | 초기 변경 설계 | F-01 기능 구현 시작 |
