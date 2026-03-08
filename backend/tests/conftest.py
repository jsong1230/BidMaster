"""
테스트 설정 및 공통 Fixture
"""
import pytest
from typing import AsyncGenerator
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient, ASGITransport
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

# 임시 Mock 구현 - 구현 후 실제 모듈로 교체
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

class MockApp(FastAPI):
    """임시 FastAPI 앱 Mock"""

    def __init__(self):
        super().__init__()
        # 임시 라우트 추가 (테스트 실행을 위해)
        @self.get("/")
        async def root():
            return {"message": "Mock API"}

        # bids 라우터 포함 (F-01 통합 테스트용 — 501 mock 라우트보다 먼저 등록)
        try:
            from src.api.v1.bids import router as bids_router
            self.include_router(bids_router, prefix="/api/v1/bids")
        except ImportError:
            pass

        @self.post("/api/v1/auth/register")
        async def mock_register(request: Request):
            return JSONResponse(
                status_code=501,
                content={"success": False, "error": {"code": "NOT_IMPLEMENTED", "message": "Not implemented yet"}}
            )

        @self.post("/api/v1/auth/login")
        async def mock_login(request: Request):
            return JSONResponse(
                status_code=501,
                content={"success": False, "error": {"code": "NOT_IMPLEMENTED", "message": "Not implemented yet"}}
            )

        @self.post("/api/v1/auth/refresh")
        async def mock_refresh(request: Request):
            return JSONResponse(
                status_code=501,
                content={"success": False, "error": {"code": "NOT_IMPLEMENTED", "message": "Not implemented yet"}}
            )

        @self.post("/api/v1/auth/logout")
        async def mock_logout(request: Request):
            return JSONResponse(
                status_code=501,
                content={"success": False, "error": {"code": "NOT_IMPLEMENTED", "message": "Not implemented yet"}}
            )

        @self.get("/api/v1/auth/me")
        async def mock_me(request: Request):
            return JSONResponse(
                status_code=501,
                content={"success": False, "error": {"code": "NOT_IMPLEMENTED", "message": "Not implemented yet"}}
            )

        @self.get("/api/v1/auth/oauth/kakao")
        async def mock_oauth_kakao(request: Request):
            return Response(status_code=302, headers={"location": "https://kauth.kakao.com/oauth/authorize"})

        @self.get("/api/v1/auth/oauth/kakao/callback")
        async def mock_oauth_callback(request: Request):
            return JSONResponse(
                status_code=501,
                content={"success": False, "error": {"code": "NOT_IMPLEMENTED", "message": "Not implemented yet"}}
            )

        @self.post("/api/v1/auth/forgot-password")
        async def mock_forgot_password(request: Request):
            return JSONResponse(
                status_code=501,
                content={"success": False, "error": {"code": "NOT_IMPLEMENTED", "message": "Not implemented yet"}}
            )

        @self.post("/api/v1/auth/reset-password")
        async def mock_reset_password(request: Request):
            return JSONResponse(
                status_code=501,
                content={"success": False, "error": {"code": "NOT_IMPLEMENTED", "message": "Not implemented yet"}}
            )

        @self.post("/api/v1/auth/change-password")
        async def mock_change_password(request: Request):
            return JSONResponse(
                status_code=501,
                content={"success": False, "error": {"code": "NOT_IMPLEMENTED", "message": "Not implemented yet"}}
            )

        @self.delete("/api/v1/auth/me")
        async def mock_delete_account(request: Request):
            return JSONResponse(
                status_code=501,
                content={"success": False, "error": {"code": "NOT_IMPLEMENTED", "message": "Not implemented yet"}}
            )


class MockUser:
    """사용자 Mock"""
    def __init__(self, id=None, email=None, password_hash=None, name=None, phone=None, role=None, company_id=None):
        self.id = id or str(uuid4())
        self.email = email or "test@example.com"
        self.password_hash = password_hash
        self.name = name or "테스트사용자"
        self.phone = phone
        self.company_id = company_id  # 기본값 None (미소속)
        self.role = role or "owner"
        self.preferences: dict = {}
        self.last_login_at = None
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        self.deleted_at: datetime | None = None


class MockRefreshToken:
    """리프레시 토큰 Mock"""
    def __init__(
        self,
        id=None,
        user_id=None,
        token_hash=None,
        expires_at=None,
        is_revoked=False,
    ):
        self.id = id or str(uuid4())
        self.user_id = user_id or str(uuid4())
        self.token_hash = token_hash
        self.device_info = None
        self.ip_address = None
        self.expires_at = expires_at or datetime.now(timezone.utc) + timedelta(days=30)
        self.is_revoked = is_revoked
        self.created_at = datetime.now(timezone.utc)


