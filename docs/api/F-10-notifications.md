# F-10 알림 시스템 API 스펙

## 개요

알림 조회, 읽음 처리, 설정 관리를 위한 API입니다. 알림 생성은 내부 서비스에서 자동으로 수행되며, 이 API는 프론트엔드 소비용입니다.

**Base URL**: `/api/v1/notifications`

---

## 공통 응답 포맷

```json
{
  "success": true,
  "data": { ... },
  "meta": { ... }
}
```

에러 응답:
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "에러 메시지"
  }
}
```

---

## 에러 코드

| 코드 | HTTP | 설명 |
|------|------|------|
| AUTH_002 | 401 | 인증 토큰이 필요합니다 |
| NOTIFICATION_001 | 404 | 알림을 찾을 수 없습니다 |
| PERMISSION_002 | 403 | 리소스 소유자가 아닙니다 |
| VALIDATION_001 | 400 | 입력값 유효성 실패 |

---

## 알림 유형 (notification type)

| 코드 | 설명 | 트리거 |
|------|------|--------|
| bid_matched | 매칭 공고 알림 | 매칭 점수 70점 이상 공고 분석 완료 시 |
| deadline | 마감 임박 알림 | 스케줄러 09:00 KST, 마감 D-3/D-1 공고 |
| bid_result | 낙찰 결과 알림 | 사용자가 입찰 결과 등록 시 |
| proposal_ready | 제안서 생성 완료 | AI 제안서 생성 완료 시 |

---

## 엔드포인트

### 1. 알림 목록 조회

```
GET /api/v1/notifications
```

**인증**: Bearer Token 필수

**쿼리 파라미터**:

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| page | int | 1 | 페이지 번호 |
| pageSize | int | 20 | 페이지 크기 (최대 100) |
| isRead | boolean | - | 필터: true(읽음), false(안읽음) |
| type | string | - | 필터: bid_matched, deadline, bid_result, proposal_ready |
| sortBy | string | createdAt | 정렬 기준 |
| sortOrder | string | desc | 정렬 방향: asc/desc |

**성공 응답** (200):
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "type": "bid_matched",
        "title": "새로운 매칭 공고: 2026년 정보시스템 고도화 사업",
        "content": "2026년 정보시스템 고도화 사업 공고가 매칭되었습니다. (적합도: 85점)",
        "data": {
          "bidId": "660e8400-e29b-41d4-a716-446655440001",
          "bidTitle": "2026년 정보시스템 고도화 사업",
          "score": 85.0,
          "recommendation": "recommended"
        },
        "isRead": false,
        "channel": "in_app",
        "sentAt": "2026-03-08T06:05:00+00:00",
        "readAt": null,
        "createdAt": "2026-03-08T06:05:00+00:00"
      },
      {
        "id": "550e8400-e29b-41d4-a716-446655440002",
        "type": "deadline",
        "title": "마감 임박: 클라우드 인프라 구축 사업 (D-3)",
        "content": "클라우드 인프라 구축 사업 공고가 3일 후 마감됩니다.",
        "data": {
          "bidId": "660e8400-e29b-41d4-a716-446655440003",
          "bidTitle": "클라우드 인프라 구축 사업",
          "deadline": "2026-03-11T17:00:00+00:00",
          "daysLeft": 3
        },
        "isRead": true,
        "channel": "in_app",
        "sentAt": "2026-03-08T00:00:00+00:00",
        "readAt": "2026-03-08T09:15:00+00:00",
        "createdAt": "2026-03-08T00:00:00+00:00"
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

**에러 응답**:
- `401 AUTH_002`: 인증 토큰 없음

---

### 2. 안읽은 알림 수 조회

```
GET /api/v1/notifications/unread-count
```

**인증**: Bearer Token 필수

폴링 방식으로 프론트엔드 헤더 뱃지 표시에 사용됩니다. 30초~1분 주기 호출 권장.

**성공 응답** (200):
```json
{
  "success": true,
  "data": {
    "unreadCount": 5
  }
}
```

**에러 응답**:
- `401 AUTH_002`: 인증 토큰 없음

---

### 3. 알림 읽음 처리

```
PATCH /api/v1/notifications/{notification_id}/read
```

**인증**: Bearer Token 필수

**경로 파라미터**:
- `notification_id` (UUID): 알림 ID

**성공 응답** (200):
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "isRead": true,
    "readAt": "2026-03-08T10:30:00+00:00"
  }
}
```

**에러 응답**:
- `401 AUTH_002`: 인증 토큰 없음
- `403 PERMISSION_002`: 본인의 알림이 아님
- `404 NOTIFICATION_001`: 알림 없음
- `422`: notification_id가 UUID 형식이 아님

---

### 4. 전체 읽음 처리

```
POST /api/v1/notifications/read-all
```

**인증**: Bearer Token 필수

현재 사용자의 모든 안읽은 알림을 읽음으로 처리합니다.

**성공 응답** (200):
```json
{
  "success": true,
  "data": {
    "updatedCount": 12
  }
}
```

**에러 응답**:
- `401 AUTH_002`: 인증 토큰 없음

---

### 5. 알림 설정 조회

```
GET /api/v1/notifications/settings
```

**인증**: Bearer Token 필수

설정 레코드가 없는 경우 기본값(모두 활성)으로 자동 생성 후 반환합니다.

**성공 응답** (200):
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

**에러 응답**:
- `401 AUTH_002`: 인증 토큰 없음

---

### 6. 알림 설정 변경

```
PUT /api/v1/notifications/settings
```

**인증**: Bearer Token 필수

부분 변경을 지원합니다. 전송한 항목만 변경되고, 전송하지 않은 항목은 유지됩니다.

**요청 본문**:
```json
{
  "settings": [
    {
      "notificationType": "bid_matched",
      "emailEnabled": false,
      "kakaoEnabled": false,
      "pushEnabled": true
    },
    {
      "notificationType": "deadline",
      "emailEnabled": true,
      "kakaoEnabled": false,
      "pushEnabled": false
    }
  ]
}
```

**필드 설명**:

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| settings | array | Y | 변경할 설정 목록 |
| settings[].notificationType | string | Y | 알림 유형 코드 |
| settings[].emailEnabled | boolean | Y | 이메일 수신 여부 |
| settings[].kakaoEnabled | boolean | Y | 카카오 알림톡 수신 여부 |
| settings[].pushEnabled | boolean | Y | 인앱 알림 수신 여부 |

**유효한 notificationType 값**: `bid_matched`, `deadline`, `bid_result`, `proposal_ready`

**성공 응답** (200):
```json
{
  "success": true,
  "data": {
    "updatedCount": 2
  }
}
```

**에러 응답**:
- `401 AUTH_002`: 인증 토큰 없음
- `400 VALIDATION_001`: 잘못된 notificationType 값

---

## 내부 알림 발송 (서비스 간 호출)

아래는 API 엔드포인트가 아닌 내부 서비스 호출 인터페이스입니다.

### 매칭 알림 발송

BidMatchService에서 호출합니다. 기존 스텁 인터페이스와 동일합니다.

```python
await notification_service.send_bid_match_notification(
    user_id="uuid",
    bid_id="uuid",
    score=85.0
)
```

### 마감 임박 알림 발송

APScheduler에서 매일 09:00 KST에 호출됩니다.

```python
count = await notification_service.send_deadline_notifications()
```

### 낙찰 결과 알림 발송

user_bid_tracking 결과 등록 시 호출됩니다.

```python
await notification_service.send_bid_result_notification(
    user_id="uuid",
    bid_id="uuid",
    is_winner=True
)
```
