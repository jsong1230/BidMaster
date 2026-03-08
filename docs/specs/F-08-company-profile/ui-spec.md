# F-08 회사 프로필 관리 — UI 설계서

## 화면 목록

| 화면명 | 경로 | 설명 |
|--------|------|------|
| 회사 프로필 관리 | `/settings/company` | 탭 기반 단일 페이지. 기본 정보 / 수행 실적 / 보유 인증 / 멤버 관리 탭 포함 |

---

## 디자인 방향

- **톤앤매너**: 전문적이고 절제된 B2B 설정 화면. Notion의 클린한 정보 구조 + Linear의 효율적 레이아웃 참조
- **색상**: primary-600 (`#486581`) 지배색 + secondary-500 (`#0F9D58`) 포인트 (완료/성공 상태) + neutral 배경
- **타이포그래피**: `Noto Sans KR` 단일 패밀리. 탭 레이블 weight-600, 카드 제목 weight-700, 본문 weight-400
- **레이아웃 패턴**: shell.html 글로벌 셸(사이드바 + 헤더) 위에 탭 기반 단일 페이지. 콘텐츠 영역 최대 너비 960px
- **반응형**: 모바일(375px) 탭 가로 스크롤 + 카드 1열 / 태블릿(768px) 2열 / 데스크톱(1024px+) 콘텐츠 너비 제한 + 슬라이드오버 패널

---

## 컴포넌트 계층

- `/settings/company` 페이지
  - `SettingsLayout` (사이드바 + 메인 영역)
    - `Breadcrumb` (대시보드 > 설정 > 회사 프로필)
    - `PageHeader` (페이지 제목 + 설명 텍스트)
    - `TabNavigation` (기본 정보 | 수행 실적 | 보유 인증 | 멤버 관리)
      - **[기본 정보 탭]** `CompanyBasicInfoTab`
        - `EmptyRegistrationState` (미등록 시)
          - `CompanyRegistrationForm`
            - `BusinessNumberInput` (하이픈 자동 포맷)
            - `TextInput` (회사명, 대표자명, 주소, 전화번호)
            - `IndustrySelect` (업종 드롭다운)
            - `ScaleRadioGroup` (소기업/중기업/대기업)
            - `Textarea` (회사 소개)
            - `FormActionButtons` (등록 / 취소)
        - `RegisteredCompanyView` (등록 후)
          - `CompanyInfoCard`
            - `InfoFieldGroup` (필드명 + 값)
            - `EditButton`
          - `CompanyEditForm` (수정 모드, inline)
      - **[수행 실적 탭]** `PerformanceTab`
        - `TabToolbar` (등록 버튼 + 정렬/필터 컨트롤)
        - `EmptyState` (실적 없을 때)
        - `PerformanceCardList`
          - `PerformanceCard`
            - `RepresentativeBadge` (대표 실적 배지)
            - `StatusBadge` (진행중/완료)
            - `ClientTypeBadge` (공공/민간)
            - `CardActionMenu` (수정 / 삭제 / 대표 지정)
        - `PerformanceSlideOver` (등록/수정 패널, 오른쪽 슬라이드)
          - `SlideOverHeader`
          - `PerformanceForm`
            - `TextInput` (프로젝트명, 발주처명)
            - `ClientTypeRadio` (공공/민간)
            - `AmountInput` (계약 금액, 천 단위 콤마)
            - `DateRangePicker` (시작일/종료일)
            - `StatusSelect` (진행중/완료)
            - `Textarea` (설명)
            - `RepresentativeToggle`
            - `DocumentUrlInput`
          - `SlideOverFooter` (저장 / 취소)
        - `DeleteConfirmModal`
      - **[보유 인증 탭]** `CertificationTab`
        - `TabToolbar` (등록 버튼)
        - `EmptyState` (인증 없을 때)
        - `CertificationTable`
          - `CertificationRow`
            - `ExpiryWarningBadge` (만료 임박 30일 경고)
            - `ExpiredBadge` (만료됨)
            - `RowActionButtons` (수정 / 삭제)
        - `CertificationModal` (등록/수정)
          - `ModalHeader`
          - `CertificationForm`
            - `TextInput` (인증명, 발급기관, 인증번호)
            - `DateInput` (발급일, 만료일)
            - `DocumentUrlInput`
          - `ModalFooter` (저장 / 취소)
        - `DeleteConfirmModal`
      - **[멤버 관리 탭]** `MemberTab` (owner만 완전 접근)
        - `TabToolbar` (팀원 초대 버튼, owner/admin만 노출)
        - `MemberTable`
          - `MemberRow`
            - `RoleBadge` (owner/admin/member)
            - `RoleChangeDropdown` (admin/member 변경, owner만 가능)
            - `RemoveMemberButton` (owner만 가능)
        - `InviteMemberModal`
          - `EmailInput`
          - `RoleSelect` (admin/member)
        - `RemoveMemberConfirmModal`
        - `PermissionNotice` (member 역할인 경우 읽기 전용 안내)

