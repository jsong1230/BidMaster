"""회사 프로필 API 엔드포인트"""
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from src.core.security import AuthError, ValidationError, decode_token
from src.services.company_service import (
    AppException,
    CompanyService,
    _register_user,
)

router = APIRouter()


# ----------------------------------------------------------------
# 의존성: 현재 사용자 정보 추출
# ----------------------------------------------------------------

def get_current_user_payload(request: Request) -> dict[str, Any]:
    """
    Authorization 헤더에서 JWT 토큰을 디코딩하여 payload 반환

    Raises:
        AuthError: AUTH_002(401) - 인증 토큰 없음
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise AuthError("AUTH_002", "인증 토큰이 필요합니다.", 401)

    token = auth_header[len("Bearer "):]
    payload = decode_token(token)
    return payload


def get_company_service() -> CompanyService:
    """CompanyService 인스턴스 반환"""
    return CompanyService(db=None)


def _get_user_id(payload: dict[str, Any]) -> str:
    """JWT payload에서 user_id 추출 (str 보장)"""
    return str(payload.get("sub") or "")


def _parse_page_params(params: dict[str, str]) -> tuple[int, int]:
    """page, pageSize 파라미터 파싱 및 검증"""
    try:
        page = int(params.get("page", 1))
    except ValueError:
        page = 1
    try:
        page_size = int(params.get("pageSize", 20))
    except ValueError:
        page_size = 20
    page = max(1, page)
    page_size = max(1, min(100, page_size))
    return page, page_size


# ----------------------------------------------------------------
# 에러 응답 헬퍼
# ----------------------------------------------------------------

def error_response(code: str, message: str, status_code: int) -> JSONResponse:
    """표준 에러 응답 생성"""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {"code": code, "message": message},
        },
    )


def success_response(data: Any, status_code: int = 200) -> JSONResponse:
    """표준 성공 응답 생성"""
    return JSONResponse(
        status_code=status_code,
        content={"success": True, "data": data},
    )


def _obj_to_dict(obj: Any) -> dict[str, Any]:
    """응답 객체를 dict로 변환 (camelCase)"""
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    result: dict[str, Any] = {}
    for attr in dir(obj):
        if not attr.startswith("_"):
            val = getattr(obj, attr)
            if callable(val):
                continue
            # snake_case → camelCase 변환
            parts = attr.split("_")
            key = parts[0] + "".join(p.capitalize() for p in parts[1:])
            # datetime을 ISO 문자열로 변환
            if hasattr(val, "isoformat"):
                val = val.isoformat()
            result[key] = val
    return result


# ----------------------------------------------------------------
# 회사 등록 POST /api/v1/companies
# ----------------------------------------------------------------

@router.post("")
async def create_company(request: Request) -> JSONResponse:
    """회사 등록 (201 Created)"""
    try:
        payload = get_current_user_payload(request)
    except AuthError as e:
        return error_response(e.code, e.message, e.status_code)

    user_id = _get_user_id(payload)
    company_id_from_token = payload.get("company_id")

    # JWT에 company_id가 있으면 이미 소속된 사용자
    if company_id_from_token:
        return error_response("COMPANY_004", "회사 프로필이 이미 존재합니다.", 409)

    try:
        body = await request.json()
    except Exception:
        return error_response("VALIDATION_001", "잘못된 요청 형식입니다.", 400)

    service = get_company_service()

    try:
        company = await service.create_company(user_id=user_id, data=body)
        return success_response(
            data={
                "id": str(company.id),
                "businessNumber": company.business_number,
                "name": company.name,
                "ceoName": company.ceo_name,
                "address": company.address,
                "phone": company.phone,
                "industry": company.industry,
                "scale": company.scale,
                "description": company.description,
                "createdAt": company.created_at.isoformat() if company.created_at else None,
            },
            status_code=201,
        )
    except ValidationError as e:
        return error_response(e.code, e.message, e.status_code)
    except AppException as e:
        return error_response(e.code, e.message, e.status_code)


# ----------------------------------------------------------------
# 내 회사 조회 GET /api/v1/companies/my
# ----------------------------------------------------------------

@router.get("/my")
async def get_my_company(request: Request) -> JSONResponse:
    """내 회사 조회 (200 OK)"""
    try:
        payload = get_current_user_payload(request)
    except AuthError as e:
        return error_response(e.code, e.message, e.status_code)

    user_id = _get_user_id(payload)
    company_id_from_token = payload.get("company_id")

    if not company_id_from_token:
        return error_response("COMPANY_001", "회사를 찾을 수 없습니다.", 404)

    service = get_company_service()

    # JWT company_id로 user 정보를 서비스 store에 등록
    mock_user_obj = type("U", (), {"id": user_id, "company_id": company_id_from_token})()
    _register_user(mock_user_obj)

    try:
        result = await service.get_my_company(user_id=user_id)
        return success_response(
            data={
                "id": str(result.id),
                "businessNumber": result.business_number,
                "name": result.name,
                "ceoName": result.ceo_name,
                "address": result.address,
                "phone": result.phone,
                "industry": result.industry,
                "scale": result.scale,
                "description": result.description,
                "memberCount": result.member_count,
                "performanceCount": result.performance_count,
                "certificationCount": result.certification_count,
                "createdAt": result.created_at.isoformat() if result.created_at else None,
                "updatedAt": result.updated_at.isoformat() if result.updated_at else None,
            }
        )
    except AppException as e:
        return error_response(e.code, e.message, e.status_code)


# ----------------------------------------------------------------
# 회사 수정 PUT /api/v1/companies/{company_id}
# ----------------------------------------------------------------

@router.put("/{company_id}")
async def update_company(company_id: str, request: Request) -> JSONResponse:
    """회사 정보 수정 (200 OK)"""
    try:
        payload = get_current_user_payload(request)
    except AuthError as e:
        return error_response(e.code, e.message, e.status_code)

    user_id = _get_user_id(payload)

    try:
        body = await request.json()
    except Exception:
        return error_response("VALIDATION_001", "잘못된 요청 형식입니다.", 400)

    service = get_company_service()

    try:
        company = await service.update_company(
            company_id=company_id,
            user_id=user_id,
            data=body,
        )
        return success_response(
            data={
                "id": str(company.id),
                "businessNumber": company.business_number,
                "name": company.name,
                "ceoName": company.ceo_name,
                "address": company.address,
                "phone": company.phone,
                "industry": company.industry,
                "scale": company.scale,
                "description": company.description,
                "updatedAt": company.updated_at.isoformat() if company.updated_at else None,
            }
        )
    except AppException as e:
        return error_response(e.code, e.message, e.status_code)
    except ValidationError as e:
        return error_response(e.code, e.message, e.status_code)


# ----------------------------------------------------------------
# 수행 실적 등록 POST /api/v1/companies/{company_id}/performances
# ----------------------------------------------------------------

@router.post("/{company_id}/performances")
async def create_performance(company_id: str, request: Request) -> JSONResponse:
    """수행 실적 등록 (201 Created)"""
    try:
        payload = get_current_user_payload(request)
    except AuthError as e:
        return error_response(e.code, e.message, e.status_code)

    user_id = _get_user_id(payload)

    try:
        body = await request.json()
    except Exception:
        return error_response("VALIDATION_001", "잘못된 요청 형식입니다.", 400)

    service = get_company_service()

    try:
        perf = await service.create_performance(
            company_id=company_id,
            user_id=user_id,
            data=body,
        )
        return success_response(
            data={
                "id": str(perf.id),
                "companyId": str(perf.company_id),
                "projectName": perf.project_name,
                "clientName": perf.client_name,
                "clientType": perf.client_type,
                "contractAmount": perf.contract_amount,
                "startDate": perf.start_date,
                "endDate": perf.end_date,
                "status": perf.status,
                "description": perf.description,
                "isRepresentative": perf.is_representative,
                "documentUrl": perf.document_url,
                "createdAt": perf.created_at.isoformat() if perf.created_at else None,
            },
            status_code=201,
        )
    except AppException as e:
        return error_response(e.code, e.message, e.status_code)
    except ValidationError as e:
        return error_response(e.code, e.message, e.status_code)


# ----------------------------------------------------------------
# 수행 실적 목록 GET /api/v1/companies/{company_id}/performances
# ----------------------------------------------------------------

@router.get("/{company_id}/performances")
async def list_performances(company_id: str, request: Request) -> JSONResponse:
    """수행 실적 목록 조회 (200 OK)"""
    try:
        payload = get_current_user_payload(request)
    except AuthError as e:
        return error_response(e.code, e.message, e.status_code)

    user_id = _get_user_id(payload)
    params = dict(request.query_params)
    page, page_size = _parse_page_params(params)
    filters: dict[str, Any] = {}
    if "status" in params:
        filters["status"] = params["status"]
    if "isRepresentative" in params:
        filters["is_representative"] = params["isRepresentative"].lower() == "true"

    service = get_company_service()

    try:
        result = await service.list_performances(
            company_id=company_id,
            user_id=user_id,
            filters=filters,
            page=page,
            page_size=page_size,
        )
        items = [
            {
                "id": str(p.id),
                "projectName": p.project_name,
                "clientName": p.client_name,
                "clientType": p.client_type,
                "contractAmount": p.contract_amount,
                "startDate": p.start_date,
                "endDate": p.end_date,
                "status": p.status,
                "isRepresentative": p.is_representative,
                "createdAt": p.created_at.isoformat() if p.created_at else None,
            }
            for p in result["items"]
        ]
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {"items": items},
                "meta": result["meta"],
            },
        )
    except AppException as e:
        return error_response(e.code, e.message, e.status_code)


# ----------------------------------------------------------------
# 수행 실적 수정 PUT /api/v1/companies/{company_id}/performances/{perf_id}
# ----------------------------------------------------------------

@router.put("/{company_id}/performances/{perf_id}")
async def update_performance(
    company_id: str, perf_id: str, request: Request
) -> JSONResponse:
    """수행 실적 수정 (200 OK)"""
    try:
        payload = get_current_user_payload(request)
    except AuthError as e:
        return error_response(e.code, e.message, e.status_code)

    user_id = _get_user_id(payload)

    try:
        body = await request.json()
    except Exception:
        return error_response("VALIDATION_001", "잘못된 요청 형식입니다.", 400)

    service = get_company_service()

    try:
        perf = await service.update_performance(
            company_id=company_id,
            perf_id=perf_id,
            user_id=user_id,
            data=body,
        )
        return success_response(
            data={
                "id": str(perf.id),
                "companyId": str(perf.company_id),
                "projectName": perf.project_name,
                "clientName": perf.client_name,
                "contractAmount": perf.contract_amount,
                "status": perf.status,
                "isRepresentative": perf.is_representative,
                "updatedAt": perf.updated_at.isoformat() if perf.updated_at else None,
            }
        )
    except AppException as e:
        return error_response(e.code, e.message, e.status_code)
    except ValidationError as e:
        return error_response(e.code, e.message, e.status_code)


# ----------------------------------------------------------------
# 수행 실적 삭제 DELETE /api/v1/companies/{company_id}/performances/{perf_id}
# ----------------------------------------------------------------

@router.delete("/{company_id}/performances/{perf_id}")
async def delete_performance(
    company_id: str, perf_id: str, request: Request
) -> JSONResponse:
    """수행 실적 소프트 삭제 (200 OK)"""
    try:
        payload = get_current_user_payload(request)
    except AuthError as e:
        return error_response(e.code, e.message, e.status_code)

    user_id = _get_user_id(payload)
    service = get_company_service()

    try:
        await service.delete_performance(
            company_id=company_id,
            perf_id=perf_id,
            user_id=user_id,
        )
        return success_response(data=None)
    except AppException as e:
        return error_response(e.code, e.message, e.status_code)


# ----------------------------------------------------------------
# 대표 실적 지정/해제 PATCH /{company_id}/performances/{perf_id}/representative
# ----------------------------------------------------------------

@router.patch("/{company_id}/performances/{perf_id}/representative")
async def set_representative(
    company_id: str, perf_id: str, request: Request
) -> JSONResponse:
    """대표 실적 지정/해제 (200 OK)"""
    try:
        payload = get_current_user_payload(request)
    except AuthError as e:
        return error_response(e.code, e.message, e.status_code)

    user_id = _get_user_id(payload)

    try:
        body = await request.json()
    except Exception:
        return error_response("VALIDATION_001", "잘못된 요청 형식입니다.", 400)

    is_representative = body.get("isRepresentative", False)
    service = get_company_service()

    try:
        perf = await service.set_representative(
            company_id=company_id,
            perf_id=perf_id,
            user_id=user_id,
            is_representative=is_representative,
        )
        return success_response(
            data={
                "id": str(perf.id),
                "projectName": perf.project_name,
                "isRepresentative": perf.is_representative,
                "updatedAt": perf.updated_at.isoformat() if perf.updated_at else None,
            }
        )
    except AppException as e:
        return error_response(e.code, e.message, e.status_code)


# ----------------------------------------------------------------
# 보유 인증 등록 POST /api/v1/companies/{company_id}/certifications
# ----------------------------------------------------------------

@router.post("/{company_id}/certifications")
async def create_certification(company_id: str, request: Request) -> JSONResponse:
    """보유 인증 등록 (201 Created)"""
    try:
        payload = get_current_user_payload(request)
    except AuthError as e:
        return error_response(e.code, e.message, e.status_code)

    user_id = _get_user_id(payload)

    try:
        body = await request.json()
    except Exception:
        return error_response("VALIDATION_001", "잘못된 요청 형식입니다.", 400)

    service = get_company_service()

    try:
        cert = await service.create_certification(
            company_id=company_id,
            user_id=user_id,
            data=body,
        )
        return success_response(
            data={
                "id": str(cert.id),
                "companyId": str(cert.company_id),
                "name": cert.name,
                "issuer": cert.issuer,
                "certNumber": cert.cert_number,
                "issuedDate": cert.issued_date,
                "expiryDate": cert.expiry_date,
                "documentUrl": cert.document_url,
                "createdAt": cert.created_at.isoformat() if cert.created_at else None,
            },
            status_code=201,
        )
    except AppException as e:
        return error_response(e.code, e.message, e.status_code)
    except ValidationError as e:
        return error_response(e.code, e.message, e.status_code)


# ----------------------------------------------------------------
# 보유 인증 목록 GET /api/v1/companies/{company_id}/certifications
# ----------------------------------------------------------------

@router.get("/{company_id}/certifications")
async def list_certifications(company_id: str, request: Request) -> JSONResponse:
    """보유 인증 목록 조회 (200 OK)"""
    try:
        payload = get_current_user_payload(request)
    except AuthError as e:
        return error_response(e.code, e.message, e.status_code)

    user_id = _get_user_id(payload)
    params = dict(request.query_params)
    page, page_size = _parse_page_params(params)

    service = get_company_service()

    try:
        result = await service.list_certifications(
            company_id=company_id,
            user_id=user_id,
            page=page,
            page_size=page_size,
        )
        items = [
            {
                "id": str(item["cert"].id),
                "name": item["cert"].name,
                "issuer": item["cert"].issuer,
                "certNumber": item["cert"].cert_number,
                "issuedDate": item["cert"].issued_date,
                "expiryDate": item["cert"].expiry_date,
                "documentUrl": item["cert"].document_url,
                "isExpired": item["is_expired"],
                "createdAt": item["cert"].created_at.isoformat() if item["cert"].created_at else None,
            }
            for item in result["items"]
        ]
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {"items": items},
                "meta": result["meta"],
            },
        )
    except AppException as e:
        return error_response(e.code, e.message, e.status_code)


# ----------------------------------------------------------------
# 보유 인증 수정 PUT /api/v1/companies/{company_id}/certifications/{cert_id}
# ----------------------------------------------------------------

@router.put("/{company_id}/certifications/{cert_id}")
async def update_certification(
    company_id: str, cert_id: str, request: Request
) -> JSONResponse:
    """보유 인증 수정 (200 OK)"""
    try:
        payload = get_current_user_payload(request)
    except AuthError as e:
        return error_response(e.code, e.message, e.status_code)

    user_id = _get_user_id(payload)

    try:
        body = await request.json()
    except Exception:
        return error_response("VALIDATION_001", "잘못된 요청 형식입니다.", 400)

    service = get_company_service()

    try:
        cert = await service.update_certification(
            company_id=company_id,
            cert_id=cert_id,
            user_id=user_id,
            data=body,
        )
        return success_response(
            data={
                "id": str(cert.id),
                "companyId": str(cert.company_id),
                "name": cert.name,
                "issuer": cert.issuer,
                "certNumber": cert.cert_number,
                "issuedDate": cert.issued_date,
                "expiryDate": cert.expiry_date,
                "documentUrl": cert.document_url,
                "updatedAt": cert.updated_at.isoformat() if cert.updated_at else None,
            }
        )
    except AppException as e:
        return error_response(e.code, e.message, e.status_code)
    except ValidationError as e:
        return error_response(e.code, e.message, e.status_code)


# ----------------------------------------------------------------
# 보유 인증 삭제 DELETE /api/v1/companies/{company_id}/certifications/{cert_id}
# ----------------------------------------------------------------

@router.delete("/{company_id}/certifications/{cert_id}")
async def delete_certification(
    company_id: str, cert_id: str, request: Request
) -> JSONResponse:
    """보유 인증 소프트 삭제 (200 OK)"""
    try:
        payload = get_current_user_payload(request)
    except AuthError as e:
        return error_response(e.code, e.message, e.status_code)

    user_id = _get_user_id(payload)
    service = get_company_service()

    try:
        await service.delete_certification(
            company_id=company_id,
            cert_id=cert_id,
            user_id=user_id,
        )
        return success_response(data=None)
    except AppException as e:
        return error_response(e.code, e.message, e.status_code)


# ----------------------------------------------------------------
# 멤버 초대 POST /api/v1/companies/{company_id}/members
# ----------------------------------------------------------------

@router.post("/{company_id}/members")
async def invite_member(company_id: str, request: Request) -> JSONResponse:
    """멤버 초대 (201 Created)"""
    try:
        payload = get_current_user_payload(request)
    except AuthError as e:
        return error_response(e.code, e.message, e.status_code)

    user_id = _get_user_id(payload)

    try:
        body = await request.json()
    except Exception:
        return error_response("VALIDATION_001", "잘못된 요청 형식입니다.", 400)

    target_email = body.get("email", "")
    role = body.get("role", "member")

    service = get_company_service()

    try:
        member = await service.invite_member(
            company_id=company_id,
            inviter_user_id=user_id,
            target_email=target_email,
            role=role,
        )
        return success_response(
            data={
                "id": str(member.id),
                "companyId": str(member.company_id),
                "userId": str(member.user_id),
                "email": getattr(member, "email", ""),
                "name": getattr(member, "name", ""),
                "role": member.role,
                "invitedAt": member.invited_at.isoformat() if member.invited_at else None,
                "joinedAt": member.joined_at.isoformat() if member.joined_at else None,
            },
            status_code=201,
        )
    except AppException as e:
        return error_response(e.code, e.message, e.status_code)
    except ValidationError as e:
        return error_response(e.code, e.message, e.status_code)


# ----------------------------------------------------------------
# 멤버 목록 GET /api/v1/companies/{company_id}/members
# ----------------------------------------------------------------

@router.get("/{company_id}/members")
async def list_members(company_id: str, request: Request) -> JSONResponse:
    """멤버 목록 조회 (200 OK)"""
    try:
        payload = get_current_user_payload(request)
    except AuthError as e:
        return error_response(e.code, e.message, e.status_code)

    user_id = _get_user_id(payload)
    params = dict(request.query_params)
    page, page_size = _parse_page_params(params)

    service = get_company_service()

    try:
        result = await service.list_members(
            company_id=company_id,
            user_id=user_id,
            page=page,
            page_size=page_size,
        )
        items = [
            {
                "id": str(m.id),
                "userId": str(m.user_id),
                "email": getattr(m, "email", ""),
                "name": getattr(m, "name", ""),
                "role": m.role,
                "joinedAt": m.joined_at.isoformat() if m.joined_at else None,
            }
            for m in result["items"]
        ]
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {"items": items},
                "meta": result["meta"],
            },
        )
    except AppException as e:
        return error_response(e.code, e.message, e.status_code)