class MockOAuthState:
    """OAuth State Mock"""
    def __init__(
        self,
        id=None,
        state=None,
        provider=None,
        redirect_url=None,
        expires_at=None,
    ):
        self.id = id or str(uuid4())
        self.state = state or str(uuid4())
        self.provider = provider or "kakao"
        self.redirect_url = redirect_url
        self.expires_at = expires_at or datetime.now(timezone.utc) + timedelta(minutes=10)
        self.created_at = datetime.now(timezone.utc)


class MockPasswordResetToken:
    """비밀번호 재설정 토큰 Mock"""
    def __init__(
        self,
        id=None,
        user_id=None,
        token_hash=None,
        expires_at=None,
        used_at=None,
    ):
        self.id = id or str(uuid4())
        self.user_id = user_id or str(uuid4())
        self.token_hash = token_hash
        self.expires_at = expires_at or datetime.now(timezone.utc) + timedelta(hours=1)
        self.used_at = used_at
        self.created_at = datetime.now(timezone.utc)


app = MockApp()


@pytest.fixture
def mock_app() -> FastAPI:
    """테스트용 FastAPI 앱 Fixture"""
    return app


# 에러 코드 정의
class AppError(Exception):
    """커스텀 에러 기본 클래스"""
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AuthError(AppError):
    """인증 관련 에러"""
    pass


class ValidationError(AppError):
    """유효성 검사 에러"""
    pass


# 에러 코드 상수
AUTH_001 = AuthError("AUTH_001", "이메일 또는 비밀번호가 올바르지 않습니다.", 401)
AUTH_002 = AuthError("AUTH_002", "인증 토큰이 필요합니다.", 401)
AUTH_003 = AuthError("AUTH_003", "토큰이 만료되었습니다.", 401)
AUTH_004 = AuthError("AUTH_004", "유효하지 않은 토큰입니다.", 401)
AUTH_005 = AuthError("AUTH_005", "로그아웃된 토큰입니다.", 401)
AUTH_006 = AuthError("AUTH_006", "리프레시 토큰이 유효하지 않습니다.", 401)
AUTH_007 = AuthError("AUTH_007", "이미 가입된 이메일입니다.", 409)
AUTH_008 = AuthError("AUTH_008", "비밀번호 재사용이 제한됩니다.", 400)
AUTH_009 = AuthError("AUTH_009", "카카오 OAuth 인증 실패", 401)
AUTH_010 = AuthError("AUTH_010", "탈퇴한 계정입니다.", 403)
AUTH_011 = AuthError("AUTH_011", "State 검증 실패 (CSRF)", 400)
AUTH_012 = AuthError("AUTH_012", "만료된 재설정 토큰입니다.", 400)
AUTH_013 = AuthError("AUTH_013", "이미 사용된 재설정 토큰입니다.", 400)

VALIDATION_001 = ValidationError("VALIDATION_001", "입력값 유효성 실패", 400)
VALIDATION_002 = ValidationError("VALIDATION_002", "필수 입력값 누락", 400)
VALIDATION_003 = ValidationError("VALIDATION_003", "입력값 길이 초과", 400)