---

## 상태 명세

### 페이지 레벨 상태

| 컴포넌트 | 상태 | 타입 | 설명 |
|----------|------|------|------|
| `CompanyProfilePage` | `activeTab` | `'basic' \| 'performance' \| 'certification' \| 'member'` | 현재 활성 탭 |
| `CompanyProfilePage` | `company` | `Company \| null` | 회사 정보. null이면 미등록 상태 |
| `CompanyProfilePage` | `isLoading` | `boolean` | 회사 정보 초기 로딩 여부 |
| `CompanyProfilePage` | `currentUserRole` | `'owner' \| 'admin' \| 'member'` | 현재 사용자의 회사 내 역할 |

### 기본 정보 탭 상태

| 컴포넌트 | 상태 | 타입 | 설명 |
|----------|------|------|------|
| `CompanyBasicInfoTab` | `isEditMode` | `boolean` | 수정 폼 표시 여부 |
| `CompanyBasicInfoTab` | `isSaving` | `boolean` | 저장 API 호출 중 여부 |
| `CompanyRegistrationForm` | `businessNumber` | `string` | 사업자등록번호 원시값 (10자리 숫자) |
| `CompanyRegistrationForm` | `formErrors` | `Record<string, string>` | 필드별 유효성 에러 메시지 |

### 수행 실적 탭 상태

| 컴포넌트 | 상태 | 타입 | 설명 |
|----------|------|------|------|
| `PerformanceTab` | `performances` | `Performance[]` | 수행 실적 목록 |
| `PerformanceTab` | `isLoading` | `boolean` | 목록 로딩 중 |
| `PerformanceTab` | `isSlideOverOpen` | `boolean` | 슬라이드오버 패널 표시 여부 |
| `PerformanceTab` | `editingPerformance` | `Performance \| null` | 수정 중인 실적. null이면 신규 등록 |
| `PerformanceTab` | `deletingPerformanceId` | `string \| null` | 삭제 확인 중인 실적 ID |
| `PerformanceTab` | `representativeCount` | `number` | 현재 대표 실적 수 (최대 5개 제한 표시용) |
| `PerformanceTab` | `filterStatus` | `'all' \| 'completed' \| 'ongoing'` | 상태 필터 |

### 보유 인증 탭 상태

| 컴포넌트 | 상태 | 타입 | 설명 |
|----------|------|------|------|
| `CertificationTab` | `certifications` | `Certification[]` | 인증 목록 |
| `CertificationTab` | `isLoading` | `boolean` | 목록 로딩 중 |
| `CertificationTab` | `isModalOpen` | `boolean` | 등록/수정 모달 표시 여부 |
| `CertificationTab` | `editingCert` | `Certification \| null` | 수정 중인 인증. null이면 신규 등록 |
| `CertificationTab` | `deletingCertId` | `string \| null` | 삭제 확인 중인 인증 ID |
| `CertificationRow` | `isExpiringSoon` | `boolean` | 만료 임박 여부 (30일 이내) |
| `CertificationRow` | `isExpired` | `boolean` | 만료 여부 |

### 멤버 관리 탭 상태

| 컴포넌트 | 상태 | 타입 | 설명 |
|----------|------|------|------|
| `MemberTab` | `members` | `Member[]` | 멤버 목록 |
| `MemberTab` | `isLoading` | `boolean` | 목록 로딩 중 |
| `MemberTab` | `isInviteModalOpen` | `boolean` | 초대 모달 표시 여부 |
| `MemberTab` | `removingMemberId` | `string \| null` | 제거 확인 중인 멤버 ID |
| `MemberTab` | `isInviting` | `boolean` | 초대 API 호출 중 |

