# API 컨벤션

## 1. 개요

BidMaster API는 RESTful 설계 원칙을 따르며, FastAPI 기반으로 구현됩니다.

### Base URL
```
Development: http://localhost:8000/api/v1
Production:  https://api.bidmaster.kr/api/v1
```

### 버전 체계
- URL Path 방식: `/api/v1`, `/api/v2`
- 하위 호환성 있는 변경은 버전 유지
- Breaking Change 시 새 버전 발행

---

## 2. 응답 포맷

### 2.1 표준 응답 구조

모든 API 응답은 다음 표준 구조를 따릅니다.

```typescript
interface ApiResponse<T> {
  success: boolean;       // 요청 성공 여부
  data?: T;               // 성공 시 응답 데이터
  error?: ApiError;       // 실패 시 에러 정보
  meta?: ResponseMeta;    // 메타데이터 (페이지네이션 등)
}

interface ApiError {
  code: string;           // 에러 코드 (ex: AUTH_001)
  message: string;        // 사용자용 메시지
  details?: Record<string, string[]>;  // 필드별 상세 에러
}

interface ResponseMeta {
  page?: number;
  pageSize?: number;
  total?: number;
  totalPages?: number;
}
```

### 2.2 성공 응답 예시

**단일 리소스 조회**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "홍길동",
    "email": "hong@example.com"
  }
}
```

**목록 조회 (페이지네이션)**
```json
{
  "success": true,
  "data": {
    "items": [
      { "id": 1, "title": "제안서 A" },
      { "id": 2, "title": "제안서 B" }
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

**생성/수정 성공**
```json
{
  "success": true,
  "data": {
    "id": 123,
    "createdAt": "2026-03-01T10:30:00Z"
  }
}
```

**삭제 성공**
```json
{
  "success": true,
  "data": null
}
```

### 2.3 에러 응답 예시

**단일 에러**
```json
{
  "success": false,
  "error": {
    "code": "AUTH_001",
    "message": "이메일 또는 비밀번호가 올바르지 않습니다."
  }
}
```

**유효성 검사 실패 (필드별 상세)**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_001",
    "message": "입력값이 유효하지 않습니다.",
    "details": {
      "email": ["유효한 이메일 형식이 아닙니다."],
      "password": ["비밀번호는 8자 이상이어야 합니다.", "특수문자를 포함해야 합니다."]
    }
  }
}
```

---

## 3. 인증

### 3.1 인증 방식

| 방식 | 용도 | 만료 시간 |
|------|------|-----------|
| Access Token | API 인증 | 1시간 |
| Refresh Token | 토큰 갱신 | 30일 |
| OAuth 2.0 (카카오) | 소셜 로그인 | - |

### 3.2 JWT 토큰 구조

**Access Token Payload**
```json
{
  "sub": "user_123",
  "email": "user@example.com",
  "role": "user",
  "companyId": 1,
  "exp": 1709304000,
  "iat": 1709300400
}
```

### 3.3 토큰 전달 방식

**요청 헤더**
```
Authorization: Bearer <access_token>
```

### 3.4 토큰 갱신

**POST /api/v1/auth/refresh**
```json
// Request
{
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}

// Response
{
  "success": true,
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresIn": 3600
  }
}
```

### 3.5 카카오 OAuth 로그인

**GET /api/v1/auth/oauth/kakao**
```
// Request (Query Parameters)
?code={authorization_code}&state={csrf_state}

