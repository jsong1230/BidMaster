# F-10 알림 시스템 -- 변경 설계서

## 1. 참조
- 인수조건: docs/project/features.md #F-10
- ERD: docs/system/erd.md (notifications, notification_settings)
- API 컨벤션: docs/system/api-conventions.md
- 공고 수집 설계: docs/specs/F-01-bid-collection/design.md (NotificationService 스텁)

---

## 2. 변경 범위

- **변경 유형**: 신규 추가 + 기존 스텁 교체
- **영향 받는 모듈**:
  - NotificationService (스텁 -> 실제 구현으로 교체)
  - Settings (이메일/카카오 알림톡 설정 추가)
  - APScheduler (마감 임박 알림 스케줄 잡 추가)
  - 모델 __init__.py (Notification, NotificationSetting 등록)
  - API 라우터 (notifications 라우터 등록)

---

## 3. 영향 분석

### 기존 API 변경

| API | 현재 | 변경 후 | 하위 호환성 |
|-----|------|---------|-------------|
| (없음) | - | 신규 알림 API 추가 | 해당 없음 |

### 기존 DB 변경

| 테이블 | 변경 내용 | 마이그레이션 전략 |
|--------|----------|------------------|
| (없음) | notifications, notification_settings 신규 생성 | 신규 마이그레이션 파일 |

### 기존 코드 변경

| 파일 | 변경 내용 |
|------|----------|
| backend/src/services/notification_service.py | 스텁 -> 실제 구현 교체 |
| backend/src/models/__init__.py | Notification, NotificationSetting 모델 import 추가 |
| backend/src/api/v1/router.py | notifications 라우터 include 추가 |
| backend/src/config.py | 이메일/카카오 설정 추가 |
| backend/src/scheduler.py | 마감 임박 알림 스케줄 잡 추가 |
| backend/src/main.py | 변경 없음 (scheduler.py에서 잡 추가) |

### 사이드 이펙트
- BidMatchService._notify_high_score_matches()가 NotificationService를 호출하고 있으며, 스텁에서 실제 구현으로 교체되므로 매칭 알림이 실제로 발송됨
- user_bid_matches.is_notified 플래그가 실제 알림 발송 성공 여부와 연동됨
- user_bid_tracking 테이블은 아직 구현되지 않았으므로, 마감 임박 알림 대상 조회 시 user_bid_matches에서 interested/participating 상태 공고를 추적해야 함 (user_bid_tracking 모델 신규 생성 필요)

---

## 4. 아키텍처 결정

### 결정 1: 이메일 발송 기술
- **선택지**: A) smtplib (직접 SMTP) / B) SendGrid API / C) AWS SES
- **결정**: A) smtplib (aiosmtplib)
- **근거**:
  - MVP 단계에서 외부 SaaS 의존성 최소화
  - aiosmtplib으로 비동기 발송 가능
  - Gmail, Naver 등 기존 SMTP 서버 활용 가능
  - 추후 SendGrid/SES로 전환 시 EmailSender 인터페이스만 교체

### 결정 2: 알림 발송 아키텍처
- **선택지**: A) 동기 발송 (API 응답 내) / B) 백그라운드 태스크 (asyncio.create_task) / C) 메시지 큐 (Celery/RQ)
- **결정**: B) 백그라운드 태스크 (asyncio.create_task)
- **근거**:
  - 알림 발송은 사용자 응답을 차단하지 않아야 함
  - 스케줄러에서 트리거되는 알림은 이미 백그라운드에서 실행됨
  - MVP 규모에서 Celery 인프라(broker, worker)는 과도함
  - 실패 시 notifications 테이블에 기록하여 재시도 가능

### 결정 3: 인앱 알림 실시간 전달 방식
- **선택지**: A) 폴링 (GET /notifications + unread count) / B) SSE / C) WebSocket
- **결정**: A) 폴링
- **근거**:
  - 알림은 초 단위 실시간성이 불필요 (30초~1분 주기 폴링이면 충분)
  - SSE/WebSocket 대비 구현 복잡도 낮음
  - 프론트엔드에서 주기적으로 unread count API 호출
  - 추후 SSE로 전환 가능 (API 엔드포인트 추가만으로)

