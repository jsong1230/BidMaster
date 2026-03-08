"""
인증 API 통합 테스트

test-spec.md 기준:
- POST /api/v1/auth/register: 회원가입
- POST /api/v1/auth/login: 로그인
- POST /api/v1/auth/logout: 로그아웃
- POST /api/v1/auth/refresh: 토큰 갱신
- GET /api/v1/auth/me: 현재 사용자 조회
"""
import pytest
from datetime import datetime, timezone
from uuid import uuid4

from tests.conftest import (
    AUTH_001,
    AUTH_002,
    AUTH_003,
    AUTH_004,
    AUTH_005,
    AUTH_006,
    AUTH_007,
    AUTH_008,
    AUTH_009,
    AUTH_010,
    AUTH_011,
    AUTH_012,
    AUTH_013,
    VALIDATION_001,
    VALIDATION_002,
    VALIDATION_003,
    ValidationError,
)


class TestRegisterAPI:
    """회원가입 API 테스트"""

    @pytest.mark.asyncio
    async def test_정상_회원가입(self, async_client, test_user_data):
        """
        Given: 유효한 이메일, 비밀번호, 이름
        When: POST /api/v1/auth/register
        Then: 201 Created, 사용자 정보 + 토큰 반환
        """
        # Arrange
        payload = {
            "email": test_user_data["email"],
            "password": test_user_data["password"],
            "name": test_user_data["name"],
            "phone": test_user_data.get("phone"),
        }

        # Act
        response = await async_client.post("/api/v1/auth/register", json=payload)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "user" in data["data"]
        assert "tokens" in data["data"]
        assert data["data"]["user"]["email"] == test_user_data["email"]
        assert data["data"]["user"]["name"] == test_user_data["name"]
        assert "accessToken" in data["data"]["tokens"]
        assert "refreshToken" in data["data"]["tokens"]

    @pytest.mark.asyncio
    async def test_중복_이메일_회원가입_실패(self, async_client, test_user_data):
        """
        Given: 이미 가입된 이메일
        When: POST /api/v1/auth/register
        Then: 409 Conflict, AUTH_007 에러
        """
        # Arrange
        payload = {
            "email": test_user_data["email"],
            "password": test_user_data["password"],
            "name": test_user_data["name"],
        }
        # 첫 번째 요청 (성공)
        await async_client.post("/api/v1/auth/register", json=payload)

        # Act: 동일 이메일로 두 번째 요청
        response = await async_client.post("/api/v1/auth/register", json=payload)

        # Assert
        assert response.status_code == 409
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "AUTH_007"

    @pytest.mark.asyncio
    async def test_약한_비밀번호로_회원가입_실패(self, async_client, test_user_data):
        """
        Given: 약한 비밀번호 "123456"
        When: POST /api/v1/auth/register
        Then: 400 Bad Request, VALIDATION_001 에러
        """
        # Arrange
        payload = {
            "email": test_user_data["email"],
            "password": "123456",
            "name": test_user_data["name"],
        }

        # Act
        response = await async_client.post("/api/v1/auth/register", json=payload)

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_001"

    @pytest.mark.asyncio
    async def test_잘못된_이메일_형식으로_회원가입_실패(self, async_client, test_user_data):
        """
        Given: 잘못된 이메일 형식
        When: POST /api/v1/auth/register
        Then: 400 Bad Request, VALIDATION_001 에러
        """
        # Arrange
        payload = {
            "email": "not-an-email",
            "password": test_user_data["password"],
            "name": test_user_data["name"],
        }

        # Act
        response = await async_client.post("/api/v1/auth/register", json=payload)

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_001"

    @pytest.mark.asyncio
    async def test_이름_누락으로_회원가입_실패(self, async_client, test_user_data):
        """
        Given: 이름 필드 누락
        When: POST /api/v1/auth/register
        Then: 400 Bad Request, VALIDATION_002 에러
        """
        # Arrange
        payload = {
            "email": test_user_data["email"],
            "password": test_user_data["password"],
            # name 누락
        }

        # Act
        response = await async_client.post("/api/v1/auth/register", json=payload)

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_002"


