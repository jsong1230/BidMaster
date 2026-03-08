"""
회사 프로필 API 통합 테스트

test-spec.md 기준:
- IT-01~IT-06: POST /api/v1/companies - 회사 등록
- IT-10~IT-12: GET /api/v1/companies/my - 내 회사 조회
- IT-20~IT-24: PUT /api/v1/companies/{id} - 회사 수정
- IT-30~IT-43: 수행 실적 CRUD API
- IT-50~IT-57: 보유 인증 CRUD API
- IT-60~IT-67: 멤버 관리 API
"""
import pytest
from uuid import uuid4

from tests.conftest import MockApp


# ============================================================
# 통합 테스트용 Mock App - companies 라우터 포함
# ============================================================

class CompanyMockApp(MockApp):
    """회사 관련 엔드포인트가 포함된 Mock App"""

    def __init__(self):
        super().__init__()
        from fastapi import Request
        from fastapi.responses import JSONResponse

        @self.post("/api/v1/companies")
        async def mock_create_company(request: Request):
            return JSONResponse(
                status_code=501,
                content={
                    "success": False,
                    "error": {"code": "NOT_IMPLEMENTED", "message": "Not implemented yet"}
                }
            )

        @self.get("/api/v1/companies/my")
        async def mock_get_my_company(request: Request):
            return JSONResponse(
                status_code=501,
                content={
                    "success": False,
                    "error": {"code": "NOT_IMPLEMENTED", "message": "Not implemented yet"}
                }
            )

        @self.put("/api/v1/companies/{company_id}")
        async def mock_update_company(company_id: str, request: Request):
            return JSONResponse(
                status_code=501,
                content={
                    "success": False,
                    "error": {"code": "NOT_IMPLEMENTED", "message": "Not implemented yet"}
                }
            )

        @self.post("/api/v1/companies/{company_id}/performances")
        async def mock_create_performance(company_id: str, request: Request):
            return JSONResponse(
                status_code=501,
                content={
                    "success": False,
                    "error": {"code": "NOT_IMPLEMENTED", "message": "Not implemented yet"}
                }
            )

        @self.get("/api/v1/companies/{company_id}/performances")
        async def mock_list_performances(company_id: str, request: Request):
            return JSONResponse(
                status_code=501,
                content={
                    "success": False,
                    "error": {"code": "NOT_IMPLEMENTED", "message": "Not implemented yet"}
                }
            )

        @self.put("/api/v1/companies/{company_id}/performances/{perf_id}")
        async def mock_update_performance(
            company_id: str, perf_id: str, request: Request
        ):
            return JSONResponse(
                status_code=501,
                content={
                    "success": False,
                    "error": {"code": "NOT_IMPLEMENTED", "message": "Not implemented yet"}
                }
            )

        @self.delete("/api/v1/companies/{company_id}/performances/{perf_id}")
        async def mock_delete_performance(
            company_id: str, perf_id: str, request: Request
        ):
            return JSONResponse(
                status_code=501,
                content={
                    "success": False,
                    "error": {"code": "NOT_IMPLEMENTED", "message": "Not implemented yet"}
                }
            )

        @self.patch(
            "/api/v1/companies/{company_id}/performances/{perf_id}/representative"
        )
        async def mock_set_representative(
            company_id: str, perf_id: str, request: Request
        ):
            return JSONResponse(
                status_code=501,
                content={
                    "success": False,
                    "error": {"code": "NOT_IMPLEMENTED", "message": "Not implemented yet"}
                }
            )

        @self.post("/api/v1/companies/{company_id}/certifications")
        async def mock_create_certification(company_id: str, request: Request):
            return JSONResponse(
                status_code=501,
                content={
                    "success": False,
                    "error": {"code": "NOT_IMPLEMENTED", "message": "Not implemented yet"}
                }
            )

        @self.get("/api/v1/companies/{company_id}/certifications")
        async def mock_list_certifications(company_id: str, request: Request):
            return JSONResponse(
                status_code=501,
                content={
                    "success": False,
                    "error": {"code": "NOT_IMPLEMENTED", "message": "Not implemented yet"}
                }
            )

        @self.put("/api/v1/companies/{company_id}/certifications/{cert_id}")
        async def mock_update_certification(
            company_id: str, cert_id: str, request: Request
        ):
            return JSONResponse(
                status_code=501,
                content={
                    "success": False,
                    "error": {"code": "NOT_IMPLEMENTED", "message": "Not implemented yet"}
                }
            )

        @self.delete("/api/v1/companies/{company_id}/certifications/{cert_id}")
        async def mock_delete_certification(
            company_id: str, cert_id: str, request: Request
        ):
            return JSONResponse(
                status_code=501,
                content={
                    "success": False,
                    "error": {"code": "NOT_IMPLEMENTED", "message": "Not implemented yet"}
                }
            )

        @self.post("/api/v1/companies/{company_id}/members")
        async def mock_invite_member(company_id: str, request: Request):
            return JSONResponse(
                status_code=501,
                content={
                    "success": False,
                    "error": {"code": "NOT_IMPLEMENTED", "message": "Not implemented yet"}
                }
            )

        @self.get("/api/v1/companies/{company_id}/members")
        async def mock_list_members(company_id: str, request: Request):
            return JSONResponse(
                status_code=501,
                content={
                    "success": False,
                    "error": {"code": "NOT_IMPLEMENTED", "message": "Not implemented yet"}
                }
            )


