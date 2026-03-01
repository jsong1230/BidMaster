# 디자인 시스템 (BidMaster)

## 1. 디자인 철학

### 비전
전문적이고 신뢰감 있는 B2B SaaS로서, 공공 입찰 제안서 작성의 복잡성을 최소화하고 사용자가 핵심 비즈니스에 집중할 수 있는 경험을 제공합니다.

### 핵심 원칙
- **전문성 (Professionalism)**: 공공 입찰 도메인의 정직함과 신뢰감 반영
- **효율성 (Efficiency)**: 복잡한 정보를 한눈에 파악 가능한 명료한 구조
- **정확성 (Precision)**: 낙찰 스코어링, 분석 결과 등 중요 데이터 명확히 전달
- **지속성 (Consistency)**: 전체 제품에서 일관된 패턴과 인터랙션 제공

---

## 2. 무드 & 톤

### 레퍼런스
- **Notion**: 클린한 정보 아키텍처, 명확한 데이터 표현
- **Linear**: 세련된 어두운 톤, 효율적인 레이아웃
- **Monday.com**: 대시보드 구성, 칸반 보드 UI
- **국세청/나라장터**: 공공 포털의 접근성, 신뢰감 있는 색상

### 전체 분위기
- **업무용 도구의 완성도**: 복잡한 기능을 직관적으로 제어
- **정보 밀도**: 화면 공간 효율적으로 활용, 스크롤 최소화
- **스토리텔링**: 데이터를 통해 입찰 전략과 결과 명확히 전달

---

## 3. UX 원칙

### 접근성 기준
- WCAG 2.1 AA 준수
- 텍스트 대비율 4.5:1 이상 (일반 텍스트), 3:1 이상 (큰 텍스트)
- 키보드 네비게이션 완벽 지원
- 포커스 표시 명확히 (2px 테두리)

### 인터랙션 패턴
- **호버**: 버튼, 링크, 데이터 카드에 미세한 배경 변화
- **피드백**: API 요청 시 로딩 스피너, 성공/실패 메시지 2초 표시
- **전환**: 페이지 이동 시 슬라이드/페이드 (200ms)
- **모달**: 오버레이 배경 dimmed, ESC 닫기 지원

### 피드백 방식
- **성공**: 녹색 체크 아이콘 + 텍스트 (상단 toast)
- **에러**: 빨간색 경고 아이콘 + 텍스트 + 해결 방법 제안
- **진행 중**: 스피너 + 진행률 퍼센트 (긴 작업 시)
- **정보**: 파란색 정보 아이콘 + 텍스트

---

## 4. 색상 팔레트

### Primary (지배색)
```css
--color-primary-50: #F0F4F8;
--color-primary-100: #D9E2EC;
--color-primary-200: #BCCCDC;
--color-primary-300: #9FB3C8;
--color-primary-400: #829AB1;
--color-primary-500: #627D98;  /* 메인 브랜드 색상: 신뢰감 있는 네이비 그레이 */
--color-primary-600: #486581;
--color-primary-700: #334E68;
--color-primary-800: #243B53;
--color-primary-900: #102A43;
```

### Secondary (보조색)
```css
--color-secondary-50: #E3F9E9;
--color-secondary-100: #C3F0D1;
--color-secondary-200: #94E7AC;
--color-secondary-300: #5ADB82;
--color-secondary-400: #34CB62;
--color-secondary-500: #0F9D58;  /* 포인트 색상: 낙찰, 성공, 완료 */
--color-secondary-600: #0B8047;
--color-secondary-700: #076136;
--color-secondary-800: #044224;
--color-secondary-900: #02210F;
```

### Neutral (중성색)
```css
--color-neutral-50: #FAFAFA;    /* 배경 */
--color-neutral-100: #F5F5F5;   /* 카드 배경 */
--color-neutral-200: #E0E0E0;   /* 구분선 */
--color-neutral-300: #BDBDBD;   /* 비활성 상태 */
--color-neutral-400: #9E9E9E;   /* 캡션, 보조 텍스트 */
--color-neutral-500: #757575;   /* 일반 텍스트 */
--color-neutral-600: #616161;   /* 제목 텍스트 */
--color-neutral-700: #424242;   /* 강조 텍스트 */
--color-neutral-800: #212121;   /* 기본 텍스트 */
--color-neutral-900: #000000;   /* 순수 검정 */
```

