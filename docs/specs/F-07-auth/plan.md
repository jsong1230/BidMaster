# F-07 사용자 인증 및 계정 관리 — 구현 계획

## 참조
- 설계서: docs/specs/F-07-auth/design.md
- 테스트 명세: docs/specs/F-07-auth/test-spec.md
- ERD: docs/system/erd.md
- API 컨벤션: docs/system/api-conventions.md

---

## 태스크 목록

### [BE] 백엔드 태스크

#### T1: DB 모델 및 마이그레이션
- [ ] T1.1: User 모델 정의 (backend/src/models/user.py)
  - 컬럼: id, email, password_hash, name, phone, kakao_id, company_id, role, preferences, last_login_at, created_at, updated_at, deleted_at
  - Soft Delete 지원 (deleted_at)
  - 인덱스: email (partial), kakao_id (partial)
- [ ] T1.2: RefreshToken 모델 정의 (backend/src/models/refresh_token.py)
  - 컬럼: id, user_id, token_hash, device_info, ip_address, expires_at, is_revoked, created_at
  - 인덱스: user_id (partial), expires_at
- [ ] T1.3: PasswordResetToken 모델 정의 (backend/src/models/password_reset_token.py)
  - 컬럼: id, user_id, token_hash, expires_at, used_at, created_at
  - 1시간 만료 정책
- [ ] T1.4: OAuthState 모델 정의 (backend/src/models/oauth_state.py)
  - 컬럼: id, state, provider, redirect_url, expires_at, created_at
  - 10분 만료 정책 (CSRF 방지)
- [ ] T1.5: Alembic 마이그레이션 생성
  - 001_create_auth_tables.py

#### T2: 스키마 정의
- [ ] T2.1: 인증 요청/응답 스키마 (backend/src/schemas/auth.py)
  - RegisterRequest, RegisterResponse
  - LoginRequest, LoginResponse
  - TokenRefreshRequest, TokenRefreshResponse
  - ChangePasswordRequest
  - ForgotPasswordRequest, ResetPasswordRequest
  - OAuthCallbackResponse
  - LogoutRequest
- [ ] T2.2: 사용자 스키마 (backend/src/schemas/user.py)
  - UserResponse, UserUpdateRequest
  - UserPreferences

#### T3: 서비스 레이어
- [ ] T3.1: TokenService (backend/src/services/token_service.py)
  - create_access_token(user_id, email, role, company_id) → 1시간 만료
  - create_refresh_token(user_id) → 30일 만료
  - decode_token(token) → payload or raise
  - hash_token(token) → SHA-256
  - revoke_refresh_token(token_hash)
  - is_token_blacklisted(jti) → Redis 확인
  - add_to_blacklist(jti, ttl)
- [ ] T3.2: AuthService (backend/src/services/auth_service.py)
  - register(email, password, name, phone) → user, tokens
  - login(email, password, device_info, ip) → user, tokens
  - logout(refresh_token, access_token_jti)
  - refresh_token(refresh_token) → new tokens
  - get_current_user(user_id) → user
  - update_user(user_id, data) → user
  - change_password(user_id, current_password, new_password)
  - delete_account(user_id, password, reason)
  - forgot_password(email) → 토큰 생성 + 이메일 발송
  - reset_password(token, new_password)
- [ ] T3.3: OAuthService (backend/src/services/oauth_service.py)
  - get_oauth_url(redirect_url) → kakao_url, state
  - handle_callback(code, state) → user, tokens, is_new_user
  - exchange_code_for_token(code) → kakao_access_token
  - get_kakao_user_info(access_token) → kakao_id, email, name

#### T4: API 엔드포인트
- [ ] T4.1: POST /api/v1/auth/register
  - 201 Created: user + tokens
  - 409: AUTH_007 (이미 가입된 이메일)
  - 400: VALIDATION_001 (입력값 유효성 실패)
- [ ] T4.2: POST /api/v1/auth/login
  - 200 OK: user + tokens
  - 401: AUTH_001 (이메일/비밀번호 불일치)
  - 403: AUTH_010 (탈퇴한 계정)