def _build_company_app():
    """실제 companies 라우터가 포함된 FastAPI 앱 생성"""
    try:
        from fastapi import FastAPI
        from src.api.v1.companies import router as companies_router
        app = FastAPI(redirect_slashes=False)
        app.include_router(companies_router, prefix="/api/v1/companies")
        return app
    except ImportError:
        return CompanyMockApp()


company_app = _build_company_app()


@pytest.fixture
async def company_client():
    """회사 관련 API 테스트용 async_client"""
    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=company_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def auth_headers():
    """인증 헤더 픽스처 (테스트용 JWT 토큰 시뮬레이션)"""
    from src.core.security import create_access_token
    user_id = str(uuid4())
    token = create_access_token(
        user_id,
        extra_data={"company_id": None, "role": "user"}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def owner_auth_headers(mock_company):
    """owner 역할 인증 헤더 (store에 멤버십 등록)"""
    from src.core.security import create_access_token
    user_id = str(uuid4())
    token = create_access_token(
        user_id,
        extra_data={"company_id": mock_company.id, "role": "owner"}
    )
    # store에 멤버십 등록
    try:
        from src.services.company_service import _register_member
        from tests.conftest import MockCompanyMember
        member = MockCompanyMember(
            company_id=mock_company.id,
            user_id=user_id,
            role="owner",
        )
        _register_member(member)
    except ImportError:
        pass
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(mock_company):
    """admin 역할 인증 헤더 (store에 멤버십 등록)"""
    from src.core.security import create_access_token
    user_id = str(uuid4())
    token = create_access_token(
        user_id,
        extra_data={"company_id": mock_company.id, "role": "admin"}
    )
    # store에 멤버십 등록
    try:
        from src.services.company_service import _register_member
        from tests.conftest import MockCompanyMember
        member = MockCompanyMember(
            company_id=mock_company.id,
            user_id=user_id,
            role="admin",
        )
        _register_member(member)
    except ImportError:
        pass
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def member_auth_headers(mock_company):
    """member 역할 인증 헤더 (store에 멤버십 등록)"""
    from src.core.security import create_access_token
    user_id = str(uuid4())
    token = create_access_token(
        user_id,
        extra_data={"company_id": mock_company.id, "role": "member"}
    )
    # store에 멤버십 등록
    try:
        from src.services.company_service import _register_member
        from tests.conftest import MockCompanyMember
        member = MockCompanyMember(
            company_id=mock_company.id,
            user_id=user_id,
            role="member",
        )
        _register_member(member)
    except ImportError:
        pass
    return {"Authorization": f"Bearer {token}"}


# ============================================================
# 2.1 회사 등록 API 통합 테스트 (IT-01~IT-06)
# ============================================================

class TestCreateCompanyAPI:
    """POST /api/v1/companies - 회사 등록 API 통합 테스트"""

    @pytest.mark.asyncio
    async def test_IT01_정상_회사_등록(self, company_client, test_company_data, auth_headers):
        """
        Given: 유효한 회사 데이터 + 인증 토큰
        When: POST /api/v1/companies
        Then: 201 Created, company 생성, company_members owner 추가, users.company_id 갱신
        """
        # Act
        response = await company_client.post(
            "/api/v1/companies",
            json=test_company_data,
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "id" in data["data"]
        assert data["data"]["businessNumber"] == test_company_data["businessNumber"]
        assert data["data"]["name"] == test_company_data["name"]

    @pytest.mark.asyncio
    async def test_IT02_미인증_요청_401(self, company_client, test_company_data):
        """
        Given: 인증 토큰 없음
        When: POST /api/v1/companies
        Then: 401 Unauthorized, AUTH_002 에러
        """
        # Act
        response = await company_client.post(
            "/api/v1/companies",
            json=test_company_data,
            # 헤더 없음
        )

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "AUTH_002"

    @pytest.mark.asyncio
    async def test_IT03_중복_사업자등록번호_409(
        self, company_client, test_company_data, auth_headers
    ):
        """
        Given: 이미 등록된 사업자등록번호
        When: POST /api/v1/companies
        Then: 409 Conflict, COMPANY_002 에러
        """
        # Arrange: 첫 번째 등록
        await company_client.post(
            "/api/v1/companies", json=test_company_data, headers=auth_headers
        )

        # Act: 동일 사업자등록번호로 두 번째 요청
        response = await company_client.post(
            "/api/v1/companies", json=test_company_data, headers=auth_headers
        )

        # Assert
        assert response.status_code == 409
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "COMPANY_002"

    @pytest.mark.asyncio
    async def test_IT04_잘못된_사업자등록번호_형식_400(
        self, company_client, auth_headers
    ):
        """
        Given: 4자리 사업자등록번호 "1234"
        When: POST /api/v1/companies
        Then: 400 Bad Request, COMPANY_003 에러
        """
        # Arrange
        invalid_data = {
            "businessNumber": "1234",  # 너무 짧은 번호
            "name": "테스트 주식회사",
        }

        # Act
        response = await company_client.post(
            "/api/v1/companies", json=invalid_data, headers=auth_headers
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "COMPANY_003"

    @pytest.mark.asyncio
    async def test_IT05_이미_소속된_사용자_409(
        self, company_client, test_company_data
    ):
        """
        Given: 이미 회사에 소속된 사용자 (company_id NOT NULL)
        When: POST /api/v1/companies
        Then: 409 Conflict, COMPANY_004 에러
        """
        # Arrange: 이미 회사에 소속된 사용자의 토큰
        from src.core.security import create_access_token
        user_id = str(uuid4())
        token = create_access_token(
            user_id,
            extra_data={"company_id": str(uuid4()), "role": "owner"}
        )
        headers_with_company = {"Authorization": f"Bearer {token}"}

        # Act
        response = await company_client.post(
            "/api/v1/companies",
            json=test_company_data,
            headers=headers_with_company,
        )

        # Assert
        assert response.status_code == 409
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "COMPANY_004"

    @pytest.mark.asyncio
    async def test_IT06_필수_필드_누락_400(self, company_client, auth_headers):
        """
        Given: businessNumber 필드 누락
        When: POST /api/v1/companies
        Then: 400 Bad Request, VALIDATION_001 에러
        """
        # Arrange
        data_without_business_number = {
            "name": "테스트 주식회사",
            "scale": "small",
        }

        # Act
        response = await company_client.post(
            "/api/v1/companies",
            json=data_without_business_number,
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] in ["VALIDATION_001", "VALIDATION_002"]


# ============================================================
# 2.2 내 회사 조회 API 통합 테스트 (IT-10~IT-12)
# ============================================================

class TestGetMyCompanyAPI:
    """GET /api/v1/companies/my - 내 회사 조회 API 통합 테스트"""

    @pytest.mark.asyncio
    async def test_IT10_소속_회사_조회_200(self, company_client, owner_auth_headers):
        """
        Given: 회사에 소속된 사용자 (company_id 존재)
        When: GET /api/v1/companies/my
        Then: 200 OK, 회사 정보 + 집계 반환
        """
        # Act
        response = await company_client.get(
            "/api/v1/companies/my", headers=owner_auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "id" in data["data"]
        assert "memberCount" in data["data"]
        assert "performanceCount" in data["data"]
        assert "certificationCount" in data["data"]

    @pytest.mark.asyncio
    async def test_IT11_미소속_사용자_404(self, company_client, auth_headers):
        """
        Given: company_id가 NULL인 사용자
        When: GET /api/v1/companies/my
        Then: 404 Not Found, COMPANY_001 에러
        """
        # Act
        response = await company_client.get(
            "/api/v1/companies/my", headers=auth_headers
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "COMPANY_001"

    @pytest.mark.asyncio
    async def test_IT12_미인증_요청_401(self, company_client):
        """
        Given: 인증 토큰 없음
        When: GET /api/v1/companies/my
        Then: 401 Unauthorized, AUTH_002 에러
        """
        # Act
        response = await company_client.get("/api/v1/companies/my")

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "AUTH_002"


# ============================================================
# 2.3 회사 수정 API 통합 테스트 (IT-20~IT-24)
# ============================================================

class TestUpdateCompanyAPI:
    """PUT /api/v1/companies/{id} - 회사 수정 API 통합 테스트"""

    @pytest.mark.asyncio
    async def test_IT20_owner가_수정_200(
        self, company_client, mock_company, owner_auth_headers
    ):
        """
        Given: owner 토큰 + 유효한 수정 데이터
        When: PUT /api/v1/companies/{id}
        Then: 200 OK, 수정된 데이터 반환
        """
        # Arrange
        update_data = {
            "name": "수정된 주식회사",
            "ceoName": "김길동",
        }

        # Act
        response = await company_client.put(
            f"/api/v1/companies/{mock_company.id}",
            json=update_data,
            headers=owner_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == update_data["name"]

    @pytest.mark.asyncio
    async def test_IT21_admin이_수정_200(self, company_client, mock_company):
        """
        Given: admin 토큰 + 유효한 수정 데이터
        When: PUT /api/v1/companies/{id}
        Then: 200 OK
        """
        # Arrange
        from src.core.security import create_access_token
        from src.services.company_service import _register_member
        from tests.conftest import MockCompanyMember
        admin_user_id = str(uuid4())
        admin_token = create_access_token(
            admin_user_id,
            extra_data={"company_id": mock_company.id, "role": "admin"}
        )
        # store에 admin 멤버십 등록
        member = MockCompanyMember(company_id=mock_company.id, user_id=admin_user_id, role="admin")
        _register_member(member)
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        update_data = {"name": "admin이 수정한 회사"}

        # Act
        response = await company_client.put(
            f"/api/v1/companies/{mock_company.id}",
            json=update_data,
            headers=admin_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_IT22_member가_수정_시도_403(
        self, company_client, mock_company, member_auth_headers
    ):
        """
        Given: member 토큰
        When: PUT /api/v1/companies/{id}
        Then: 403 Forbidden, PERMISSION_001 에러
        """
        # Arrange
        update_data = {"name": "member 수정 시도"}

        # Act
        response = await company_client.put(
            f"/api/v1/companies/{mock_company.id}",
            json=update_data,
            headers=member_auth_headers,
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "PERMISSION_001"

    @pytest.mark.asyncio
    async def test_IT23_다른_회사_수정_시도_403(
        self, company_client, owner_auth_headers
    ):
        """
        Given: owner 토큰이지만 다른 회사 ID로 요청
        When: PUT /api/v1/companies/{다른_회사_id}
        Then: 403 Forbidden, PERMISSION_001 에러
        """
        # Arrange
        other_company_id = str(uuid4())
        update_data = {"name": "다른 회사 수정 시도"}

        # Act
        response = await company_client.put(
            f"/api/v1/companies/{other_company_id}",
            json=update_data,
            headers=owner_auth_headers,
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "PERMISSION_001"

    @pytest.mark.asyncio
    async def test_IT24_존재하지_않는_회사_404(self, company_client):
        """
        Given: 존재하지 않는 회사에 멤버십이 있는 사용자
        When: PUT /api/v1/companies/{존재하지_않는_id}
        Then: 404 Not Found, COMPANY_001 에러
        """
        # Arrange: 존재하지 않는 회사에 멤버십을 가진 사용자
        from src.core.security import create_access_token
        from src.services.company_service import _register_member
        from tests.conftest import MockCompanyMember
        non_existent_id = str(uuid4())
        user_id = str(uuid4())
        token = create_access_token(
            user_id,
            extra_data={"company_id": non_existent_id, "role": "owner"}
        )
        # 멤버십을 store에 등록 (그러나 회사는 등록하지 않음)
        member = MockCompanyMember(company_id=non_existent_id, user_id=user_id, role="owner")
        _register_member(member)
        headers_with_member = {"Authorization": f"Bearer {token}"}

        update_data = {"name": "테스트"}

        # Act
        response = await company_client.put(
            f"/api/v1/companies/{non_existent_id}",
            json=update_data,
            headers=headers_with_member,
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "COMPANY_001"


# ============================================================
# 2.4 수행 실적 API 통합 테스트 (IT-30~IT-43)
# ============================================================

class TestPerformanceAPI:
    """수행 실적 CRUD API 통합 테스트"""

    @pytest.mark.asyncio
    async def test_IT30_정상_실적_등록_201(
        self,
        company_client,
        mock_company,
        test_performance_data,
        member_auth_headers,
    ):
        """
        Given: member 토큰 + 유효한 실적 데이터
        When: POST /api/v1/companies/{id}/performances
        Then: 201 Created, Performance 생성
        """
        # Act
        response = await company_client.post(
            f"/api/v1/companies/{mock_company.id}/performances",
            json=test_performance_data,
            headers=member_auth_headers,
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "id" in data["data"]
        assert data["data"]["projectName"] == test_performance_data["projectName"]

    @pytest.mark.asyncio
    async def test_IT31_대표_실적으로_등록_is_representative_true(
        self, company_client, mock_company, test_performance_data, member_auth_headers
    ):
        """
        Given: isRepresentative=true
        When: POST /api/v1/companies/{id}/performances
        Then: 201 Created, is_representative=true
        """
        # Arrange
        data_with_representative = {**test_performance_data, "isRepresentative": True}

        # Act
        response = await company_client.post(
            f"/api/v1/companies/{mock_company.id}/performances",
            json=data_with_representative,
            headers=member_auth_headers,
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["isRepresentative"] is True

    @pytest.mark.asyncio
    async def test_IT32_대표_실적_초과_400(
        self, company_client, mock_company, test_performance_data, owner_auth_headers
    ):
        """
        Given: 이미 5개의 대표 실적 + isRepresentative=true
        When: POST /api/v1/companies/{id}/performances
        Then: 400 Bad Request, COMPANY_005 에러
        """
        # Arrange
        data_with_representative = {**test_performance_data, "isRepresentative": True}

        # 5개 등록 (성공)
        for _ in range(5):
            await company_client.post(
                f"/api/v1/companies/{mock_company.id}/performances",
                json=data_with_representative,
                headers=owner_auth_headers,
            )

        # Act: 6번째 대표 실적 등록 시도
        response = await company_client.post(
            f"/api/v1/companies/{mock_company.id}/performances",
            json=data_with_representative,
            headers=owner_auth_headers,
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "COMPANY_005"

    @pytest.mark.asyncio
    async def test_IT33_비멤버_실적_등록_시도_403(
        self, company_client, mock_company, test_performance_data
    ):
        """
        Given: 해당 회사 멤버가 아닌 사용자
        When: POST /api/v1/companies/{id}/performances
        Then: 403 Forbidden, PERMISSION_001 에러
        """
        # Arrange: 다른 회사 멤버의 토큰
        from src.core.security import create_access_token
        token = create_access_token(
            str(uuid4()),
            extra_data={"company_id": str(uuid4()), "role": "owner"}
        )
        other_headers = {"Authorization": f"Bearer {token}"}

        # Act
        response = await company_client.post(
            f"/api/v1/companies/{mock_company.id}/performances",
            json=test_performance_data,
            headers=other_headers,
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "PERMISSION_001"

    @pytest.mark.asyncio
    async def test_IT34_실적_목록_조회_페이지네이션(
        self, company_client, mock_company, member_auth_headers
    ):
        """
        Given: page=1, pageSize=10
        When: GET /api/v1/companies/{id}/performances
        Then: 200 OK, items + meta 반환
        """
        # Act
        response = await company_client.get(
            f"/api/v1/companies/{mock_company.id}/performances",
            params={"page": 1, "pageSize": 10},
            headers=member_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "items" in data["data"]
        assert "page" in data["meta"]
        assert "total" in data["meta"]

    @pytest.mark.asyncio
    async def test_IT35_대표_실적_필터링(
        self, company_client, mock_company, member_auth_headers
    ):
        """
        Given: isRepresentative=true 필터
        When: GET /api/v1/companies/{id}/performances?isRepresentative=true
        Then: 200 OK, 대표 실적만 반환
        """
        # Act
        response = await company_client.get(
            f"/api/v1/companies/{mock_company.id}/performances",
            params={"isRepresentative": "true"},
            headers=member_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        for item in data["data"]["items"]:
            assert item["isRepresentative"] is True

    @pytest.mark.asyncio
    async def test_IT36_상태_필터링(
        self, company_client, mock_company, member_auth_headers
    ):
        """
        Given: status=completed 필터
        When: GET /api/v1/companies/{id}/performances?status=completed
        Then: 200 OK, 완료된 실적만 반환
        """
        # Act
        response = await company_client.get(
            f"/api/v1/companies/{mock_company.id}/performances",
            params={"status": "completed"},
            headers=member_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        for item in data["data"]["items"]:
            assert item["status"] == "completed"

    @pytest.mark.asyncio
    async def test_IT37_정렬_계약금액_내림차순(
        self, company_client, mock_company, member_auth_headers
    ):
        """
        Given: sortBy=contractAmount, sortOrder=desc
        When: GET /api/v1/companies/{id}/performances
        Then: 200 OK, 금액 내림차순 정렬
        """
        # Act
        response = await company_client.get(
            f"/api/v1/companies/{mock_company.id}/performances",
            params={"sortBy": "contractAmount", "sortOrder": "desc"},
            headers=member_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        items = data["data"]["items"]
        if len(items) > 1:
            for i in range(len(items) - 1):
                assert items[i]["contractAmount"] >= items[i + 1]["contractAmount"]

    @pytest.mark.asyncio
    async def test_IT38_owner가_실적_수정_200(
        self, company_client, mock_company, mock_performance, owner_auth_headers
    ):
        """
        Given: owner 토큰 + 유효한 수정 데이터
        When: PUT /api/v1/companies/{id}/performances/{perfId}
        Then: 200 OK
        """
        # Arrange
        update_data = {"projectName": "수정된 프로젝트"}

        # Act
        response = await company_client.put(
            f"/api/v1/companies/{mock_company.id}/performances/{mock_performance.id}",
            json=update_data,
            headers=owner_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["projectName"] == update_data["projectName"]

    @pytest.mark.asyncio
    async def test_IT39_member가_실적_수정_시도_403(
        self,
        company_client,
        mock_company,
        mock_performance,
        member_auth_headers,
    ):
        """
        Given: member 토큰
        When: PUT /api/v1/companies/{id}/performances/{perfId}
        Then: 403 Forbidden, PERMISSION_001 에러
        """
        # Act
        response = await company_client.put(
            f"/api/v1/companies/{mock_company.id}/performances/{mock_performance.id}",
            json={"projectName": "member 수정 시도"},
            headers=member_auth_headers,
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "PERMISSION_001"

    @pytest.mark.asyncio
    async def test_IT40_실적_정상_삭제_200(
        self, company_client, mock_company, mock_performance, owner_auth_headers
    ):
        """
        Given: owner 토큰
        When: DELETE /api/v1/companies/{id}/performances/{perfId}
        Then: 200 OK, data: null
        """
        # Act
        response = await company_client.delete(
            f"/api/v1/companies/{mock_company.id}/performances/{mock_performance.id}",
            headers=owner_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] is None

    @pytest.mark.asyncio
    async def test_IT41_존재하지_않는_실적_삭제_404(
        self, company_client, mock_company, owner_auth_headers
    ):
        """
        Given: 잘못된 perfId
        When: DELETE /api/v1/companies/{id}/performances/{perfId}
        Then: 404 Not Found, COMPANY_006 에러
        """
        # Arrange
        non_existent_perf_id = str(uuid4())

        # Act
        response = await company_client.delete(
            f"/api/v1/companies/{mock_company.id}/performances/{non_existent_perf_id}",
            headers=owner_auth_headers,
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "COMPANY_006"

    @pytest.mark.asyncio
    async def test_IT42_대표_실적_지정_200(
        self, company_client, mock_company, mock_performance, owner_auth_headers
    ):
        """
        Given: isRepresentative=true
        When: PATCH /api/v1/companies/{id}/performances/{perfId}/representative
        Then: 200 OK
        """
        # Act
        response = await company_client.patch(
            f"/api/v1/companies/{mock_company.id}/performances/{mock_performance.id}/representative",
            json={"isRepresentative": True},
            headers=owner_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["isRepresentative"] is True

    @pytest.mark.asyncio
    async def test_IT43_대표_실적_해제_200(
        self,
        company_client,
        mock_company,
        mock_representative_performance,
        owner_auth_headers,
    ):
        """
        Given: isRepresentative=false (대표 해제)
        When: PATCH /api/v1/companies/{id}/performances/{perfId}/representative
        Then: 200 OK
        """
        # Act
        response = await company_client.patch(
            f"/api/v1/companies/{mock_company.id}/performances/{mock_representative_performance.id}/representative",
            json={"isRepresentative": False},
            headers=owner_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["isRepresentative"] is False


# ============================================================
# 2.5 보유 인증 API 통합 테스트 (IT-50~IT-57)
# ============================================================

class TestCertificationAPI:
    """보유 인증 CRUD API 통합 테스트"""

    @pytest.mark.asyncio
    async def test_IT50_정상_인증_등록_201(
        self, company_client, mock_company, test_certification_data, member_auth_headers
    ):
        """
        Given: member 토큰 + 유효한 인증 데이터
        When: POST /api/v1/companies/{id}/certifications
        Then: 201 Created, Certification 생성
        """
        # Act
        response = await company_client.post(
            f"/api/v1/companies/{mock_company.id}/certifications",
            json=test_certification_data,
            headers=member_auth_headers,
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "id" in data["data"]
        assert data["data"]["name"] == test_certification_data["name"]

    @pytest.mark.asyncio
    async def test_IT51_비멤버_인증_등록_시도_403(
        self, company_client, mock_company, test_certification_data
    ):
        """
        Given: 해당 회사 멤버가 아닌 사용자
        When: POST /api/v1/companies/{id}/certifications
        Then: 403 Forbidden, PERMISSION_001 에러
        """
        # Arrange: 다른 회사 멤버의 토큰
        from src.core.security import create_access_token
        token = create_access_token(
            str(uuid4()),
            extra_data={"company_id": str(uuid4()), "role": "owner"}
        )
        other_headers = {"Authorization": f"Bearer {token}"}

        # Act
        response = await company_client.post(
            f"/api/v1/companies/{mock_company.id}/certifications",
            json=test_certification_data,
            headers=other_headers,
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "PERMISSION_001"

    @pytest.mark.asyncio
    async def test_IT52_인증_목록_조회_페이지네이션(
        self, company_client, mock_company, member_auth_headers
    ):
        """
        Given: page=1
        When: GET /api/v1/companies/{id}/certifications
        Then: 200 OK, items + meta 반환
        """
        # Act
        response = await company_client.get(
            f"/api/v1/companies/{mock_company.id}/certifications",
            params={"page": 1},
            headers=member_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "items" in data["data"]
        assert "page" in data["meta"]
        assert "total" in data["meta"]

    @pytest.mark.asyncio
    async def test_IT53_정렬_만료일_오름차순(
        self, company_client, mock_company, member_auth_headers
    ):
        """
        Given: sortBy=expiryDate, sortOrder=asc
        When: GET /api/v1/companies/{id}/certifications
        Then: 200 OK, 만료일 오름차순 정렬
        """
        # Act
        response = await company_client.get(
            f"/api/v1/companies/{mock_company.id}/certifications",
            params={"sortBy": "expiryDate", "sortOrder": "asc"},
            headers=member_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_IT54_owner가_인증_수정_200(
        self, company_client, mock_company, mock_certification, owner_auth_headers
    ):
        """
        Given: owner 토큰 + 유효한 수정 데이터
        When: PUT /api/v1/companies/{id}/certifications/{certId}
        Then: 200 OK
        """
        # Arrange
        update_data = {"name": "수정된 인증명"}

        # Act
        response = await company_client.put(
            f"/api/v1/companies/{mock_company.id}/certifications/{mock_certification.id}",
            json=update_data,
            headers=owner_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == update_data["name"]

    @pytest.mark.asyncio
    async def test_IT55_member가_인증_수정_시도_403(
        self, company_client, mock_company, mock_certification, member_auth_headers
    ):
        """
        Given: member 토큰
        When: PUT /api/v1/companies/{id}/certifications/{certId}
        Then: 403 Forbidden, PERMISSION_001 에러
        """
        # Act
        response = await company_client.put(
            f"/api/v1/companies/{mock_company.id}/certifications/{mock_certification.id}",
            json={"name": "member 수정 시도"},
            headers=member_auth_headers,
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "PERMISSION_001"

    @pytest.mark.asyncio
    async def test_IT56_인증_정상_삭제_200(
        self, company_client, mock_company, mock_certification, owner_auth_headers
    ):
        """
        Given: owner 토큰
        When: DELETE /api/v1/companies/{id}/certifications/{certId}
        Then: 200 OK, data: null
        """
        # Act
        response = await company_client.delete(
            f"/api/v1/companies/{mock_company.id}/certifications/{mock_certification.id}",
            headers=owner_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] is None

    @pytest.mark.asyncio
    async def test_IT57_존재하지_않는_인증_삭제_404(
        self, company_client, mock_company, owner_auth_headers
    ):
        """
        Given: 잘못된 certId
        When: DELETE /api/v1/companies/{id}/certifications/{certId}
        Then: 404 Not Found, COMPANY_007 에러
        """
        # Arrange
        non_existent_cert_id = str(uuid4())

        # Act
        response = await company_client.delete(
            f"/api/v1/companies/{mock_company.id}/certifications/{non_existent_cert_id}",
            headers=owner_auth_headers,
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "COMPANY_007"


# ============================================================
# 2.6 멤버 관리 API 통합 테스트 (IT-60~IT-67)
# ============================================================

class TestMemberAPI:
    """멤버 관리 API 통합 테스트"""

    @pytest.mark.asyncio
    async def test_IT60_owner가_멤버_초대_201(
        self, company_client, mock_company, owner_auth_headers
    ):
        """
        Given: owner 토큰 + 유효한 이메일
        When: POST /api/v1/companies/{id}/members
        Then: 201 Created, CompanyMember 생성
        """
        # Arrange: 초대할 사용자를 store에 등록
        from src.services.company_service import _register_user
        from tests.conftest import MockUser
        target_user = MockUser(email="newmember@test.com", name="신규멤버")
        target_user.company_id = None
        _register_user(target_user)

        invite_data = {
            "email": "newmember@test.com",
            "role": "member",
        }

        # Act
        response = await company_client.post(
            f"/api/v1/companies/{mock_company.id}/members",
            json=invite_data,
            headers=owner_auth_headers,
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "id" in data["data"]
        assert data["data"]["role"] == "member"

    @pytest.mark.asyncio
    async def test_IT61_admin이_멤버_초대_201(self, company_client, mock_company):
        """
        Given: admin 토큰 + 유효한 이메일
        When: POST /api/v1/companies/{id}/members
        Then: 201 Created
        """
        # Arrange: 초대할 사용자를 store에 등록
        from src.services.company_service import _register_user, _register_member
        from tests.conftest import MockUser, MockCompanyMember
        target_user = MockUser(email="anothermember@test.com", name="또다른멤버")
        target_user.company_id = None
        _register_user(target_user)

        from src.core.security import create_access_token
        admin_user_id = str(uuid4())
        admin_token = create_access_token(
            admin_user_id,
            extra_data={"company_id": mock_company.id, "role": "admin"}
        )
        # admin 멤버십 등록
        member = MockCompanyMember(company_id=mock_company.id, user_id=admin_user_id, role="admin")
        _register_member(member)
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        invite_data = {
            "email": "anothermember@test.com",
            "role": "member",
        }

        # Act
        response = await company_client.post(
            f"/api/v1/companies/{mock_company.id}/members",
            json=invite_data,
            headers=admin_headers,
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_IT62_member가_초대_시도_403(
        self, company_client, mock_company, member_auth_headers
    ):
        """
        Given: member 토큰
        When: POST /api/v1/companies/{id}/members
        Then: 403 Forbidden, PERMISSION_003 에러
        """
        # Arrange
        invite_data = {
            "email": "someuser@test.com",
            "role": "member",
        }

        # Act
        response = await company_client.post(
            f"/api/v1/companies/{mock_company.id}/members",
            json=invite_data,
            headers=member_auth_headers,
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "PERMISSION_003"

    @pytest.mark.asyncio
    async def test_IT63_존재하지_않는_이메일_초대_404(
        self, company_client, mock_company, owner_auth_headers
    ):
        """
        Given: 시스템에 없는 이메일
        When: POST /api/v1/companies/{id}/members
        Then: 404 Not Found, COMPANY_008 에러
        """
        # Arrange
        invite_data = {
            "email": "nonexistent@test.com",
            "role": "member",
        }

        # Act
        response = await company_client.post(
            f"/api/v1/companies/{mock_company.id}/members",
            json=invite_data,
            headers=owner_auth_headers,
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "COMPANY_008"

    @pytest.mark.asyncio
    async def test_IT64_이미_멤버인_사용자_초대_409(
        self, company_client, mock_company, owner_auth_headers
    ):
        """
        Given: 기존 멤버 이메일
        When: POST /api/v1/companies/{id}/members
        Then: 409 Conflict, COMPANY_009 에러
        """
        # Arrange: 초대할 사용자를 store에 등록
        from src.services.company_service import _register_user
        from tests.conftest import MockUser
        target_user = MockUser(email="existingmember@test.com", name="기존멤버")
        target_user.company_id = None
        _register_user(target_user)

        invite_data = {
            "email": "existingmember@test.com",
            "role": "member",
        }

        # 첫 번째 초대 성공 후
        await company_client.post(
            f"/api/v1/companies/{mock_company.id}/members",
            json=invite_data,
            headers=owner_auth_headers,
        )

        # Act: 동일 이메일로 두 번째 초대
        response = await company_client.post(
            f"/api/v1/companies/{mock_company.id}/members",
            json=invite_data,
            headers=owner_auth_headers,
        )

        # Assert
        assert response.status_code == 409
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "COMPANY_009"

    @pytest.mark.asyncio
    async def test_IT65_다른_회사_소속_사용자_초대_409(
        self, company_client, mock_company, owner_auth_headers
    ):
        """
        Given: 다른 회사에 소속된 사용자 이메일
        When: POST /api/v1/companies/{id}/members
        Then: 409 Conflict, COMPANY_010 에러
        """
        # Arrange: 다른 회사에 소속된 사용자를 store에 등록
        from src.services.company_service import _register_user
        from tests.conftest import MockUser
        target_user = MockUser(email="othercompanymember@test.com", name="타회사멤버")
        target_user.company_id = str(uuid4())  # 다른 회사 ID
        _register_user(target_user)

        invite_data = {
            "email": "othercompanymember@test.com",
            "role": "member",
        }

        # Act
        response = await company_client.post(
            f"/api/v1/companies/{mock_company.id}/members",
            json=invite_data,
            headers=owner_auth_headers,
        )

        # Assert
        assert response.status_code == 409
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "COMPANY_010"

    @pytest.mark.asyncio
    async def test_IT66_멤버_목록_조회_200(
        self, company_client, mock_company, member_auth_headers
    ):
        """
        Given: member 토큰
        When: GET /api/v1/companies/{id}/members
        Then: 200 OK, items + meta 반환
        """
        # Act
        response = await company_client.get(
            f"/api/v1/companies/{mock_company.id}/members",
            headers=member_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "items" in data["data"]
        assert "page" in data["meta"]
        assert "total" in data["meta"]

    @pytest.mark.asyncio
    async def test_IT67_비멤버_멤버목록_조회_403(
        self, company_client, mock_company
    ):
        """
        Given: 해당 회사 비멤버 사용자
        When: GET /api/v1/companies/{id}/members
        Then: 403 Forbidden, PERMISSION_001 에러
        """
        # Arrange: 다른 회사 멤버의 토큰
        from src.core.security import create_access_token
        token = create_access_token(
            str(uuid4()),
            extra_data={"company_id": str(uuid4()), "role": "owner"}
        )
        other_headers = {"Authorization": f"Bearer {token}"}

        # Act
        response = await company_client.get(
            f"/api/v1/companies/{mock_company.id}/members",
            headers=other_headers,
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "PERMISSION_001"


# ============================================================
# 입력값 경계 테스트
# ============================================================

class TestCompanyInputBoundaries:
    """회사 관련 입력값 경계 조건 테스트"""

    @pytest.mark.asyncio
    async def test_회사명_200자_최대_성공(self, company_client, auth_headers):
        """
        Given: 회사명 200자
        When: POST /api/v1/companies
        Then: 201 Created (성공)
        """
        # Arrange
        data = {
            "businessNumber": "1234567891",
            "name": "가" * 200,  # 200자
            "scale": "small",
        }

        # Act
        response = await company_client.post(
            "/api/v1/companies", json=data, headers=auth_headers
        )

        # Assert
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_회사명_201자_초과_실패(self, company_client, auth_headers):
        """
        Given: 회사명 201자
        When: POST /api/v1/companies
        Then: 400 Bad Request, VALIDATION_003 에러
        """
        # Arrange
        data = {
            "businessNumber": "1234567891",
            "name": "가" * 201,  # 201자 - 초과
            "scale": "small",
        }

        # Act
        response = await company_client.post(
            "/api/v1/companies", json=data, headers=auth_headers
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] in ["VALIDATION_001", "VALIDATION_003"]

    @pytest.mark.asyncio
    async def test_사업자등록번호_0000000000_실패(self, company_client, auth_headers):
        """
        Given: 사업자등록번호 "0000000000" (모두 0)
        When: POST /api/v1/companies
        Then: 400 Bad Request, COMPANY_003 에러
        """
        # Arrange
        data = {
            "businessNumber": "0000000000",
            "name": "테스트 주식회사",
        }

        # Act
        response = await company_client.post(
            "/api/v1/companies", json=data, headers=auth_headers
        )

        # Assert
        assert response.status_code == 400
        response_data = response.json()
        assert response_data["error"]["code"] == "COMPANY_003"
