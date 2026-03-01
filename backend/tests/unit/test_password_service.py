"""
비밀번호 해싱/검증 단위 테스트

test-spec.md 기준:
- get_password_hash: 일반 비밀번호 해싱
- verify_password: 올바른/잘못된 비밀번호 검증
"""
import pytest

# TODO: 구현 후 import 수정
# from src.core.security import get_password_hash, verify_password


class TestPasswordHashing:
    """비밀번호 해싱 기능 테스트"""

    def test_일반_비밀번호_해싱(self):
        """
        Given: 일반 비밀번호 "SecureP@ss123"
        When: 비밀번호 해싱 함수 호출
        Then: bcrypt 해시 문자열 반환 ($2b$12$...)
        """
        # Arrange
        password = "SecureP@ss123"

        # Act
        # hash_result = get_password_hash(password)
        hash_result = None  # TODO: 구현 후 제거

        # Assert
        assert hash_result is not None
        assert hash_result.startswith("$2b$")
        assert len(hash_result) == 60  # bcrypt 해시 표준 길이

    def test_동일_비밀번호_해싱_다른_결과(self):
        """
        Given: 동일한 비밀번호 "SecureP@ss123"
        When: 비밀번호 해싱 함수 2회 호출
        Then: 매번 다른 해시값 반환 (salt 적용)
        """
        # Arrange
        password = "SecureP@ss123"

        # Act
        # hash1 = get_password_hash(password)
        # hash2 = get_password_hash(password)
        hash1 = None  # TODO: 구현 후 제거
        hash2 = None  # TODO: 구현 후 제거

        # Assert
        assert hash1 is not None
        assert hash2 is not None
        assert hash1 != hash2  # salt로 인해 다른 해시

    def test_올바른_비밀번호_검증(self):
        """
        Given: 원본 비밀번호와 그 해시값
        When: verify_password 호출
        Then: True 반환
        """
        # Arrange
        password = "SecureP@ss123"
        # password_hash = get_password_hash(password)
        password_hash = None  # TODO: 구현 후 제거

        # Act
        # result = verify_password(password, password_hash)
        result = False  # TODO: 구현 후 제거

        # Assert
        assert result is True

    def test_잘못된_비밀번호_검증(self):
        """
        Given: 원본 비밀번호와 다른 비밀번호
        When: verify_password 호출
        Then: False 반환
        """
        # Arrange
        password = "SecureP@ss123"
        wrong_password = "WrongP@ss"
        # password_hash = get_password_hash(password)
        password_hash = None  # TODO: 구현 후 제거

        # Act
        # result = verify_password(wrong_password, password_hash)
        result = True  # TODO: 구현 후 제거 (올바르면 False여야 함)

        # Assert
        assert result is False

    def test_빈_비밀번호_검증(self):
        """
        Given: 빈 비밀번호
        When: verify_password 호출
        Then: False 반환
        """
        # Arrange
        password = "SecureP@ss123"
        empty_password = ""
        # password_hash = get_password_hash(password)
        password_hash = None  # TODO: 구현 후 제거

        # Act
        # result = verify_password(empty_password, password_hash)
        result = True  # TODO: 구현 후 제거 (올바르면 False여야 함)

        # Assert
        assert result is False


class TestPasswordValidation:
    """비밀번호 유효성 검사 테스트"""

    def test_비밀번호_최소_길이_8자(self):
        """
        Given: 8자 이상의 비밀번호
        When: 비밀번호 유효성 검사
        Then: 검사 통과
        """
        # Arrange
        password = "SecureP@ss123"  # 14자

        # Act
        # is_valid = validate_password(password)
        is_valid = False  # TODO: 구현 후 제거

        # Assert
        assert is_valid is True

    def test_비밀번호_최소_길이_미달(self):
        """
        Given: 7자 비밀번호
        When: 비밀번호 유효성 검사
        Then: VALIDATION_001 에러
        """
        # Arrange
        password = "Secur12"  # 7자

        # Act
        # is_valid = validate_password(password)
        is_valid = True  # TODO: 구현 후 제거 (올바르면 False여야 함)

        # Assert
        assert is_valid is False

    def test_비밀번호_최대_길이_64자(self):
        """
        Given: 64자 이하의 비밀번호
        When: 비밀번호 유효성 검사
        Then: 검사 통과
        """
        # Arrange
        password = "A" * 64

        # Act
        # is_valid = validate_password(password)
        is_valid = False  # TODO: 구현 후 제거

        # Assert
        assert is_valid is True

    def test_비밀번호_최대_길이_초과(self):
        """
        Given: 65자 비밀번호
        When: 비밀번호 유효성 검사
        Then: VALIDATION_003 에러
        """
        # Arrange
        password = "A" * 65

        # Act
        # is_valid = validate_password(password)
        is_valid = True  # TODO: 구현 후 제거 (올바르면 False여야 함)

        # Assert
        assert is_valid is False

    def test_약한_비밀번호_검사(self):
        """
        Given: "123456" 같은 약한 비밀번호
        When: 비밀번호 유효성 검사
        Then: VALIDATION_001 에러
        """
        # Arrange
        password = "123456"

        # Act
        # is_valid = validate_password(password)
        is_valid = True  # TODO: 구현 후 제거 (올바르면 False여야 함)

        # Assert
        assert is_valid is False

    def test_영문_숫자_특수문자_조합_검사(self):
        """
        Given: 영문 대소문자, 숫자, 특수문자 조합
        When: 비밀번호 유효성 검사
        Then: 검사 통과
        """
        # Arrange
        password = "SecureP@ss123"

        # Act
        # is_valid = validate_password(password)
        is_valid = False  # TODO: 구현 후 제거

        # Assert
        assert is_valid is True