- [ ] T4.3: POST /api/v1/auth/refresh
  - 200 OK: new tokens
  - 401: AUTH_005 (로그아웃된 토큰), AUTH_006 (유효하지 않은 토큰)
- [ ] T4.4: POST /api/v1/auth/logout
  - 200 OK: success
  - 멱등성 보장 (이미 로그아웃된 토큰도 성공)
- [ ] T4.5: GET /api/v1/auth/oauth/kakao
  - 302 Redirect to Kakao OAuth
  - state 생성 및 저장
- [ ] T4.6: GET /api/v1/auth/oauth/kakao/callback
  - 200 OK: user + tokens + isNewUser
  - 400: AUTH_011 (State 검증 실패)
  - 401: AUTH_009 (카카오 OAuth 인증 실패)
- [ ] T4.7: GET /api/v1/auth/me
  - 200 OK: user + preferences
  - 401: AUTH_002/003/004/005
- [ ] T4.8: PATCH /api/v1/auth/me
  - 200 OK: updated user
- [ ] T4.9: POST /api/v1/auth/change-password
  - 200 OK: success
  - 401: AUTH_001 (현재 비밀번호 불일치)
  - 400: AUTH_008 (이전 비밀번호 재사용)
- [ ] T4.10: POST /api/v1/auth/forgot-password
  - 200 OK: message (존재하지 않는 이메일도 동일 응답)
- [ ] T4.11: POST /api/v1/auth/reset-password
  - 200 OK: success
  - 400: AUTH_012 (만료된 토큰), AUTH_013 (이미 사용된 토큰)
- [ ] T4.12: DELETE /api/v1/auth/me
  - 200 OK: success (soft delete)
  - 401: AUTH_001 (비밀번호 불일치)

#### T5: 인증 의존성 및 미들웨어
- [ ] T5.1: get_current_user 의존성 (backend/src/api/deps.py)
  - Authorization 헤더 파싱
  - 토큰 검증 (만료, 블랙리스트)
  - 사용자 조회
- [ ] T5.2: Rate Limiting 미들웨어
  - /auth/login: 10회/1분
  - /auth/register: 5회/1시간
  - /auth/forgot-password: 3회/1시간
  - /auth/refresh: 30회/1분

#### T6: 보안 유틸리티
- [ ] T6.1: 비밀번호 검증 (backend/src/core/security.py)
  - get_password_hash(password) → bcrypt ($2b$12$)
  - verify_password(plain, hashed) → bool
  - validate_password_strength(password) → bool
    - 최소 8자, 최대 64자
    - 영문 대소문자, 숫자, 특수문자 중 3가지 이상
- [ ] T6.2: JWT 유틸리티 확장
  - create_access_token() → HS256 서명
  - create_refresh_token() → 30일 만료
  - decode_token() → 만료/변조 검증

---

### [FE] 프론트엔드 태스크

#### T7: 인증 상태 관리
- [ ] T7.1: AuthContext 및 Provider 생성 (frontend/src/lib/auth-context.tsx)
  - AuthState: user, isLoading, isAuthenticated
  - AuthActions: login, loginWithKakao, logout, refreshTokens, updateProfile
- [ ] T7.2: use-auth 훅 구현 (frontend/src/hooks/use-auth.ts)
  - 컨텍스트 래퍼
  - 편의 메서드
- [ ] T7.3: auth-api 클라이언트 구현 (frontend/src/lib/api/auth-api.ts)
  - register(data)
  - login(email, password)
  - logout()
  - refreshToken(refreshToken)
  - getMe()
  - updateMe(data)
  - changePassword(currentPassword, newPassword)
  - forgotPassword(email)
  - resetPassword(token, newPassword)
  - getKakaoLoginUrl()
  - handleKakaoCallback(code, state)
  - deleteAccount(password, reason)

#### T8: 인증 페이지
- [ ] T8.1: 로그인 페이지 (frontend/src/app/(auth)/login/page.tsx)
  - 이메일/비밀번호 입력 폼
  - 카카오 로그인 버튼
  - 비밀번호 찾기 링크
  - 회원가입 링크
  - 에러 메시지 표시
- [ ] T8.2: 회원가입 페이지 (frontend/src/app/(auth)/register/page.tsx)
  - 이메일, 비밀번호, 이름, 전화번호 입력
  - 비밀번호 강도 표시
  - 실시간 유효성 검사