### 결정 4: 마감 임박 알림 스케줄
- **선택지**: A) 매시간 체크 / B) 매일 09:00 1회 체크 / C) 매일 09:00, 18:00 2회 체크
- **결정**: B) 매일 09:00 1회 체크 (KST)
- **근거**:
  - D-3, D-1 기준이므로 하루 1회 체크면 충분
  - 영업일 시작 시간인 09:00에 발송하여 업무 중 확인 가능
  - 스케줄러 부하 최소화

### 결정 5: 카카오 알림톡 처리
- **선택지**: A) 필수 구현 / B) 선택적 구현 (환경변수 제어)
- **결정**: B) 선택적 구현 (환경변수 제어)
- **근거**:
  - 기능 요구사항에 "선택사항"으로 명시됨
  - KAKAO_ALIMTALK_ENABLED=true 시에만 카카오 알림톡 발송
  - 카카오 비즈니스 계정 및 템플릿 승인이 필요하므로 환경 준비 전까지 비활성화
  - 인터페이스만 정의하고, 스텁 구현으로 대체

### 결정 6: 낙찰 결과 알림 트리거
- **선택지**: A) 스케줄러 기반 (크롤링 후 자동 감지) / B) 수동 등록 시 트리거
- **결정**: B) 수동 등록 시 트리거
- **근거**:
  - user_bid_tracking에서 결과(won/lost)를 등록할 때 알림 발송
  - 현재 낙찰 결과 자동 수집 기능이 없으므로 수동 등록이 현실적
  - F-06 대시보드에서 결과 입력 시 연동

---

## 5. API 설계

### 5.1 GET /api/v1/notifications
알림 목록 조회

- **목적**: 현재 사용자의 알림 목록 조회 (페이지네이션, 필터링)
- **인증**: 필요 (Bearer Token)
- **Query Parameters**:
  | Parameter | Type | Default | 설명 |
  |-----------|------|---------|------|
  | page | int | 1 | 페이지 번호 |
  | pageSize | int | 20 | 페이지당 항목 수 (최대 100) |
  | isRead | boolean | | 필터: true(읽음), false(안읽음) |
  | type | string | | 필터: bid_matched, deadline, bid_result, proposal_ready |
  | sortBy | string | createdAt | 정렬 필드 |
  | sortOrder | string | desc | 정렬 방향 |
- **Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "type": "bid_matched",
        "title": "새로운 매칭 공고",
        "content": "2026년 정보시스템 고도화 사업 공고가 매칭되었습니다. (적합도: 85점)",
        "data": {
          "bidId": "uuid",
          "bidTitle": "2026년 정보시스템 고도화 사업",
          "score": 85.0
        },
        "isRead": false,
        "channel": "in_app",
        "sentAt": "2026-03-08T06:05:00Z",
        "readAt": null,
        "createdAt": "2026-03-08T06:05:00Z"
      }
    ]
  },
  "meta": {
    "page": 1,
    "pageSize": 20,
    "total": 45,
    "totalPages": 3
  }
}
```
- **에러 케이스**:
  | 코드 | HTTP Status | 상황 |
  |------|-------------|------|
  | AUTH_002 | 401 | 인증 토큰 없음 |

### 5.2 GET /api/v1/notifications/unread-count
안읽은 알림 수 조회

- **목적**: 헤더 뱃지에 표시할 안읽은 알림 수 반환
- **인증**: 필요 (Bearer Token)
- **Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "unreadCount": 5
  }
}
```

### 5.3 PATCH /api/v1/notifications/{id}/read
알림 읽음 처리

- **목적**: 특정 알림을 읽음으로 표시
- **인증**: 필요 (Bearer Token)
- **Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "isRead": true,
    "readAt": "2026-03-08T10:30:00Z"
  }
}
```
- **에러 케이스**:
  | 코드 | HTTP Status | 상황 |
  |------|-------------|------|
  | NOTIFICATION_001 | 404 | 알림을 찾을 수 없음 |
  | PERMISSION_002 | 403 | 본인의 알림이 아님 |

### 5.4 POST /api/v1/notifications/read-all
전체 읽음 처리

- **목적**: 현재 사용자의 모든 안읽은 알림을 읽음으로 표시
- **인증**: 필요 (Bearer Token)
- **Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "updatedCount": 12
  }
}
```