@pytest.fixture
async def async_client(mock_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """
    테스트용 비동기 HTTP 클라이언트 Fixture
    """
    transport = ASGITransport(app=mock_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def auth_error_codes():
    """인증 에러 코드들"""
    return {
        "AUTH_001": AUTH_001,
        "AUTH_002": AUTH_002,
        "AUTH_003": AUTH_003,
        "AUTH_004": AUTH_004,
        "AUTH_005": AUTH_005,
        "AUTH_006": AUTH_006,
        "AUTH_007": AUTH_007,
        "AUTH_008": AUTH_008,
        "AUTH_009": AUTH_009,
        "AUTH_010": AUTH_010,
        "AUTH_011": AUTH_011,
        "AUTH_012": AUTH_012,
        "AUTH_013": AUTH_013,
    }


@pytest.fixture
def validation_error_codes():
    """유효성 검사 에러 코드들"""
    return {
        "VALIDATION_001": VALIDATION_001,
        "VALIDATION_002": VALIDATION_002,
        "VALIDATION_003": VALIDATION_003,
    }


@pytest.fixture
def mock_user():
    """테스트용 사용자 Mock Fixture"""
    user = MockUser(
        id=str(uuid4()),
        email="test@example.com",
        name="테스트사용자",
        phone="010-1234-5678",
    )
    user.company_id = None  # 기본값: 미소속
    try:
        from src.services.company_service import _register_user
        _register_user(user)
    except ImportError:
        pass
    return user


@pytest.fixture
def mock_kakao_user():
    """테스트용 카카오 사용자 Mock Fixture"""
    return MockUser(
        id=str(uuid4()),
        email="user@kakao.com",
        name="카카오사용자",
        phone=None,
    )


@pytest.fixture
def mock_admin_user():
    """테스트용 관리자 Mock Fixture"""
    return MockUser(
        id=str(uuid4()),
        email="admin@bidmaster.kr",
        name="관리자",
        role="admin",
    )


@pytest.fixture
def mock_deleted_user():
    """테스트용 삭제된 사용자 Mock Fixture"""
    user = MockUser(
        id=str(uuid4()),
        email="deleted@example.com",
        name="삭제된사용자",
    )
    user.deleted_at = datetime.now(timezone.utc)
    return user


@pytest.fixture
def mock_refresh_token():
    """테스트용 리프레시 토큰 Mock Fixture"""
    return MockRefreshToken(
        id=str(uuid4()),
        user_id=str(uuid4()),
        token_hash="hash_" + str(uuid4()),
    )


@pytest.fixture
def mock_expired_refresh_token():
    """테스트용 만료된 리프레시 토큰 Mock Fixture"""
    return MockRefreshToken(
        id=str(uuid4()),
        user_id=str(uuid4()),
        token_hash="expired_hash_" + str(uuid4()),
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
    )


@pytest.fixture
def mock_revoked_refresh_token():
    """테스트용 폐기된 리프레시 토큰 Mock Fixture"""
    return MockRefreshToken(
        id=str(uuid4()),
        user_id=str(uuid4()),
        token_hash="revoked_hash_" + str(uuid4()),
        is_revoked=True,
    )


@pytest.fixture
def mock_oauth_state():
    """테스트용 OAuth State Mock Fixture"""
    return MockOAuthState(
        id=str(uuid4()),
        state=str(uuid4()),
        provider="kakao",
    )


@pytest.fixture
def mock_expired_oauth_state():
    """테스트용 만료된 OAuth State Mock Fixture"""
    return MockOAuthState(
        id=str(uuid4()),
        state="expired_state",
        provider="kakao",
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=11),
    )


@pytest.fixture
def mock_password_reset_token():
    """테스트용 비밀번호 재설정 토큰 Mock Fixture"""
    return MockPasswordResetToken(
        id=str(uuid4()),
        user_id=str(uuid4()),
        token_hash="reset_hash_" + str(uuid4()),
    )


@pytest.fixture
def mock_expired_password_reset_token():
    """테스트용 만료된 비밀번호 재설정 토큰 Mock Fixture"""
    return MockPasswordResetToken(
        id=str(uuid4()),
        user_id=str(uuid4()),
        token_hash="expired_reset_hash_" + str(uuid4()),
        expires_at=datetime.now(timezone.utc) - timedelta(hours=2),
    )


@pytest.fixture
def mock_used_password_reset_token():
    """테스트용 사용된 비밀번호 재설정 토큰 Mock Fixture"""
    return MockPasswordResetToken(
        id=str(uuid4()),
        user_id=str(uuid4()),
        token_hash="used_reset_hash_" + str(uuid4()),
        used_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def test_user_data():
    """테스트용 사용자 데이터 Fixture"""
    return {
        "email": "test@example.com",
        "password": "SecureP@ss123",
        "name": "테스트사용자",
        "phone": "010-1234-5678",
    }


@pytest.fixture
def test_kakao_user_data():
    """테스트용 카카오 사용자 데이터 Fixture"""
    return {
        "kakao_id": "1234567890",
        "email": "user@kakao.com",
        "name": "카카오사용자",
    }


@pytest.fixture
def test_admin_data():
    """테스트용 관리자 데이터 Fixture"""
    return {
        "email": "admin@bidmaster.kr",
        "password": "AdminP@ss456",
        "name": "관리자",
        "role": "admin",
    }


@pytest.fixture
def mock_http_response():
    """테스트용 HTTP 응답 Mock Fixture"""
    def _create_response(
        status_code: int = 200,
        success: bool = True,
        data: dict | None = None,
        error: str | None = None,
    ):
        return {
            "status_code": status_code,
            "json": lambda: {
                "success": success,
                "data": data,
                "error": error,
            },
        }
    return _create_response


@pytest.fixture
def mock_auth_service():
    """AuthService Mock Fixture"""
    service = AsyncMock()
    service.register = AsyncMock()
    service.login = AsyncMock()
    service.refresh_token = AsyncMock()
    service.logout = AsyncMock()
    return service


@pytest.fixture
def mock_oauth_service():
    """OAuthService Mock Fixture"""
    service = AsyncMock()
    service.get_oauth_url = AsyncMock()
    service.handle_callback = AsyncMock()
    return service


@pytest.fixture
def mock_user_repository():
    """UserRepository Mock Fixture"""
    repo = AsyncMock()
    repo.find_by_email = AsyncMock()
    repo.find_by_kakao_id = AsyncMock()
    repo.find_by_id = AsyncMock()
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    return repo


@pytest.fixture
def mock_token_repository():
    """TokenRepository Mock Fixture"""
    repo = AsyncMock()
    repo.find_by_hash = AsyncMock()
    repo.create = AsyncMock()
    repo.revoke = AsyncMock()
    return repo


# ============================================================
# F-08 회사 프로필 관련 Mock 클래스 & Fixture
# ============================================================

class MockCompany:
    """회사 Mock"""
    def __init__(
        self,
        id=None,
        business_number=None,
        name=None,
        ceo_name=None,
        address=None,
        phone=None,
        industry=None,
        scale=None,
        description=None,
        deleted_at=None,
    ):
        self.id = id or str(uuid4())
        self.business_number = business_number or "1234567891"
        self.name = name or "테스트 주식회사"
        self.ceo_name = ceo_name or "홍길동"
        self.address = address or "서울특별시 강남구"
        self.phone = phone or "02-1234-5678"
        self.industry = industry or "IT서비스"
        self.scale = scale or "small"
        self.description = description or "테스트 회사입니다"
        self.deleted_at = deleted_at
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)


class MockCompanyMember:
    """회사 멤버 Mock"""
    def __init__(
        self,
        id=None,
        company_id=None,
        user_id=None,
        role=None,
        invited_at=None,
        joined_at=None,
    ):
        self.id = id or str(uuid4())
        self.company_id = company_id or str(uuid4())
        self.user_id = user_id or str(uuid4())
        self.role = role or "member"
        self.invited_at = invited_at or datetime.now(timezone.utc)
        self.joined_at = joined_at or datetime.now(timezone.utc)
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)