- [ ] T8.3: 비밀번호 찾기 페이지 (frontend/src/app/(auth)/forgot-password/page.tsx)
  - 이메일 입력
  - 발송 완료 메시지
- [ ] T8.4: 비밀번호 재설정 페이지 (frontend/src/app/(auth)/reset-password/[token]/page.tsx)
  - 토큰 검증
  - 새 비밀번호 입력
  - 완료 후 로그인 페이지 리다이렉트

#### T9: 인증 가드
- [ ] T9.1: 미들웨어 구현 (frontend/src/middleware.ts)
  - protectedRoutes: /dashboard, /bids, /proposals, /settings, /teams
  - authRoutes: /login, /register, /forgot-password, /reset-password
  - 미인증 시: protectedRoutes → /login
  - 이미 인증 시: authRoutes → /dashboard
- [ ] T9.2: 토큰 자동 갱신 로직 (frontend/src/lib/api/client.ts)
  - 401 응답 시 refresh 요청
  - 원래 요청 재시도
  - 갱신 실패 시 로그아웃

#### T10: UI 컴포넌트
- [ ] T10.1: 공통 입력 필드 (frontend/src/components/auth/auth-input.tsx)
- [ ] T10.2: 비밀번호 입력 필드 (frontend/src/components/auth/password-input.tsx)
  - 표시/숨기기 토글
  - 강도 표시기
- [ ] T10.3: 소셜 로그인 버튼 (frontend/src/components/auth/social-login-button.tsx)
- [ ] T10.4: 인증 폼 레이아웃 (frontend/src/components/auth/auth-layout.tsx)

---

### [TEST] 테스트 태스크

#### T11: 백엔드 단위 테스트
- [ ] T11.1: 비밀번호 해싱 테스트 (tests/unit/test_security.py)
  - 해싱, 검증, 빈 비밀번호
- [ ] T11.2: JWT 토큰 테스트 (tests/unit/test_security.py)
  - 생성, 디코딩, 만료, 변조
- [ ] T11.3: AuthService 테스트 (tests/unit/test_auth_service.py)
  - 회원가입, 로그인, 로그아웃, 토큰 갱신
  - 중복 이메일, 잘못된 비밀번호
- [ ] T11.4: OAuthService 테스트 (tests/unit/test_oauth_service.py)
  - URL 생성, 콜백 처리, 신규/기존 사용자
- [ ] T11.5: 비밀번호 재설정 테스트 (tests/unit/test_password_reset.py)
  - 토큰 생성, 만료, 사용됨

#### T12: 백엔드 통합 테스트
- [ ] T12.1: 회원가입 → 로그인 → API 호출 플로우
- [ ] T12.2: 토큰 갱신 플로우
- [ ] T12.3: 카카오 OAuth 전체 플로우 (mock)
- [ ] T12.4: 비밀번호 재설정 플로우
- [ ] T12.5: 동시 세션 관리 테스트
- [ ] T12.6: Rate Limiting 테스트

#### T13: E2E 테스트 (Playwright)
- [ ] T13.1: 회원가입 → 로그인 → 로그아웃 플로우
- [ ] T13.2: 카카오 로그인 플로우
- [ ] T13.3: 비밀번호 찾기 → 재설정 플로우
- [ ] T13.4: 토큰 만료 → 자동 갱신 테스트
- [ ] T13.5: 인증 가드 테스트 (protected/auth routes)

---

## 병렬 실행 판단

### BE와 FE 병렬 실행
- BE와 FE는 API 계약이 정의되어 있어 병렬 실행 가능
- FE는 MSW(Mock Service Worker)로 API 모킹하여 개발 진행

### BE 내부 순서
1. T1 (DB 모델) → T2 (스키마) → T3 (서비스) → T4 (API) → T5 (의존성) → T6 (보안)
2. T6은 T3과 병렬 가능

### FE 내부 순서
1. T7 (상태 관리) → T8 (페이지) → T9 (가드) → T10 (UI 컴포넌트)
2. T10은 T8과 병렬 가능