---

## 인터랙션 명세

### 탭 전환

- 탭 클릭 → 해당 탭 콘텐츠 표시, URL hash 업데이트 (`#basic`, `#performance`, `#certification`, `#member`)
- 페이지 진입 시 URL hash가 있으면 해당 탭 활성화, 없으면 기본 탭(`#basic`) 활성화

### 기본 정보 — 회사 등록 흐름

- 페이지 진입 → `GET /api/v1/companies/my` 호출 → 404 응답이면 등록 폼 표시
- 사업자등록번호 입력 → 숫자 이외 입력 무시, 10자리 입력 시 `000-00-00000` 형식으로 디스플레이 (저장값은 숫자만)
- `등록` 버튼 클릭 → 필드 유효성 검사 → `POST /api/v1/companies` → 성공 시 등록된 정보 카드 뷰로 전환 + 성공 toast
- 필드 에러: 에러 메시지는 해당 입력 필드 아래에 `text-error-500` `text-sm`으로 표시

### 기본 정보 — 수정 흐름

- `수정` 버튼 클릭 → inline 수정 폼으로 전환 (카드 뷰 → 폼 전환, 페이지 이동 없음)
- 사업자등록번호 필드는 수정 모드에서 비활성화(disabled) 표시, 안내 텍스트 포함
- `저장` 클릭 → `PUT /api/v1/companies/{id}` → 성공 시 카드 뷰로 복귀 + 성공 toast
- `취소` 클릭 → 변경 내용 폐기, 카드 뷰로 복귀

### 수행 실적 — 등록/수정 슬라이드오버

- `실적 등록` 버튼 클릭 → 오른쪽에서 슬라이드오버 패널 진입 (transform translateX, 300ms ease)
- 수정 아이콘 클릭 → 해당 실적 데이터 폼에 채워진 상태로 슬라이드오버 진입
- `저장` 클릭 → 유효성 검사 → API 호출 → 성공 시 목록 갱신 + 패널 닫힘 + 성공 toast
- 대표 실적 토글 ON → 현재 대표 실적 수가 5개이면 토글 비활성화 + 경고 메시지 표시
- 패널 외부(오버레이) 클릭 또는 ESC → 패널 닫힘 (변경 내용이 있으면 "취소할까요?" 확인)
- 계약 금액 입력 → blur 시 천 단위 콤마 포맷 적용 (예: `500,000,000`)

### 수행 실적 — 대표 실적 지정/해제

- 카드 액션 메뉴 → `대표 실적 지정` / `대표 실적 해제` → `PATCH /api/v1/companies/{id}/performances/{perfId}/representative`
- 지정 성공 시 카드에 별 아이콘 + `대표 실적` 배지 즉시 반영 (낙관적 업데이트)
- 5개 초과 시 error toast 표시: "대표 실적은 최대 5개까지 지정할 수 있습니다."

### 수행 실적 — 삭제

- 카드 액션 메뉴 → `삭제` → 확인 모달 표시 ("이 실적을 삭제하면 복구할 수 없습니다. 삭제할까요?")
- 확인 클릭 → `DELETE` 호출 → 목록에서 제거 + 성공 toast

### 보유 인증 — 등록/수정 모달

- `인증 등록` 버튼 클릭 → 모달 표시
- 수정 버튼 클릭 → 해당 인증 데이터 채워진 모달 표시
- `저장` 클릭 → API 호출 → 성공 시 모달 닫힘 + 테이블 갱신 + 성공 toast
- 만료일이 발급일보다 이전이면 만료일 필드에 실시간 에러 표시
- ESC 또는 오버레이 클릭 → 모달 닫힘

### 보유 인증 — 만료 상태 표시

- 현재일 기준 만료일이 30일 이내 → `만료 임박` warning 배지 표시
- 현재일 기준 만료일이 지남 → `만료됨` error 배지 표시
- 만료일 없음 → 배지 미표시

### 멤버 관리 — 초대

- `팀원 초대` 버튼 클릭 → 이메일 + 역할 입력 모달
- `초대` 클릭 → `POST /api/v1/companies/{id}/members` → 성공 시 모달 닫힘 + 멤버 목록 갱신 + 성공 toast
- 이미 소속된 멤버 이메일 입력 시 → COMPANY_009 에러 → "이미 해당 회사의 멤버입니다." 인라인 에러