### Semantic (의미 색상)
```css
/* 성공/낙찰 */
--color-success-50: #E8F5E9;
--color-success-100: #C8E6C9;
--color-success-500: #4CAF50;
--color-success-700: #2E7D32;

/* 경고/주의 */
--color-warning-50: #FFF8E1;
--color-warning-100: #FFECB3;
--color-warning-500: #FFC107;
--color-warning-700: #F57C00;

/* 에러/거절 */
--color-error-50: #FFEBEE;
--color-error-100: #FFCDD2;
--color-error-500: #F44336;
--color-error-700: #C62828;

/* 정보/진행 */
--color-info-50: #E3F2FD;
--color-info-100: #BBDEFB;
--color-info-500: #2196F3;
--color-info-700: #1565C0;
```

### 스코어링 색상 (특수용도)
낙찰 가능성, 적합도 점수를 시각적으로 표현

| 점수 범위 | 색상 | 의미 | 색상 코드 |
|----------|------|------|----------|
| 80~100 | Success | 매우 높음 (참여 추천) | `--color-success-500` |
| 60~79 | Secondary | 높음 | `--color-secondary-500` |
| 40~59 | Warning | 중간 (고민 필요) | `--color-warning-500` |
| 0~39 | Error | 낮음 (비추천) | `--color-error-500` |

### 다크모드 지원
기본적으로 라이트 모드만 지원. B2B 도구로서 정확한 색상 표현이 중요하여 다크모드는 요청 시 추가 개발.

---

## 5. 타이포그래피

### 폰트
```css
--font-display: 'Noto Sans KR', 'Pretendard', -apple-system, sans-serif;
--font-body: 'Noto Sans KR', 'Pretendard', -apple-system, sans-serif;
--font-mono: 'Fira Code', 'D2Coding', monospace;
```

### 타이포그래피 스케일
| 용도 | 크기 | Weight | Line-height | Letter-spacing |
|------|------|--------|-------------|----------------|
| Hero / 대제목 | 2.5rem (40px) | 700 | 1.2 | -0.02em |
| 페이지 제목 | 2rem (32px) | 700 | 1.3 | -0.01em |
| 섹션 제목 | 1.5rem (24px) | 700 | 1.3 | -0.01em |
| 소제목 | 1.25rem (20px) | 600 | 1.4 | normal |
| 본문 | 1rem (16px) | 400 | 1.6 | normal |
| 작은 본문 | 0.875rem (14px) | 400 | 1.6 | normal |
| 캡션 | 0.75rem (12px) | 400 | 1.5 | 0.01em |
| 코드/데이터 | 0.875rem (14px) | 500 | 1.4 | normal |

---

## 6. 스페이싱 시스템

```css
--space-1: 0.25rem (4px);
--space-2: 0.5rem (8px);
--space-3: 0.75rem (12px);
--space-4: 1rem (16px);      /* 기본 간격 */
--space-5: 1.25rem (20px);
--space-6: 1.5rem (24px);    /* 섹션 간격 */
--space-8: 2rem (32px);      /* 블록 간격 */
--space-10: 2.5rem (40px);
--space-12: 3rem (48px);     /* 대 섹션 간격 */
--space-16: 4rem (64px);
--space-20: 5rem (80px);
--space-24: 6rem (96px);
```

---

## 7. 컴포넌트 기본 스타일

### Button
```css
/* Primary */
.btn-primary {
  background: var(--color-primary-600);
  color: white;
  padding: var(--space-3) var(--space-6);
  border-radius: 6px;
  font-weight: 600;
  transition: all 150ms ease;
}

.btn-primary:hover {
  background: var(--color-primary-700);
}

/* Secondary */
.btn-secondary {
  background: white;
  color: var(--color-primary-600);
  border: 1px solid var(--color-primary-200);
  padding: var(--space-3) var(--space-6);
  border-radius: 6px;
  font-weight: 600;
}

/* Ghost */
.btn-ghost {
  background: transparent;
  color: var(--color-neutral-700);
  padding: var(--space-3) var(--space-6);
  border-radius: 6px;
}

.btn-ghost:hover {
  background: var(--color-neutral-100);
}
```

### Input
```css
.input {
  background: white;
  border: 1px solid var(--color-neutral-200);
  border-radius: 6px;
  padding: var(--space-3) var(--space-4);
  font-size: 1rem;
  color: var(--color-neutral-800);
  transition: border-color 150ms ease;
}

.input:focus {
  outline: none;
  border-color: var(--color-primary-500);
  box-shadow: 0 0 0 3px rgba(98, 125, 152, 0.1);
}

.input::placeholder {
  color: var(--color-neutral-400);
}
```