### 테스트 순서
- T11, T12는 BE 완료 후 진행
- T13은 FE 완료 후 진행

---

## 의존성

### 외부 의존성
| 항목 | 설명 | 필수 여부 |
|------|------|-----------|
| 카카오 OAuth 앱 등록 | KAKAO_CLIENT_ID, KAKAO_CLIENT_SECRET | 필수 |
| Redis | 토큰 블랙리스트 | 필수 |
| SMTP 설정 | 이메일 발송 (비밀번호 재설정) | 초기엔 콘솔 로그로 대체 가능 |

### 환경 변수
```env
# Backend
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30

KAKAO_CLIENT_ID=your-kakao-client-id
KAKAO_CLIENT_SECRET=your-kakao-client-secret
KAKAO_REDIRECT_URI=http://localhost:8000/api/v1/auth/oauth/kakao/callback

REDIS_URL=redis://localhost:6379/0

# SMTP (선택적)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-email
SMTP_PASSWORD=your-password
```

---

## 파일 생성 목록

### Backend 신규 파일
```
backend/
├── src/
│   ├── models/
│   │   ├── user.py
│   │   ├── refresh_token.py
│   │   ├── password_reset_token.py
│   │   └── oauth_state.py
│   ├── schemas/
│   │   ├── auth.py
│   │   └── user.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── oauth_service.py
│   │   └── token_service.py
│   ├── repositories/
│   │   ├── user_repository.py
│   │   └── token_repository.py
│   ├── api/
│   │   └── v1/
│   │       └── auth.py
│   └── core/
│       └── security.py (확장)
├── alembic/
│   └── versions/
│       └── 001_create_auth_tables.py
└── tests/
    ├── unit/
    │   ├── test_security.py
    │   ├── test_auth_service.py
    │   ├── test_oauth_service.py
    │   └── test_password_reset.py
    └── integration/
        └── test_auth_flow.py
```

### Frontend 신규 파일
```
frontend/
├── src/
│   ├── app/
│   │   └── (auth)/
│   │       ├── login/
│   │       │   └── page.tsx
│   │       ├── register/
│   │       │   └── page.tsx
│   │       ├── forgot-password/
│   │       │   └── page.tsx
│   │       └── reset-password/
│   │           └── [token]/
│   │               └── page.tsx
│   ├── lib/
│   │   ├── auth-context.tsx
│   │   └── api/
│   │       └── auth-api.ts
│   ├── hooks/
│   │   └── use-auth.ts
│   ├── components/
│   │   └── auth/
│   │       ├── auth-input.tsx
│   │       ├── password-input.tsx
│   │       ├── social-login-button.tsx
│   │       └── auth-layout.tsx
│   └── middleware.ts
└── tests/
    └── e2e/
        └── auth.spec.ts
```

---

## 예상 소요 시간

| 영역 | 태스크 | 예상 시간 |
|------|--------|-----------|
| BE | T1 (DB 모델) | 1시간 |
| BE | T2 (스키마) | 0.5시간 |
| BE | T3 (서비스) | 2시간 |
| BE | T4 (API) | 1.5시간 |
| BE | T5 (의존성) | 0.5시간 |
| BE | T6 (보안) | 0.5시간 |
| **BE 합계** | | **6시간** |
| FE | T7 (상태 관리) | 1시간 |
| FE | T8 (페이지) | 2시간 |
| FE | T9 (가드) | 0.5시간 |
| FE | T10 (UI) | 0.5시간 |
| **FE 합계** | | **4시간** |
| TEST | T11-T13 | 3시간 |
| **전체 합계** | | **13시간** |

---

## 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|-----------|
| 카카오 OAuth 앱 승인 지연 | 카카오 로그인 구현 지연 | 이메일/비밀번호 로그인 먼저 구현 |
| Redis 연결 이슈 | 블랙리스트 미작동 | DB 기반 폴백 구현 |
| SMTP 설정 문제 | 비밀번호 재설정 불가 | 초기엔 콘솔 로그로 토큰 출력 |

---

## 변경 이력

| 날짜 | 변경 내용 | 이유 |
|------|----------|------|
| 2026-03-02 | 초기 plan.md 작성 | F-07 구현 시작 |
