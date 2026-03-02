"""
JWT 토큰 생성/검증 단위 테스트

test-spec.md 기준:
- create_access_token: 기본/커스텀 만료 시간, 페이로드 검증
- create_refresh_token: 리프레시 토큰 생성
- decode_token: 유효/만료/변조된 토큰 처리
"""
import pytest
from datetime import datetime, timedelta, timezone
from jose import jwt
from jose.exceptions import JWTError as DecodeError, ExpiredSignatureError

from src.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    AuthError,
)
from src.config import get_settings

settings = get_settings()


class TestCreateAccessToken:
    """액세스 토큰 생성 테스트"""

    def test_기본_만료시간_1시간(self):
        """
        Given: user_id가 주어짐
        When: 기본 만료시간으로 액세스 토큰 생성
        Then: exp = now + 1시간
        """
        # Arrange
        user_id = "user-123"
        now = datetime.now(timezone.utc)

        # Act
        token = create_access_token(user_id)

        # Assert
        assert token is not None

        # 토큰 디코딩
        decoded = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        exp_time = datetime.fromtimestamp(decoded["exp"], timezone.utc)

        # 만료 시간이 현재 시간으로부터 약 1시간인지 확인
        time_diff = exp_time - now
        assert timedelta(minutes=59) <= time_diff <= timedelta(minutes=61)

    def test_커스텀_만료시간_2시간(self):
        """
        Given: user_id와 2시간 만료 delta가 주어짐
        When: 커스텀 만료시간으로 액세스 토큰 생성
        Then: exp = now + 2시간
        """
        # Arrange
        user_id = "user-123"
        expires_delta = timedelta(hours=2)
        now = datetime.now(timezone.utc)

        # Act
        token = create_access_token(user_id, expires_delta=expires_delta)

        # Assert
        assert token is not None

        # 토큰 디코딩
        decoded = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        exp_time = datetime.fromtimestamp(decoded["exp"], timezone.utc)

        # 만료 시간이 현재 시간으로부터 약 2시간인지 확인
        time_diff = exp_time - now
        assert timedelta(minutes=119) <= time_diff <= timedelta(minutes=121)

    def test_페이로드_필드_검증(self):
        """
        Given: user_id가 주어짐
        When: 액세스 토큰 생성
        Then: 페이로드에 sub, exp, iat 포함
        """
        # Arrange
        user_id = "user-123"

        # Act
        token = create_access_token(user_id)

        # Assert
        assert token is not None

        # 토큰 디코딩
        decoded = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])

        # 필드 존재 확인
        assert "sub" in decoded
        assert "exp" in decoded
        assert "iat" in decoded

        # 필드 값 확인
        assert decoded["sub"] == user_id
        assert decoded["iat"] is not None
        assert decoded["exp"] is not None

    def test_토큰_형식_검증(self):
        """
        Given: user_id가 주어짐
        When: 액세스 토큰 생성
        Then: JWT 형식의 토큰 반환 (3개의 .으로 구분)
        """
        # Arrange
        user_id = "user-123"

        # Act
        token = create_access_token(user_id)

        # Assert
        assert token is not None
        # JWT는 3개의 파트로 구성됨
        parts = token.split(".")
        assert len(parts) == 3


class TestCreateRefreshToken:
    """리프레시 토큰 생성 테스트"""

    def test_리프레시_토큰_생성_30일_만료(self):
        """
        Given: user_id가 주어짐
        When: 리프레시 토큰 생성
        Then: exp = now + 30일
        """
        # Arrange
        user_id = "user-123"
        now = datetime.now(timezone.utc)

        # Act
        token = create_refresh_token(user_id)

        # Assert
        assert token is not None

        # 토큰 디코딩
        decoded = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        exp_time = datetime.fromtimestamp(decoded["exp"], timezone.utc)

        # 만료 시간이 현재 시간으로부터 약 30일인지 확인
        time_diff = exp_time - now
        assert timedelta(days=29) <= time_diff <= timedelta(days=31)

    def test_리프레시_토큰에_jti_포함(self):
        """
        Given: user_id가 주어짐
        When: 리프레시 토큰 생성
        Then: 페이로드에 jti (JWT ID) 포함
        """
        # Arrange
        user_id = "user-123"

        # Act
        token = create_refresh_token(user_id)

        # Assert
        assert token is not None

        # 토큰 디코딩
        decoded = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])

        # jti 존재 확인
        assert "jti" in decoded
        assert decoded["jti"] is not None

    def test_리프레시_토큰_고유성(self):
        """
        Given: 동일한 user_id
        When: 리프레시 토큰을 2회 생성
        Then: 각각 다른 토큰 반환 (jti로 구분)
        """
        # Arrange
        user_id = "user-123"

        # Act
        token1 = create_refresh_token(user_id)
        token2 = create_refresh_token(user_id)

        # Assert
        assert token1 is not None
        assert token2 is not None
        assert token1 != token2

        # jti가 다른지 확인
        decoded1 = jwt.decode(token1, settings.secret_key, algorithms=[settings.algorithm])
        decoded2 = jwt.decode(token2, settings.secret_key, algorithms=[settings.algorithm])
        assert decoded1["jti"] != decoded2["jti"]