class TestLoginAPI:
    """로그인 API 테스트"""

    @pytest.mark.asyncio
    async def test_정상_로그인(self, async_client, test_user_data):
        """
        Given: 가입된 사용자
        When: POST /api/v1/auth/login
        Then: 200 OK, 토큰 + 사용자 정보 반환
        """
        # Arrange: 회원가입 먼저
        register_payload = {
            "email": test_user_data["email"],
            "password": test_user_data["password"],
            "name": test_user_data["name"],
        }
        await async_client.post("/api/v1/auth/register", json=register_payload)

        # Act: 로그인
        login_payload = {
            "email": test_user_data["email"],
            "password": test_user_data["password"],
        }
        response = await async_client.post("/api/v1/auth/login", json=login_payload)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "user" in data["data"]
        assert "tokens" in data["data"]
        assert data["data"]["user"]["email"] == test_user_data["email"]
        assert "accessToken" in data["data"]["tokens"]
        assert "refreshToken" in data["data"]["tokens"]

    @pytest.mark.asyncio
    async def test_잘못된_비밀번호로_로그인_실패(self, async_client, test_user_data):
        """
        Given: 가입된 사용자
        When: POST /api/v1/auth/login (잘못된 비밀번호)
        Then: 401 Unauthorized, AUTH_001 에러
        """
        # Arrange: 회원가입 먼저
        register_payload = {
            "email": test_user_data["email"],
            "password": test_user_data["password"],
            "name": test_user_data["name"],
        }
        await async_client.post("/api/v1/auth/register", json=register_payload)

        # Act: 잘못된 비밀번호로 로그인
        login_payload = {
            "email": test_user_data["email"],
            "password": "WrongP@ss",
        }
        response = await async_client.post("/api/v1/auth/login", json=login_payload)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "AUTH_001"

    @pytest.mark.asyncio
    async def test_존재하지_않는_이메일로_로그인_실패(self, async_client):
        """
        Given: 존재하지 않는 이메일
        When: POST /api/v1/auth/login
        Then: 401 Unauthorized, AUTH_001 에러 (동일 메시지)
        """
        # Arrange
        login_payload = {
            "email": "unknown@example.com",
            "password": "SomeP@ss123",
        }

        # Act
        response = await async_client.post("/api/v1/auth/login", json=login_payload)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "AUTH_001"
        assert "이메일 또는 비밀번호" in data["error"]["message"]

    @pytest.mark.asyncio
    async def test_탈퇴한_계정으로_로그인_실패(self, async_client, test_user_data, mock_deleted_user):
        """
        Given: 탈퇴한 계정
        When: POST /api/v1/auth/login
        Then: 403 Forbidden, AUTH_010 에러
        """
        # Arrange: 탈퇴한 계정으로 로그인 시도
        login_payload = {
            "email": mock_deleted_user.email,
            "password": test_user_data["password"],
        }

        # Act
        response = await async_client.post("/api/v1/auth/login", json=login_payload)

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "AUTH_010"


