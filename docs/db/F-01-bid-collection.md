# F-01 공고 자동 수집 및 매칭 DB 스키마 확정본

## 개요

나라장터 공고 데이터 저장 및 사용자-공고 매칭 결과를 관리하는 테이블 정의입니다.

---

## 테이블 목록

| 테이블명 | 설명 |
|----------|------|
| bids | 공고 정보 |
| bid_attachments | 공고 첨부파일 |
| user_bid_matches | 사용자-공고 매칭 결과 |

---

## bids

공고 기본 정보를 저장합니다.

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|---------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 공고 ID |
| bid_number | VARCHAR(30) | NOT NULL, UNIQUE | 공고 번호 (나라장터 기준) |
| title | VARCHAR(500) | NOT NULL | 공고명 |
| organization | VARCHAR(200) | NOT NULL | 발주기관명 |
| region | VARCHAR(50) | NULLABLE | 지역 |
| category | VARCHAR(100) | NULLABLE | 입찰 카테고리 |
| bid_type | VARCHAR(50) | NULLABLE | 입찰 방식 (일반경쟁/제한경쟁 등) |
| contract_method | VARCHAR(50) | NULLABLE | 계약 방법 (적격심사/최저가 등) |
| budget | BIGINT | NULLABLE | 예산 (원) |
| estimated_price | BIGINT | NULLABLE | 추정 가격 (원) |
| announcement_date | DATE | NULLABLE | 공고일 |
| deadline | TIMESTAMPTZ | NULLABLE | 입찰 마감일 |
| open_date | TIMESTAMPTZ | NULLABLE | 개찰일 |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'open' | 상태 (open/closed/awarded/cancelled) |
| description | TEXT | NULLABLE | 공고 내용 |
| scoring_criteria | JSONB | NULLABLE | 평가 기준 (기술:가격 배점 등) |
| source_url | VARCHAR(1000) | NULLABLE | 나라장터 원문 URL |
| crawled_at | TIMESTAMPTZ | NOT NULL | 수집 시각 |
| deleted_at | TIMESTAMPTZ | NULLABLE | 소프트 삭제 시각 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 생성 시각 |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 수정 시각 |

**인덱스**:
```sql
CREATE UNIQUE INDEX idx_bids_bid_number ON bids(bid_number);
CREATE INDEX idx_bids_status ON bids(status);
CREATE INDEX idx_bids_deadline ON bids(deadline DESC);
CREATE INDEX idx_bids_organization ON bids(organization);
CREATE INDEX idx_bids_region ON bids(region);
CREATE INDEX idx_bids_announcement_date ON bids(announcement_date DESC);
CREATE INDEX idx_bids_deleted_at ON bids(deleted_at) WHERE deleted_at IS NULL;
```

**SQLAlchemy 모델**: `backend/src/models/bid.py`

---

## bid_attachments

공고 첨부파일 정보 및 추출 텍스트를 저장합니다.

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|---------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 첨부파일 ID |
| bid_id | UUID | FK → bids(id) ON DELETE CASCADE | 공고 ID |
| filename | VARCHAR(500) | NOT NULL | 파일명 |
| file_type | VARCHAR(10) | NOT NULL | 파일 유형 (PDF/HWP/DOC 등) |
| file_url | VARCHAR(1000) | NOT NULL | 나라장터 다운로드 URL |
| file_size | BIGINT | NULLABLE | 파일 크기 (bytes) |
| extracted_text | TEXT | NULLABLE | 파싱된 텍스트 내용 |
| parse_status | VARCHAR(20) | NOT NULL, DEFAULT 'pending' | 파싱 상태 (pending/success/failed/skipped) |
| parse_error | TEXT | NULLABLE | 파싱 실패 사유 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 생성 시각 |

**인덱스**:
```sql
CREATE INDEX idx_bid_attachments_bid_id ON bid_attachments(bid_id);
CREATE INDEX idx_bid_attachments_file_type ON bid_attachments(file_type);
CREATE INDEX idx_bid_attachments_parse_status ON bid_attachments(parse_status);
```

**SQLAlchemy 모델**: `backend/src/models/bid_attachment.py`

---

## user_bid_matches

사용자별 공고 매칭 분석 결과를 저장합니다.

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|---------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 매칭 결과 ID |
| user_id | UUID | FK → users(id) ON DELETE CASCADE | 사용자 ID |
| bid_id | UUID | FK → bids(id) ON DELETE CASCADE | 공고 ID |
| suitability_score | FLOAT | NOT NULL, DEFAULT 0 | 적합도 점수 (TF-IDF 기반) |
| competition_score | FLOAT | NOT NULL, DEFAULT 0 | 경쟁력 점수 (미래 확장용) |
| capability_score | FLOAT | NOT NULL, DEFAULT 0 | 역량 점수 (미래 확장용) |
| market_score | FLOAT | NOT NULL, DEFAULT 0 | 시장 점수 (미래 확장용) |
| total_score | FLOAT | NOT NULL, DEFAULT 0 | 종합 점수 (0~100) |
| recommendation | VARCHAR(20) | NOT NULL | 추천 등급 (recommended/neutral/not_recommended) |
| recommendation_reason | TEXT | NULLABLE | 추천 이유 |
| is_notified | BOOLEAN | NOT NULL, DEFAULT false | 알림 발송 여부 |
| analyzed_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 분석 시각 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 생성 시각 |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 수정 시각 |

**제약조건**:
```sql
UNIQUE(user_id, bid_id)  -- 사용자-공고 조합은 유일
```

**인덱스**:
```sql
CREATE UNIQUE INDEX idx_user_bid_matches_user_bid ON user_bid_matches(user_id, bid_id);
CREATE INDEX idx_user_bid_matches_user_id ON user_bid_matches(user_id);
CREATE INDEX idx_user_bid_matches_bid_id ON user_bid_matches(bid_id);
CREATE INDEX idx_user_bid_matches_total_score ON user_bid_matches(total_score DESC);
CREATE INDEX idx_user_bid_matches_recommendation ON user_bid_matches(recommendation);
```

**SQLAlchemy 모델**: `backend/src/models/user_bid_match.py`

---

## 관계 다이어그램

```
bids (1) ─────────── (N) bid_attachments
  │
  └─── user_bid_matches (N) ─── (1) users
```

---

## 마이그레이션

마이그레이션 파일은 추후 Alembic으로 생성 예정입니다. 현재 MVP 단계에서는 인메모리 스토어를 사용합니다.

```
alembic revision --autogenerate -m "add_bid_tables"
alembic upgrade head
```

---

## 참고 사항

- `bid_number`는 나라장터 공고번호+차수 조합 (`{bidNtceNo}-{bidNtceOrd}` 형식)으로 유일성 보장
- `scoring_criteria`는 JSONB로 유연하게 저장 (`{"technical": 80, "price": 20}` 등)
- `extracted_text`는 PDF/HWP 파싱 결과이며 TF-IDF 매칭에 활용
- `total_score` 범위: 0~100 (TF-IDF 유사도 × 100 + 구조적 보너스, 100 초과 시 cap)