class TestDecodeToken:
    """토큰 디코딩 테스트"""

    def test_유효한_토큰_디코딩(self):
        """
        Given: 유효한 액세스 토큰
        When: 토큰 디코딩
        Then: 페이로드 디코딩 성공
        """
        # Arrange
        user_id = "user-123"
        token = create_access_token(user_id)

        # Act
        payload = decode_token(token)

        # Assert
        assert payload is not None
        assert payload["sub"] == user_id
        assert "exp" in payload
        assert "iat" in payload

    def test_만료된_토큰_디코딩(self):
        """
        Given: 만료된 액세스 토큰
        When: 토큰 디코딩
        Then: AUTH_003 에러 (토큰 만료)
        """
        # Arrange
        user_id = "user-123"
        expired_token = jwt.encode(
            {"sub": user_id, "exp": datetime.now(timezone.utc) - timedelta(hours=1)},
            settings.secret_key,
            algorithm=settings.algorithm,
        )

        # Act & Assert
        with pytest.raises(AuthError) as exc_info:
            decode_token(expired_token)

        assert exc_info.value.code == "AUTH_003"
        assert exc_info.value.status_code == 401

    def test_변조된_토큰_디코딩(self):
        """
        Given: 변조된 액세스 토큰
        When: 토큰 디코딩
        Then: AUTH_004 에러 (유효하지 않은 토큰)
        """
        # Arrange
        user_id = "user-123"
        valid_token = create_access_token(user_id)
        # 토큰 변조 (일부 변경)
        tampered_token = valid_token[:-10] + "tampered"

        # Act & Assert
        with pytest.raises(AuthError) as exc_info:
            decode_token(tampered_token)

        assert exc_info.value.code == "AUTH_004"

    def test_잘못된_시그니처(self):
        """
        Given: 다른 시크릿 키로 서명된 토큰
        When: 토큰 디코딩
        Then: AUTH_004 에러
        """
        # Arrange
        user_id = "user-123"
        # 다른 시크릿 키로 생성
        token = jwt.encode(
            {"sub": user_id, "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
            "different-secret-key",
            algorithm=settings.algorithm,
        )

        # Act & Assert
        with pytest.raises(AuthError) as exc_info:
            decode_token(token)

        assert exc_info.value.code == "AUTH_004"

    def test_빈_토큰_디코딩(self):
        """
        Given: 빈 문자열 토큰
        When: 토큰 디코딩
        Then: AUTH_002 에러 (토큰 없음)
        """
        # Arrange
        empty_token = ""

        # Act & Assert
        with pytest.raises(AuthError) as exc_info:
            decode_token(empty_token)

        assert exc_info.value.code == "AUTH_002"

    def test_None_토큰_디코딩(self):
        """
        Given: None 토큰
        When: 토큰 디코딩
        Then: AUTH_002 에러 (토큰 없음)
        """
        # Act & Assert
        with pytest.raises(AuthError) as exc_info:
            decode_token(None)

        assert exc_info.value.code == "AUTH_002"

    def test_잘못된_형식의_토큰(self):
        """
        Given: JWT 형식이 아닌 문자열
        When: 토큰 디코딩
        Then: AUTH_004 에러
        """
        # Arrange
        invalid_token = "not-a-valid-jwt-token"

        # Act & Assert
        with pytest.raises(AuthError) as exc_info:
            decode_token(invalid_token)

        assert exc_info.value.code == "AUTH_004"


class TestTokenPayload:
    """토큰 페이로드 관련 테스트"""

    def test_토큰에서_user_id_추출(self):
        """
        Given: 유효한 토큰
        When: user_id 추출
        Then: 정확한 user_id 반환
        """
        # Arrange
        user_id = "user-123"
        token = create_access_token(user_id)

        # Act
        payload = decode_token(token)
        extracted_id = payload["sub"]

        # Assert
        assert extracted_id == user_id

    def test_토큰에_추가_데이터_포함(self):
        """
        Given: user_id와 추가 데이터
        When: 액세스 토큰 생성
        Then: 페이로드에 추가 데이터 포함
        """
        # Arrange
        user_id = "user-123"
        extra_data = {
            "email": "user@example.com",
            "role": "owner",
            "company_id": "company-123",
        }

        # Act
        token = create_access_token(user_id, extra_data=extra_data)

        # Assert
        assert token is not None

        decoded = decode_token(token)
        assert decoded["sub"] == user_id
        assert decoded.get("email") == extra_data["email"]
        assert decoded.get("role") == extra_data["role"]
        assert decoded.get("company_id") == extra_data["company_id"]