class TestRefreshTokenAPI:
    """토큰 갱신 API 테스트"""

    @pytest.mark.asyncio
    async def test_정상_토큰_갱신(self, async_client, test_user_data):
        """
        Given: 유효한 리프레시 토큰
        When: POST /api/v1/auth/refresh
        Then: 200 OK, 새 액세스 토큰 + 새 리프레시 토큰
        """
        # Arrange: 로그인하여 토큰 획득
        register_payload = {
            "email": test_user_data["email"],
            "password": test_user_data["password"],
            "name": test_user_data["name"],
        }
        await async_client.post("/api/v1/auth/register", json=register_payload)

        login_payload = {
            "email": test_user_data["email"],
            "password": test_user_data["password"],
        }
        login_response = await async_client.post("/api/v1/auth/login", json=login_payload)
        refresh_token = login_response.json()["data"]["tokens"]["refreshToken"]

        # Act: 토큰 갱신
        refresh_payload = {"refreshToken": refresh_token}
        response = await async_client.post("/api/v1/auth/refresh", json=refresh_payload)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "accessToken" in data["data"]
        assert "refreshToken" in data["data"]
        # 새 토큰이 이전과 다른지 확인
        assert data["data"]["accessToken"] != login_response.json()["data"]["tokens"]["accessToken"]
        assert data["data"]["refreshToken"] != refresh_token

    @pytest.mark.asyncio
    async def test_만료된_리프레시_토큰으로_갱신_실패(
        self, async_client, mock_expired_refresh_token
    ):
        """
        Given: 만료된 리프레시 토큰
        When: POST /api/v1/auth/refresh
        Then: 401 Unauthorized, AUTH_006 에러
        """
        # Arrange
        refresh_payload = {"refreshToken": "expired_token_value"}

        # Act
        response = await async_client.post("/api/v1/auth/refresh", json=refresh_payload)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "AUTH_006"

    @pytest.mark.asyncio
    async def test_폐기된_토큰으로_갱신_실패(self, async_client, mock_revoked_refresh_token):
        """
        Given: 폐기된(is_revoked=True) 리프레시 토큰
        When: POST /api/v1/auth/refresh
        Then: 401 Unauthorized, AUTH_005 에러
        """
        # Arrange
        refresh_payload = {"refreshToken": "revoked_token_value"}

        # Act
        response = await async_client.post("/api/v1/auth/refresh", json=refresh_payload)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "AUTH_005"

    @pytest.mark.asyncio
    async def test_기존_토큰_폐기_확인(self, async_client, test_user_data):
        """
        Given: 유효한 리프레시 토큰
        When: POST /api/v1/auth/refresh
        Then: 기존 토큰 is_revoked = True
        """
        # Arrange: 로그인하여 토큰 획득
        register_payload = {
            "email": test_user_data["email"],
            "password": test_user_data["password"],
            "name": test_user_data["name"],
        }
        await async_client.post("/api/v1/auth/register", json=register_payload)

        login_payload = {
            "email": test_user_data["email"],
            "password": test_user_data["password"],
        }
        login_response = await async_client.post("/api/v1/auth/login", json=login_payload)
        refresh_token = login_response.json()["data"]["tokens"]["refreshToken"]

        # Act: 토큰 갱신
        refresh_payload = {"refreshToken": refresh_token}
        await async_client.post("/api/v1/auth/refresh", json=refresh_payload)

        # Act: 이전 토큰으로 다시 갱신 시도
        response = await async_client.post("/api/v1/auth/refresh", json=refresh_payload)

        # Assert: 이미 사용된 토큰은 is_revoked=True이므로 AUTH_005 반환
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] in ("AUTH_005", "AUTH_006")