### Card
```css
.card {
  background: white;
  border: 1px solid var(--color-neutral-200);
  border-radius: 8px;
  padding: var(--space-6);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.card-hoverable:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border-color: var(--color-primary-300);
}
```

### Badge
```css
.badge {
  display: inline-flex;
  align-items: center;
  padding: var(--space-1) var(--space-3);
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
}

.badge-success {
  background: var(--color-success-50);
  color: var(--color-success-700);
}

.badge-warning {
  background: var(--color-warning-50);
  color: var(--color-warning-700);
}

.badge-error {
  background: var(--color-error-50);
  color: var(--color-error-700);
}

.badge-info {
  background: var(--color-info-50);
  color: var(--color-info-700);
}
```

### Modal
```css
.modal-overlay {
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(2px);
}

.modal-content {
  background: white;
  border-radius: 12px;
  max-width: 560px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.modal-header {
  padding: var(--space-6);
  border-bottom: 1px solid var(--color-neutral-200);
}

.modal-body {
  padding: var(--space-6);
}

.modal-footer {
  padding: var(--space-6);
  border-top: 1px solid var(--color-neutral-200);
}
```

---

## 8. 레이아웃 그리드 시스템

### 컨테이너
```css
.container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 var(--space-6);
}
```

### 그리드 (Tailwind 기준)
- 12열 그리드 시스템
- 간격(gap): var(--space-6)
- 모바일: 1열 (375px)
- 태블릿: 2열 (768px)
- 데스크톱: 3-4열 (1024px+)

---

## 9. 아이콘

### 라이브러리
- **Lucide Icons**: 깔끔한 윤곽선 스타일, 일관된 굵기
- **Heroicons**: 대체 옵션
- SVG 직접 사용 가능 (추천 시 최적화)

### 사용 원칙
- 사이즈: 16px (작은), 20px (기본), 24px (큰)
- 색상: 상황에 맞는 의미 색상 (success, warning, error, info)
- 라인 굵기: 2px 일관 유지

---

## 10. 다크모드 지원 (향후 확장 예정)

**현재 미지원**: B2B 도구로서 라이트 모드 우선
향후 요청 시 구현 계획 있음. 구현 시 주의사항:
- 대비율 7:1 이상 유지
- 데이터 시각화 색상 재정의
- 그림자 대신 명도차 사용

### 다크모드 색상 매핑 (예정)

| 토큰 | 라이트 | 다크 |
|------|--------|------|
| 배경 | `#FFFFFF` | `#0F172A` |
| 카드 배경 | `#FFFFFF` | `#1E293B` |
| 텍스트 | `#212121` | `#F9FAFB` |
| 보조 텍스트 | `#757575` | `#9CA3AF` |
| 구분선 | `#E0E0E0` | `#334E68` |

---

## 11. Tailwind 설정 (tailwind.config.js)

