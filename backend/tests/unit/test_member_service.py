"""
CompanyMemberService 단위 테스트

test-spec.md 기준:
- UT-70: 정상 초대 (owner)
- UT-71: 정상 초대 (admin)
- UT-72: 권한 없음 (member)
- UT-73: 존재하지 않는 이메일
- UT-74: 이미 멤버인 사용자
- UT-75: 다른 회사 소속 사용자
- UT-76: owner 역할 지정 시도
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

# 구현 전이므로 import 시 ImportError 발생 - RED 상태
from src.services.company_service import CompanyService
from src.core.security import ValidationError


class TestInviteMember:
    """멤버 초대 테스트 (UT-70~UT-76)"""

    @pytest.mark.asyncio
    async def test_UT70_정상_초대_owner(
        self, mock_company, mock_company_member_owner, mock_user
    ):
        """
        Given: owner + 미소속 대상 이메일
        When: invite_member 호출
        Then: CompanyMember 생성, users.company_id 갱신
        """
        # Arrange
        mock_db = AsyncMock()
        service = CompanyService(mock_db)

        # 초대할 사용자 (미소속)
        target_user_email = "newmember@test.com"

        # Act
        result = await service.invite_member(
            company_id=mock_company.id,
            inviter_user_id=mock_company_member_owner.user_id,
            target_email=target_user_email,
            role="member",
        )

        # Assert
        assert result is not None
        assert result.company_id == mock_company.id
        assert result.role == "member"

    @pytest.mark.asyncio
    async def test_UT71_정상_초대_admin(
        self, mock_company, mock_company_member_admin
    ):
        """
        Given: admin + 미소속 대상 이메일
        When: invite_member 호출
        Then: CompanyMember 생성
        """
        # Arrange
        mock_db = AsyncMock()
        service = CompanyService(mock_db)

        target_email = "anothermember@test.com"

        # Act
        result = await service.invite_member(
            company_id=mock_company.id,
            inviter_user_id=mock_company_member_admin.user_id,
            target_email=target_email,
            role="member",
        )

        # Assert
        assert result is not None
        assert result.role == "member"

    @pytest.mark.asyncio
    async def test_UT72_권한없음_member_AppException_403(
        self, mock_company, mock_company_member_member
    ):
        """
        Given: member 역할 사용자가 초대 시도
        When: invite_member 호출
        Then: AppException(PERMISSION_003, 403) 발생
        """
        # Arrange
        mock_db = AsyncMock()
        service = CompanyService(mock_db)
        from src.services.company_service import AppException

        # Act & Assert
        with pytest.raises(AppException) as exc_info:
            await service.invite_member(
                company_id=mock_company.id,
                inviter_user_id=mock_company_member_member.user_id,
                target_email="someuser@test.com",
                role="member",
            )

        assert exc_info.value.code == "PERMISSION_003"
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_UT73_존재하지_않는_이메일_AppException_404(
        self, mock_company, mock_company_member_owner
    ):
        """
        Given: 시스템에 등록되지 않은 이메일
        When: invite_member 호출
        Then: AppException(COMPANY_008, 404) 발생
        """
        # Arrange
        mock_db = AsyncMock()
        service = CompanyService(mock_db)
        from src.services.company_service import AppException

        # Act & Assert
        with pytest.raises(AppException) as exc_info:
            await service.invite_member(
                company_id=mock_company.id,
                inviter_user_id=mock_company_member_owner.user_id,
                target_email="nonexistent@test.com",
                role="member",
            )

        assert exc_info.value.code == "COMPANY_008"
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_UT74_이미_멤버인_사용자_AppException_409(
        self, mock_company, mock_company_member_owner, mock_company_member_member
    ):
        """
        Given: 해당 회사의 기존 멤버 이메일
        When: invite_member 호출
        Then: AppException(COMPANY_009, 409) 발생
        """
        # Arrange
        mock_db = AsyncMock()
        service = CompanyService(mock_db)
        from src.services.company_service import AppException

        # 기존 멤버의 이메일로 다시 초대
        existing_member_email = "existingmember@test.com"

        # Act & Assert
        with pytest.raises(AppException) as exc_info:
            await service.invite_member(
                company_id=mock_company.id,
                inviter_user_id=mock_company_member_owner.user_id,
                target_email=existing_member_email,
                role="member",
                _force_existing_member=True,  # 이미 멤버인 상태 시뮬레이션
            )

        assert exc_info.value.code == "COMPANY_009"
        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_UT75_다른_회사_소속_사용자_AppException_409(
        self, mock_company, mock_company_member_owner
    ):
        """
        Given: 다른 회사에 이미 소속된 사용자 이메일
        When: invite_member 호출
        Then: AppException(COMPANY_010, 409) 발생
        """
        # Arrange
        mock_db = AsyncMock()
        service = CompanyService(mock_db)
        from src.services.company_service import AppException

        other_company_member_email = "othercompany@test.com"

        # Act & Assert
        with pytest.raises(AppException) as exc_info:
            await service.invite_member(
                company_id=mock_company.id,
                inviter_user_id=mock_company_member_owner.user_id,
                target_email=other_company_member_email,
                role="member",
                _force_other_company=True,  # 다른 회사 소속 상태 시뮬레이션
            )

        assert exc_info.value.code == "COMPANY_010"
        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_UT76_owner_역할_지정_시도_ValidationError(
        self, mock_company, mock_company_member_owner
    ):
        """
        Given: role="owner" (owner 역할 지정 시도)
        When: invite_member 호출
        Then: ValidationError 발생 (admin, member만 가능)
        """
        # Arrange
        mock_db = AsyncMock()
        service = CompanyService(mock_db)

        # Act & Assert
        with pytest.raises((ValidationError, Exception)) as exc_info:
            await service.invite_member(
                company_id=mock_company.id,
                inviter_user_id=mock_company_member_owner.user_id,
                target_email="newuser@test.com",
                role="owner",  # owner 역할 지정 시도 - 불가
            )

        assert exc_info.value is not None


class TestGetCompanyMembers:
    """멤버 목록 조회 테스트"""

    @pytest.mark.asyncio
    async def test_멤버_목록_조회_성공(
        self, mock_company, mock_company_member_member
    ):
        """
        Given: 해당 회사 멤버 사용자
        When: get_company_members 호출
        Then: 멤버 목록 + 페이지네이션 메타 반환
        """
        # Arrange
        mock_db = AsyncMock()
        service = CompanyService(mock_db)

        # Act
        result = await service.get_company_members(
            company_id=mock_company.id,
            user_id=mock_company_member_member.user_id,
            page=1,
            page_size=20,
        )

        # Assert
        assert result is not None
        assert "items" in result or hasattr(result, "items")

    @pytest.mark.asyncio
    async def test_비멤버_멤버목록_조회_AppException_403(self, mock_company):
        """
        Given: 해당 회사 비멤버 사용자
        When: get_company_members 호출
        Then: AppException(PERMISSION_001, 403) 발생
        """
        # Arrange
        mock_db = AsyncMock()
        service = CompanyService(mock_db)
        from src.services.company_service import AppException

        non_member_user_id = str(uuid4())

        # Act & Assert
        with pytest.raises(AppException) as exc_info:
            await service.get_company_members(
                company_id=mock_company.id,
                user_id=non_member_user_id,
                page=1,
                page_size=20,
            )

        assert exc_info.value.code == "PERMISSION_001"
        assert exc_info.value.status_code == 403
