# F-07 사용자 인증 및 계정 관리 — 기술 설계서

## 1. 참조
- 인수조건: docs/project/features.md #F-07
- 시스템 설계: docs/system/erd.md, docs/system/api-conventions.md
- 네비게이션: docs/system/navigation.md
- 디자인 시스템: docs/system/design-system.md

---

## 2. 아키텍처 결정

### 결정 1: JWT 인증 방식
- **선택지**: A) 세션 기반 / B) JWT 기반
- **결정**: JWT 기반 (Access Token + Refresh Token)
- **근거**:
  - 수평 확장 용이 (Stateless)
  - 마이크로서비스 구조 대응 가능
  - 모바일 앱 확장 고려

### 결정 2: 소셜 로그인 제공처
- **선택지**: A) 카카오만 / B) 카카오 + 네이버 / C) 카카오 + 구글
- **결정**: 카카오만 (1차), 확장 가능 구조
- **근거**:
  - B2B SaaS 주 타겟층 한국 기업
  - 카카오 계정 보급률 높음
  - 추후 네이버/구글 확장 용이한 구조로 설계

### 결정 3: 토큰 저장 위치
- **선택지**: A) LocalStorage / B) HttpOnly Cookie / C) 메모리 + Refresh Token
- **결정**: HttpOnly Cookie + 메모리 (Access Token은 메모리, Refresh Token은 HttpOnly Cookie)
- **근거**:
  - XSS 방지 (HttpOnly Cookie)
  - CSRF 방지 (SameSite Strict)
  - 자동 갱신 가능 (Refresh Token)

---

## 3. API 설계

### 3.1 POST /api/v1/auth/register
이메일/비밀번호 회원가입

- **목적**: 신규 사용자 계정 생성
- **인증**: 불필요
- **Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecureP@ss123",
  "name": "홍길동",
  "phone": "010-1234-5678"
}
```
- **Response** (201 Created):
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "name": "홍길동",
      "phone": "010-1234-5678",
      "createdAt": "2026-03-01T10:00:00Z"
    },
    "tokens": {
      "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "expiresIn": 3600
    }
  }
}
```
- **에러 케이스**:
  | 코드 | HTTP Status | 상황 |
  |------|-------------|------|
  | AUTH_007 | 409 | 이미 가입된 이메일 |
  | VALIDATION_001 | 400 | 입력값 유효성 실패 |

### 3.2 POST /api/v1/auth/login
이메일/비밀번호 로그인

- **목적**: 사용자 인증 및 토큰 발급
- **인증**: 불필요
- **Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecureP@ss123"
}
```
- **Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "name": "홍길동",
      "companyId": "uuid",
      "role": "owner"
    },
    "tokens": {
      "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "expiresIn": 3600
    }
  }
}
```
- **에러 케이스**:
  | 코드 | HTTP Status | 상황 |
  |------|-------------|------|
  | AUTH_001 | 401 | 이메일 또는 비밀번호 불일치 |
  | AUTH_010 | 403 | 탈퇴한 계정 |

### 3.3 POST /api/v1/auth/refresh
토큰 갱신