class MockPerformance:
    """수행 실적 Mock"""
    def __init__(
        self,
        id=None,
        company_id=None,
        project_name=None,
        client_name=None,
        client_type=None,
        contract_amount=None,
        start_date=None,
        end_date=None,
        status=None,
        description=None,
        is_representative=False,
        document_url=None,
        deleted_at=None,
    ):
        self.id = id or str(uuid4())
        self.company_id = company_id or str(uuid4())
        self.project_name = project_name or "공공 SI 프로젝트"
        self.client_name = client_name or "한국정보화진흥원"
        self.client_type = client_type or "public"
        self.contract_amount = contract_amount or 500000000
        self.start_date = start_date or "2024-01-01"
        self.end_date = end_date or "2024-12-31"
        self.status = status or "completed"
        self.description = description or "전자정부 시스템 구축"
        self.is_representative = is_representative
        self.document_url = document_url
        self.deleted_at = deleted_at
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)


class MockCertification:
    """보유 인증 Mock"""
    def __init__(
        self,
        id=None,
        company_id=None,
        name=None,
        issuer=None,
        cert_number=None,
        issued_date=None,
        expiry_date=None,
        document_url=None,
        deleted_at=None,
    ):
        self.id = id or str(uuid4())
        self.company_id = company_id or str(uuid4())
        self.name = name or "GS인증 1등급"
        self.issuer = issuer or "한국정보통신기술협회"
        self.cert_number = cert_number or "GS-2024-0001"
        self.issued_date = issued_date or "2024-01-15"
        self.expiry_date = expiry_date or "2027-01-14"
        self.document_url = document_url
        self.deleted_at = deleted_at
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)


@pytest.fixture(autouse=True)
def reset_company_store():
    """각 테스트 전후로 CompanyService 인-메모리 저장소 초기화"""
    try:
        from src.services.company_service import _reset_store
        _reset_store()
    except ImportError:
        pass
    yield
    try:
        from src.services.company_service import _reset_store
        _reset_store()
    except ImportError:
        pass