```javascript
module.exports = {
  content: [
    './frontend/src/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Primary
        primary: {
          50: '#F0F4F8',
          100: '#D9E2EC',
          200: '#BCCCDC',
          300: '#9FB3C8',
          400: '#829AB1',
          500: '#627D98',  // 메인 브랜드 색상
          600: '#486581',
          700: '#334E68',
          800: '#243B53',
          900: '#102A43',
        },
        // Secondary
        secondary: {
          50: '#E3F9E9',
          100: '#C3F0D1',
          200: '#94E7AC',
          300: '#5ADB82',
          400: '#34CB62',
          500: '#0F9D58',  // 포인트 색상: 낙찰, 성공, 완료
          600: '#0B8047',
          700: '#076136',
          800: '#044224',
          900: '#02210F',
        },
        // Neutral
        neutral: {
          50: '#FAFAFA',
          100: '#F5F5F5',
          200: '#E0E0E0',
          300: '#BDBDBD',
          400: '#9E9E9E',
          500: '#757575',
          600: '#616161',
          700: '#424242',
          800: '#212121',
          900: '#000000',
        },
        // Semantic
        success: {
          50: '#E8F5E9',
          100: '#C8E6C9',
          500: '#4CAF50',
          700: '#2E7D32',
        },
        warning: {
          50: '#FFF8E1',
          100: '#FFECB3',
          500: '#FFC107',
          700: '#F57C00',
        },
        error: {
          50: '#FFEBEE',
          100: '#FFCDD2',
          500: '#F44336',
          700: '#C62828',
        },
        info: {
          50: '#E3F2FD',
          100: '#BBDEFB',
          500: '#2196F3',
          700: '#1565C0',
        },
      },
      fontFamily: {
        sans: ['"Noto Sans KR"', '"Pretendard"', '-apple-system', 'sans-serif'],
        mono: ['"Fira Code"', '"D2Coding"', 'monospace'],
      },
      fontSize: {
        '40': ['2.5rem', { lineHeight: '1.2', letterSpacing: '-0.02em' }],
        '32': ['2rem', { lineHeight: '1.3', letterSpacing: '-0.01em' }],
        '24': ['1.5rem', { lineHeight: '1.3', letterSpacing: '-0.01em' }],
        '20': ['1.25rem', { lineHeight: '1.4' }],
        '16': ['1rem', { lineHeight: '1.6' }],
        '14': ['0.875rem', { lineHeight: '1.6' }],
        '12': ['0.75rem', { lineHeight: '1.5', letterSpacing: '0.01em' }],
      },
      spacing: {
        '1': '0.25rem',   // 4px
        '2': '0.5rem',    // 8px
        '3': '0.75rem',   // 12px
        '4': '1rem',      // 16px
        '5': '1.25rem',   // 20px
        '6': '1.5rem',    // 24px
        '8': '2rem',      // 32px
        '10': '2.5rem',   // 40px
        '12': '3rem',     // 48px
        '16': '4rem',     // 64px
        '20': '5rem',     // 80px
        '24': '6rem',     // 96px
      },
      borderRadius: {
        'DEFAULT': '6px',
        'lg': '8px',
        'xl': '12px',
      },
      boxShadow: {
        sm: '0 1px 3px rgba(0, 0, 0, 0.04)',
        md: '0 4px 12px rgba(0, 0, 0, 0.08)',
        lg: '0 20px 60px rgba(0, 0, 0, 0.15)',
      },
      transitionDuration: {
        '150': '150ms',
        '200': '200ms',
        '300': '300ms',
      },
    },
  },
  plugins: [],
};
```

---

## 12. Google Fonts Import

```html
<!-- Noto Sans KR (한국어) -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&display=swap" rel="stylesheet">

<!-- Pretendard (대체 한국어 폰트) -->
<link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css" rel="stylesheet">

<!-- Fira Code (코드 폰트) -->
<link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
```

---

## 13. 디자인 검증 체크리스트

### 접근성 (Accessibility)
- [ ] 텍스트 대비율 WCAG 2.1 AA 준수 (4.5:1 이상)
- [ ] 큰 텍스트(18px+) 대비율 3:1 이상
- [ ] 대화형 요소 최소 44px (터치 타겟)
- [ ] 포커스 표시 명확 (2px 테두리)
- [ ] 키보드 네비게이션 완벽 지원

### 일관성 (Consistency)
- [ ] 색상 토큰 일관성 유지
- [ ] 폰트 크기/웨이트 스케일 준수
- [ ] 스페이싱 시스템 준수
- [ ] 컴포넌트 스타일 일관성

### 반응형 (Responsive)
- [ ] 모바일(375px) 레이아웃 확인
- [ ] 태블릿(768px) 레이아웃 확인
- [ ] 데스크탑(1024px) 레이아웃 확인
- [ ] 와이드(1280px+) 레이아웃 확인

### 사용성 (Usability)
- [ ] 호버 피드백 명확
- [ ] 로딩 상태 표시
- [ ] 에러 메시지 명확하고 해결 방법 제공
- [ ] 성공 피드백 표시 (2초 내 자동 사라짐)

---

## 14. 컴포넌트 사용 예시

### 스코어링 컴포넌트

```tsx
// 스코어에 따른 색상 결정
const getScoreColor = (score: number): string => {
  if (score >= 80) return 'bg-success-500 text-white';
  if (score >= 60) return 'bg-secondary-500 text-white';
  if (score >= 40) return 'bg-warning-500 text-white';
  return 'bg-error-500 text-white';
};

// 스코어 배지
<Badge variant={getScoreColor(score)}>{score}점</Badge>
```

### 진행률 표시

```tsx
// 제안서 생성 진행률
<ProgressBar value={progress} color="primary" />
```

### 알림 카운트

```tsx
// 미읽음 알림 수
<NotificationBadge count={unreadCount} />
```

---

## 15. 버전 관리

| 버전 | 날짜 | 변경사항 | 작성자 |
|------|------|----------|--------|
| 1.0.0 | 2026-03-01 | 초기 디자인 시스템 정립 | ui-designer |
| 1.1.0 | 2026-03-01 | 스코어링 색상, Tailwind 설정 추가 | ui-designer |