### 멤버 관리 — 제거

- 제거 버튼 클릭 → 확인 모달 ("멤버를 제거하면 해당 사용자는 더 이상 회사 리소스에 접근할 수 없습니다.")
- owner는 제거 불가 (버튼 비활성화)
- 본인(current user) 제거 불가 (버튼 비활성화)

### Toast 알림

- 성공: 좌하단 `bg-success-50 border-success-500 text-success-700` 토스트, 2초 후 자동 소멸
- 에러: 좌하단 `bg-error-50 border-error-500 text-error-700` 토스트, 4초 유지 + 수동 닫기 가능

---

## 화면별 상태 시나리오

### 기본 정보 탭

| 시나리오 | UI 표현 |
|----------|---------|
| 로딩 중 | 카드 영역에 스켈레톤 UI (3개 행, `animate-pulse` bg-neutral-200) |
| 미등록 상태 | "회사 정보를 아직 등록하지 않았습니다" 안내 + 등록 폼 표시 |
| 등록 완료 | 정보 카드 뷰 (라벨-값 쌍) + 우측 상단 `수정` 버튼 |
| 수정 모드 | 카드 뷰 → 폼 전환, 사업자등록번호 disabled 표시 |
| 저장 중 | `저장` 버튼 disabled + 스피너 아이콘 |
| 저장 성공 | 수정 모드 종료, 성공 toast |
| API 에러 | 폼 상단에 error 배너 표시 |

### 수행 실적 탭

| 시나리오 | UI 표현 |
|----------|---------|
| 로딩 중 | 카드 3개 스켈레톤 (모바일 1열, 데스크톱 2열) |
| 빈 상태 | 중앙 정렬 안내 텍스트 + `실적 등록` CTA 버튼 |
| 목록 표시 | 카드형 리스트. 모바일 1열, 768px+ 2열 |
| 슬라이드오버 오픈 | 오른쪽에서 슬라이드인, 배경 dimmed 오버레이 |
| 저장 중 | 저장 버튼 disabled + 스피너 |
| 삭제 확인 | 확인 모달 표시 |

### 보유 인증 탭

| 시나리오 | UI 표현 |
|----------|---------|
| 로딩 중 | 테이블 행 5개 스켈레톤 |
| 빈 상태 | 중앙 정렬 안내 텍스트 + `인증 등록` CTA 버튼 |
| 목록 표시 | 테이블형. 모바일에서는 카드형으로 전환 |
| 만료 임박 | `만료 임박` warning 배지 + 행 배경 `bg-warning-50` |
| 만료됨 | `만료됨` error 배지 + 행 텍스트 `text-neutral-400` |
| 모달 오픈 | 중앙 모달, 최대 너비 560px |

### 멤버 관리 탭

| 시나리오 | UI 표현 |
|----------|---------|
| 로딩 중 | 테이블 행 3개 스켈레톤 |
| member 역할 접근 | 탭 접근 가능하나 초대/제거 버튼 미노출, 상단에 "목록 조회만 가능합니다" 안내 배너 |
| owner | 초대 버튼 + 모든 멤버 제거 버튼 활성화 (본인 제외) |
| admin | 초대 버튼 활성화, 제거 버튼은 owner 외 멤버에 대해서만 |
| 초대 모달 | 이메일 + 역할(admin/member) 선택 |
| 제거 확인 | 확인 모달, owner는 제거 불가 (버튼 자체 미노출) |

---

## 레이아웃 상세

### 페이지 구조 (데스크톱)

```
┌────────────────────────────────────────────────────────┐
│  헤더 (글로벌 셸)                                       │
├──────────┬─────────────────────────────────────────────┤
│          │  대시보드 > 설정 > 회사 프로필   (브레드크럼) │
│  사이드  │─────────────────────────────────────────────│
│  바      │  회사 프로필                  (페이지 제목)  │
│          │  회사 기본 정보, 수행 실적, 인증을 관리합니다 │
│  (글로벌 │─────────────────────────────────────────────│
│   셸)    │  [기본 정보] [수행 실적] [보유 인증] [멤버]  │
│          │─────────────────────────────────────────────│
│          │                                             │
│          │  탭 콘텐츠 영역 (max-width: 960px)          │
│          │                                             │
└──────────┴─────────────────────────────────────────────┘
```

