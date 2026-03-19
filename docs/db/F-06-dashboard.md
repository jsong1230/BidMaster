# F-06 입찰 현황 대시보드 — DB 스키마 확정본

> 구현 완료일: 2026-03-19

---

## 신규 테이블: user_bid_tracking

### 정의

```sql
CREATE TABLE user_bid_tracking (
    id          UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID            NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    bid_id      UUID            NOT NULL REFERENCES bids(id) ON DELETE CASCADE,
    status      VARCHAR(20)     NOT NULL DEFAULT 'interested',
    my_bid_price DECIMAL(15, 0) NULL,
    is_winner   BOOLEAN         NULL,
    submitted_at TIMESTAMP      NULL,
    result_at   TIMESTAMP       NULL,
    notes       TEXT            NULL,
    created_at  TIMESTAMP       NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP       NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_user_bid_tracking UNIQUE (user_id, bid_id),
    CONSTRAINT chk_tracking_status CHECK (
        status IN ('interested', 'participating', 'submitted', 'won', 'lost')
    )
);
```

### 컬럼 설명

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | UUID | PK | 추적 고유 ID |
| user_id | UUID | FK(users), NOT NULL | 사용자 ID |
| bid_id | UUID | FK(bids), NOT NULL | 공고 ID |
| status | VARCHAR(20) | NOT NULL, CHECK | 추적 상태 |
| my_bid_price | DECIMAL(15,0) | NULL | 나의 투찰 금액 |
| is_winner | BOOLEAN | NULL | 낙찰 여부 (won=true, lost=false, 기타=null) |
| submitted_at | TIMESTAMP | NULL | 제출 시각 (status=submitted 시 자동 설정) |
| result_at | TIMESTAMP | NULL | 결과 확인 시각 (status=won/lost 시 자동 설정) |
| notes | TEXT | NULL | 메모 (최대 10000자) |
| created_at | TIMESTAMP | NOT NULL | 생성 시각 |
| updated_at | TIMESTAMP | NOT NULL | 수정 시각 |

### 허용 status 값

| 값 | 의미 |
|----|------|
| interested | 관심 등록 |
| participating | 참여 준비 |
| submitted | 제출 완료 |
| won | 낙찰 |
| lost | 탈락 |

---

## 인덱스

```sql
-- 사용자별 전체 조회
CREATE INDEX idx_user_bid_tracking_user
    ON user_bid_tracking(user_id);

-- 사용자별 상태 필터 조회
CREATE INDEX idx_user_bid_tracking_user_status
    ON user_bid_tracking(user_id, status);

-- 유니크 제약 (user_id, bid_id)
CREATE UNIQUE INDEX idx_user_bid_tracking_unique
    ON user_bid_tracking(user_id, bid_id);

-- 낙찰 이력 조회 (result_at DESC)
CREATE INDEX idx_user_bid_tracking_result_at
    ON user_bid_tracking(user_id, result_at DESC);

-- 생성 시각 기준 통계
CREATE INDEX idx_user_bid_tracking_created
    ON user_bid_tracking(user_id, created_at DESC);
```

> 참고: `WHERE is_winner = TRUE` 부분 인덱스는 PostgreSQL에서만 지원됩니다.
> SQLite 테스트 환경에서는 적용되지 않습니다.

---

## 기존 테이블 변경

### users 테이블
- `bid_trackings` relationship 추가 (SQLAlchemy ORM 레벨, DDL 변경 없음)

### bids 테이블
- `trackings` relationship 추가 (SQLAlchemy ORM 레벨, DDL 변경 없음)

### companies 테이블 (버그 수정)
- `user` relationship에 `foreign_keys` 명시하여 SQLAlchemy 모호성 오류 수정

---

## 비즈니스 규칙 (서비스 레이어)

### 자동 필드 설정

| 조건 | 자동 설정 필드 |
|------|---------------|
| status = submitted | submitted_at = NOW() (최초 설정 시) |
| status = won | is_winner = true, result_at = NOW() |
| status = lost | is_winner = false, result_at = NOW() |

### Upsert 로직
1. (user_id, bid_id) 조합으로 기존 레코드 조회
2. 없으면 INSERT (is_created=True, HTTP 201)
3. 있으면 UPDATE (is_created=False, HTTP 200)

---

## 캐싱 전략 (Redis)

```
dashboard:summary:{user_id}:{period}     TTL: 30초
dashboard:pipeline:{user_id}             TTL: 30초
dashboard:statistics:{user_id}:{months}  TTL: 5분 (300초)
```

### 캐시 무효화 트리거
- `POST /api/v1/bids/{bid_id}/tracking` 호출 시:
  - `dashboard:summary:{user_id}:*` 삭제
  - `dashboard:pipeline:{user_id}` 삭제

> Redis 미설치 시 graceful degradation: 캐시 없이 실시간 쿼리로 동작
