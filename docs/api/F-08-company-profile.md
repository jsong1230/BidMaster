# F-08 회사 프로필 관리 API 스펙 (확정본)

## 개요

- Base URL: `/api/v1/companies`
- 인증: Bearer JWT (모든 엔드포인트)
- 응답 형식: `{ success: bool, data?: any, error?: { code, message }, meta?: any }`

---

## 에러 코드 목록

| 코드 | HTTP 상태 | 설명 |
|------|-----------|------|
| AUTH_002 | 401 | 인증 토큰 없음 또는 만료 |
| COMPANY_001 | 404 | 회사를 찾을 수 없음 |
| COMPANY_002 | 409 | 사업자등록번호 중복 |
| COMPANY_003 | 400 | 사업자등록번호 형식/체크섬 오류 |
| COMPANY_004 | 409 | 이미 다른 회사에 소속된 사용자 |
| COMPANY_005 | 404 | 수행 실적을 찾을 수 없음 |
| COMPANY_006 | 404 | 보유 인증을 찾을 수 없음 |
| COMPANY_007 | 400 | 대표 실적 초과 (최대 3개) |
| COMPANY_008 | 404 | 초대 대상 이메일을 시스템에서 찾을 수 없음 |
| COMPANY_009 | 409 | 이미 해당 회사 멤버인 사용자 |
| COMPANY_010 | 409 | 다른 회사에 소속된 사용자 초대 불가 |
| PERMISSION_001 | 403 | 접근 권한 없음 (비멤버) |
| PERMISSION_003 | 403 | 멤버 초대 권한 없음 (member 역할) |
| VALIDATION_001 | 400 | 잘못된 요청 형식 |

---

## 1. 회사 등록

### `POST /api/v1/companies`

회사 프로필을 등록합니다. 등록자는 자동으로 `owner` 역할이 됩니다.

**요청 헤더**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**요청 바디**
```json
{
  "businessNumber": "string (10자리 숫자, 체크섬 검증)",
  "name": "string (최대 200자)",
  "ceoName": "string",
  "address": "string (optional)",
  "phone": "string (optional)",
  "industry": "string (optional)",
  "scale": "string (optional)",
  "description": "string (optional)"
}
```

**응답 201 Created**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "businessNumber": "string",
    "name": "string",
    "ceoName": "string",
    "address": "string|null",
    "phone": "string|null",
    "industry": "string|null",
    "scale": "string|null",
    "description": "string|null",
    "createdAt": "ISO8601"
  }
}
```

**에러 응답**
- 401: AUTH_002 (미인증)
- 400: COMPANY_003 (사업자등록번호 형식 오류)
- 409: COMPANY_002 (사업자등록번호 중복)
- 409: COMPANY_004 (이미 소속된 사용자)

---

## 2. 내 회사 조회

### `GET /api/v1/companies/my`

현재 로그인한 사용자의 소속 회사 프로필을 조회합니다.

**응답 200 OK**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "businessNumber": "string",
    "name": "string",
    "ceoName": "string",
    "address": "string|null",
    "phone": "string|null",
    "industry": "string|null",
    "scale": "string|null",
    "description": "string|null",
    "memberCount": 0,
    "performanceCount": 0,
    "certificationCount": 0,
    "createdAt": "ISO8601",
    "updatedAt": "ISO8601"
  }
}
```

**에러 응답**
- 401: AUTH_002 (미인증)
- 404: COMPANY_001 (미소속 또는 회사 없음)

---

## 3. 회사 정보 수정

### `PUT /api/v1/companies/{company_id}`

회사 정보를 수정합니다. `owner` 또는 `admin`만 가능합니다.
`businessNumber`는 수정 불가 (요청에 포함되어도 무시).

**경로 파라미터**
- `company_id`: uuid

**요청 바디** (모든 필드 optional)
```json
{
  "name": "string",
  "ceoName": "string",
  "address": "string",
  "phone": "string",
  "industry": "string",
  "scale": "string",
  "description": "string"
}
```