// Response
{
  "success": true,
  "data": {
    "accessToken": "...",
    "refreshToken": "...",
    "isNewUser": true,
    "user": {
      "id": 1,
      "email": "user@kakao.com",
      "name": "홍길동"
    }
  }
}
```

### 3.6 인증 실패 응답

| HTTP Status | Code | 상황 |
|-------------|------|------|
| 401 | AUTH_002 | 토큰 없음 |
| 401 | AUTH_003 | 토큰 만료 |
| 401 | AUTH_004 | 토큰 무효 |
| 401 | AUTH_005 | 토큰 블랙리스트 (로그아웃됨) |

---

## 4. HTTP 상태 코드

### 4.1 성공 응답

| Status | 의미 | 사용 시나리오 |
|--------|------|---------------|
| 200 OK | 성공 | 조회, 수정, 삭제 |
| 201 Created | 생성됨 | 리소스 생성 |
| 204 No Content | 내용 없음 | 삭제 완료 (본문 없음) |

### 4.2 에러 응답

| Status | 의미 | 사용 시나리오 |
|--------|------|---------------|
| 400 Bad Request | 잘못된 요청 | 유효성 검사 실패 |
| 401 Unauthorized | 인증 필요 | 토큰 없음/만료 |
| 403 Forbidden | 권한 없음 | 리소스 접근 권한 없음 |
| 404 Not Found | 리소스 없음 | 존재하지 않는 ID |
| 409 Conflict | 충돌 | 중복 데이터, 비즈니스 규칙 위반 |
| 422 Unprocessable Entity | 처리 불가 | 요청 형식은 맞으나 의미상 처리 불가 |
| 429 Too Many Requests | 요청 과다 | Rate Limit 초과 |
| 500 Internal Server Error | 서버 에러 | 예기치 않은 서버 오류 |
| 503 Service Unavailable | 서비스 불가 | 유지보수, 과부하 |

---

## 5. 에러 코드 체계

### 5.1 코드 형식

```
{카테고리}_{순번}
```

### 5.2 카테고리별 에러 코드

#### 인증 (AUTH)
| Code | Message | HTTP Status |
|------|---------|-------------|
| AUTH_001 | 이메일 또는 비밀번호가 올바르지 않습니다. | 401 |
| AUTH_002 | 인증 토큰이 필요합니다. | 401 |
| AUTH_003 | 토큰이 만료되었습니다. | 401 |
| AUTH_004 | 유효하지 않은 토큰입니다. | 401 |
| AUTH_005 | 로그아웃된 토큰입니다. | 401 |
| AUTH_006 | 리프레시 토큰이 유효하지 않습니다. | 401 |
| AUTH_007 | 이미 가입된 이메일입니다. | 409 |
| AUTH_008 | 비밀번호 재사용이 제한됩니다. | 400 |
| AUTH_009 | 카카오 OAuth 인증 실패 | 401 |

#### 유효성 검사 (VALIDATION)
| Code | Message | HTTP Status |
|------|---------|-------------|
| VALIDATION_001 | 입력값이 유효하지 않습니다. | 400 |
| VALIDATION_002 | 필수 필드가 누락되었습니다. | 400 |
| VALIDATION_003 | 필드 길이 제한을 초과했습니다. | 400 |
| VALIDATION_004 | 필드 형식이 올바르지 않습니다. | 400 |

#### 회사/프로필 (COMPANY)
| Code | Message | HTTP Status |
|------|---------|-------------|
| COMPANY_001 | 회사를 찾을 수 없습니다. | 404 |
| COMPANY_002 | 이미 등록된 사업자등록번호입니다. | 409 |
| COMPANY_003 | 사업자등록번호 검증 실패 | 400 |
| COMPANY_004 | 회사 프로필이 이미 존재합니다. | 409 |

#### 공고 (BID)
| Code | Message | HTTP Status |
|------|---------|-------------|
| BID_001 | 공고를 찾을 수 없습니다. | 404 |
| BID_002 | 공고가 이미 마감되었습니다. | 400 |
| BID_003 | 첨부파일 파싱에 실패했습니다. | 422 |

#### 제안서 (PROPOSAL)
| Code | Message | HTTP Status |
|------|---------|-------------|
| PROPOSAL_001 | 제안서를 찾을 수 없습니다. | 404 |
| PROPOSAL_002 | 제안서 생성 권한이 없습니다. | 403 |
| PROPOSAL_003 | 제안서 생성 중 오류가 발생했습니다. | 500 |
| PROPOSAL_004 | AI 생성 시간이 초과되었습니다. | 504 |
| PROPOSAL_005 | 제안서 버전을 찾을 수 없습니다. | 404 |

#### 결제/구독 (PAYMENT)
| Code | Message | HTTP Status |
|------|---------|-------------|
| PAYMENT_001 | 결제 정보를 찾을 수 없습니다. | 404 |
| PAYMENT_002 | 이미 활성화된 구독이 있습니다. | 409 |
| PAYMENT_003 | 결제 승인 실패 | 402 |
| PAYMENT_004 | 환불이 불가능한 상태입니다. | 400 |
| PAYMENT_005 | 웹훅 서명 검증 실패 | 400 |

#### 권한 (PERMISSION)
| Code | Message | HTTP Status |
|------|---------|-------------|
| PERMISSION_001 | 접근 권한이 없습니다. | 403 |
| PERMISSION_002 | 리소스 소유자가 아닙니다. | 403 |
| PERMISSION_003 | 팀원 초대 권한이 없습니다. | 403 |
| PERMISSION_004 | 구독이 필요한 기능입니다. | 402 |

#### 요청 제한 (RATE_LIMIT)
| Code | Message | HTTP Status |
|------|---------|-------------|
| RATE_LIMIT_001 | 요청 횟수를 초과했습니다. 잠시 후 다시 시도해주세요. | 429 |
| RATE_LIMIT_002 | AI 생성 요청 한도를 초과했습니다. | 429 |

#### 서버 (SERVER)
| Code | Message | HTTP Status |
|------|---------|-------------|
| SERVER_001 | 내부 서버 오류가 발생했습니다. | 500 |
| SERVER_002 | 외부 서비스 연동 실패 | 502 |
| SERVER_003 | 서비스 점검 중입니다. | 503 |

---

## 6. 페이지네이션

### 6.1 요청 파라미터

| Parameter | Type | Default | Max | 설명 |
|-----------|------|---------|-----|------|
| page | int | 1 | - | 페이지 번호 (1부터 시작) |
| pageSize | int | 20 | 100 | 페이지당 항목 수 |

### 6.2 요청 예시

```
GET /api/v1/proposals?page=2&pageSize=20
```

### 6.3 응답 형식

```json
{
  "success": true,
  "data": {
    "items": [...]
  },
  "meta": {
    "page": 2,
    "pageSize": 20,
    "total": 95,
    "totalPages": 5
  }
}
```

---

## 7. 필터링 및 정렬

### 7.1 필터링

**쿼리 파라미터 방식**
```
GET /api/v1/bids?status=open&region=서울&minBudget=10000000
```

**날짜 범위 필터**
```
GET /api/v1/bids?startDate=2026-01-01&endDate=2026-03-31
```

### 7.2 정렬

| Parameter | Type | Default | 설명 |
|-----------|------|---------|------|
| sortBy | string | createdAt | 정렬 필드 |
| sortOrder | string | desc | 정렬 방향 (asc/desc) |

**요청 예시**
```
GET /api/v1/proposals?sortBy=updatedAt&sortOrder=desc
```

### 7.3 검색

```
GET /api/v1/bids?keyword=SI&searchField=title
```

---

## 8. SSE 스트리밍 (Server-Sent Events)

제안서 AI 생성 등 장시간 실행되는 작업은 SSE를 통해 실시간 진행 상황을 전달합니다.

### 8.1 엔드포인트

```
GET /api/v1/proposals/{id}/generate/stream
```

### 8.2 요청 헤더

```
Accept: text/event-stream
Authorization: Bearer <access_token>
```

### 8.3 이벤트 형식

**이벤트 타입**

| Event | 설명 |
|-------|------|
| progress | 진행 상황 업데이트 |
| section | 섹션 생성 완료 |
| complete | 전체 생성 완료 |
| error | 오류 발생 |

**진행 상황 이벤트**
```
event: progress
data: {"percent": 30, "message": "사업 개요 섹션 생성 중..."}