### 5.5 GET /api/v1/notifications/settings
알림 설정 조회

- **목적**: 현재 사용자의 알림 유형별 설정 조회
- **인증**: 필요 (Bearer Token)
- **Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "settings": [
      {
        "notificationType": "bid_matched",
        "label": "매칭 공고 알림",
        "emailEnabled": true,
        "kakaoEnabled": false,
        "pushEnabled": true
      },
      {
        "notificationType": "deadline",
        "label": "마감 임박 알림",
        "emailEnabled": true,
        "kakaoEnabled": false,
        "pushEnabled": true
      },
      {
        "notificationType": "bid_result",
        "label": "낙찰 결과 알림",
        "emailEnabled": true,
        "kakaoEnabled": false,
        "pushEnabled": true
      },
      {
        "notificationType": "proposal_ready",
        "label": "제안서 생성 완료 알림",
        "emailEnabled": true,
        "kakaoEnabled": false,
        "pushEnabled": true
      }
    ]
  }
}
```

### 5.6 PUT /api/v1/notifications/settings
알림 설정 변경

- **목적**: 알림 유형별 채널 on/off 설정 변경
- **인증**: 필요 (Bearer Token)
- **Request Body**:
```json
{
  "settings": [
    {
      "notificationType": "bid_matched",
      "emailEnabled": true,
      "kakaoEnabled": false,
      "pushEnabled": false
    },
    {
      "notificationType": "deadline",
      "emailEnabled": false,
      "kakaoEnabled": false,
      "pushEnabled": true
    }
  ]
}
```
- **Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "updatedCount": 2
  }
}
```
- **에러 케이스**:
  | 코드 | HTTP Status | 상황 |
  |------|-------------|------|
  | VALIDATION_001 | 400 | 잘못된 notification_type 값 |

---

## 6. DB 설계

ERD (docs/system/erd.md)에 정의된 테이블 구조를 기본으로 사용합니다.

### 6.1 notifications 테이블

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 알림 ID |
| user_id | UUID | FK -> users.id, NOT NULL | 수신자 ID |
| type | VARCHAR(50) | NOT NULL | 알림 유형 (bid_matched, deadline, bid_result, proposal_ready) |
| title | VARCHAR(200) | NOT NULL | 알림 제목 |
| content | TEXT | NOT NULL | 알림 내용 |
| data | JSONB | | 관련 데이터 (bid_id, proposal_id, score 등) |
| is_read | BOOLEAN | NOT NULL, DEFAULT FALSE | 읽음 여부 |
| channel | VARCHAR(20) | NOT NULL, DEFAULT 'in_app' | 발송 채널 (in_app, email, kakao) |
| sent_at | TIMESTAMP | | 발송 시간 (이메일/카카오 실제 발송 시간) |
| read_at | TIMESTAMP | | 읽음 시간 |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 생성 시간 |

**Check Constraints**:
```sql
ALTER TABLE notifications
    ADD CONSTRAINT chk_notifications_type
    CHECK (type IN ('bid_matched', 'deadline', 'bid_result', 'proposal_ready'));

ALTER TABLE notifications
    ADD CONSTRAINT chk_notifications_channel
    CHECK (channel IN ('in_app', 'email', 'kakao'));
```

### 6.2 notification_settings 테이블

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 설정 ID |
| user_id | UUID | FK -> users.id, NOT NULL | 사용자 ID |
| notification_type | VARCHAR(50) | NOT NULL | 알림 유형 |
| email_enabled | BOOLEAN | NOT NULL, DEFAULT TRUE | 이메일 수신 여부 |
| kakao_enabled | BOOLEAN | NOT NULL, DEFAULT FALSE | 카카오 알림톡 수신 여부 (기본 비활성) |
| push_enabled | BOOLEAN | NOT NULL, DEFAULT TRUE | 인앱 푸시 수신 여부 |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 생성 시간 |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 수정 시간 |