**응답 200 OK**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "businessNumber": "string",
    "name": "string",
    "ceoName": "string",
    "address": "string|null",
    "phone": "string|null",
    "industry": "string|null",
    "scale": "string|null",
    "description": "string|null",
    "updatedAt": "ISO8601"
  }
}
```

**에러 응답**
- 401: AUTH_002
- 403: PERMISSION_001 (비멤버 또는 member 역할)
- 404: COMPANY_001 (회사 없음)

---

## 4. 수행 실적 등록

### `POST /api/v1/companies/{company_id}/performances`

수행 실적을 등록합니다. 회사 멤버만 가능합니다.
대표 실적은 최대 3개까지 지정 가능합니다.

**요청 바디**
```json
{
  "projectName": "string",
  "clientName": "string",
  "clientType": "string (public|private)",
  "contractAmount": 0,
  "startDate": "YYYY-MM-DD",
  "endDate": "YYYY-MM-DD",
  "status": "string (ongoing|completed)",
  "description": "string (optional)",
  "isRepresentative": false,
  "documentUrl": "string (optional)"
}
```

**응답 201 Created**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "companyId": "uuid",
    "projectName": "string",
    "clientName": "string",
    "clientType": "string",
    "contractAmount": 0,
    "startDate": "YYYY-MM-DD",
    "endDate": "YYYY-MM-DD",
    "status": "string",
    "description": "string|null",
    "isRepresentative": false,
    "documentUrl": "string|null",
    "createdAt": "ISO8601"
  }
}
```

**에러 응답**
- 401: AUTH_002
- 403: PERMISSION_001 (비멤버)
- 400: COMPANY_007 (대표 실적 3개 초과)

---

## 5. 수행 실적 목록 조회

### `GET /api/v1/companies/{company_id}/performances`

수행 실적 목록을 조회합니다. 회사 멤버만 가능합니다.

**쿼리 파라미터**
| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| page | int | 1 | 페이지 번호 |
| pageSize | int | 20 | 페이지 크기 |
| status | string | - | 상태 필터 (ongoing\|completed) |
| isRepresentative | bool | - | 대표 실적 필터 |
| sort | string | - | 정렬 (contractAmount_desc 등) |

**응답 200 OK**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "projectName": "string",
        "clientName": "string",
        "clientType": "string",
        "contractAmount": 0,
        "startDate": "YYYY-MM-DD",
        "endDate": "YYYY-MM-DD",
        "status": "string",
        "isRepresentative": false,
        "createdAt": "ISO8601"
      }
    ]
  },
  "meta": {
    "page": 1,
    "pageSize": 20,
    "total": 0,
    "totalPages": 0
  }
}
```

---

## 6. 수행 실적 수정

### `PUT /api/v1/companies/{company_id}/performances/{perf_id}`

수행 실적을 수정합니다. `owner` 또는 `admin`만 가능합니다.

**응답 200 OK**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "companyId": "uuid",
    "projectName": "string",
    "clientName": "string",
    "contractAmount": 0,
    "status": "string",
    "isRepresentative": false,
    "updatedAt": "ISO8601"
  }
}
```

---

## 7. 수행 실적 삭제

### `DELETE /api/v1/companies/{company_id}/performances/{perf_id}`

수행 실적을 소프트 삭제합니다. `owner` 또는 `admin`만 가능합니다.

**응답 200 OK**
```json
{
  "success": true,
  "data": null
}
```

---

## 8. 대표 실적 지정/해제

### `PATCH /api/v1/companies/{company_id}/performances/{perf_id}/representative`

특정 실적의 대표 실적 여부를 변경합니다. `owner` 또는 `admin`만 가능합니다.

**요청 바디**
```json
{
  "isRepresentative": true
}
```

