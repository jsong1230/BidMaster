# F-07 사용자 인증 및 계정 관리 — 테스트 명세

## 참조
- 설계서: docs/specs/F-07-auth/design.md
- 인수조건: docs/project/features.md #F-07
- API 컨벤션: docs/system/api-conventions.md

---

## 단위 테스트

### 1. 비밀번호 해싱 (core/security.py)

| 대상 | 시나리오 | 입력 | 예상 결과 |
|------|----------|------|-----------|
| get_password_hash | 일반 비밀번호 해싱 | "SecureP@ss123" | bcrypt 해시 문자열 반환 ($2b$12$...) |
| get_password_hash | 동일 비밀번호 해싱 | "SecureP@ss123" (2회) | 매번 다른 해시 (salt 적용) |
| verify_password | 올바른 비밀번호 | ("SecureP@ss123", hash) | True |
| verify_password | 잘못된 비밀번호 | ("WrongP@ss", hash) | False |
| verify_password | 빈 비밀번호 | ("", hash) | False |

### 2. JWT 토큰 생성 (core/security.py)

| 대상 | 시나리오 | 입력 | 예상 결과 |
|------|----------|------|-----------|
| create_access_token | 기본 만료 시간 | user_id="user-123" | exp = now + 1시간 |
| create_access_token | 커스텀 만료 시간 | user_id, timedelta(hours=2) | exp = now + 2시간 |
| create_access_token | 페이로드 검증 | user_id="user-123" | sub, exp, iat 포함 |
| create_refresh_token | 리프레시 토큰 생성 | user_id="user-123" | exp = now + 30일 |
| decode_token | 유효한 토큰 | valid_token | 페이로드 디코딩 성공 |
| decode_token | 만료된 토큰 | expired_token | ExpiredSignatureError |
| decode_token | 변조된 토큰 | tampered_token | InvalidSignatureError |

### 3. AuthService - 회원가입

| 대상 | 시나리오 | 입력 | 예상 결과 |
|------|----------|------|-----------|
| register | 정상 회원가입 | email, password, name | User 생성, 토큰 반환 |
| register | 중복 이메일 | existing_email | AUTH_007 에러 |
| register | 약한 비밀번호 | "123456" | VALIDATION_001 에러 |
| register | 잘못된 이메일 형식 | "not-email" | VALIDATION_001 에러 |
| register | 이름 누락 | email, password only | VALIDATION_002 에러 |

### 4. AuthService - 로그인

| 대상 | 시나리오 | 입력 | 예상 결과 |
|------|----------|------|-----------|
| login | 정상 로그인 | valid_email, valid_password | 토큰 + 사용자 정보 반환 |
| login | 잘못된 비밀번호 | valid_email, wrong_password | AUTH_001 에러 |
| login | 존재하지 않는 이메일 | unknown_email | AUTH_001 에러 (동일 메시지) |
| login | 탈퇴한 계정 | deleted_user_email | AUTH_010 에러 |
| login | last_login_at 갱신 | valid_login | last_login_at = now |

### 5. AuthService - 토큰 갱신

| 대상 | 시나리오 | 입력 | 예상 결과 |
|------|----------|------|-----------|
| refresh_token | 정상 갱신 | valid_refresh_token | 새 access_token, refresh_token |
| refresh_token | 만료된 리프레시 토큰 | expired_refresh_token | AUTH_006 에러 |
| refresh_token | 폐기된 토큰 | revoked_token | AUTH_005 에러 |
| refresh_token | 존재하지 않는 토큰 | unknown_token | AUTH_006 에러 |
| refresh_token | 기존 토큰 폐기 확인 | valid_refresh_token | 기존 토큰 is_revoked = True |

### 6. AuthService - 로그아웃

| 대상 | 시나리오 | 입력 | 예상 결과 |
|------|----------|------|-----------|
| logout | 정상 로그아웃 | valid_refresh_token | is_revoked = True |
| logout | 이미 로그아웃된 토큰 | revoked_token | 성공 (멱등성) |
| logout | 액세스 토큰 블랙리스트 | access_token_jti | Redis에 블랙리스트 추가 |

### 7. OAuthService - 카카오 로그인

