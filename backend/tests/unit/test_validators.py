"""
사업자등록번호 검증 유틸리티 단위 테스트

test-spec.md 기준:
- UT-01: 유효한 사업자등록번호 - True 반환
- UT-02: 10자리 미만 - ValidationError(COMPANY_003)
- UT-03: 10자리 초과 - ValidationError(COMPANY_003)
- UT-04: 숫자가 아닌 문자 포함 - ValidationError(COMPANY_003)
- UT-05: 빈 문자열 - ValidationError(COMPANY_003)
- UT-06: 체크섬 불일치 - ValidationError(COMPANY_003)
- UT-07: 모두 0 - ValidationError(COMPANY_003)
"""
import pytest

# 구현 전이므로 import 시 ImportError 발생 - RED 상태
from src.utils.validators import validate_business_number
from src.core.security import ValidationError


class TestValidateBusinessNumber:
    """사업자등록번호 검증 함수 테스트"""

    def test_UT01_유효한_사업자등록번호_True_반환(self):
        """
        Given: 유효한 체크섬을 가진 사업자등록번호 "1234567890"
        When: validate_business_number 호출
        Then: True 반환
        """
        # Arrange
        # 사업자등록번호 체크섬 알고리즘:
        # 가중치: [1, 3, 7, 1, 3, 7, 1, 3, 5]
        # "1234567890" - 실제 유효한 번호로 가정 (테스트 명세 기준)
        valid_number = "1234567890"

        # Act
        result = validate_business_number(valid_number)

        # Assert
        assert result is True

    def test_UT02_10자리_미만_ValidationError(self):
        """
        Given: 8자리 사업자등록번호 "12345678"
        When: validate_business_number 호출
        Then: ValidationError (COMPANY_003) 발생
        """
        # Arrange
        short_number = "12345678"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            validate_business_number(short_number)

        assert exc_info.value.code == "COMPANY_003"

    def test_UT03_10자리_초과_ValidationError(self):
        """
        Given: 11자리 사업자등록번호 "12345678901"
        When: validate_business_number 호출
        Then: ValidationError (COMPANY_003) 발생
        """
        # Arrange
        long_number = "12345678901"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            validate_business_number(long_number)

        assert exc_info.value.code == "COMPANY_003"

    def test_UT04_숫자가_아닌_문자_포함_ValidationError(self):
        """
        Given: 알파벳이 포함된 사업자등록번호 "123456789a"
        When: validate_business_number 호출
        Then: ValidationError (COMPANY_003) 발생
        """
        # Arrange
        alpha_number = "123456789a"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            validate_business_number(alpha_number)

        assert exc_info.value.code == "COMPANY_003"

    def test_UT05_빈_문자열_ValidationError(self):
        """
        Given: 빈 문자열 ""
        When: validate_business_number 호출
        Then: ValidationError (COMPANY_003) 발생
        """
        # Arrange
        empty_number = ""

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            validate_business_number(empty_number)

        assert exc_info.value.code == "COMPANY_003"

    def test_UT06_체크섬_불일치_ValidationError(self):
        """
        Given: 체크섬이 불일치하는 사업자등록번호 "1234567891"
        When: validate_business_number 호출
        Then: ValidationError (COMPANY_003) 발생
        """
        # Arrange
        # "1234567891" - 마지막 자리가 체크섬과 불일치하는 번호
        invalid_checksum_number = "1234567891"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            validate_business_number(invalid_checksum_number)

        assert exc_info.value.code == "COMPANY_003"

    def test_UT07_모두_0_ValidationError(self):
        """
        Given: 모두 0인 사업자등록번호 "0000000000"
        When: validate_business_number 호출
        Then: ValidationError (COMPANY_003) 발생
        """
        # Arrange
        all_zeros = "0000000000"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            validate_business_number(all_zeros)

        assert exc_info.value.code == "COMPANY_003"

    def test_하이픈_포함_번호_ValidationError(self):
        """
        Given: 하이픈이 포함된 사업자등록번호 "123-45-67890"
        When: validate_business_number 호출
        Then: ValidationError (COMPANY_003) 발생
        """
        # Arrange
        hyphen_number = "123-45-67890"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            validate_business_number(hyphen_number)

        assert exc_info.value.code == "COMPANY_003"

    def test_공백_포함_번호_ValidationError(self):
        """
        Given: 공백이 포함된 사업자등록번호 "1234 567890"
        When: validate_business_number 호출
        Then: ValidationError (COMPANY_003) 발생
        """
        # Arrange
        space_number = "1234 567890"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            validate_business_number(space_number)

        assert exc_info.value.code == "COMPANY_003"

    def test_None_입력_ValidationError(self):
        """
        Given: None 입력
        When: validate_business_number 호출
        Then: ValidationError (COMPANY_003) 발생
        """
        # Act & Assert
        with pytest.raises((ValidationError, TypeError)):
            validate_business_number(None)
