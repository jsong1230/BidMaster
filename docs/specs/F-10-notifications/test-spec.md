# F-10 알림 시스템 -- 테스트 명세

## 참조
- 설계서: docs/specs/F-10-notifications/design.md
- 인수조건: docs/project/features.md #F-10

---

## 단위 테스트

### NotificationService

| 대상 | 시나리오 | 입력 | 예상 결과 |
|------|----------|------|-----------|
| send_notification | 정상 알림 생성 | user_id, type="bid_matched", title, content | notifications 레코드 생성, is_read=False |
| send_notification | 사용자 설정에 따른 이메일 발송 | email_enabled=True | EmailSender.send() 호출됨 |
| send_notification | 이메일 비활성화 시 발송 안 함 | email_enabled=False | EmailSender.send() 호출 안 됨 |
| send_notification | 카카오 비활성화(기본) 시 발송 안 함 | kakao_enabled=False | KakaoAlimtalkSender.send() 호출 안 됨 |
| send_bid_match_notification | 기존 인터페이스 호환 | user_id(str), bid_id(str), score=85.0 | notifications 레코드 생성, 타입=bid_matched |
| send_bid_match_notification | bid 정보 조회하여 제목 생성 | bid_id | title에 공고 제목 포함 |
| send_deadline_notifications | D-3 마감 공고 감지 | 마감일이 3일 후인 공고 + 참여 중 사용자 | 해당 사용자에게 알림 생성 |
| send_deadline_notifications | D-1 마감 공고 감지 | 마감일이 1일 후인 공고 + 참여 중 사용자 | 해당 사용자에게 알림 생성 |
| send_deadline_notifications | D-5 마감 공고 (대상 아님) | 마감일이 5일 후인 공고 | 알림 발송 안 됨 |
| send_deadline_notifications | 중복 알림 방지 | 당일 이미 D-3 알림 발송된 공고 | 추가 알림 발송 안 됨 |
| send_deadline_notifications | 참여 중이 아닌 공고 | interested/participating이 아닌 상태 | 알림 발송 안 됨 |
| send_bid_result_notification | 낙찰 결과 알림 | is_winner=True | "낙찰" 키워드 포함 알림 생성 |
| send_bid_result_notification | 실패 결과 알림 | is_winner=False | "유감" 키워드 포함 알림 생성 |
| send_admin_alert | 관리자 알림 발송 | message="수집 실패" | 이메일 발송 호출 |
| get_notifications | 페이지네이션 | page=1, page_size=10 | 최대 10건 반환, 전체 건수 포함 |
| get_notifications | 읽음 필터 | is_read=False | 안읽은 알림만 반환 |
| get_notifications | 유형 필터 | type="deadline" | deadline 타입만 반환 |
| get_notifications | 정렬 (최신순) | sortOrder=desc | created_at 내림차순 |
| get_unread_count | 안읽은 수 | 5건 안읽음 | 5 반환 |
| get_unread_count | 전부 읽음 | 0건 안읽음 | 0 반환 |
| mark_as_read | 정상 읽음 처리 | 본인의 알림 ID | is_read=True, read_at 설정 |
| mark_as_read | 타인의 알림 | 타인의 알림 ID | PERMISSION_002 예외 |
| mark_as_read | 존재하지 않는 알림 | 없는 UUID | NOTIFICATION_001 예외 |
| mark_as_read | 이미 읽은 알림 | is_read=True인 알림 | 정상 처리 (멱등) |
| mark_all_as_read | 전체 읽음 | 안읽은 알림 5건 | 5건 업데이트, 반환값 5 |
| mark_all_as_read | 안읽은 알림 없음 | 0건 | 반환값 0 |
| get_settings | 설정 존재 시 | user_id | 4개 알림 유형 설정 반환 |
| get_settings | 설정 미존재 시 (최초 조회) | user_id (신규) | 기본 설정 4개 자동 생성 후 반환 |
| update_settings | 정상 변경 | bid_matched의 emailEnabled=false | 해당 레코드 업데이트 |
| update_settings | 잘못된 notification_type | type="invalid_type" | VALIDATION_001 예외 |
| update_settings | 부분 변경 (1개만) | 1개 설정만 전송 | 해당 1개만 변경, 나머지 유지 |

### EmailSender

| 대상 | 시나리오 | 입력 | 예상 결과 |
|------|----------|------|-----------|
| send | 정상 발송 | to, subject, body_html | True 반환 |
| send | SMTP 연결 실패 | 잘못된 호스트 | False 반환, 에러 로그 기록 |
| send | email_enabled=False 시 | 설정 비활성 | 발송 시도 안 함, True 반환 |
| _render_template | bid_matched 템플릿 | context 딕셔너리 | HTML 문자열 반환 |
| _render_template | 존재하지 않는 템플릿 | 잘못된 template_name | TemplateNotFound 예외 |

### KakaoAlimtalkSender

| 대상 | 시나리오 | 입력 | 예상 결과 |
|------|----------|------|-----------|
| send | 비활성화 상태 (기본) | enabled=False | 로그만 기록, True 반환 |

---

## 통합 테스트

### 알림 목록 조회 API