- **목적**: 액세스 토큰 만료 시 갱신
- **인증**: 불필요 (Refresh Token으로 인증)
- **Request Body**:
```json
{
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```
- **Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresIn": 3600
  }
}
```
- **에러 케이스**:
  | 코드 | HTTP Status | 상황 |
  |------|-------------|------|
  | AUTH_006 | 401 | 유효하지 않은 리프레시 토큰 |
  | AUTH_005 | 401 | 로그아웃된 토큰 (블랙리스트) |

### 3.4 POST /api/v1/auth/logout
로그아웃

- **목적**: 리프레시 토큰 무효화
- **인증**: 필요 (Bearer Token)
- **Request Body**:
```json
{
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```
- **Response** (200 OK):
```json
{
  "success": true,
  "data": null
}
```

### 3.5 GET /api/v1/auth/oauth/kakao
카카오 OAuth 로그인 시작

- **목적**: 카카오 로그인 redirect
- **인증**: 불필요
- **Response**: 302 Redirect to Kakao OAuth

### 3.6 GET /api/v1/auth/oauth/kakao/callback
카카오 OAuth 콜백

- **목적**: 카카오 인증 완료 후 토큰 발급
- **인증**: 불필요
- **Query Parameters**: `code`, `state`
- **Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@kakao.com",
      "name": "홍길동",
      "isNewUser": false
    },
    "tokens": {
      "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "expiresIn": 3600
    }
  }
}
```
- **에러 케이스**:
  | 코드 | HTTP Status | 상황 |
  |------|-------------|------|
  | AUTH_009 | 401 | 카카오 OAuth 인증 실패 |
  | AUTH_011 | 400 | State 검증 실패 (CSRF) |

### 3.7 GET /api/v1/auth/me
현재 사용자 정보 조회

- **목적**: 로그인된 사용자 정보 확인
- **인증**: 필요 (Bearer Token)
- **Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "홍길동",
    "phone": "010-1234-5678",
    "companyId": "uuid",
    "role": "owner",
    "preferences": {
      "notifications": {
        "email": true,
        "kakao": true
      }
    },
    "lastLoginAt": "2026-03-01T09:00:00Z",
    "createdAt": "2026-01-15T10:00:00Z"
  }
}
```
- **에러 케이스**:
  | 코드 | HTTP Status | 상황 |
  |------|-------------|------|
  | AUTH_002 | 401 | 토큰 없음 |
  | AUTH_003 | 401 | 토큰 만료 |
  | AUTH_004 | 401 | 유효하지 않은 토큰 |

### 3.8 PATCH /api/v1/auth/me
계정 정보 수정

- **목적**: 이름, 전화번호 등 수정
- **인증**: 필요 (Bearer Token)
- **Request Body**:
```json
{
  "name": "홍길순",
  "phone": "010-9876-5432"
}
```
- **Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "홍길순",
    "phone": "010-9876-5432",
    "updatedAt": "2026-03-01T10:30:00Z"
  }
}
```

### 3.9 POST /api/v1/auth/change-password
비밀번호 변경

- **목적**: 로그인 상태에서 비밀번호 변경
- **인증**: 필요 (Bearer Token)
- **Request Body**:
```json
{
  "currentPassword": "OldP@ss123",
  "newPassword": "NewSecureP@ss456"
}
```
- **Response** (200 OK):
```json
{
  "success": true,
  "data": null
}
```
- **에러 케이스**:
  | 코드 | HTTP Status | 상황 |
  |------|-------------|------|
  | AUTH_001 | 401 | 현재 비밀번호 불일치 |
  | AUTH_008 | 400 | 이전 비밀번호 재사용 |

### 3.10 POST /api/v1/auth/forgot-password
비밀번호 찾기 (재설정 링크 발송)

