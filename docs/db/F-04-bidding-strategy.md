# F-04 낙찰가 예측 및 투찰 전략 — DB 스키마 확정본

## 개요

F-04는 신규 테이블을 생성하지 않습니다.

- **사용 테이블**: bid_win_history (F-02에서 생성, 읽기 전용)
- **인메모리 스토어**: BiddingStrategyService.SAMPLE_WIN_HISTORY (서비스 구동 중 유지)
- **시뮬레이션 저장**: 없음 (무상태, 실시간 계산)

---

## 인메모리 낙찰 이력 스토어

F-02의 bid_win_history 테이블이 구현되기 전까지 서비스 내부 인메모리 데이터를 사용합니다.

### SAMPLE_WIN_HISTORY 구조

| 필드 | 타입 | 설명 |
|------|------|------|
| bid_number | string | 공고 번호 |
| winner_name | string | 낙찰업체명 |
| winner_business_number | string | 사업자등록번호 |
| winning_price | int | 낙찰 금액 (원) |
| bid_rate | float | 낙찰가율 (winning_price / estimated_price) |
| winning_date | string | 낙찰 날짜 (YYYY-MM-DD) |
| _organization | string | 발주기관 (필터용) |
| _category | string | 분류 (필터용) |
| _bid_type | string | 입찰 유형 |
| _contract_method | string | 계약 방식 (적격심사/최저가) |

---

## bid_win_history 테이블 (F-02 생성, 공유 사용)

F-02 설계서 참조. F-04에서는 읽기 전용으로 사용.

**F-04 쿼리 패턴:**
```sql
SELECT bid_rate
FROM bid_win_history
WHERE category = :category
  AND contract_method = :contract_method
  AND winning_date >= NOW() - INTERVAL '1 year'
ORDER BY winning_date DESC;
```

**활용 인덱스:**
- `idx_bid_win_history_date` (winning_date)
- `idx_bid_win_history_bid_number` (bid_number)

---

## user_bid_tracking 테이블 (향후 F-06용)

F-04에서는 사용하지 않으나, 관련성이 높아 ERD에 포함됨.

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | UUID | PK | 추적 ID |
| user_id | UUID | FK -> users.id, NOT NULL | 사용자 ID |
| bid_id | UUID | FK -> bids.id, NOT NULL | 공고 ID |
| status | VARCHAR(20) | NOT NULL | interested/participating/submitted/won/lost |
| my_bid_price | DECIMAL(15,0) | | 투찰 금액 |
| is_winner | BOOLEAN | | 낙찰 여부 |
| submitted_at | TIMESTAMP | | 제출 시간 |
| result_at | TIMESTAMP | | 결과 확인 시간 |
| notes | TEXT | | 메모 |
| created_at | TIMESTAMP | NOT NULL | 생성 시간 |
| updated_at | TIMESTAMP | NOT NULL | 수정 시간 |

**Unique Constraint**: (user_id, bid_id)

---

## 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-03-08 | F-04 구현 완료, DB 스키마 확정 |