| API | 시나리오 | 입력 | 예상 결과 |
|-----|----------|------|-----------|
| GET /notifications | 정상 조회 | 인증 토큰 | 200, 알림 목록 반환 |
| GET /notifications | 미인증 | 토큰 없음 | 401, AUTH_002 |
| GET /notifications | 페이지네이션 | page=2&pageSize=5 | 200, meta에 page=2 |
| GET /notifications | 안읽음 필터 | isRead=false | 200, 안읽은 알림만 |
| GET /notifications | 유형 필터 | type=bid_matched | 200, bid_matched만 |
| GET /notifications | 빈 목록 | 알림 없는 사용자 | 200, items=[], total=0 |

### 안읽은 알림 수 API

| API | 시나리오 | 입력 | 예상 결과 |
|-----|----------|------|-----------|
| GET /notifications/unread-count | 정상 | 인증 토큰 | 200, unreadCount 숫자 |
| GET /notifications/unread-count | 미인증 | 토큰 없음 | 401 |

### 알림 읽음 처리 API

| API | 시나리오 | 입력 | 예상 결과 |
|-----|----------|------|-----------|
| PATCH /notifications/{id}/read | 정상 읽음 | 본인 알림 ID | 200, isRead=true, readAt 설정 |
| PATCH /notifications/{id}/read | 없는 알림 | 존재하지 않는 UUID | 404, NOTIFICATION_001 |
| PATCH /notifications/{id}/read | 타인 알림 | 다른 사용자의 알림 ID | 403, PERMISSION_002 |
| PATCH /notifications/{id}/read | 잘못된 UUID | "not-a-uuid" | 422 |

### 전체 읽음 처리 API

| API | 시나리오 | 입력 | 예상 결과 |
|-----|----------|------|-----------|
| POST /notifications/read-all | 정상 | 인증 토큰 | 200, updatedCount 반환 |
| POST /notifications/read-all | 이미 전부 읽음 | 안읽은 알림 없음 | 200, updatedCount=0 |

### 알림 설정 API

| API | 시나리오 | 입력 | 예상 결과 |
|-----|----------|------|-----------|
| GET /notifications/settings | 정상 조회 | 인증 토큰 | 200, 4개 알림 유형 설정 |
| GET /notifications/settings | 최초 조회 (설정 없음) | 신규 사용자 | 200, 기본값으로 4개 생성 후 반환 |
| PUT /notifications/settings | 정상 변경 | 유효한 settings 배열 | 200, updatedCount |
| PUT /notifications/settings | 잘못된 type | notificationType="invalid" | 400, VALIDATION_001 |
| PUT /notifications/settings | 미인증 | 토큰 없음 | 401, AUTH_002 |
| PUT /notifications/settings | 빈 배열 | settings=[] | 200, updatedCount=0 |

---

## 경계 조건 / 에러 케이스

### 알림 생성
- 존재하지 않는 user_id로 알림 생성 시 FK 위반 에러 처리
- data 필드에 매우 큰 JSON 전달 시 정상 저장 (JSONB 제한 없음)
- 동시에 여러 알림 생성 시 데이터 무결성 유지

### 이메일 발송
- SMTP 서버 연결 타임아웃 (5초) 시 graceful 실패
- SMTP 인증 실패 시 에러 로그 + 알림 레코드는 정상 생성
- 수신자 이메일 주소가 유효하지 않은 형식일 때 발송 스킵

### 마감 임박 알림
- 마감일이 오늘인 공고 (D-0): 알림 대상 아님 (D-3, D-1만 해당)
- 마감일이 이미 지난 공고: 알림 대상 아님
- closed/cancelled 상태 공고: 알림 대상 아님 (open 상태만)
- 하루에 D-3과 D-1이 동시에 해당하는 경우: 불가능 (논리적으로 겹치지 않음)
- user_bid_tracking에 submitted 상태 사용자: 이미 제출했으므로 알림 대상에서 제외할지 결정 필요 -> 포함 (마감 후 수정/재제출 가능성)

### 알림 설정
- 사용자가 직접 DB에서 notification_settings를 삭제한 경우: GET /settings 시 기본값으로 재생성
- notification_type에 정의되지 않은 유형 전달: VALIDATION_001 에러

### 동시성
- 여러 매칭 알림이 동시에 발송될 때 race condition 없음 확인
- mark_all_as_read 호출 중 새 알림이 도착하는 경우: 새 알림은 안읽음 유지 (WHERE created_at <= 요청 시점)

---

## 회귀 테스트

| 기존 기능 | 영향 여부 | 검증 방법 |
|-----------|-----------|-----------|
| F-01 매칭 알림 (스텁) | 높음 - 스텁이 실제 구현으로 교체됨 | BidMatchService._notify_high_score_matches()가 NotificationService의 새 구현을 사용해도 정상 동작 확인. 기존 인터페이스(send_bid_match_notification(user_id, bid_id, score)) 호환성 검증 |
| F-01 공고 수집 스케줄러 | 중간 - scheduler.py에 새 잡 추가 | 기존 bid_collection 잡이 정상 동작하는지 확인. create_scheduler()에서 두 잡이 독립적으로 등록되는지 검증 |
| F-01 수동 수집 API | 낮음 | POST /bids/collect API 정상 동작 확인 |
| F-07 인증 | 낮음 | 알림 API 엔드포인트에서 Bearer 토큰 인증이 기존 auth 미들웨어와 동일하게 동작 |
| F-02 스코어링 | 낮음 | 스코어링 결과가 알림 발송과 독립적으로 동작 확인 |
| 기존 APScheduler lifespan | 중간 | main.py lifespan에서 scheduler가 정상 시작/종료 확인 (새 잡 추가 후에도) |