@pytest.fixture
def test_company_data():
    """테스트용 회사 데이터 Fixture"""
    return {
        "businessNumber": "1234567891",
        "name": "테스트 주식회사",
        "ceoName": "홍길동",
        "address": "서울특별시 강남구",
        "phone": "02-1234-5678",
        "industry": "IT서비스",
        "scale": "small",
        "description": "테스트 회사입니다",
    }


@pytest.fixture
def test_performance_data():
    """테스트용 수행 실적 데이터 Fixture"""
    return {
        "projectName": "공공 SI 프로젝트",
        "clientName": "한국정보화진흥원",
        "clientType": "public",
        "contractAmount": 500000000,
        "startDate": "2024-01-01",
        "endDate": "2024-12-31",
        "status": "completed",
        "description": "전자정부 시스템 구축",
        "isRepresentative": False,
    }


@pytest.fixture
def test_certification_data():
    """테스트용 보유 인증 데이터 Fixture"""
    return {
        "name": "GS인증 1등급",
        "issuer": "한국정보통신기술협회",
        "certNumber": "GS-2024-0001",
        "issuedDate": "2024-01-15",
        "expiryDate": "2027-01-14",
    }


@pytest.fixture
def mock_company():
    """테스트용 회사 Mock Fixture"""
    company = MockCompany(
        id=str(uuid4()),
        business_number="1234567891",
        name="테스트 주식회사",
        ceo_name="홍길동",
        address="서울특별시 강남구",
        scale="small",
    )
    try:
        from src.services.company_service import _register_company
        _register_company(company)
    except ImportError:
        pass
    return company


@pytest.fixture
def mock_deleted_company():
    """테스트용 삭제된 회사 Mock Fixture"""
    company = MockCompany(
        id=str(uuid4()),
        business_number="9876543210",
        name="삭제된 주식회사",
    )
    company.deleted_at = datetime.now(timezone.utc)
    try:
        from src.services.company_service import _register_company
        _register_company(company)
    except ImportError:
        pass
    return company


@pytest.fixture
def mock_company_member_owner(mock_company, mock_user):
    """테스트용 owner 역할 멤버 Mock Fixture"""
    member = MockCompanyMember(
        id=str(uuid4()),
        company_id=mock_company.id,
        user_id=mock_user.id,
        role="owner",
    )
    try:
        from src.services.company_service import _register_member, _register_user
        _register_user(mock_user)
        _register_member(member)
    except ImportError:
        pass
    return member


@pytest.fixture
def mock_company_member_admin(mock_company):
    """테스트용 admin 역할 멤버 Mock Fixture"""
    member = MockCompanyMember(
        id=str(uuid4()),
        company_id=mock_company.id,
        user_id=str(uuid4()),
        role="admin",
    )
    try:
        from src.services.company_service import _register_member
        _register_member(member)
    except ImportError:
        pass
    return member


@pytest.fixture
def mock_company_member_member(mock_company):
    """테스트용 member 역할 멤버 Mock Fixture"""
    member = MockCompanyMember(
        id=str(uuid4()),
        company_id=mock_company.id,
        user_id=str(uuid4()),
        role="member",
    )
    try:
        from src.services.company_service import _register_member
        _register_member(member)
    except ImportError:
        pass
    return member


@pytest.fixture
def mock_performance(mock_company):
    """테스트용 수행 실적 Mock Fixture"""
    performance = MockPerformance(
        id=str(uuid4()),
        company_id=mock_company.id,
        project_name="공공 SI 프로젝트",
        client_name="한국정보화진흥원",
        contract_amount=500000000,
    )
    try:
        from src.services.company_service import _register_performance
        _register_performance(performance)
    except ImportError:
        pass
    return performance


@pytest.fixture
def mock_representative_performance(mock_company):
    """테스트용 대표 실적 Mock Fixture"""
    performance = MockPerformance(
        id=str(uuid4()),
        company_id=mock_company.id,
        project_name="대표 실적 프로젝트",
        is_representative=True,
    )
    try:
        from src.services.company_service import _register_performance
        _register_performance(performance)
    except ImportError:
        pass
    return performance


@pytest.fixture
def mock_certification(mock_company):
    """테스트용 보유 인증 Mock Fixture"""
    certification = MockCertification(
        id=str(uuid4()),
        company_id=mock_company.id,
        name="GS인증 1등급",
        issuer="한국정보통신기술협회",
    )
    try:
        from src.services.company_service import _register_certification
        _register_certification(certification)
    except ImportError:
        pass
    return certification