class TestLogoutAPI:
    """로그아웃 API 테스트"""

    @pytest.mark.asyncio
    async def test_정상_로그아웃(self, async_client, test_user_data):
        """
        Given: 로그인된 사용자
        When: POST /api/v1/auth/logout
        Then: 200 OK, 리프레시 토큰 무효화
        """
        # Arrange: 로그인하여 토큰 획득
        register_payload = {
            "email": test_user_data["email"],
            "password": test_user_data["password"],
            "name": test_user_data["name"],
        }
        await async_client.post("/api/v1/auth/register", json=register_payload)

        login_payload = {
            "email": test_user_data["email"],
            "password": test_user_data["password"],
        }
        login_response = await async_client.post("/api/v1/auth/login", json=login_payload)
        refresh_token = login_response.json()["data"]["tokens"]["refreshToken"]
        access_token = login_response.json()["data"]["tokens"]["accessToken"]

        # Act: 로그아웃
        logout_payload = {"refreshToken": refresh_token}
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await async_client.post(
            "/api/v1/auth/logout", json=logout_payload, headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_이미_로그아웃된_토큰으로_로그아웃_성공_멱등성(self, async_client, test_user_data):
        """
        Given: 이미 로그아웃된 토큰
        When: POST /api/v1/auth/logout
        Then: 200 OK (멱등성)
        """
        # Arrange
        logout_payload = {"refreshToken": "already_revoked_token"}

        # Act
        response = await async_client.post("/api/v1/auth/logout", json=logout_payload)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestGetCurrentUserAPI:
    """현재 사용자 조회 API 테스트"""

    @pytest.mark.asyncio
    async def test_정상_사용자_조회(self, async_client, test_user_data):
        """
        Given: 유효한 액세스 토큰
        When: GET /api/v1/auth/me
        Then: 200 OK, 사용자 정보 반환
        """
        # Arrange: 로그인하여 토큰 획득
        register_payload = {
            "email": test_user_data["email"],
            "password": test_user_data["password"],
            "name": test_user_data["name"],
        }
        await async_client.post("/api/v1/auth/register", json=register_payload)

        login_payload = {
            "email": test_user_data["email"],
            "password": test_user_data["password"],
        }
        login_response = await async_client.post("/api/v1/auth/login", json=login_payload)
        access_token = login_response.json()["data"]["tokens"]["accessToken"]

        # Act: 사용자 정보 조회
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await async_client.get("/api/v1/auth/me", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["email"] == test_user_data["email"]
        assert data["data"]["name"] == test_user_data["name"]

    @pytest.mark.asyncio
    async def test_토큰_없이_사용자_조회_실패(self, async_client):
        """
        Given: 인증 토큰 없음
        When: GET /api/v1/auth/me
        Then: 401 Unauthorized, AUTH_002 에러
        """
        # Act
        response = await async_client.get("/api/v1/auth/me")

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "AUTH_002"

    @pytest.mark.asyncio
    async def test_만료된_토큰으로_사용자_조회_실패(self, async_client):
        """
        Given: 만료된 액세스 토큰
        When: GET /api/v1/auth/me
        Then: 401 Unauthorized, AUTH_003 에러
        """
        # Arrange
        headers = {"Authorization": "Bearer expired_token"}

        # Act
        response = await async_client.get("/api/v1/auth/me", headers=headers)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "AUTH_003"


class TestOAuthKakaoAPI:
    """카카오 OAuth API 테스트"""

    @pytest.mark.asyncio
    async def test_OAuth_인증_URL_생성(self, async_client):
        """
        Given: redirect_url
        When: GET /api/v1/auth/oauth/kakao
        Then: 302 Redirect to Kakao OAuth
        """
        # Arrange
        params = {"redirect_url": "http://localhost:3000/auth/callback"}

        # Act
        response = await async_client.get("/api/v1/auth/oauth/kakao", params=params)

        # Assert
        assert response.status_code == 302
        assert "kakao.com" in response.headers.get("location", "")

    @pytest.mark.asyncio
    async def test_OAuth_콜백_정상처리_신규사용자(self, async_client):
        """
        Given: 유효한 code와 state
        When: GET /api/v1/auth/oauth/kakao/callback
        Then: 200 OK, 토큰 + 사용자 정보, isNewUser = True
        """
        # Arrange
        params = {"code": "valid_code", "state": "valid_state"}

        # Act
        response = await async_client.get(
            "/api/v1/auth/oauth/kakao/callback", params=params
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["user"]["isNewUser"] is True

    @pytest.mark.asyncio
    async def test_OAuth_콜백_잘못된_state(self, async_client):
        """
        Given: 유효한 code와 잘못된 state
        When: GET /api/v1/auth/oauth/kakao/callback
        Then: 400 Bad Request, AUTH_011 에러
        """
        # Arrange
        params = {"code": "valid_code", "state": "invalid_state"}

        # Act
        response = await async_client.get(
            "/api/v1/auth/oauth/kakao/callback", params=params
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "AUTH_011"


class TestPasswordResetAPI:
    """비밀번호 재설정 API 테스트"""

    @pytest.mark.asyncio
    async def test_비밀번호_찾기_요청_존재하는_이메일(self, async_client, test_user_data):
        """
        Given: 가입된 이메일
        When: POST /api/v1/auth/forgot-password
        Then: 200 OK, "이메일 발송 완료" 메시지
        """
        # Arrange: 회원가입 먼저
        register_payload = {
            "email": test_user_data["email"],
            "password": test_user_data["password"],
            "name": test_user_data["name"],
        }
        await async_client.post("/api/v1/auth/register", json=register_payload)

        # Act
        payload = {"email": test_user_data["email"]}
        response = await async_client.post("/api/v1/auth/forgot-password", json=payload)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "발송" in data["data"]["message"]

    @pytest.mark.asyncio
    async def test_비밀번호_찾기_요청_없는_이메일_동일_응답(self, async_client):
        """
        Given: 존재하지 않는 이메일
        When: POST /api/v1/auth/forgot-password
        Then: 200 OK (보안: 동일한 성공 응답)
        """
        # Arrange
        payload = {"email": "unknown@example.com"}

        # Act
        response = await async_client.post("/api/v1/auth/forgot-password", json=payload)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_비밀번호_재설정_정상처리(self, async_client, mock_password_reset_token):
        """
        Given: 유효한 재설정 토큰과 새 비밀번호
        When: POST /api/v1/auth/reset-password
        Then: 200 OK
        """
        # Arrange
        payload = {
            "token": "valid_reset_token",
            "newPassword": "NewSecureP@ss456",
        }

        # Act
        response = await async_client.post("/api/v1/auth/reset-password", json=payload)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_비밀번호_재설정_만료된_토큰(
        self, async_client, mock_expired_password_reset_token
    ):
        """
        Given: 만료된 재설정 토큰
        When: POST /api/v1/auth/reset-password
        Then: 400 Bad Request, AUTH_012 에러
        """
        # Arrange
        payload = {
            "token": "expired_reset_token",
            "newPassword": "NewSecureP@ss456",
        }

        # Act
        response = await async_client.post("/api/v1/auth/reset-password", json=payload)

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "AUTH_012"

    @pytest.mark.asyncio
    async def test_비밀번호_재설정_사용된_토큰(
        self, async_client, mock_used_password_reset_token
    ):
        """
        Given: 이미 사용된 재설정 토큰
        When: POST /api/v1/auth/reset-password
        Then: 400 Bad Request, AUTH_013 에러
        """
        # Arrange
        payload = {
            "token": "used_reset_token",
            "newPassword": "NewSecureP@ss456",
        }

        # Act
        response = await async_client.post("/api/v1/auth/reset-password", json=payload)

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "AUTH_013"


class TestChangePasswordAPI:
    """비밀번호 변경 API 테스트"""

    @pytest.mark.asyncio
    async def test_비밀번호_변경_정상처리(self, async_client, test_user_data):
        """
        Given: 로그인된 사용자, 올바른 현재 비밀번호, 새 비밀번호
        When: POST /api/v1/auth/change-password
        Then: 200 OK
        """
        # Arrange: 로그인
        register_payload = {
            "email": test_user_data["email"],
            "password": test_user_data["password"],
            "name": test_user_data["name"],
        }
        await async_client.post("/api/v1/auth/register", json=register_payload)

        login_payload = {
            "email": test_user_data["email"],
            "password": test_user_data["password"],
        }
        login_response = await async_client.post("/api/v1/auth/login", json=login_payload)
        access_token = login_response.json()["data"]["tokens"]["accessToken"]

        # Act: 비밀번호 변경
        payload = {
            "currentPassword": test_user_data["password"],
            "newPassword": "NewSecureP@ss456",
        }
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await async_client.post(
            "/api/v1/auth/change-password", json=payload, headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_비밀번호_변경_현재비밀번호_불일치(self, async_client, test_user_data):
        """
        Given: 로그인된 사용자, 잘못된 현재 비밀번호
        When: POST /api/v1/auth/change-password
        Then: 401 Unauthorized, AUTH_001 에러
        """
        # Arrange: 로그인
        register_payload = {
            "email": test_user_data["email"],
            "password": test_user_data["password"],
            "name": test_user_data["name"],
        }
        await async_client.post("/api/v1/auth/register", json=register_payload)

        login_payload = {
            "email": test_user_data["email"],
            "password": test_user_data["password"],
        }
        login_response = await async_client.post("/api/v1/auth/login", json=login_payload)
        access_token = login_response.json()["data"]["tokens"]["accessToken"]

        # Act: 잘못된 현재 비밀번호로 변경 시도
        payload = {
            "currentPassword": "WrongP@ss",
            "newPassword": "NewSecureP@ss456",
        }
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await async_client.post(
            "/api/v1/auth/change-password", json=payload, headers=headers
        )

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "AUTH_001"

    @pytest.mark.asyncio
    async def test_비밀번호_변경_이전비밀번호_재사용(self, async_client, test_user_data):
        """
        Given: 로그인된 사용자, 이전 비밀번호와 동일한 새 비밀번호
        When: POST /api/v1/auth/change-password
        Then: 400 Bad Request, AUTH_008 에러
        """
        # Arrange: 로그인
        register_payload = {
            "email": test_user_data["email"],
            "password": test_user_data["password"],
            "name": test_user_data["name"],
        }
        await async_client.post("/api/v1/auth/register", json=register_payload)

        login_payload = {
            "email": test_user_data["email"],
            "password": test_user_data["password"],
        }
        login_response = await async_client.post("/api/v1/auth/login", json=login_payload)
        access_token = login_response.json()["data"]["tokens"]["accessToken"]

        # Act: 이전 비밀번호와 동일한 비밀번호로 변경 시도
        payload = {
            "currentPassword": test_user_data["password"],
            "newPassword": test_user_data["password"],  # 동일
        }
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await async_client.post(
            "/api/v1/auth/change-password", json=payload, headers=headers
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "AUTH_008"


class TestDeleteAccountAPI:
    """계정 탈퇴 API 테스트"""

    @pytest.mark.asyncio
    async def test_계정_탈퇴_정상처리(self, async_client, test_user_data):
        """
        Given: 로그인된 사용자, 올바른 비밀번호
        When: DELETE /api/v1/auth/me
        Then: 200 OK, deleted_at 설정
        """
        # Arrange: 로그인
        register_payload = {
            "email": test_user_data["email"],
            "password": test_user_data["password"],
            "name": test_user_data["name"],
        }
        await async_client.post("/api/v1/auth/register", json=register_payload)

        login_payload = {
            "email": test_user_data["email"],
            "password": test_user_data["password"],
        }
        login_response = await async_client.post("/api/v1/auth/login", json=login_payload)
        access_token = login_response.json()["data"]["tokens"]["accessToken"]

        # Act: 계정 탈퇴
        import json as _json
        payload = {"password": test_user_data["password"], "reason": "서비스 불만족"}
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        response = await async_client.request(
            "DELETE", "/api/v1/auth/me",
            content=_json.dumps(payload).encode(),
            headers=headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_계정_탈퇴_비밀번호_불일치(self, async_client, test_user_data):
        """
        Given: 로그인된 사용자, 잘못된 비밀번호
        When: DELETE /api/v1/auth/me
        Then: 401 Unauthorized, AUTH_001 에러
        """
        # Arrange: 로그인
        register_payload = {
            "email": test_user_data["email"],
            "password": test_user_data["password"],
            "name": test_user_data["name"],
        }
        await async_client.post("/api/v1/auth/register", json=register_payload)

        login_payload = {
            "email": test_user_data["email"],
            "password": test_user_data["password"],
        }
        login_response = await async_client.post("/api/v1/auth/login", json=login_payload)
        access_token = login_response.json()["data"]["tokens"]["accessToken"]

        # Act: 잘못된 비밀번호로 탈퇴 시도
        import json as _json
        payload = {"password": "WrongP@ss", "reason": "서비스 불만족"}
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        response = await async_client.request(
            "DELETE", "/api/v1/auth/me",
            content=_json.dumps(payload).encode(),
            headers=headers,
        )

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "AUTH_001"
