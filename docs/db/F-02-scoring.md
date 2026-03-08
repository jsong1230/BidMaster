# F-02 낙찰 가능성 스코어링 — DB 스키마 확정본

> 구현 완료일: 2026-03-08
> 기준 브랜치: feature/F-02-scoring-dev

---

## 1. 신규 테이블

### bid_win_history (낙찰 이력)

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | VARCHAR(36) | PK | UUID 문자열 (gen_random_uuid()) |
| bid_number | VARCHAR(50) | NOT NULL | 공고번호 |
| winner_name | VARCHAR(200) | NOT NULL | 낙찰자명 |
| winner_business_number | VARCHAR(10) | NULL | 낙찰자 사업자번호 (10자리) |
| winning_price | NUMERIC(15,0) | NOT NULL | 낙찰 금액 (원) |
| bid_rate | NUMERIC(5,4) | NULL | 낙찰율 (낙찰가/추정가, 예: 0.8920) |
| winning_date | DATE | NULL | 낙찰일 |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | 생성 시간 |

**인덱스**

```sql
CREATE INDEX idx_bid_win_history_bid_number ON bid_win_history(bid_number);
CREATE INDEX idx_bid_win_history_winner ON bid_win_history(winner_business_number);
CREATE INDEX idx_bid_win_history_date ON bid_win_history(winning_date);
```

**샘플 시드 데이터 (인메모리)**

MVP 단계에서 DB 연결 없이 동작하기 위해 아래 3건의 샘플 데이터를 인메모리에 로드합니다.

- `(주)가나다소프트` — 행정안전부/정보화/일반경쟁, 420,000,000원
- `(주)라마바시스템` — 행정안전부/정보화/일반경쟁, 380,000,000원
- `(주)사아자테크` — 국토교통부/건설/제한경쟁, 250,000,000원

---

## 2. 기존 테이블 변경

### user_bid_matches — recommendation CHECK 제약 확장

```sql
-- 기존 CHECK 삭제 후 새로 생성 (strongly_recommended 추가)
ALTER TABLE user_bid_matches
    DROP CONSTRAINT IF EXISTS chk_recommendation;

ALTER TABLE user_bid_matches
    ADD CONSTRAINT chk_recommendation
    CHECK (recommendation IS NULL OR recommendation IN (
        'strongly_recommended', 'recommended', 'neutral', 'not_recommended'
    ));
```

**변경 이유**: F-02 스코어링 결과에 `strongly_recommended` 등급 추가 (기존 3단계 → 4단계)

---

## 3. 인메모리 저장소 구조

MVP 단계에서는 DB 없이 인메모리 딕셔너리로 동작합니다.

### _BID_WIN_HISTORY (낙찰 이력)

```python
# 키: 인덱스 (list)
# 검색 조건: _organization, _category, _bid_type 필드로 필터링
_BID_WIN_HISTORY: list[dict] = [...]
```

### _SCORING_CACHE (스코어링 결과 캐시)

```python
# 키: "{user_id}:{bid_id}"
# 값: ScoringResult 딕셔너리
_SCORING_CACHE: dict[str, dict] = {}
```

---

## 4. 마이그레이션 전략

| 대상 | 마이그레이션 방법 | 위험도 |
|------|-----------------|--------|
| bid_win_history 신규 생성 | CREATE TABLE | 낮음 |
| user_bid_matches CHECK 확장 | ALTER TABLE | 낮음 (기존 데이터 영향 없음) |

기존 `user_bid_matches` 레코드의 `recommendation` 값은 `recommended/neutral/not_recommended` 중 하나이므로 CHECK 제약 확장은 하위 호환됩니다.