# 회사 관련 에러 코드 상수
class AppException(Exception):
    """애플리케이션 예외"""
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


COMPANY_001 = AppException("COMPANY_001", "회사를 찾을 수 없습니다.", 404)
COMPANY_002 = AppException("COMPANY_002", "이미 등록된 사업자등록번호입니다.", 409)
COMPANY_003 = AppException("COMPANY_003", "사업자등록번호 검증 실패", 400)
COMPANY_004 = AppException("COMPANY_004", "회사 프로필이 이미 존재합니다.", 409)
COMPANY_005 = AppException("COMPANY_005", "대표 실적은 최대 5개까지 지정할 수 있습니다.", 400)
COMPANY_006 = AppException("COMPANY_006", "수행 실적을 찾을 수 없습니다.", 404)
COMPANY_007 = AppException("COMPANY_007", "인증 정보를 찾을 수 없습니다.", 404)
COMPANY_008 = AppException("COMPANY_008", "초대 대상 사용자를 찾을 수 없습니다.", 404)
COMPANY_009 = AppException("COMPANY_009", "이미 해당 회사의 멤버입니다.", 409)
COMPANY_010 = AppException("COMPANY_010", "대상 사용자가 이미 다른 회사에 소속되어 있습니다.", 409)
PERMISSION_001 = AppException("PERMISSION_001", "접근 권한이 없습니다.", 403)
PERMISSION_003 = AppException("PERMISSION_003", "팀원 초대 권한이 없습니다.", 403)


@pytest.fixture
def company_error_codes():
    """회사 관련 에러 코드들"""
    return {
        "COMPANY_001": COMPANY_001,
        "COMPANY_002": COMPANY_002,
        "COMPANY_003": COMPANY_003,
        "COMPANY_004": COMPANY_004,
        "COMPANY_005": COMPANY_005,
        "COMPANY_006": COMPANY_006,
        "COMPANY_007": COMPANY_007,
        "COMPANY_008": COMPANY_008,
        "COMPANY_009": COMPANY_009,
        "COMPANY_010": COMPANY_010,
        "PERMISSION_001": PERMISSION_001,
        "PERMISSION_003": PERMISSION_003,
    }


# ============================================================
# F-01 공고 자동 수집 및 매칭 관련 Mock 클래스 & Fixture
# ============================================================

# 공고 관련 에러 코드 상수
BID_001 = AppException("BID_001", "공고를 찾을 수 없습니다.", 404)
BID_002 = AppException("BID_002", "공고가 이미 마감되었습니다.", 400)
BID_003 = AppException("BID_003", "첨부파일 파싱에 실패했습니다.", 422)
BID_004 = AppException("BID_004", "공고 수집이 이미 진행 중입니다.", 409)
BID_005 = AppException("BID_005", "공공데이터포털 API 연동에 실패했습니다.", 502)
BID_006 = AppException("BID_006", "매칭 분석 중 오류가 발생했습니다.", 500)


class MockBid:
    """공고 Mock"""
    def __init__(
        self,
        id=None,
        bid_number=None,
        title=None,
        organization=None,
        region=None,
        category=None,
        bid_type=None,
        contract_method=None,
        budget=None,
        announcement_date=None,
        deadline=None,
        open_date=None,
        status=None,
        description=None,
        scoring_criteria=None,
        crawled_at=None,
        deleted_at=None,
    ):
        self.id = id or str(uuid4())
        self.bid_number = bid_number or "20260308001-00"
        self.title = title or "2026년 정보시스템 고도화 사업"
        self.organization = organization or "행정안전부"
        self.region = region or "서울"
        self.category = category or "정보화"
        self.bid_type = bid_type or "일반경쟁"
        self.contract_method = contract_method or "적격심사"
        self.budget = budget or 500000000
        self.announcement_date = announcement_date or "2026-03-08"
        self.deadline = deadline or datetime(2026, 3, 22, 17, 0, 0, tzinfo=timezone.utc)
        self.open_date = open_date or datetime(2026, 3, 23, 10, 0, 0, tzinfo=timezone.utc)
        self.status = status or "open"
        self.description = description or "공공기관 정보시스템 고도화 사업"
        self.scoring_criteria = scoring_criteria or {"technical": 80, "price": 20}
        self.crawled_at = crawled_at or datetime.now(timezone.utc)
        self.deleted_at = deleted_at
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)