**Unique Constraint**: (user_id, notification_type)

**Check Constraints**:
```sql
ALTER TABLE notification_settings
    ADD CONSTRAINT chk_notification_settings_type
    CHECK (notification_type IN ('bid_matched', 'deadline', 'bid_result', 'proposal_ready'));
```

### 6.3 기본 설정 초기화

사용자 가입 시 4개 알림 유형에 대한 기본 설정 레코드를 자동 생성합니다.

```python
DEFAULT_NOTIFICATION_TYPES = [
    ("bid_matched", "매칭 공고 알림"),
    ("deadline", "마감 임박 알림"),
    ("bid_result", "낙찰 결과 알림"),
    ("proposal_ready", "제안서 생성 완료 알림"),
]
```

기존 사용자에 대해서는 마이그레이션 시 기본 설정 레코드를 일괄 생성합니다.

---

## 7. 서비스 설계

### 7.1 NotificationService -- 알림 통합 서비스

**책임**: 알림 생성, 발송 채널 분기, 알림 조회/설정 관리

```python
class NotificationService:
    """알림 통합 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.email_sender = EmailSender()
        self.kakao_sender = KakaoAlimtalkSender()  # 스텁

    async def send_notification(
        self,
        user_id: UUID,
        notification_type: str,
        title: str,
        content: str,
        data: dict | None = None,
    ) -> Notification:
        """
        알림 발송 메인 플로우

        1. notification_settings 조회 (사용자 설정 확인)
        2. in_app 알림 레코드 생성 (notifications 테이블)
        3. email_enabled이면 이메일 발송 (백그라운드)
        4. kakao_enabled이면 카카오 알림톡 발송 (백그라운드)
        Returns: 생성된 Notification 레코드
        """

    async def send_bid_match_notification(
        self,
        user_id: UUID | str,
        bid_id: UUID | str,
        score: float,
    ) -> None:
        """
        매칭 알림 발송 (기존 스텁 인터페이스 유지)

        - BidMatchService에서 호출하는 기존 인터페이스와 동일
        - 내부적으로 send_notification() 호출
        - bid 정보 조회하여 title/content 생성
        """

    async def send_deadline_notifications(self) -> int:
        """
        마감 임박 알림 일괄 발송 (스케줄러에서 호출)

        1. user_bid_tracking에서 참여 중(interested, participating) 상태 조회
        2. 마감일이 D-3 또는 D-1인 공고 필터링
        3. 해당 사용자들에게 알림 발송
        Returns: 발송된 알림 수
        """

    async def send_bid_result_notification(
        self,
        user_id: UUID,
        bid_id: UUID,
        is_winner: bool,
    ) -> None:
        """
        낙찰/실패 결과 알림 발송

        - user_bid_tracking에서 결과 등록 시 호출
        - is_winner에 따라 제목/내용 분기
        """

    async def send_admin_alert(self, message: str) -> None:
        """
        관리자 알림 발송 (기존 스텁 인터페이스 유지)

        - 시스템 오류, 수집 실패 등 관리자 대상 알림
        - 이메일로 발송
        """

    async def get_notifications(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        is_read: bool | None = None,
        notification_type: str | None = None,
    ) -> tuple[list[Notification], int]:
        """
        알림 목록 조회

        Returns: (알림 목록, 전체 건수)
        """

    async def get_unread_count(self, user_id: UUID) -> int:
        """안읽은 알림 수 조회"""

    async def mark_as_read(self, notification_id: UUID, user_id: UUID) -> Notification:
        """
        단일 알림 읽음 처리

        - 본인의 알림이 아니면 PERMISSION_002 에러
        """

    async def mark_all_as_read(self, user_id: UUID) -> int:
        """전체 읽음 처리, Returns: 업데이트된 건수"""

    async def get_settings(self, user_id: UUID) -> list[NotificationSetting]:
        """알림 설정 조회 (없으면 기본값 생성)"""

    async def update_settings(
        self,
        user_id: UUID,
        settings: list[dict],
    ) -> int:
        """알림 설정 변경, Returns: 업데이트된 건수"""
```