event: progress
data: {"percent": 60, "message": "수행 계획 섹션 생성 중..."}
```

**섹션 완료 이벤트**
```
event: section
data: {
  "sectionId": "overview",
  "title": "사업 개요",
  "content": "# 사업 개요\n\n본 제안서는...",
  "wordCount": 520
}
```

**전체 완료 이벤트**
```
event: complete
data: {
  "proposalId": 123,
  "totalSections": 8,
  "totalWordCount": 4500,
  "generatedAt": "2026-03-01T10:35:00Z"
}
```

**오류 이벤트**
```
event: error
data: {
  "code": "PROPOSAL_004",
  "message": "AI 생성 시간이 초과되었습니다."
}
```

### 8.4 클라이언트 연결 예시

```typescript
const eventSource = new EventSource(
  '/api/v1/proposals/123/generate/stream',
  { headers: { Authorization: `Bearer ${token}` } }
);

eventSource.addEventListener('progress', (e) => {
  const data = JSON.parse(e.data);
  updateProgressBar(data.percent, data.message);
});

eventSource.addEventListener('section', (e) => {
  const data = JSON.parse(e.data);
  renderSection(data);
});

eventSource.addEventListener('complete', (e) => {
  const data = JSON.parse(e.data);
  showCompletionNotice(data);
  eventSource.close();
});