class MockBidAttachment:
    """공고 첨부파일 Mock"""
    def __init__(
        self,
        id=None,
        bid_id=None,
        filename=None,
        file_type=None,
        file_url=None,
        extracted_text=None,
    ):
        self.id = id or str(uuid4())
        self.bid_id = bid_id or str(uuid4())
        self.filename = filename or "제안요청서.pdf"
        self.file_type = file_type or "PDF"
        self.file_url = file_url or "https://nara.go.kr/files/rfp.pdf"
        self.extracted_text = extracted_text
        self.created_at = datetime.now(timezone.utc)


class MockUserBidMatch:
    """사용자-공고 매칭 결과 Mock"""
    def __init__(
        self,
        id=None,
        user_id=None,
        bid_id=None,
        suitability_score=None,
        competition_score=0,
        capability_score=0,
        market_score=0,
        total_score=None,
        recommendation=None,
        recommendation_reason=None,
        is_notified=False,
        analyzed_at=None,
    ):
        self.id = id or str(uuid4())
        self.user_id = user_id or str(uuid4())
        self.bid_id = bid_id or str(uuid4())
        self.suitability_score = suitability_score or 75.0
        self.competition_score = competition_score
        self.capability_score = capability_score
        self.market_score = market_score
        self.total_score = total_score or self.suitability_score
        self.recommendation = recommendation or "recommended"
        self.recommendation_reason = recommendation_reason or "높은 적합도를 보입니다."
        self.is_notified = is_notified
        self.analyzed_at = analyzed_at or datetime.now(timezone.utc)
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)


class MockHttpResponse:
    """테스트용 HTTP 응답 Mock"""
    def __init__(self, status_code: int = 200, json_data: dict | None = None):
        self.status_code = status_code
        self._json_data = json_data or {}

    def json(self):
        return self._json_data


class MockBidParserService:
    """파싱 서비스 Mock (통합 테스트용)"""

    async def parse_attachment(self, attachment):
        """PDF는 텍스트 반환, 그 외 None"""
        if attachment.file_type == "PDF":
            return "추출된 PDF 텍스트 내용"
        return None

    async def parse_all_for_bid(self, bid_id, attachments):
        """PDF 첨부파일 수만큼 반환"""
        return len([a for a in attachments if a.file_type == "PDF"])


# 나라장터 API Mock 응답 데이터
NARA_API_SAMPLE_RESPONSE = {
    "response": {
        "header": {"resultCode": "00", "resultMsg": "NORMAL SERVICE."},
        "body": {
            "items": [
                {
                    "bidNtceNo": "20260308001",
                    "bidNtceOrd": "00",
                    "bidNtceNm": "2026년 정보시스템 고도화 사업",
                    "ntceInsttNm": "행정안전부",
                    "dminsttNm": "정보화전략과",
                    "presmptPrce": "500000000",
                    "bidNtceDt": "2026/03/08",
                    "bidClseDt": "2026/03/22 17:00:00",
                    "opengDt": "2026/03/23 10:00:00",
                    "ntceKindNm": "일반경쟁",
                    "cntrctMthdNm": "적격심사",
                }
            ],
            "numOfRows": 100,
            "pageNo": 1,
            "totalCount": 1,
        }
    }
}

NARA_API_EMPTY_RESPONSE = {
    "response": {
        "header": {"resultCode": "00", "resultMsg": "NORMAL SERVICE."},
        "body": {"items": [], "numOfRows": 100, "pageNo": 1, "totalCount": 0}
    }
}