| 대상 | 시나리오 | 입력 | 예상 결과 |
|------|----------|------|-----------|
| get_oauth_url | 인증 URL 생성 | redirect_url | 카카오 인증 URL + state |
| get_oauth_url | state 저장 확인 | redirect_url | oauth_states에 저장 |
| handle_callback | 정상 콜백 | valid_code, valid_state | 토큰 + 사용자 정보 |
| handle_callback | 신규 사용자 | new_kakao_user | isNewUser = True |
| handle_callback | 기존 사용자 | existing_kakao_user | isNewUser = False |
| handle_callback | 잘못된 state | invalid_state | AUTH_011 에러 |
| handle_callback | 만료된 state | expired_state | AUTH_011 에러 |
| handle_callback | 카카오 토큰 오류 | invalid_code | AUTH_009 에러 |

### 8. 비밀번호 재설정

| 대상 | 시나리오 | 입력 | 예상 결과 |
|------|----------|------|-----------|
| forgot_password | 존재하는 이메일 | existing_email | 재설정 토큰 생성, 이메일 발송 |
| forgot_password | 존재하지 않는 이메일 | unknown_email | 동일한 성공 응답 (보안) |
| reset_password | 정상 재설정 | valid_token, new_password | 비밀번호 변경, 토큰 used_at 갱신 |
| reset_password | 만료된 토큰 | expired_token | AUTH_012 에러 |
| reset_password | 이미 사용된 토큰 | used_token | AUTH_013 에러 |

### 9. 비밀번호 변경

| 대상 | 시나리오 | 입력 | 예상 결과 |
|------|----------|------|-----------|
| change_password | 정상 변경 | valid_current, valid_new | 비밀번호 변경 성공 |
| change_password | 현재 비밀번호 불일치 | wrong_current | AUTH_001 에러 |
| change_password | 이전 비밀번호 재사용 | same_as_old | AUTH_008 에러 |
| change_password | 약한 새 비밀번호 | "123456" | VALIDATION_001 에러 |

### 10. 계정 탈퇴

| 대상 | 시나리오 | 입력 | 예상 결과 |
|------|----------|------|-----------|
| delete_account | 정상 탈퇴 | valid_password | deleted_at = now |
| delete_account | 비밀번호 불일치 | wrong_password | AUTH_001 에러 |
| delete_account | 소셜 로그인 사용자 | kakao_user | 비밀번호 없이 탈퇴 가능? (설계 결정 필요) |

### 11. 사용자 정보 조회/수정

| 대상 | 시나리오 | 입력 | 예상 결과 |
|------|----------|------|-----------|
| get_current_user | 정상 조회 | valid_token | 사용자 정보 반환 |
| get_current_user | 없는 사용자 | deleted_user_token | AUTH_004 에러 |
| update_user | 이름 변경 | new_name | 이름 업데이트 |
| update_user | 전화번호 변경 | new_phone | 전화번호 업데이트 |
| update_user | 이메일 변경 | new_email | 이메일 업데이트 + 인증 필요? |

---

## 통합 테스트

### 1. 회원가입 → 로그인 → API 호출

| API | 시나리오 | 입력 | 예상 결과 |
|-----|----------|------|-----------|
| POST /auth/register | 회원가입 | email, password, name | 201, user + tokens |
| POST /auth/login | 로그인 | email, password | 200, tokens |
| GET /auth/me | 사용자 조회 | access_token | 200, user info |
| POST /auth/logout | 로그아웃 | refresh_token | 200, success |
| GET /auth/me | 로그아웃 후 접근 | old_access_token | 401, AUTH_005 |

### 2. 토큰 갱신 플로우

| API | 시나리오 | 입력 | 예상 결과 |
|-----|----------|------|-----------|
| POST /auth/login | 로그인 | email, password | 200, tokens |
| POST /auth/refresh | 토큰 갱신 | refresh_token | 200, new tokens |
| POST /auth/refresh | 이전 토큰 사용 | old_refresh_token | 401, AUTH_006 |
| POST /auth/refresh | 새 토큰 사용 | new_refresh_token | 200, 또 새 tokens |

### 3. 카카오 OAuth 전체 플로우

| API | 시나리오 | 입력 | 예상 결과 |
|-----|----------|------|-----------|
| GET /auth/oauth/kakao | OAuth 시작 | - | 302, Location: kakao.com |
| GET /auth/oauth/kakao/callback | 콜백 | code, state | 200, tokens + isNewUser |

### 4. 비밀번호 재설정 플로우

| API | 시나리오 | 입력 | 예상 결과 |
|-----|----------|------|-----------|
| POST /auth/forgot-password | 요청 | email | 200, email sent |
| POST /auth/reset-password | 재설정 | token, new_password | 200, success |
| POST /auth/login | 새 비밀번호 로그인 | email, new_password | 200, tokens |
| POST /auth/login | 이전 비밀번호 로그인 | email, old_password | 401, AUTH_001 |

