# F-10 알림 시스템 -- 구현 계획서

## 참조
- 설계서: docs/specs/F-10-notifications/design.md
- 인수조건: docs/project/features.md #F-10
- 테스트 명세: docs/specs/F-10-notifications/test-spec.md

---

## 구현 상태 확인

### 백엔드: ✅ 구현 완료
- 모델: notification.py, notification_setting.py ✅
- 스키마: notification.py ✅
- 서비스: notification_service.py, email_sender.py, kakao_sender.py ✅
- API: notifications.py ✅
- 라우터: router.py에 등록됨 ✅
- 스케줄러: scheduler.py에 deadline_notifications 잡 등록됨 ✅
- 이메일 템플릿: 5개 모두 존재 ✅
- 설정: config.py에 SMTP/카카오/알림 설정 추가됨 ✅

### 프론트엔드: ❌ 미구현
- 알림 API 클라이언트 필요
- 알림 Zustand 스토어 필요
- 알림 벨 컴포넌트 (헤더) 필요
- 알림 목록 페이지 필요
- 알림 설정 페이지 필요

---

## 태스크 목록 (프론트엔드만)

### Phase 1: 타입 정의 + API 클라이언트

#### T1: 타입 및 API
- [ ] [frontend] `frontend/src/types/notification.ts` — 알림 관련 TypeScript 타입
- [ ] [frontend] `frontend/src/lib/api/notifications.ts` — 알림 API 클라이언트

| 태스크 | 설명 | 파일 |
|--------|------|------|
| T1-1 | 알림 TypeScript 타입 | frontend/src/types/notification.ts |
| T1-2 | 알림 API 클라이언트 | frontend/src/lib/api/notifications.ts |

### Phase 2: 상태 관리

#### T2: Zustand 스토어
- [ ] [frontend] `frontend/src/lib/stores/notification-store.ts` — 알림 Zustand 스토어 (목록, unread count, 폴링)

| 태스크 | 설명 | 파일 |
|--------|------|------|
| T2-1 | 알림 Zustand 스토어 | frontend/src/lib/stores/notification-store.ts |

### Phase 3: UI 컴포넌트 + 페이지

#### T3: 컴포넌트
- [ ] [frontend] `frontend/src/components/layout/NotificationBell.tsx` — 헤더 알림 벨 + 드롭다운
- [ ] [frontend] `frontend/src/components/notifications/NotificationItem.tsx` — 알림 아이템 컴포넌트
- [ ] [frontend] `frontend/src/components/notifications/NotificationList.tsx` — 알림 목록 컴포넌트
- [ ] [frontend] `frontend/src/components/notifications/NotificationSettingsForm.tsx` — 알림 설정 폼

| 태스크 | 설명 | 파일 |
|--------|------|------|
| T3-1 | NotificationBell (헤더 알림) | frontend/src/components/layout/NotificationBell.tsx |
| T3-2 | NotificationItem 컴포넌트 | frontend/src/components/notifications/NotificationItem.tsx |
| T3-3 | NotificationList 컴포넌트 | frontend/src/components/notifications/NotificationList.tsx |
| T3-4 | NotificationSettingsForm | frontend/src/components/notifications/NotificationSettingsForm.tsx |

#### T4: 페이지
- [ ] [frontend] `frontend/src/app/(main)/(dashboard)/notifications/page.tsx` — 알림 목록 페이지
- [ ] [frontend] `frontend/src/app/(main)/(dashboard)/settings/notifications/page.tsx` — 알림 설정 페이지

| 태스크 | 설명 | 파일 |
|--------|------|------|
| T4-1 | 알림 목록 페이지 | frontend/src/app/(main)/(dashboard)/notifications/page.tsx |
| T4-2 | 알림 설정 페이지 | frontend/src/app/(main)/(dashboard)/settings/notifications/page.tsx |

#### T5: 레이아웃 통합
- [ ] [frontend] `frontend/src/components/layout/Sidebar.tsx` — NotificationBell 통합 (헤더 영역)

| 태스크 | 설명 | 파일 |
|--------|------|------|
| T5-1 | Sidebar/헤더에 NotificationBell 통합 | frontend/src/components/layout/Sidebar.tsx |

---

### Phase 4: 검증
- [ ] [shared] 백엔드 기존 테스트 회귀 확인
- [ ] [shared] 프론트엔드 빌드 검증
- [ ] [shared] quality-gate 검증

---

## 태스크 의존성

```
T1 (타입/API) → T2 (스토어) → T3 (컴포넌트) → T4 (페이지)
T3-1 (NotificationBell) → T5 (레이아웃 통합)
Phase 3 → Phase 4
```

## 병렬 실행 판단

- Agent Team 권장: No (프론트엔드만, 단일 에이전트 순차 진행)