- **목적**: 비밀번호 재설정 이메일 발송
- **인증**: 불필요
- **Request Body**:
```json
{
  "email": "user@example.com"
}
```
- **Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "message": "비밀번호 재설정 링크를 이메일로 발송했습니다."
  }
}
```
- **참고**: 존재하지 않는 이메일이어도 동일한 응답 (보안)

### 3.11 POST /api/v1/auth/reset-password
비밀번호 재설정

- **목적**: 토큰 기반 비밀번호 재설정
- **인증**: 불필요 (재설정 토큰으로 인증)
- **Request Body**:
```json
{
  "token": "reset-token-uuid",
  "newPassword": "NewSecureP@ss456"
}
```
- **Response** (200 OK):
```json
{
  "success": true,
  "data": null
}
```
- **에러 케이스**:
  | 코드 | HTTP Status | 상황 |
  |------|-------------|------|
  | AUTH_012 | 400 | 만료된 재설정 토큰 |
  | AUTH_013 | 400 | 이미 사용된 재설정 토큰 |

### 3.12 DELETE /api/v1/auth/me
계정 탈퇴 (Soft Delete)

- **목적**: 사용자 계정 삭제 요청
- **인증**: 필요 (Bearer Token)
- **Request Body**:
```json
{
  "password": "CurrentP@ss123",
  "reason": "서비스 불만족"
}
```
- **Response** (200 OK):
```json
{
  "success": true,
  "data": null
}
```
- **에러 케이스**:
  | 코드 | HTTP Status | 상황 |
  |------|-------------|------|
  | AUTH_001 | 401 | 비밀번호 불일치 |

---

## 4. DB 설계

### 4.1 users 테이블 (ERD 참조, F-07 관련 컬럼 상세)

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 사용자 고유 ID |
| email | VARCHAR(255) | UK, NOT NULL | 이메일 (로그인 ID) |
| password_hash | VARCHAR(255) | | 비밀번호 해시 (소셜 로그인 시 NULL) |
| name | VARCHAR(100) | NOT NULL | 사용자 이름 |
| phone | VARCHAR(20) | | 전화번호 |
| kakao_id | VARCHAR(100) | UK | 카카오 사용자 ID |
| company_id | UUID | FK → companies.id | 소속 회사 ID |
| role | VARCHAR(20) | NOT NULL, DEFAULT 'member' | 역할 (owner, manager, member) |
| preferences | JSONB | DEFAULT '{}' | 사용자 설정 |
| last_login_at | TIMESTAMP | | 최종 로그인 시간 |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 생성 시간 |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 수정 시간 |
| deleted_at | TIMESTAMP | | 삭제 시간 (Soft Delete) |

**인덱스**:
```sql
CREATE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_kakao_id ON users(kakao_id) WHERE kakao_id IS NOT NULL;
```

### 4.2 refresh_tokens 테이블

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 토큰 고유 ID |
| user_id | UUID | FK → users.id, NOT NULL | 사용자 ID |
| token_hash | VARCHAR(255) | UK, NOT NULL | 토큰 해시값 (SHA-256) |
| device_info | VARCHAR(500) | | 디바이스 정보 (User-Agent) |
| ip_address | VARCHAR(45) | | 발급 시 IP 주소 |
| expires_at | TIMESTAMP | NOT NULL | 만료 시간 |
| is_revoked | BOOLEAN | NOT NULL, DEFAULT FALSE | 폐기 여부 |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 생성 시간 |

**인덱스**:
```sql
CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_id) WHERE is_revoked = FALSE;
CREATE INDEX idx_refresh_tokens_expires ON refresh_tokens(expires_at);
```

### 4.3 password_reset_tokens 테이블 (신규)

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 토큰 고유 ID |
| user_id | UUID | FK → users.id, NOT NULL | 사용자 ID |
| token_hash | VARCHAR(255) | UK, NOT NULL | 토큰 해시값 |
| expires_at | TIMESTAMP | NOT NULL | 만료 시간 (1시간) |
| used_at | TIMESTAMP | | 사용 시간 |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 생성 시간 |

**인덱스**:
```sql
CREATE INDEX idx_password_reset_tokens_user ON password_reset_tokens(user_id) WHERE used_at IS NULL;
```

### 4.4 oauth_states 테이블 (신규)

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 상태 고유 ID |
| state | VARCHAR(100) | UK, NOT NULL | CSRF 방지용 state 값 |
| provider | VARCHAR(20) | NOT NULL | OAuth 제공자 (kakao) |
| redirect_url | VARCHAR(500) | | 콜백 후 리다이렉트 URL |
| expires_at | TIMESTAMP | NOT NULL | 만료 시간 (10분) |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 생성 시간 |

---

## 5. 시퀀스 흐름

### 5.1 이메일 회원가입

```
사용자 → Frontend → POST /auth/register → AuthService → DB
    │                                              │
    │  1. 이메일/비밀번호/이름 입력                  │
    │ ────────────────────────────────────────────►│
    │                                              │ 2. 이메일 중복 확인
    │                                              │ 3. 비밀번호 해싱 (bcrypt)
    │                                              │ 4. 사용자 생성
    │                                              │ 5. Access Token 생성 (1시간)
    │                                              │ 6. Refresh Token 생성 (30일)
    │                                              │ 7. Refresh Token 저장 (DB)
    │  ◄───────────────────────────────────────────│
    │  8. 사용자 정보 + 토큰 반환                    │
```

### 5.2 로그인

```
사용자 → Frontend → POST /auth/login → AuthService → DB → Redis
    │                                             │        │
    │  1. 이메일/비밀번호 입력                     │        │
    │ ───────────────────────────────────────────►│        │
    │                                             │ 2. 사용자 조회 (deleted_at IS NULL)
    │                                             │ 3. 비밀번호 검증
    │                                             │        │ 4. 기존 토큰 블랙리스트 확인
    │                                             │ 5. Access Token 생성
    │                                             │ 6. Refresh Token 생성
    │                                             │ 7. Refresh Token 저장
    │                                             │ 8. last_login_at 갱신
    │  ◄──────────────────────────────────────────│        │
    │  9. 토큰 + 사용자 정보 반환                   │        │
```

### 5.3 토큰 갱신

```
Frontend → POST /auth/refresh → AuthService → DB → Redis
    │                               │             │
    │  1. Refresh Token 전송        │             │
    │ ─────────────────────────────►│             │
    │                               │ 2. 토큰 해시 계산
    │                               │ 3. 토큰 조회 (is_revoked = FALSE)
    │                               │ 4. 만료 확인
    │                               │             │ 5. 블랙리스트 확인
    │                               │ 6. 기존 토큰 폐기 (is_revoked = TRUE)
    │                               │ 7. 새 Access Token 생성
    │                               │ 8. 새 Refresh Token 생성
    │                               │ 9. 새 토큰 저장
    │  ◄────────────────────────────│             │
    │  10. 새 토큰 반환              │             │
