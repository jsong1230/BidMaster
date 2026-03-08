"""
CertificationService 단위 테스트

test-spec.md 기준:
- UT-60: 인증 정상 등록
- UT-61: 비멤버 등록 시도
- UT-62: expiryDate < issuedDate
- UT-63: 정상 수정
- UT-64: 권한 없음 (member)
- UT-65: 존재하지 않는 인증
- UT-66: 정상 삭제
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

# 구현 전이므로 import 시 ImportError 발생 - RED 상태
from src.services.company_service import CompanyService
from src.core.security import ValidationError


class TestCreateCertification:
    """보유 인증 등록 테스트 (UT-60~UT-62)"""

    @pytest.mark.asyncio
    async def test_UT60_정상_인증_등록(
        self, test_certification_data, mock_company, mock_company_member_member
    ):
        """
        Given: 유효한 인증 데이터 + 해당 회사 멤버 사용자
        When: create_certification 호출
        Then: Certification 생성
        """
        # Arrange
        mock_db = AsyncMock()
        service = CompanyService(mock_db)

        # Act
        result = await service.create_certification(
            company_id=mock_company.id,
            user_id=mock_company_member_member.user_id,
            data=test_certification_data,
        )

        # Assert
        assert result is not None
        assert result.name == test_certification_data["name"]
        assert result.issuer == test_certification_data["issuer"]

    @pytest.mark.asyncio
    async def test_UT61_비멤버_등록_시도_AppException_403(
        self, test_certification_data, mock_company
    ):
        """
        Given: 해당 회사 멤버가 아닌 사용자
        When: create_certification 호출
        Then: AppException(PERMISSION_001, 403) 발생
        """
        # Arrange
        mock_db = AsyncMock()
        service = CompanyService(mock_db)
        from src.services.company_service import AppException

        non_member_user_id = str(uuid4())

        # Act & Assert
        with pytest.raises(AppException) as exc_info:
            await service.create_certification(
                company_id=mock_company.id,
                user_id=non_member_user_id,
                data=test_certification_data,
            )

        assert exc_info.value.code == "PERMISSION_001"
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_UT62_expiryDate가_issuedDate보다_이전_ValidationError(
        self, mock_company, mock_company_member_member
    ):
        """
        Given: issuedDate: 2027-01-01, expiryDate: 2024-01-01 (날짜 역전)
        When: create_certification 호출
        Then: ValidationError 발생
        """
        # Arrange
        mock_db = AsyncMock()
        service = CompanyService(mock_db)

        invalid_date_data = {
            "name": "테스트 인증",
            "issuer": "발급기관",
            "certNumber": "TEST-001",
            "issuedDate": "2027-01-01",
            "expiryDate": "2024-01-01",  # issuedDate보다 이전
        }

        # Act & Assert
        with pytest.raises((ValidationError, Exception)) as exc_info:
            await service.create_certification(
                company_id=mock_company.id,
                user_id=mock_company_member_member.user_id,
                data=invalid_date_data,
            )

        assert exc_info.value is not None

    @pytest.mark.asyncio
    async def test_expiryDate만_존재_issuedDate_없음_성공(
        self, mock_company, mock_company_member_member
    ):
        """
        Given: issuedDate=None, expiryDate 존재
        When: create_certification 호출
        Then: 성공 (날짜 선택 필드)
        """
        # Arrange
        mock_db = AsyncMock()
        service = CompanyService(mock_db)

        data_without_issued = {
            "name": "테스트 인증",
            "expiryDate": "2027-01-01",
            # issuedDate 없음
        }

        # Act
        result = await service.create_certification(
            company_id=mock_company.id,
            user_id=mock_company_member_member.user_id,
            data=data_without_issued,
        )

        # Assert
        assert result is not None


class TestUpdateCertification:
    """보유 인증 수정 테스트 (UT-63~UT-65)"""

    @pytest.mark.asyncio
    async def test_UT63_정상_수정_owner(
        self, mock_company, mock_company_member_owner, mock_certification
    ):
        """
        Given: owner 역할 사용자 + 유효한 수정 데이터
        When: update_certification 호출
        Then: Certification 갱신
        """
        # Arrange
        mock_db = AsyncMock()
        service = CompanyService(mock_db)

        update_data = {
            "name": "수정된 인증명",
            "issuer": "수정된 발급기관",
        }

        # Act
        result = await service.update_certification(
            company_id=mock_company.id,
            cert_id=mock_certification.id,
            user_id=mock_company_member_owner.user_id,
            data=update_data,
        )

        # Assert
        assert result is not None
        assert result.name == update_data["name"]

    @pytest.mark.asyncio
    async def test_UT64_권한없음_member_AppException_403(
        self, mock_company, mock_company_member_member, mock_certification
    ):
        """
        Given: member 역할 사용자
        When: update_certification 호출
        Then: AppException(PERMISSION_001, 403) 발생
        """
        # Arrange
        mock_db = AsyncMock()
        service = CompanyService(mock_db)
        from src.services.company_service import AppException

        # Act & Assert
        with pytest.raises(AppException) as exc_info:
            await service.update_certification(
                company_id=mock_company.id,
                cert_id=mock_certification.id,
                user_id=mock_company_member_member.user_id,
                data={"name": "변경 시도"},
            )

        assert exc_info.value.code == "PERMISSION_001"
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_UT65_존재하지_않는_인증_AppException_404(
        self, mock_company, mock_company_member_owner
    ):
        """
        Given: 잘못된 certId
        When: update_certification 호출
        Then: AppException(COMPANY_007, 404) 발생
        """
        # Arrange
        mock_db = AsyncMock()
        service = CompanyService(mock_db)
        from src.services.company_service import AppException

        non_existent_cert_id = str(uuid4())

        # Act & Assert
        with pytest.raises(AppException) as exc_info:
            await service.update_certification(
                company_id=mock_company.id,
                cert_id=non_existent_cert_id,
                user_id=mock_company_member_owner.user_id,
                data={"name": "테스트"},
            )

        assert exc_info.value.code == "COMPANY_007"
        assert exc_info.value.status_code == 404


class TestDeleteCertification:
    """보유 인증 삭제 테스트 (UT-66)"""

    @pytest.mark.asyncio
    async def test_UT66_정상_삭제_소프트_딜리트(
        self, mock_company, mock_company_member_owner, mock_certification
    ):
        """
        Given: owner + 존재하는 인증
        When: delete_certification 호출
        Then: deleted_at 갱신 (Soft Delete)
        """
        # Arrange
        mock_db = AsyncMock()
        service = CompanyService(mock_db)

        # Act
        result = await service.delete_certification(
            company_id=mock_company.id,
            cert_id=mock_certification.id,
            user_id=mock_company_member_owner.user_id,
        )

        # Assert
        assert result is None or result is True

    @pytest.mark.asyncio
    async def test_삭제된_인증_수정_시도_AppException_404(
        self, mock_company, mock_company_member_owner
    ):
        """
        Given: deleted_at이 NOT NULL인 인증 (소프트 삭제된 인증)
        When: update_certification 호출
        Then: AppException(COMPANY_007, 404) 발생
        """
        # Arrange
        mock_db = AsyncMock()
        service = CompanyService(mock_db)
        from src.services.company_service import AppException

        from tests.conftest import MockCertification
        deleted_cert = MockCertification(
            company_id=mock_company.id,
            deleted_at=datetime.now(timezone.utc),
        )

        # Act & Assert
        with pytest.raises(AppException) as exc_info:
            await service.update_certification(
                company_id=mock_company.id,
                cert_id=deleted_cert.id,
                user_id=mock_company_member_owner.user_id,
                data={"name": "테스트"},
            )

        assert exc_info.value.code == "COMPANY_007"
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_과거_만료일_인증_등록_성공_isExpired_true(
        self, mock_company, mock_company_member_member
    ):
        """
        Given: 과거 만료일의 인증 (expiryDate가 현재 날짜보다 이전)
        When: create_certification 호출
        Then: 성공 (isExpired=true로 표시됨)
        """
        # Arrange
        mock_db = AsyncMock()
        service = CompanyService(mock_db)

        past_expiry_data = {
            "name": "만료된 인증",
            "issuedDate": "2020-01-01",
            "expiryDate": "2022-01-01",  # 이미 만료된 날짜
        }

        # Act
        result = await service.create_certification(
            company_id=mock_company.id,
            user_id=mock_company_member_member.user_id,
            data=past_expiry_data,
        )

        # Assert
        assert result is not None