eventSource.addEventListener('error', (e) => {
  const data = JSON.parse(e.data);
  showError(data.message);
  eventSource.close();
});
```

---

## 9. 파일 업로드

### 9.1 업로드 방식

**Multipart Form Data**
```
POST /api/v1/upload
Content-Type: multipart/form-data

file: (binary)
type: "proposal" | "certificate" | "performance"
```

### 9.2 파일 제한

| 항목 | 제한 |
|------|------|
| 최대 크기 | 10MB |
| 허용 확장자 | PDF, HWP, DOCX, XLSX, PNG, JPG |
| 파일명 길이 | 255자 |

### 9.3 응답

```json
{
  "success": true,
  "data": {
    "fileId": "abc123",
    "url": "https://storage.bidmaster.kr/files/abc123.pdf",
    "fileName": "제안서_초안.pdf",
    "fileSize": 2048576,
    "mimeType": "application/pdf"
  }
}
```

---

## 10. Rate Limiting

### 10.1 기본 제한

| 대상 | 제한 | 윈도우 |
|------|------|--------|
| 일반 API | 100회 | 1분 |
| 인증 API | 10회 | 1분 |
| AI 생성 | 10회 | 1시간 |
| 파일 업로드 | 20회 | 1시간 |

### 10.2 응답 헤더

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1709304060
```

### 10.3 제한 초과 응답

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_001",
    "message": "요청 횟수를 초과했습니다. 30초 후 다시 시도해주세요."
  }
}
```

---

## 11. API 엔드포인트 네이밍 규칙

### 11.1 리소스 명명

- 복수형 명사 사용: `/users`, `/proposals`, `/bids`
- kebab-case 사용: `/company-profiles`, `/bid-matches`
- 중첩 리소스: `/companies/{id}/performances`

### 11.2 액션 엔드포인트

동사가 필요한 경우 리소스 뒤에 배치:
```
POST /api/v1/proposals/{id}/generate
POST /api/v1/bids/{id}/match
POST /api/v1/auth/logout
```

### 11.3 HTTP 메서드 사용

| Method | 용도 | 멱등성 |
|--------|------|--------|
| GET | 조회 | O |
| POST | 생성 | X |
| PUT | 전체 수정 | O |
| PATCH | 부분 수정 | O |
| DELETE | 삭제 | O |

---

## 12. 구현 가이드

### 12.1 FastAPI 응답 래퍼

```python
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    error: Optional[dict] = None
    meta: Optional[dict] = None

class ApiError(BaseModel):
    code: str
    message: str
    details: Optional[dict[str, list[str]]] = None
```

### 12.2 커스텀 예외 클래스

```python
class AppException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: dict | None = None
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details

# 사용 예시
raise AppException(
    code="AUTH_001",
    message="이메일 또는 비밀번호가 올바르지 않습니다.",
    status_code=401
)
```

### 12.3 전역 예외 핸들러

```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )
```

---

## 변경 이력

| 날짜 | 변경 내용 | 작성자 |
|------|-----------|--------|
| 2026-03-01 | 초안 작성 | architect |