### 기본 정보 카드 레이아웃 (등록 후)

```
┌──────────────────────────────────────────────────────┐
│  회사 기본 정보                         [수정 버튼]   │
├──────────────────────────────────────────────────────┤
│  사업자등록번호   123-45-67890                        │
│  회사명          주식회사 비드마스터                  │
│  대표자명        홍길동                               │
│  업종            소프트웨어 개발업                    │
│  규모            소기업                               │
│  주소            서울특별시 강남구 테헤란로 123        │
│  전화번호        02-1234-5678                         │
├──────────────────────────────────────────────────────┤
│  회사 소개                                            │
│  AI 기반 입찰 자동화 솔루션 기업입니다.               │
└──────────────────────────────────────────────────────┘
```

### 수행 실적 카드 (목록 아이템)

```
┌─────────────────────────────────────────────────────┐
│  ★ 대표 실적   ● 완료   공공                         │
│                                                     │
│  공공데이터 포털 고도화 사업                          │
│  행정안전부                                          │
│                                                     │
│  계약 금액   500,000,000원                           │
│  기간        2024-01-15 ~ 2024-12-31                │
│                                                [⋮]  │
└─────────────────────────────────────────────────────┘
```

### 수행 실적 슬라이드오버 (오른쪽)

```
      ┌──────────────────────────────────┐
      │  수행 실적 등록          [✕]     │
      ├──────────────────────────────────┤
      │  프로젝트명 *                    │
      │  [                            ]  │
      │                                  │
      │  발주처명 *                      │
      │  [                            ]  │
      │                                  │
      │  발주처 유형                     │
      │  ○ 공공기관   ○ 민간기업         │
      │                                  │
      │  계약 금액 *                     │
      │  [              ] 원             │
      │                                  │
      │  기간 *                          │
      │  [시작일    ] ~ [종료일    ]      │
      │                                  │
      │  상태 *                          │
      │  [진행중 ▾              ]        │
      │                                  │
      │  설명                            │
      │  [                            ]  │
      │  [                            ]  │
      │                                  │
      │  대표 실적 지정                  │
      │  [●──] ON                        │
      │  대표 실적은 제안서 생성 시       │
      │  우선 활용됩니다. (3/5)          │
      │                                  │
      │  첨부파일 URL                    │
      │  [                            ]  │
      ├──────────────────────────────────┤
      │  [취소]             [저장]       │
      └──────────────────────────────────┘
```

### 보유 인증 테이블 (데스크톱)

```
┌─────────────────────────────────────────────────────────────────────┐
│  인증명       발급기관      인증번호       발급일     만료일    액션  │
├─────────────────────────────────────────────────────────────────────┤
│  GS인증 1등급  한국정보통신  GS-2024-0123  2024-06-15  2027-06-14  [수정][삭제]  │
│  ISO 27001     BSI Group     IS-789012     2023-03-10  2026-03-09  [수정][삭제]  │
│  벤처기업인증  중소벤처기업부  V-2024-5678  2024-01-20  ⚠ 만료 임박 [수정][삭제]  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 반응형 설계

### 모바일 (375px)

- 탭: 가로 스크롤 가능한 탭 바 (`overflow-x: auto`, 스크롤바 숨김)
- 수행 실적: 카드 1열 full-width
- 보유 인증: 테이블 → 카드형 전환 (인증명 + 배지 위, 세부 정보 아래)
- 멤버 목록: 카드형 (이름+이메일+역할 배지, 액션 버튼)
- 슬라이드오버: 전체 화면 너비(100vw)로 표시
- 모달: 화면 하단에서 시트(sheet) 방식으로 표시

### 태블릿 (768px)

- 수행 실적: 카드 2열 그리드
- 보유 인증: 테이블 표시 (컬럼 일부 줄임)
- 슬라이드오버: 너비 480px 고정

### 데스크톱 (1024px+)

- 수행 실적: 카드 2열 (max-width 960px 내에서)
- 보유 인증: 테이블 전체 컬럼 표시
- 슬라이드오버: 너비 520px 고정
- 모달: 중앙 표시, max-width 560px

---

## 빈 상태(Empty State) 설계

### 수행 실적 빈 상태

```
        [아이콘: clipboard with pen, 64px, neutral-300]

        아직 등록된 수행 실적이 없습니다

        과거 사업 경험을 등록하면 제안서 생성 시
        자동으로 활용됩니다.

        [수행 실적 등록하기]   ← btn-primary