```

### 5.4 카카오 OAuth 로그인

```
사용자 → Frontend → GET /auth/oauth/kakao → Kakao → Callback → AuthService → DB
    │           │                              │           │              │
    │  1. 카카오 로그인 클릭                    │           │              │
    │ ─────────►│                              │           │              │
    │           │  2. state 생성 & 저장         │           │              │
    │           │  3. 302 Redirect to Kakao    │           │              │
    │  ◄────────│                              │           │              │
    │  4. Kakao 로그인 페이지                   │           │              │
    │ ──────────────────────────────────────────►│          │              │
    │  5. 사용자 승인                           │           │              │
    │  ◄─────────────────────────────────────────│          │              │
    │  6. Redirect with code, state             │           │              │
    │ ─────────────────────────────────────────────────────►│              │
    │                                          │           │ 7. state 검증
    │                                          │           │ 8. code → access_token 교환
    │                                          │           │ 9. 카카오 사용자 정보 조회
    │                                          │           │              │ 10. kakao_id로 사용자 조회
    │                                          │           │              │ 11. 신규: 사용자 생성 / 기존: 조회
    │                                          │           │              │ 12. 토큰 생성
    │  ◄───────────────────────────────────────────────────────────────────│
    │  13. 토큰 + 사용자 정보 반환                            │
```

### 5.5 로그아웃

```
Frontend → POST /auth/logout → AuthService → DB → Redis
    │                             │               │
    │  1. Refresh Token + Access Token            │
    │ ───────────────────────────►│               │
    │                             │ 2. 토큰 해시 계산
    │                             │ 3. Refresh Token 폐기 (is_revoked = TRUE)
    │                             │               │ 4. Access Token 블랙리스트 추가
    │  ◄──────────────────────────│               │
    │  5. 성공 응답                │               │
```

---

## 6. 영향 범위

### 6.1 수정 필요 파일
| 파일 | 변경 내용 |
|------|----------|
| backend/src/api/v1/auth.py | 전체 API 구현 |
| backend/src/core/security.py | 리프레시 토큰 생성/검증 함수 추가 |
| backend/src/config.py | JWT 설정 확장 (refresh token 만료 시간 등) |
| backend/src/api/deps.py | 인증 의존성 구현 |

### 6.2 신규 생성 파일
| 파일 | 설명 |
|------|------|
| backend/src/models/user.py | User 모델 |
| backend/src/models/refresh_token.py | RefreshToken 모델 |
| backend/src/models/password_reset_token.py | PasswordResetToken 모델 |
| backend/src/models/oauth_state.py | OAuthState 모델 |
| backend/src/schemas/auth.py | 요청/응답 스키마 |
| backend/src/schemas/user.py | 사용자 스키마 |
| backend/src/services/auth_service.py | 인증 비즈니스 로직 |
| backend/src/services/oauth_service.py | OAuth 로직 (카카오) |
| backend/src/services/token_service.py | 토큰 관리 로직 |
| backend/src/repositories/user_repository.py | 사용자 DB 접근 |
| backend/src/repositories/token_repository.py | 토큰 DB 접근 |
| backend/alembic/versions/xxx_create_auth_tables.py | 마이그레이션 |
| frontend/src/app/(auth)/login/page.tsx | 로그인 페이지 |
| frontend/src/app/(auth)/register/page.tsx | 회원가입 페이지 |
| frontend/src/app/(auth)/forgot-password/page.tsx | 비밀번호 찾기 페이지 |
| frontend/src/app/(auth)/reset-password/[token]/page.tsx | 비밀번호 재설정 페이지 |
| frontend/src/lib/auth-context.tsx | 인증 상태 관리 |
| frontend/src/lib/api/auth-api.ts | 인증 API 클라이언트 |
| frontend/src/hooks/use-auth.ts | 인증 훅 |
| frontend/src/middleware.ts | 인증 가드 미들웨어 |

---

## 7. 보안 설계

### 7.1 비밀번호 정책
- 최소 8자, 최대 64자
- 영문 대소문자, 숫자, 특수문자 중 3가지 이상 조합
- 이메일과 유사하지 않아야 함
- 최근 5개 비밀번호 재사용 금지
- bcrypt (cost factor 12)

### 7.2 JWT 보안
- **Access Token**: 1시간 만료, 민감 정보 미포함
- **Refresh Token**: 30일 만료, UUID + SHA-256 해시 저장
- **서명 알고리즘**: HS256 (운영환경에서 RS256 고려)
- **페이로드**: sub (user_id), email, role, companyId, exp, iat

### 7.3 토큰 블랙리스트 (Redis)
```
Key: blacklist:{access_token_jti}
Value: "1"
TTL: 토큰 남은 만료 시간
```

### 7.4 OAuth 보안
- **State Parameter**: UUID v4, 10분 만료
- **PKCE**: 모바일 확장 고려 시 구현
- **Redirect URI 검증**: 사전 등록된 URL만 허용

### 7.5 Rate Limiting
| 엔드포인트 | 제한 | 윈도우 |
|------------|------|--------|
| POST /auth/login | 10회 | 1분 |
| POST /auth/register | 5회 | 1시간 |
| POST /auth/forgot-password | 3회 | 1시간 |
| POST /auth/refresh | 30회 | 1분 |

### 7.6 이메일 보안
- 비밀번호 재설정 링크: 1시간 만료
- 일회용 토큰 (사용 후 즉시 무효화)
- 이메일 변경 시 기존 이메일로 알림 발송

---

## 8. 성능 설계

### 8.1 인덱스 계획
```sql
-- users 테이블
CREATE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_kakao_id ON users(kakao_id) WHERE kakao_id IS NOT NULL;