### 5. 동시 세션 관리

| API | 시나리오 | 입력 | 예상 결과 |
|-----|----------|------|-----------|
| POST /auth/login | 디바이스 A 로그인 | email, password | 200, tokens_A |
| POST /auth/login | 디바이스 B 로그인 | email, password | 200, tokens_B |
| POST /auth/logout | 디바이스 A 로그아웃 | refresh_token_A | 200, success |
| POST /auth/refresh | 디바이스 A 갱신 시도 | refresh_token_A | 401, AUTH_005 |
| POST /auth/refresh | 디바이스 B 갱신 | refresh_token_B | 200, new tokens |

### 6. Rate Limiting

| API | 시나리오 | 입력 | 예상 결과 |
|-----|----------|------|-----------|
| POST /auth/login | 10회 연속 실패 | wrong_password × 10 | 429, RATE_LIMIT_001 |
| POST /auth/login | 1분 대기 후 | correct_password | 200, tokens |
| POST /auth/register | 6회 연속 시도 | different_emails × 6 | 429, RATE_LIMIT_001 |

---

## E2E 테스트 (Playwright)

### 1. 회원가입 → 이메일 인증 → 로그인

```
1. /register 페이지 접근
2. 이메일, 비밀번호, 이름 입력
3. 회원가입 버튼 클릭
4. /dashboard로 리다이렉트 확인
5. 헤더에 사용자 이름 표시 확인
```

### 2. 로그인 → 대시보드 접근 → 로그아웃

```
1. /login 페이지 접근
2. 이메일, 비밀번호 입력
3. 로그인 버튼 클릭
4. /dashboard로 리다이렉트 확인
5. 로그아웃 버튼 클릭
6. / (랜딩)으로 리다이렉트 확인
7. /dashboard 직접 접근 시 /login으로 리다이렉트
```

### 3. 카카오 로그인 (신규 사용자)

```
1. /login 페이지 접근
2. "카카오로 로그인" 버튼 클릭
3. 카카오 로그인 페이지로 이동
4. 카카오 계정으로 로그인
5. 동의 화면 승인 (최초 1회)
6. /dashboard로 리다이렉트
7. isNewUser = true 확인 (온보딩 표시)
```

### 4. 비밀번호 찾기 → 재설정

```
1. /login 페이지 접근
2. "비밀번호 찾기" 링크 클릭
3. /forgot-password 페이지 이동
4. 이메일 입력 후 전송
5. "이메일 발송 완료" 메시지 확인
6. 이메일에서 재설정 링크 클릭
7. /reset-password/[token] 페이지 이동
8. 새 비밀번호 입력
9. /login으로 리다이렉트
10. 새 비밀번호로 로그인 성공
```

### 5. 토큰 만료 → 자동 갱신

```
1. 로그인 후 대시보드 접근
2. Access Token 만료 대기 (또는 강제 만료)
3. API 요청 (예: 공고 목록)
4. 자동으로 토큰 갱신되어 정상 응답
5. 사용자는 갱신 과정 인지 못함
```

### 6. 인증 가드 테스트

```
1. 미로그인 상태로 /dashboard 접근 → /login 리다이렉트
2. 미로그인 상태로 /bids 접근 → /login 리다이렉트
3. 미로그인 상태로 /settings 접근 → /login 리다이렉트
4. 로그인 상태로 /login 접근 → /dashboard 리다이렉트
5. 로그인 상태로 /register 접근 → /dashboard 리다이렉트
```

---

## 경계 조건 / 에러 케이스

### 1. 입력값 경계

| 케이스 | 입력 | 예상 결과 |
|--------|------|-----------|
| 이메일 최대 길이 | 255자 | 성공 |
| 이메일 초과 | 256자 | VALIDATION_003 |
| 비밀번호 최소 | 8자 | 성공 |
| 비밀번호 미만 | 7자 | VALIDATION_001 |
| 비밀번호 최대 | 64자 | 성공 |
| 비밀번호 초과 | 65자 | VALIDATION_003 |
| 이름 최대 | 100자 | 성공 |
| 이름 초과 | 101자 | VALIDATION_003 |
| 빈 문자열 | "" | VALIDATION_002 |

### 2. 특수문자/유니코드

