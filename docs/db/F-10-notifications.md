# F-10 알림 시스템 DB 스키마

## 개요

알림 메시지 저장 및 사용자별 알림 설정 관리를 위한 스키마입니다.
ERD(docs/system/erd.md) 6장 "알림 (F-10)" 섹션에 정의된 테이블을 기반으로 구현합니다.

---

## 신규 테이블

### 1. notifications

알림 메시지를 저장합니다. 인앱 알림, 이메일/카카오 발송 이력을 모두 기록합니다.

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 알림 ID |
| user_id | UUID | FK -> users.id, NOT NULL | 수신자 ID |
| type | VARCHAR(50) | NOT NULL | 알림 유형 |
| title | VARCHAR(200) | NOT NULL | 알림 제목 |
| content | TEXT | NOT NULL | 알림 내용 |
| data | JSONB | DEFAULT '{}' | 관련 데이터 (bid_id, score 등) |
| is_read | BOOLEAN | NOT NULL, DEFAULT FALSE | 읽음 여부 |
| channel | VARCHAR(20) | NOT NULL, DEFAULT 'in_app' | 발송 채널 |
| sent_at | TIMESTAMP | | 발송 시간 |
| read_at | TIMESTAMP | | 읽음 시간 |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 생성 시간 |

**type 허용 값**: `bid_matched`, `deadline`, `bid_result`, `proposal_ready`

**channel 허용 값**: `in_app`, `email`, `kakao`

### 2. notification_settings

사용자별 알림 유형에 대한 수신 채널 설정을 저장합니다.

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 설정 ID |
| user_id | UUID | FK -> users.id, NOT NULL | 사용자 ID |
| notification_type | VARCHAR(50) | NOT NULL | 알림 유형 |
| email_enabled | BOOLEAN | NOT NULL, DEFAULT TRUE | 이메일 수신 여부 |
| kakao_enabled | BOOLEAN | NOT NULL, DEFAULT FALSE | 카카오 수신 여부 |
| push_enabled | BOOLEAN | NOT NULL, DEFAULT TRUE | 인앱 푸시 수신 여부 |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 생성 시간 |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 수정 시간 |

**notification_type 허용 값**: `bid_matched`, `deadline`, `bid_result`, `proposal_ready`

---

## 제약조건

### Check Constraints

```sql
-- notifications: 알림 유형 제한
ALTER TABLE notifications
    ADD CONSTRAINT chk_notifications_type
    CHECK (type IN ('bid_matched', 'deadline', 'bid_result', 'proposal_ready'));

-- notifications: 채널 제한
ALTER TABLE notifications
    ADD CONSTRAINT chk_notifications_channel
    CHECK (channel IN ('in_app', 'email', 'kakao'));

-- notification_settings: 알림 유형 제한
ALTER TABLE notification_settings
    ADD CONSTRAINT chk_notification_settings_type
    CHECK (notification_type IN ('bid_matched', 'deadline', 'bid_result', 'proposal_ready'));
```

### Unique Constraints

```sql
-- notification_settings: 사용자별 알림 유형 유니크
ALTER TABLE notification_settings
    ADD CONSTRAINT uq_notification_settings_user_type
    UNIQUE (user_id, notification_type);
```

### Foreign Keys

```sql
-- notifications -> users
ALTER TABLE notifications
    ADD CONSTRAINT fk_notifications_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- notification_settings -> users
ALTER TABLE notification_settings
    ADD CONSTRAINT fk_notification_settings_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
```

**참고**: 사용자 삭제 시 알림 및 설정 레코드도 함께 삭제합니다 (CASCADE). 알림은 사용자 없이 의미가 없으므로 RESTRICT 대신 CASCADE를 사용합니다.

---

## 인덱스

```sql
-- 안읽은 알림 조회 (가장 빈번한 쿼리)
CREATE INDEX idx_notifications_user_unread
    ON notifications(user_id, is_read)
    WHERE is_read = FALSE;

-- 알림 목록 조회 (생성일 내림차순)
CREATE INDEX idx_notifications_user_created
    ON notifications(user_id, created_at DESC);

-- 마감 임박 중복 알림 방지용 (당일 발송 여부 체크)
CREATE INDEX idx_notifications_dedup
    ON notifications(user_id, type, (created_at::date))
    WHERE type = 'deadline';

-- 알림 설정 유니크 인덱스 (Unique Constraint에 의해 자동 생성)
-- CREATE UNIQUE INDEX idx_notification_settings_unique
--     ON notification_settings(user_id, notification_type);
```

---

## 마이그레이션 전략

### 신규 테이블 생성

```sql
-- 1. notifications 테이블 생성
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    data JSONB DEFAULT '{}',
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    channel VARCHAR(20) NOT NULL DEFAULT 'in_app',
    sent_at TIMESTAMP,
    read_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 2. notification_settings 테이블 생성
CREATE TABLE notification_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL,
    email_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    kakao_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    push_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, notification_type)
);
```

### 기존 사용자 기본 설정 생성

```sql
-- 기존 사용자에 대해 4개 알림 유형 기본 설정 일괄 생성
INSERT INTO notification_settings (user_id, notification_type, email_enabled, kakao_enabled, push_enabled)
SELECT
    u.id,
    t.notification_type,
    TRUE,   -- email_enabled
    FALSE,  -- kakao_enabled
    TRUE    -- push_enabled
FROM users u
CROSS JOIN (
    VALUES
        ('bid_matched'),
        ('deadline'),
        ('bid_result'),
        ('proposal_ready')
) AS t(notification_type)
WHERE u.deleted_at IS NULL
ON CONFLICT (user_id, notification_type) DO NOTHING;
```

---

## SQLAlchemy 모델

### Notification

```python
# backend/src/models/notification.py

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    data = Column(JSONB, default=dict)
    is_read = Column(Boolean, nullable=False, default=False)
    channel = Column(String(20), nullable=False, default="in_app")
    sent_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_notifications_user_unread", "user_id", "is_read", postgresql_where=text("is_read = FALSE")),
        Index("idx_notifications_user_created", "user_id", created_at.desc()),
    )
```

### NotificationSetting

```python
# backend/src/models/notification_setting.py

class NotificationSetting(Base):
    __tablename__ = "notification_settings"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    notification_type = Column(String(50), nullable=False)
    email_enabled = Column(Boolean, nullable=False, default=True)
    kakao_enabled = Column(Boolean, nullable=False, default=False)
    push_enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint("user_id", "notification_type", name="uq_notification_settings_user_type"),
    )
```

---

## 기존 테이블 영향

| 테이블 | 영향 | 설명 |
|--------|------|------|
| users | 없음 | FK 참조 대상 (변경 불필요) |
| user_bid_matches | 없음 | is_notified 플래그 기존 로직 유지 |
| bids | 없음 | 알림 data 필드에서 bid_id 참조 (FK 아님, JSONB) |

---

## 데이터 볼륨 예측

| 테이블 | 예상 볼륨 (1년) | 근거 |
|--------|----------------|------|
| notifications | ~50,000건 | 100 사용자 x 500건/년 (매칭+마감+결과) |
| notification_settings | ~400건 | 100 사용자 x 4 유형 |

알림 데이터는 무한 증가하므로, 추후 6개월 이상 된 알림은 아카이빙 또는 삭제 정책 검토 필요.