@pytest.fixture(autouse=True)
def reset_bid_store():
    """각 테스트 전후로 BidService 인-메모리 저장소 초기화"""
    try:
        from src.services.bid_collector_service import _reset_store
        _reset_store()
    except (ImportError, AttributeError):
        pass

    # 통합 테스트에서 SAMPLE_BID_ID가 _SAMPLE_BIDS에 등록되도록 초기화
    try:
        from tests.integration.test_bid_api import SAMPLE_BID_ID
        from src.api.v1.bids import _SAMPLE_BIDS, _SAMPLE_MATCHES
        from datetime import datetime, timezone
        if SAMPLE_BID_ID not in _SAMPLE_BIDS:
            _SAMPLE_BIDS[SAMPLE_BID_ID] = {
                "id": SAMPLE_BID_ID,
                "bidNumber": "20260308999-00",
                "title": "2026년 테스트 공고",
                "description": "통합 테스트용 공고",
                "organization": "테스트기관",
                "region": "서울",
                "category": "정보화",
                "bidType": "일반경쟁",
                "contractMethod": "적격심사",
                "budget": 300000000,
                "estimatedPrice": 270000000,
                "announcementDate": "2026-03-08",
                "deadline": "2026-03-22T17:00:00+00:00",
                "openDate": "2026-03-23T10:00:00+00:00",
                "status": "open",
                "scoringCriteria": {"technical": 80, "price": 20},
                "attachments": [
                    {
                        "id": "att-sample-001",
                        "filename": "제안요청서.pdf",
                        "fileType": "PDF",
                        "fileUrl": "https://nara.go.kr/files/sample_rfp.pdf",
                        "hasExtractedText": True,
                    }
                ],
                "crawledAt": "2026-03-08T06:00:00+00:00",
                "createdAt": "2026-03-08T06:00:05+00:00",
            }
        match_key = f"user-owner-001:{SAMPLE_BID_ID}"
        if match_key not in _SAMPLE_MATCHES:
            _SAMPLE_MATCHES[match_key] = {
                "id": f"match-sample-001",
                "bidId": SAMPLE_BID_ID,
                "userId": "user-owner-001",
                "suitabilityScore": 78.5,
                "competitionScore": 0,
                "capabilityScore": 0,
                "marketScore": 0,
                "totalScore": 78.5,
                "recommendation": "recommended",
                "recommendationReason": "높은 적합도를 보입니다.",
                "isNotified": True,
                "analyzedAt": "2026-03-08T06:05:00+00:00",
            }
    except (ImportError, AttributeError):
        pass

    yield
    try:
        from src.services.bid_collector_service import _reset_store
        _reset_store()
    except (ImportError, AttributeError):
        pass


@pytest.fixture
def mock_bid():
    """테스트용 공고 Mock Fixture"""
    return MockBid(
        id=str(uuid4()),
        bid_number="20260308001-00",
        title="2026년 정보시스템 고도화 사업",
        organization="행정안전부",
        status="open",
    )


@pytest.fixture
def mock_closed_bid():
    """테스트용 마감된 공고 Mock Fixture"""
    return MockBid(
        id=str(uuid4()),
        bid_number="20260201001-00",
        title="2026년 1월 IT 구축 사업",
        status="closed",
    )


@pytest.fixture
def mock_bid_attachment_pdf(mock_bid):
    """테스트용 PDF 첨부파일 Mock Fixture"""
    return MockBidAttachment(
        id=str(uuid4()),
        bid_id=mock_bid.id,
        filename="제안요청서.pdf",
        file_type="PDF",
        file_url="https://nara.go.kr/files/rfp.pdf",
        extracted_text="제안요청서 추출 텍스트: 정보시스템 구축 요건...",
    )


@pytest.fixture
def mock_bid_attachment_hwp(mock_bid):
    """테스트용 HWP 첨부파일 Mock Fixture"""
    return MockBidAttachment(
        id=str(uuid4()),
        bid_id=mock_bid.id,
        filename="과업지시서.hwp",
        file_type="HWP",
        file_url="https://nara.go.kr/files/task.hwp",
        extracted_text=None,
    )


@pytest.fixture
def mock_user_bid_match(mock_user, mock_bid):
    """테스트용 매칭 결과 Mock Fixture"""
    return MockUserBidMatch(
        id=str(uuid4()),
        user_id=mock_user.id,
        bid_id=mock_bid.id,
        suitability_score=78.5,
        total_score=78.5,
        recommendation="recommended",
        recommendation_reason="높은 적합도: 회사 업종이 공고 분야와 일치합니다.",
    )


@pytest.fixture
def mock_low_score_match(mock_user, mock_bid):
    """테스트용 낮은 점수 매칭 결과 Mock Fixture"""
    return MockUserBidMatch(
        id=str(uuid4()),
        user_id=mock_user.id,
        bid_id=mock_bid.id,
        suitability_score=25.0,
        total_score=25.0,
        recommendation="not_recommended",
        recommendation_reason="낮은 적합도: 업종이 공고 분야와 맞지 않습니다.",
    )


@pytest.fixture
def mock_http_client_for_nara():
    """나라장터 API 호출용 HTTP 클라이언트 Mock Fixture"""
    client = AsyncMock()
    response = MockHttpResponse(status_code=200, json_data=NARA_API_SAMPLE_RESPONSE)
    client.get = AsyncMock(return_value=response)
    return client


@pytest.fixture
def bid_error_codes():
    """공고 관련 에러 코드들"""
    return {
        "BID_001": BID_001,
        "BID_002": BID_002,
        "BID_003": BID_003,
        "BID_004": BID_004,
        "BID_005": BID_005,
        "BID_006": BID_006,
    }
