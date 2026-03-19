# NotificationBell

헤더 영역에 표시되는 알림 벨 컴포넌트입니다.

## 위치

`frontend/src/components/layout/NotificationBell.tsx`

## 기능

- 안읽은 알림 수 뱃지 표시 (빨간 원형, 99+ 처리)
- 클릭 시 드롭다운 — 최근 5개 알림 미리보기
- 드롭다운 내 "전체 읽음" 버튼
- "전체 알림 보기" 링크 → `/notifications`
- 외부 클릭, ESC 키로 드롭다운 닫기
- 컴포넌트 마운트 시 30초 폴링 자동 시작 (언마운트 시 정지)

## 사용 위치

`Sidebar.tsx` 로고 영역 우측

```tsx
import { NotificationBell } from './NotificationBell';

// Sidebar 헤더 영역
<div className="h-16 flex items-center justify-between px-6 border-b border-neutral-200">
  <Link href="/dashboard">BidMaster</Link>
  <NotificationBell />
</div>
```

## 상태

`useNotificationStore`에서 다음 상태를 구독합니다:
- `unreadCount` — 뱃지 숫자
- `notifications` — 드롭다운 목록 (최근 5개)
- `isLoading` — 스켈레톤 표시

## 접근성

- `role="button"`, `aria-label`으로 안읽은 수 알림
- 키보드: ESC 드롭다운 닫기
- 포커스 링: `focus:ring-2 focus:ring-[#486581]`