### 7.2 EmailSender -- 이메일 발송

```python
class EmailSender:
    """이메일 발송 (aiosmtplib)"""

    def __init__(self):
        self.settings = get_settings()

    async def send(
        self,
        to_email: str,
        subject: str,
        body_html: str,
    ) -> bool:
        """
        이메일 발송

        - aiosmtplib.send 사용
        - SMTP 설정: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
        - 실패 시 False 반환 + 로그 기록 (예외 전파 안 함)
        """

    def _render_template(
        self,
        template_name: str,
        context: dict,
    ) -> str:
        """
        이메일 HTML 템플릿 렌더링 (Jinja2)

        템플릿 종류:
        - bid_matched.html: 매칭 공고 알림
        - deadline.html: 마감 임박 알림
        - bid_result.html: 낙찰 결과 알림
        - proposal_ready.html: 제안서 완료 알림
        """
```

### 7.3 KakaoAlimtalkSender -- 카카오 알림톡 (스텁)

```python
class KakaoAlimtalkSender:
    """카카오 알림톡 발송 (환경변수로 제어, 기본 비활성)"""

    def __init__(self):
        self.settings = get_settings()
        self.enabled = self.settings.kakao_alimtalk_enabled

    async def send(
        self,
        phone: str,
        template_code: str,
        variables: dict,
    ) -> bool:
        """
        카카오 알림톡 발송

        - KAKAO_ALIMTALK_ENABLED=false이면 로그만 기록
        - 향후 카카오 비즈메시지 API 연동
        """
```

---

## 8. 알림 유형 및 트리거 설계

### 8.1 알림 유형 정의

| 유형 코드 | 트리거 시점 | 발송 주체 | 제목 템플릿 |
|-----------|-----------|-----------|-------------|
| bid_matched | 매칭 분석 완료 (total_score >= 70) | BidMatchService | "새로운 매칭 공고: {bid_title}" |
| deadline | 마감 D-3, D-1 | 스케줄러 (09:00 KST) | "마감 임박: {bid_title} (D-{days})" |
| bid_result | user_bid_tracking 결과 등록 시 | API 호출 시 | "낙찰 결과: {bid_title}" |
| proposal_ready | 제안서 AI 생성 완료 시 | ProposalService (F-03) | "제안서 생성 완료: {proposal_title}" |

### 8.2 알림별 data 필드 구조

**bid_matched**:
```json
{
  "bidId": "uuid",
  "bidTitle": "공고 제목",
  "score": 85.0,
  "recommendation": "recommended"
}
```

**deadline**:
```json
{
  "bidId": "uuid",
  "bidTitle": "공고 제목",
  "deadline": "2026-03-22T17:00:00Z",
  "daysLeft": 3
}
```

**bid_result**:
```json
{
  "bidId": "uuid",
  "bidTitle": "공고 제목",
  "isWinner": true,
  "winningPrice": 450000000
}
```

**proposal_ready**:
```json
{
  "proposalId": "uuid",
  "proposalTitle": "제안서 제목",
  "bidId": "uuid"
}
```

---

## 9. 스케줄러 통합 설계

### 9.1 마감 임박 알림 스케줄 잡

```python
# backend/src/scheduler.py에 추가

async def scheduled_deadline_notifications() -> None:
    """
    마감 임박 알림 스케줄러 작업

    1. 현재 날짜 기준 D-3, D-1 마감 공고 조회
    2. 해당 공고에 참여 중인 사용자 목록 조회 (user_bid_tracking)
    3. 각 사용자에게 알림 발송
    """

# create_scheduler()에 잡 추가
scheduler.add_job(
    scheduled_deadline_notifications,
    CronTrigger(hour=9, minute=0, timezone="Asia/Seoul"),
    id="deadline_notifications",
    name="마감 임박 알림",
    replace_existing=True,
    max_instances=1,
)
```