**응답 200 OK**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "projectName": "string",
    "isRepresentative": true,
    "updatedAt": "ISO8601"
  }
}
```

---

## 9. 보유 인증 등록

### `POST /api/v1/companies/{company_id}/certifications`

보유 인증을 등록합니다. 회사 멤버만 가능합니다.

**요청 바디**
```json
{
  "name": "string",
  "issuer": "string",
  "certNumber": "string",
  "issuedDate": "YYYY-MM-DD",
  "expiryDate": "YYYY-MM-DD (optional)",
  "documentUrl": "string (optional)"
}
```

**응답 201 Created**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "companyId": "uuid",
    "name": "string",
    "issuer": "string",
    "certNumber": "string",
    "issuedDate": "YYYY-MM-DD",
    "expiryDate": "YYYY-MM-DD|null",
    "documentUrl": "string|null",
    "createdAt": "ISO8601"
  }
}
```

---

## 10. 보유 인증 목록 조회

### `GET /api/v1/companies/{company_id}/certifications`

보유 인증 목록을 조회합니다. 회사 멤버만 가능합니다.

**쿼리 파라미터**
| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| page | int | 1 | 페이지 번호 |
| pageSize | int | 20 | 페이지 크기 |
| sort | string | - | 정렬 (expiryDate_asc 등) |

**응답 200 OK**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "name": "string",
        "issuer": "string",
        "certNumber": "string",
        "issuedDate": "YYYY-MM-DD",
        "expiryDate": "YYYY-MM-DD|null",
        "documentUrl": "string|null",
        "isExpired": false,
        "createdAt": "ISO8601"
      }
    ]
  },
  "meta": {
    "page": 1,
    "pageSize": 20,
    "total": 0,
    "totalPages": 0
  }
}
```

---

## 11. 보유 인증 수정

### `PUT /api/v1/companies/{company_id}/certifications/{cert_id}`

보유 인증을 수정합니다. `owner` 또는 `admin`만 가능합니다.

**응답 200 OK**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "companyId": "uuid",
    "name": "string",
    "issuer": "string",
    "certNumber": "string",
    "issuedDate": "YYYY-MM-DD",
    "expiryDate": "YYYY-MM-DD|null",
    "documentUrl": "string|null",
    "updatedAt": "ISO8601"
  }
}
```

---

## 12. 보유 인증 삭제

### `DELETE /api/v1/companies/{company_id}/certifications/{cert_id}`

보유 인증을 소프트 삭제합니다. `owner` 또는 `admin`만 가능합니다.

**응답 200 OK**
```json
{
  "success": true,
  "data": null
}
```

---

## 13. 멤버 초대

### `POST /api/v1/companies/{company_id}/members`

새 멤버를 회사에 초대합니다. `owner` 또는 `admin`만 가능합니다.
`owner` 역할은 지정 불가 (`admin`, `member`만 가능).

**요청 바디**
```json
{
  "email": "string",
  "role": "admin|member"
}
```

**응답 201 Created**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "companyId": "uuid",
    "userId": "uuid",
    "email": "string",
    "name": "string",
    "role": "string",
    "invitedAt": "ISO8601",
    "joinedAt": "ISO8601|null"
  }
}
```

**에러 응답**
- 401: AUTH_002
- 403: PERMISSION_003 (member 역할은 초대 불가)
- 404: COMPANY_008 (이메일로 사용자를 찾을 수 없음)
- 409: COMPANY_009 (이미 해당 회사 멤버)
- 409: COMPANY_010 (다른 회사 소속 사용자)

---

## 14. 멤버 목록 조회

### `GET /api/v1/companies/{company_id}/members`

회사 멤버 목록을 조회합니다. 회사 멤버만 가능합니다.

**쿼리 파라미터**
| 파라미터 | 타입 | 기본값 |
|---------|------|--------|
| page | int | 1 |
| pageSize | int | 20 |

**응답 200 OK**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "userId": "uuid",
        "email": "string",
        "name": "string",
        "role": "owner|admin|member",
        "joinedAt": "ISO8601"
      }
    ]
  },
  "meta": {
    "page": 1,
    "pageSize": 20,
    "total": 0,
    "totalPages": 0
  }
}
```

**에러 응답**
- 401: AUTH_002
- 403: PERMISSION_001 (비멤버)