| 케이스 | 입력 | 예상 결과 |
|--------|------|-----------|
| 한글 이름 | "홍길동" | 성공 |
| 이모지 이름 | "홍길동🎉" | 성공 (또는 제한?) |
| 이메일 유니코드 | "user@한글.com" | 성공 (Punycode 변환) |
| 비밀번호 유니코드 | "패스워드123!" | 성공 |

### 3. 동시성 이슈

| 케이스 | 시나리오 | 예상 결과 |
|--------|----------|-----------|
| 동시 회원가입 | 동일 이메일로 2회 동시 요청 | 1개만 성공, 1개 AUTH_007 |
| 동시 토큰 갱신 | 동일 refresh_token으로 2회 동시 요청 | 1개만 성공, 1개 AUTH_006 |
| 동시 로그아웃 | 동일 토큰으로 2회 동시 로그아웃 | 둘 다 성공 (멱등성) |

### 4. DB 장애

| 케이스 | 시나리오 | 예상 결과 |
|--------|----------|-----------|
| DB 연결 실패 | 로그인 요청 중 DB 다운 | SERVER_001 에러 |
| Redis 연결 실패 | 블랙리스트 확인 불가 | 정상 동작 (블랙리스트 스킵?) |

### 5. 외부 서비스 장애

| 케이스 | 시나리오 | 예상 결과 |
|--------|----------|-----------|
| 카카오 API 타임아웃 | OAuth 콜백 처리 중 | AUTH_009 에러 |
| 이메일 발송 실패 | 비밀번호 재설정 이메일 | 재시도 또는 SERVER_002 |

---

## 보안 테스트

### 1. SQL Injection

| 케이스 | 입력 | 예상 결과 |
|--------|------|-----------|
| 이메일 SQLi | "admin'--@test.com" | 일반 문자열로 처리 |
| 비밀번호 SQLi | "' OR '1'='1" | 일반 문자열로 처리 |

### 2. XSS

| 케이스 | 입력 | 예상 결과 |
|--------|------|-----------|
| 이름 XSS | "<script>alert(1)</script>" | 이스케이프 처리 |
| 에러 메시지 XSS | 악성 스크립트 | 이스케이프 처리 |

### 3. CSRF

| 케이스 | 시나리오 | 예상 결과 |
|--------|----------|-----------|
| OAuth state 없음 | state 없이 콜백 호출 | AUTH_011 에러 |
| OAuth state 변조 | 다른 state 값 사용 | AUTH_011 에러 |

### 4. 토큰 탈취 시나리오

| 케이스 | 시나리오 | 대응 |
|--------|----------|------|
| Access Token 탈취 | 만료 전 사용 가능 | 1시간 후 자동 만료 |
| Refresh Token 탈취 | 새 토큰 발급 가능 | 로그아웃 시 폐기, 의심스러운 활동 감지 |
| 토큰 재생 공격 | 이전 토큰 재사용 | 폐기된 토큰 거부 |

### 5. 무차별 대입 공격

| 케이스 | 시나리오 | 대응 |
|--------|----------|------|
| 로그인 무차별 | 1000회 비밀번호 시도 | Rate Limiting (10회/분) |
| 토큰 무차별 | 임의 토큰 검증 | Rate Limiting + 빠른 실패 |

---

## 테스트 데이터

### 1. 정상 사용자

```json
{
  "email": "test@example.com",
  "password": "SecureP@ss123",
  "name": "테스트사용자",
  "phone": "010-1234-5678"
}
```

### 2. 카카오 사용자

```json
{
  "kakao_id": "1234567890",
  "email": "user@kakao.com",
  "name": "카카오사용자"
}
```

### 3. 관리자

```json
{
  "email": "admin@bidmaster.kr",
  "password": "AdminP@ss456",
  "name": "관리자",
  "role": "admin"
}
```

---

## 테스트 환경

### Backend
- pytest + pytest-asyncio
- httpx (AsyncClient)
- testcontainers (PostgreSQL, Redis)
- faker (테스트 데이터 생성)

### Frontend
- Playwright (E2E)
- MSW (API Mocking)
- Testing Library (컴포넌트 테스트)

---

## 테스트 커버리지 목표

| 영역 | 목표 |
|------|------|
| 단위 테스트 | 90% 이상 |
| 통합 테스트 | 주요 시나리오 100% |
| E2E 테스트 | 핵심 사용자 경로 100% |

---

## 변경 이력

| 날짜 | 변경 내용 | 이유 |
|------|----------|------|
| 2026-03-01 | 초기 테스트 명세 작성 | F-07 기능 구현 시작 |