### 9.2 마감 임박 알림 대상 판별 로직

```python
# D-3, D-1 계산
from datetime import date, timedelta

today = date.today()
d_minus_3 = today + timedelta(days=3)
d_minus_1 = today + timedelta(days=1)

# 쿼리: deadline 날짜가 D-3 또는 D-1인 open 상태 공고
# + user_bid_tracking에서 해당 공고에 interested/participating 상태인 사용자
```

### 9.3 중복 알림 방지

- 동일 user + bid + type + date 조합으로 이미 알림이 발송된 경우 중복 발송하지 않음
- notifications 테이블에서 당일 발송 여부를 체크

---

## 10. 시퀀스 흐름

### 10.1 매칭 알림 발송 (기존 F-01 파이프라인 연동)

```
BidMatchService.analyze_new_bids_for_all_users()
    |
    | 1. 매칭 점수 70점 이상 공고 감지
    |
    v
NotificationService.send_bid_match_notification(user_id, bid_id, score)
    |
    | 2. notification_settings 조회 (사용자 설정)
    | 3. notifications 테이블에 in_app 알림 생성
    | 4. email_enabled? -> asyncio.create_task(EmailSender.send())
    | 5. kakao_enabled? -> asyncio.create_task(KakaoAlimtalkSender.send())
    | 6. user_bid_matches.is_notified = True
    |
    v
알림 발송 완료
```

### 10.2 마감 임박 알림 (스케줄러)

```
APScheduler (09:00 KST)
    |
    | 1. scheduled_deadline_notifications() 호출
    |
    v
NotificationService.send_deadline_notifications()
    |
    | 2. D-3, D-1 마감 공고 + 참여 중인 사용자 조회
    | 3. 중복 알림 체크 (당일 동일 알림 이미 발송?)
    | 4. 각 사용자에게 send_notification() 호출
    |    |- in_app 알림 레코드 생성
    |    |- 이메일 발송 (설정에 따라)
    |
    v
완료 (발송 건수 로깅)
```

### 10.3 알림 목록 조회 (프론트엔드)

```
사용자 -> Frontend -> GET /notifications -> NotificationsAPI -> DB
    |                                              |
    | 1. 알림 목록 요청 (is_read, type 필터)         |
    | ------------------------------------------>|
    |                                              | 2. notifications 테이블 조회
    |  <------------------------------------------|
    | 3. 알림 목록 + 페이지네이션 반환                 |
    |                                              |
    |    GET /notifications/unread-count            |
    | ------------------------------------------>|
    |                                              | 4. COUNT(is_read=false) 조회
    |  <------------------------------------------|
    | 5. 뱃지 숫자 표시                              |
```

---

## 11. 영향 범위

### 11.1 수정 필요 파일

| 파일 | 변경 내용 |
|------|----------|
| backend/src/services/notification_service.py | 스텁 -> 실제 구현 교체 |
| backend/src/models/__init__.py | Notification, NotificationSetting import 추가 |
| backend/src/api/v1/router.py | notifications 라우터 include |
| backend/src/config.py | SMTP, 카카오 알림톡 설정 추가 |
| backend/src/scheduler.py | scheduled_deadline_notifications 잡 추가 |

### 11.2 신규 생성 파일

| 파일 | 설명 |
|------|------|
| backend/src/models/notification.py | Notification 모델 |
| backend/src/models/notification_setting.py | NotificationSetting 모델 |
| backend/src/schemas/notification.py | 알림 관련 Pydantic 스키마 |
| backend/src/services/email_sender.py | 이메일 발송 서비스 |
| backend/src/services/kakao_sender.py | 카카오 알림톡 발송 서비스 (스텁) |
| backend/src/api/v1/notifications.py | 알림 API 엔드포인트 |
| backend/src/templates/email/bid_matched.html | 매칭 알림 이메일 템플릿 |
| backend/src/templates/email/deadline.html | 마감 임박 이메일 템플릿 |
| backend/src/templates/email/bid_result.html | 낙찰 결과 이메일 템플릿 |
| backend/src/templates/email/proposal_ready.html | 제안서 완료 이메일 템플릿 |
| backend/src/templates/email/base.html | 이메일 기본 레이아웃 템플릿 |

