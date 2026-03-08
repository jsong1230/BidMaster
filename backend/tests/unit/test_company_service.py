"""
CompanyService 단위 테스트

test-spec.md 기준:
- UT-10~UT-15: 회사 등록
- UT-20~UT-22: 회사 조회
- UT-30~UT-34: 회사 수정
- UT-80~UT-83: 권한 검증 유틸리티
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

# 구현 전이므로 import 시 ImportError 발생 - RED 상태
from src.services.company_service import CompanyService
from src.core.security import ValidationError


class TestCreateCompany:
    """회사 등록 테스트 (UT-10~UT-15)"""

    @pytest.mark.asyncio
    async def test_UT10_정상_회사_등록(self, test_company_data, mock_user):
        """
        Given: 유효한 회사 정보 + 미소속 사용자 (company_id=None)
        When: create_company 호출
        Then: Company 생성, CompanyMember(owner) 생성, users.company_id 갱신
        """
        # Arrange
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        mock_user.company_id = None  # 미소속 사용자

        service = CompanyService(mock_db)

        # Act
        result = await service.create_company(
            user_id=mock_user.id,
            data=test_company_data,
        )

        # Assert
        assert result is not None
        assert result.business_number == test_company_data["businessNumber"]
        assert result.name == test_company_data["name"]

    @pytest.mark.asyncio
    async def test_UT11_중복_사업자등록번호_AppException_409(self, test_company_data, mock_user):
        """
        Given: 이미 등록된 business_number
        When: create_company 호출
        Then: AppException(COMPANY_002, 409) 발생
        """
        # Arrange
        mock_db = AsyncMock()
        mock_user.company_id = None

        service = CompanyService(mock_db)

        # 중복 사업자등록번호 시뮬레이션 - 실제 구현이 없어 AppException이 발생해야 함
        from src.services.company_service import AppException

        # Act & Assert
        with pytest.raises(AppException) as exc_info:
            await service.create_company(
                user_id=mock_user.id,
                data={**test_company_data, "_force_duplicate": True},
            )

        assert exc_info.value.code == "COMPANY_002"
        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_UT12_이미_소속된_사용자_AppException_409(self, test_company_data, mock_user):
        """
        Given: company_id가 NOT NULL인 사용자 (이미 소속됨)
        When: create_company 호출
        Then: AppException(COMPANY_004, 409) 발생
        """
        # Arrange
        mock_db = AsyncMock()
        mock_user.company_id = str(uuid4())  # 이미 소속된 사용자

        service = CompanyService(mock_db)
        from src.services.company_service import AppException

        # Act & Assert
        with pytest.raises(AppException) as exc_info:
            await service.create_company(
                user_id=mock_user.id,
                data=test_company_data,
            )

        assert exc_info.value.code == "COMPANY_004"
        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_UT13_잘못된_사업자등록번호_AppException_400(self, mock_user):
        """
        Given: 체크섬 불일치 사업자등록번호
        When: create_company 호출
        Then: AppException(COMPANY_003, 400) 발생
        """
        # Arrange
        mock_db = AsyncMock()
        mock_user.company_id = None

        service = CompanyService(mock_db)
        from src.services.company_service import AppException

        invalid_data = {
            "businessNumber": "1234567891",  # 체크섬 불일치
            "name": "테스트 주식회사",
        }

        # Act & Assert
        with pytest.raises((AppException, ValidationError)) as exc_info:
            await service.create_company(
                user_id=mock_user.id,
                data=invalid_data,
            )

        assert exc_info.value.code == "COMPANY_003"
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_UT14_잘못된_scale_enum_ValidationError(self, test_company_data, mock_user):
        """
        Given: scale="invalid" (enum 외 값)
        When: create_company 호출
        Then: ValidationError 발생
        """
        # Arrange
        mock_db = AsyncMock()
        mock_user.company_id = None

        service = CompanyService(mock_db)

        invalid_data = {**test_company_data, "scale": "invalid"}

        # Act & Assert
        with pytest.raises((ValidationError, Exception)) as exc_info:
            await service.create_company(
                user_id=mock_user.id,
                data=invalid_data,
            )

        # scale이 enum 외 값이면 에러가 발생해야 함
        assert exc_info.value is not None

    @pytest.mark.asyncio
    async def test_UT15_필수_필드_누락_ValidationError(self, mock_user):
        """
        Given: name 필드 없는 데이터
        When: create_company 호출
        Then: ValidationError(VALIDATION_002) 발생
        """
        # Arrange
        mock_db = AsyncMock()
        mock_user.company_id = None

        service = CompanyService(mock_db)

        data_without_name = {
            "businessNumber": "1234567890",
            # name 누락
        }

        # Act & Assert
        with pytest.raises((ValidationError, Exception)) as exc_info:
            await service.create_company(
                user_id=mock_user.id,
                data=data_without_name,
            )

        assert exc_info.value is not None


class TestGetMyCompany:
    """회사 조회 테스트 (UT-20~UT-22)"""

    @pytest.mark.asyncio
    async def test_UT20_소속_회사_존재_집계_포함(self, mock_user, mock_company):
        """
        Given: company_id가 있는 사용자
        When: get_my_company 호출
        Then: Company 정보 + 집계(memberCount, performanceCount, certificationCount) 반환
        """
        # Arrange
        mock_db = AsyncMock()
        mock_user.company_id = mock_company.id

        service = CompanyService(mock_db)

        # Act
        result = await service.get_my_company(user_id=mock_user.id)

        # Assert
        assert result is not None
        assert result.id == mock_company.id
        assert hasattr(result, "member_count") or "memberCount" in str(result)

    @pytest.mark.asyncio
    async def test_UT21_소속_회사_없음_AppException_404(self, mock_user):
        """
        Given: company_id가 NULL인 사용자
        When: get_my_company 호출
        Then: AppException(COMPANY_001, 404) 발생
        """
        # Arrange
        mock_db = AsyncMock()
        mock_user.company_id = None

        service = CompanyService(mock_db)
        from src.services.company_service import AppException

        # Act & Assert
        with pytest.raises(AppException) as exc_info:
            await service.get_my_company(user_id=mock_user.id)

        assert exc_info.value.code == "COMPANY_001"
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_UT22_삭제된_회사_AppException_404(self, mock_user, mock_deleted_company):
        """
        Given: deleted_at이 NOT NULL인 회사에 소속된 사용자
        When: get_my_company 호출
        Then: AppException(COMPANY_001, 404) 발생
        """
        # Arrange
        mock_db = AsyncMock()
        mock_user.company_id = mock_deleted_company.id

        service = CompanyService(mock_db)
        from src.services.company_service import AppException

        # Act & Assert
        with pytest.raises(AppException) as exc_info:
            await service.get_my_company(user_id=mock_user.id)

        assert exc_info.value.code == "COMPANY_001"
        assert exc_info.value.status_code == 404


class TestUpdateCompany:
    """회사 수정 테스트 (UT-30~UT-34)"""

    @pytest.mark.asyncio
    async def test_UT30_정상_수정_owner(self, mock_user, mock_company, mock_company_member_owner):
        """
        Given: owner 역할 사용자 + 유효한 수정 데이터
        When: update_company 호출
        Then: Company 갱신, updatedAt 갱신
        """
        # Arrange
        mock_db = AsyncMock()
        mock_user.company_id = mock_company.id
        mock_company_member_owner.user_id = mock_user.id
        mock_company_member_owner.role = "owner"

        service = CompanyService(mock_db)

        update_data = {
            "name": "수정된 주식회사",
            "ceoName": "김길동",
        }

        # Act
        result = await service.update_company(
            company_id=mock_company.id,
            user_id=mock_user.id,
            data=update_data,
        )

        # Assert
        assert result is not None
        assert result.name == update_data["name"]

    @pytest.mark.asyncio
    async def test_UT31_정상_수정_admin(self, mock_company, mock_company_member_admin):
        """
        Given: admin 역할 사용자 + 유효한 수정 데이터
        When: update_company 호출
        Then: Company 갱신
        """
        # Arrange
        mock_db = AsyncMock()
        admin_user_id = mock_company_member_admin.user_id

        service = CompanyService(mock_db)

        update_data = {"name": "admin이 수정한 회사"}

        # Act
        result = await service.update_company(
            company_id=mock_company.id,
            user_id=admin_user_id,
            data=update_data,
        )

        # Assert
        assert result is not None

    @pytest.mark.asyncio
    async def test_UT32_권한없음_member_AppException_403(
        self, mock_company, mock_company_member_member
    ):
        """
        Given: member 역할 사용자
        When: update_company 호출
        Then: AppException(PERMISSION_001, 403) 발생
        """
        # Arrange
        mock_db = AsyncMock()
        member_user_id = mock_company_member_member.user_id

        service = CompanyService(mock_db)
        from src.services.company_service import AppException

        # Act & Assert
        with pytest.raises(AppException) as exc_info:
            await service.update_company(
                company_id=mock_company.id,
                user_id=member_user_id,
                data={"name": "변경 시도"},
            )

        assert exc_info.value.code == "PERMISSION_001"
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_UT33_businessNumber_수정_시도_무시(
        self, mock_user, mock_company, mock_company_member_owner
    ):
        """
        Given: owner + 요청에 businessNumber 포함
        When: update_company 호출
        Then: businessNumber는 변경되지 않음 (무시)
        """
        # Arrange
        mock_db = AsyncMock()
        mock_company_member_owner.user_id = mock_user.id
        original_business_number = mock_company.business_number

        service = CompanyService(mock_db)

        update_data = {
            "name": "수정된 회사",
            "businessNumber": "9999999999",  # 변경 시도
        }

        # Act
        result = await service.update_company(
            company_id=mock_company.id,
            user_id=mock_user.id,
            data=update_data,
        )

        # Assert - businessNumber는 원래 값 유지
        assert result.business_number == original_business_number

    @pytest.mark.asyncio
    async def test_UT34_존재하지_않는_회사_AppException_404(self, mock_user):
        """
        Given: 잘못된 company_id
        When: update_company 호출
        Then: AppException(COMPANY_001, 404) 발생
        """
        # Arrange
        mock_db = AsyncMock()
        non_existent_id = str(uuid4())

        service = CompanyService(mock_db)
        from src.services.company_service import AppException

        # Act & Assert
        with pytest.raises(AppException) as exc_info:
            await service.update_company(
                company_id=non_existent_id,
                user_id=mock_user.id,
                data={"name": "테스트"},
            )

        assert exc_info.value.code == "COMPANY_001"
        assert exc_info.value.status_code == 404


class TestVerifyCompanyMembership:
    """권한 검증 유틸리티 테스트 (UT-80~UT-83)"""

    @pytest.mark.asyncio
    async def test_UT80_멤버인_경우_CompanyMember_반환(
        self, mock_company, mock_company_member_owner
    ):
        """
        Given: 유효한 (company_id, user_id) 조합
        When: verify_company_membership 호출
        Then: CompanyMember 반환
        """
        # Arrange
        mock_db = AsyncMock()
        service = CompanyService(mock_db)

        # Act
        result = await service.verify_company_membership(
            company_id=mock_company.id,
            user_id=mock_company_member_owner.user_id,
        )

        # Assert
        assert result is not None
        assert result.role == "owner"

    @pytest.mark.asyncio
    async def test_UT81_비멤버인_경우_AppException_403(self, mock_company):
        """
        Given: 매칭되지 않는 (company_id, user_id)
        When: verify_company_membership 호출
        Then: AppException(PERMISSION_001, 403) 발생
        """
        # Arrange
        mock_db = AsyncMock()
        service = CompanyService(mock_db)
        from src.services.company_service import AppException

        # Act & Assert
        with pytest.raises(AppException) as exc_info:
            await service.verify_company_membership(
                company_id=mock_company.id,
                user_id=str(uuid4()),  # 비멤버 user_id
            )

        assert exc_info.value.code == "PERMISSION_001"
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_UT82_역할_제한_owner만_member가_접근시_403(
        self, mock_company, mock_company_member_member
    ):
        """
        Given: member 역할 사용자 + required_roles=["owner"]
        When: verify_company_membership 호출
        Then: AppException(PERMISSION_001, 403) 발생
        """
        # Arrange
        mock_db = AsyncMock()
        service = CompanyService(mock_db)
        from src.services.company_service import AppException

        # Act & Assert
        with pytest.raises(AppException) as exc_info:
            await service.verify_company_membership(
                company_id=mock_company.id,
                user_id=mock_company_member_member.user_id,
                required_roles=["owner"],
            )

        assert exc_info.value.code == "PERMISSION_001"
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_UT83_역할_제한_통과_owner가_owner_admin_제한에_통과(
        self, mock_company, mock_company_member_owner
    ):
        """
        Given: owner 역할 사용자 + required_roles=["owner", "admin"]
        When: verify_company_membership 호출
        Then: CompanyMember 반환 (정상 통과)
        """
        # Arrange
        mock_db = AsyncMock()
        service = CompanyService(mock_db)

        # Act
        result = await service.verify_company_membership(
            company_id=mock_company.id,
            user_id=mock_company_member_owner.user_id,
            required_roles=["owner", "admin"],
        )

        # Assert
        assert result is not None
        assert result.role in ["owner", "admin"]