```

### 보유 인증 빈 상태

```
        [아이콘: award/badge, 64px, neutral-300]

        아직 등록된 보유 인증이 없습니다

        GS인증, ISO, 벤처기업인증 등 보유 인증을
        등록하면 제안서의 전문성이 강화됩니다.

        [인증 등록하기]   ← btn-primary
```

---

## 권한 기반 UI 분기

| 역할 | 기본 정보 | 수행 실적 등록 | 수행 실적 수정/삭제 | 대표 지정 | 인증 등록 | 인증 수정/삭제 | 멤버 초대 | 멤버 제거 |
|------|----------|--------------|-------------------|----------|----------|--------------|----------|----------|
| owner | 수정 가능 | O | O | O | O | O | O | O (본인 제외) |
| admin | 수정 가능 | O | O | O | O | O | O | owner 제외 |
| member | 조회만 | O (등록만) | X | X | O (등록만) | X | X | X |

- owner/admin의 수정/삭제 버튼: 기본 표시
- member의 수정/삭제 버튼: 미노출 (DOM에서 제거)
- 멤버 관리 탭: 역할에 따라 액션 버튼 가시성 제어

---

## 디자인 토큰

```css
/* design-system.md 토큰 기준 */

--color-primary: #486581;        /* btn-primary, 탭 active 밑줄, focus ring */
--color-primary-light: #F0F4F8;  /* 탭 hover 배경 */
--color-accent: #0F9D58;         /* 완료 상태 배지, 대표 실적 별 아이콘 */

--color-bg-page: #FAFAFA;        /* 페이지 배경 */
--color-bg-card: #FFFFFF;        /* 카드, 모달, 슬라이드오버 배경 */
--color-border: #E0E0E0;         /* 카드, 테이블, 입력 필드 테두리 */
--color-text-primary: #212121;   /* 주요 텍스트 */
--color-text-secondary: #757575; /* 보조 텍스트, 레이블 */
--color-text-caption: #9E9E9E;   /* 캡션, placeholder */

--font-sans: 'Noto Sans KR', 'Pretendard', -apple-system, sans-serif;

--radius-card: 8px;              /* 카드, 모달 모서리 */
--radius-input: 6px;             /* 입력 필드 모서리 */
--radius-badge: 9999px;          /* 배지 모서리 */

--shadow-card: 0 1px 3px rgba(0, 0, 0, 0.04);
--shadow-slideover: -4px 0 20px rgba(0, 0, 0, 0.1);
--shadow-modal: 0 20px 60px rgba(0, 0, 0, 0.15);

--transition-fast: 150ms ease;
--transition-panel: 300ms ease;  /* 슬라이드오버, 모달 진입 */
```

---

## 에러 처리 명세

| 에러 코드 | 표시 위치 | 표시 방법 |
|----------|---------|---------|
| COMPANY_002 (중복 사업자번호) | 사업자등록번호 입력 필드 하단 | 인라인 에러 텍스트 |
| COMPANY_003 (형식 검증 실패) | 사업자등록번호 입력 필드 하단 | 인라인 에러 텍스트 |
| COMPANY_004 (이미 회사 소속) | 폼 상단 | 에러 배너 |
| COMPANY_005 (대표 실적 초과) | 대표 실적 토글 하단 또는 error toast | 인라인 경고 또는 toast |
| COMPANY_008 (초대 대상 없음) | 이메일 입력 필드 하단 | 인라인 에러 텍스트 |
| COMPANY_009 (이미 멤버) | 이메일 입력 필드 하단 | 인라인 에러 텍스트 |
| COMPANY_010 (다른 회사 소속) | 이메일 입력 필드 하단 | 인라인 에러 텍스트 |
| PERMISSION_001 (권한 없음) | error toast | 4초 toast |
| VALIDATION_001 (유효성 실패) | 각 필드 하단 | 인라인 에러 텍스트 |
| 네트워크/서버 오류 | 해당 탭 영역 상단 | 에러 배너 + "다시 시도" 버튼 |

---

## 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-03-02 | F-08 UI 설계서 초안 작성 |