---

## 12. 성능 설계

### 12.1 인덱스 계획

```sql
-- ERD에 이미 정의된 인덱스
CREATE INDEX idx_notifications_user_unread
    ON notifications(user_id, is_read) WHERE is_read = FALSE;
CREATE INDEX idx_notifications_user_created
    ON notifications(user_id, created_at DESC);

-- 추가 인덱스: 중복 알림 방지용 복합 인덱스
CREATE INDEX idx_notifications_dedup
    ON notifications(user_id, type, created_at::date)
    WHERE type = 'deadline';

-- 알림 설정 유니크 인덱스
CREATE UNIQUE INDEX idx_notification_settings_unique
    ON notification_settings(user_id, notification_type);
```

### 12.2 캐싱 전략

```
# 안읽은 알림 수 캐시 (Redis)
notifications:unread:{user_id} -> int (TTL: 60초)
- 알림 생성/읽음 처리 시 캐시 무효화

# 알림 설정 캐시 (Redis)
notifications:settings:{user_id} -> json (TTL: 5분)
- 알림 설정 변경 시 캐시 무효화
```

### 12.3 이메일 발송 성능

- 백그라운드 태스크로 발송하여 API 응답 차단 없음
- 마감 임박 알림 일괄 발송 시 대량 이메일은 순차 발송 (SMTP 서버 부하 고려)
- 발송 간 0.1초 딜레이 적용 (throttling)
- 발송 실패 시 재시도하지 않음 (MVP), 로그 기록만

---

## 13. 에러 코드 요약

### 신규 에러 코드 (F-10 추가)

| 코드 | HTTP Status | 메시지 |
|------|-------------|--------|
| NOTIFICATION_001 | 404 | 알림을 찾을 수 없습니다. |
| NOTIFICATION_002 | 500 | 알림 발송에 실패했습니다. |
| NOTIFICATION_003 | 500 | 이메일 발송에 실패했습니다. |

### 기존 공통 에러 코드 (재사용)

| 코드 | HTTP Status | 메시지 |
|------|-------------|--------|
| AUTH_002 | 401 | 인증 토큰이 필요합니다. |
| PERMISSION_002 | 403 | 리소스 소유자가 아닙니다. |
| VALIDATION_001 | 400 | 입력값이 유효하지 않습니다. |

---

## 14. 설정 변경

### backend/src/config.py 추가 필드

```python
class Settings(BaseSettings):
    # ... 기존 설정 ...

    # 이메일 (F-10)
    smtp_host: str = ""  # 환경변수: SMTP_HOST
    smtp_port: int = 587  # 환경변수: SMTP_PORT
    smtp_user: str = ""  # 환경변수: SMTP_USER
    smtp_password: str = ""  # 환경변수: SMTP_PASSWORD
    smtp_from_email: str = "noreply@bidmaster.kr"
    smtp_from_name: str = "BidMaster"
    email_enabled: bool = True  # 이메일 발송 활성화 여부

    # 카카오 알림톡 (F-10, 선택사항)
    kakao_alimtalk_enabled: bool = False  # 기본 비활성
    kakao_alimtalk_api_key: str = ""
    kakao_alimtalk_sender_key: str = ""

    # 알림 스케줄러 (F-10)
    deadline_notification_hour: int = 9  # KST 마감 임박 알림 시각
    deadline_notification_days: str = "3,1"  # D-3, D-1
```

---

## 15. 의존성 추가

### requirements.txt 추가

```
aiosmtplib>=2.0.0          # 비동기 이메일 발송
jinja2>=3.1.0              # 이메일 템플릿 렌더링
```

**참고**: Jinja2는 FastAPI 의존성으로 이미 설치되어 있을 수 있음. 명시적으로 추가.

---

## 변경 이력

| 날짜 | 변경 내용 | 이유 |
|------|----------|------|
| 2026-03-08 | 초기 변경 설계 | F-10 알림 시스템 구현 시작 |