-- refresh_tokens 테이블
CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_id) WHERE is_revoked = FALSE;
CREATE INDEX idx_refresh_tokens_expires ON refresh_tokens(expires_at);

-- 정기 정리 (만료된 토큰 삭제)
-- Cron: 매일 00:00 UTC
DELETE FROM refresh_tokens WHERE expires_at < NOW() - INTERVAL '7 days';
```

### 8.2 Redis 캐싱 전략
```
# 블랙리스트
blacklist:{jti} → "1" (TTL: 토큰 남은 시간)

# 사용자 세션 정보 (선택적)
session:{user_id} → {last_activity, device_count} (TTL: 1시간)
```

### 8.3 DB 커넥션 풀
- AsyncPG 풀 사이즈: 10
- Max Overflow: 20

---

## 9. 프론트엔드 흐름

### 9.1 인증 상태 관리
```typescript
// AuthContext 구조
interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

interface AuthActions {
  login: (email: string, password: string) => Promise<void>;
  loginWithKakao: () => void;
  logout: () => Promise<void>;
  refreshTokens: () => Promise<void>;
}
```

### 9.2 토큰 저장 및 갱신
- **Access Token**: 메모리 (React State)
- **Refresh Token**: HttpOnly Cookie (서버 설정)
- **자동 갱신**: 401 응답 시 자동 refresh → 원래 요청 재시도

### 9.3 인증 가드 (Middleware)
```typescript
// protectedRoutes: /dashboard, /bids, /proposals, /settings, /teams
// authRoutes: /login, /register, /forgot-password, /reset-password

// 미인증 시: protectedRoutes → /login
// 이미 인증 시: authRoutes → /dashboard
```

---

## 10. 에러 코드 요약

| 코드 | HTTP Status | 메시지 |
|------|-------------|--------|
| AUTH_001 | 401 | 이메일 또는 비밀번호가 올바르지 않습니다. |
| AUTH_002 | 401 | 인증 토큰이 필요합니다. |
| AUTH_003 | 401 | 토큰이 만료되었습니다. |
| AUTH_004 | 401 | 유효하지 않은 토큰입니다. |
| AUTH_005 | 401 | 로그아웃된 토큰입니다. |
| AUTH_006 | 401 | 리프레시 토큰이 유효하지 않습니다. |
| AUTH_007 | 409 | 이미 가입된 이메일입니다. |
| AUTH_008 | 400 | 비밀번호 재사용이 제한됩니다. |
| AUTH_009 | 401 | 카카오 OAuth 인증 실패 |
| AUTH_010 | 403 | 탈퇴한 계정입니다. |
| AUTH_011 | 400 | State 검증 실패 (CSRF) |
| AUTH_012 | 400 | 만료된 재설정 토큰입니다. |
| AUTH_013 | 400 | 이미 사용된 재설정 토큰입니다. |

---

## 변경 이력

| 날짜 | 변경 내용 | 이유 |
|------|----------|------|
| 2026-03-01 | 초기 설계 | F-07 기능 구현 시작 |
