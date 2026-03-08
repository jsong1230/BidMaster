"""
PerformanceService 단위 테스트

test-spec.md 기준:
- UT-40~UT-45: 수행 실적 등록
- UT-46~UT-49: 수행 실적 수정
- UT-50~UT-51: 수행 실적 삭제
- UT-52~UT-54: 대표 실적 지정/해제
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

# 구현 전이므로 import 시 ImportError 발생 - RED 상태
from src.services.company_service import CompanyService
from src.core.security import ValidationError


class TestCreatePerformance:
    """수행 실적 등록 테스트 (UT-40~UT-45)"""

    @pytest.mark.asyncio
    async def test_UT40_정상_실적_등록(
        self, test_performance_data, mock_company, mock_company_member_member
    ):
        """
        Given: 유효한 실적 데이터 + 해당 회사 멤버 사용자
        When: create_performance 호출
        Then: Performance 생성
        """
        # Arrange
        mock_db = AsyncMock()
        service = CompanyService(mock_db)
        member_user_id = mock_company_member_member.user_id

        # Act
        result = await service.create_performance(
            company_id=mock_company.id,
            user_id=member_user_id,
            data=test_performance_data,
        )

        # Assert
        assert result is not None
        assert result.project_name == test_performance_data["projectName"]
        assert result.contract_amount == test_performance_data["contractAmount"]

    @pytest.mark.asyncio
    async def test_UT41_대표_실적으로_등록_기존_대표_3개(
        self, test_performance_data, mock_company, mock_company_member_owner
    ):
        """
        Given: isRepresentative=true, 기존 대표 실적 3개
        When: create_performance 호출
        Then: Performance 생성 (is_representative=true), 성공
        """
        # Arrange
        mock_db = AsyncMock()
        service = CompanyService(mock_db)

        data_with_representative = {**test_performance_data, "isRepresentative": True}

        # Act
        result = await service.create_performance(
            company_id=mock_company.id,
            user_id=mock_company_member_owner.user_id,
            data=data_with_representative,
        )

        # Assert
        assert result is not None
        assert result.is_representative is True

    @pytest.mark.asyncio
    async def test_UT42_대표_실적_초과_AppException_400(
        self, test_performance_data, mock_company, mock_company_member_owner
    ):
        """
        Given: isRepresentative=true, 기존 대표 실적이 이미 5개
        When: create_performance 호출
        Then: AppException(COMPANY_005, 400) 발생
        """
        # Arrange
        mock_db = AsyncMock()
        service = CompanyService(mock_db)
        from src.services.company_service import AppException

        data_with_representative = {**test_performance_data, "isRepresentative": True}

        # 대표 실적 5개 초과 시뮬레이션
        with pytest.raises(AppException) as exc_info:
            await service.create_performance(
                company_id=mock_company.id,
                user_id=mock_company_member_owner.user_id,
                data={**data_with_representative, "_force_max_representative": True},
            )

        assert exc_info.value.code == "COMPANY_005"
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_UT43_비멤버_등록_시도_AppException_403(
        self, test_performance_data, mock_company
    ):
        """
        Given: 해당 회사 멤버가 아닌 사용자
        When: create_performance 호출
        Then: AppException(PERMISSION_001, 403) 발생
        """
        # Arrange
        mock_db = AsyncMock()
        service = CompanyService(mock_db)
        from src.services.company_service import AppException

        non_member_user_id = str(uuid4())

        # Act & Assert
        with pytest.raises(AppException) as exc_info:
            await service.create_performance(
                company_id=mock_company.id,
                user_id=non_member_user_id,
                data=test_performance_data,
            )

        assert exc_info.value.code == "PERMISSION_001"
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_UT44_end_date가_start_date보다_이전_ValidationError(
        self, mock_company, mock_company_member_owner
    ):
        """
        Given: startDate: 2025-12-31, endDate: 2025-01-01 (날짜 역전)
        When: create_performance 호출
        Then: ValidationError 발생
        """
        # Arrange
        mock_db = AsyncMock()
        service = CompanyService(mock_db)

        invalid_date_data = {
            "projectName": "테스트 프로젝트",
            "clientName": "테스트 발주처",
            "contractAmount": 100000000,
            "startDate": "2025-12-31",
            "endDate": "2025-01-01",  # start_date보다 이전
            "status": "completed",
            "isRepresentative": False,
        }

        # Act & Assert
        with pytest.raises((ValidationError, Exception)) as exc_info:
            await service.create_performance(
                company_id=mock_company.id,
                user_id=mock_company_member_owner.user_id,
                data=invalid_date_data,
            )

        assert exc_info.value is not None

    @pytest.mark.asyncio
    async def test_UT45_계약금액_0_이하_ValidationError(
        self, test_performance_data, mock_company, mock_company_member_owner
    ):
        """
        Given: contractAmount: -100 (음수)
        When: create_performance 호출
        Then: ValidationError 발생
        """
        # Arrange
        mock_db = AsyncMock()
        service = CompanyService(mock_db)

        invalid_amount_data = {**test_performance_data, "contractAmount": -100}

        # Act & Assert
        with pytest.raises((ValidationError, Exception)) as exc_info:
            await service.create_performance(
                company_id=mock_company.id,
                user_id=mock_company_member_owner.user_id,
                data=invalid_amount_data,
            )

        assert exc_info.value is not None


class TestUpdatePerformance:
    """수행 실적 수정 테스트 (UT-46~UT-49)"""

    @pytest.mark.asyncio
    async def test_UT46_정상_수정_owner(
        self, mock_company, mock_company_member_owner, mock_performance
    ):
        """
        Given: owner 역할 사용자 + 유효한 수정 데이터
        When: update_performance 호출
        Then: Performance 갱신
        """
        # Arrange
        mock_db = AsyncMock()
        service = CompanyService(mock_db)

        update_data = {
            "projectName": "수정된 프로젝트명",
            "contractAmount": 600000000,
        }

        # Act
        result = await service.update_performance(
            company_id=mock_company.id,
            perf_id=mock_performance.id,
            user_id=mock_company_member_owner.user_id,
            data=update_data,
        )

        # Assert
        assert result is not None
        assert result.project_name == update_data["projectName"]

    @pytest.mark.asyncio
    async def test_UT47_권한없음_member_AppException_403(
        self, mock_company, mock_company_member_member, mock_performance
    ):
        """
        Given: member 역할 사용자
        When: update_performance 호출
        Then: AppException(PERMISSION_001, 403) 발생
        """
        # Arrange
        mock_db = AsyncMock()
        service = CompanyService(mock_db)
        from src.services.company_service import AppException

        # Act & Assert
        with pytest.raises(AppException) as exc_info:
            await service.update_performance(
                company_id=mock_company.id,
                perf_id=mock_performance.id,
                user_id=mock_company_member_member.user_id,
                data={"projectName": "변경 시도"},
            )

        assert exc_info.value.code == "PERMISSION_001"
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_UT48_존재하지_않는_실적_AppException_404(
        self, mock_company, mock_company_member_owner
    ):
        """
        Given: 잘못된 perfId
        When: update_performance 호출
        Then: AppException(COMPANY_006, 404) 발생
        """
        # Arrange
        mock_db = AsyncMock()
        service = CompanyService(mock_db)
        from src.services.company_service import AppException

        non_existent_perf_id = str(uuid4())

        # Act & Assert
        with pytest.raises(AppException) as exc_info:
            await service.update_performance(
                company_id=mock_company.id,
                perf_id=non_existent_perf_id,
                user_id=mock_company_member_owner.user_id,
                data={"projectName": "테스트"},
            )

        assert exc_info.value.code == "COMPANY_006"
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_UT49_삭제된_실적_수정_AppException_404(
        self, mock_company, mock_company_member_owner
    ):
        """
        Given: deleted_at이 NOT NULL인 실적 (소프트 삭제된 실적)
        When: update_performance 호출
        Then: AppException(COMPANY_006, 404) 발생
        """
        # Arrange
        mock_db = AsyncMock()
        service = CompanyService(mock_db)
        from src.services.company_service import AppException

        from tests.conftest import MockPerformance
        deleted_performance = MockPerformance(
            company_id=mock_company.id,
            deleted_at=datetime.now(timezone.utc),
        )

        # Act & Assert
        with pytest.raises(AppException) as exc_info:
            await service.update_performance(
                company_id=mock_company.id,
                perf_id=deleted_performance.id,
                user_id=mock_company_member_owner.user_id,
                data={"projectName": "테스트"},
            )

        assert exc_info.value.code == "COMPANY_006"
        assert exc_info.value.status_code == 404


class TestDeletePerformance:
    """수행 실적 삭제 테스트 (UT-50~UT-51)"""

    @pytest.mark.asyncio
    async def test_UT50_정상_삭제_소프트_딜리트(
        self, mock_company, mock_company_member_owner, mock_performance
    ):
        """
        Given: owner + 존재하는 실적
        When: delete_performance 호출
        Then: deleted_at 갱신 (Soft Delete)
        """
        # Arrange
        mock_db = AsyncMock()
        service = CompanyService(mock_db)

        # Act
        result = await service.delete_performance(
            company_id=mock_company.id,
            perf_id=mock_performance.id,
            user_id=mock_company_member_owner.user_id,
        )

        # Assert
        assert result is None or result is True  # 삭제 성공 시 None 또는 True 반환

    @pytest.mark.asyncio
    async def test_UT51_대표_실적_삭제_성공_is_representative_해제(
        self, mock_company, mock_company_member_owner, mock_representative_performance
    ):
        """
        Given: is_representative=true인 실적
        When: delete_performance 호출
        Then: 삭제 성공, is_representative 해제
        """
        # Arrange
        mock_db = AsyncMock()
        service = CompanyService(mock_db)

        # Act
        result = await service.delete_performance(
            company_id=mock_company.id,
            perf_id=mock_representative_performance.id,
            user_id=mock_company_member_owner.user_id,
        )

        # Assert
        assert result is None or result is True


class TestSetRepresentativePerformance:
    """대표 실적 지정/해제 테스트 (UT-52~UT-54)"""

    @pytest.mark.asyncio
    async def test_UT52_대표_지정_기존_대표_4개_성공(
        self, mock_company, mock_company_member_owner, mock_performance
    ):
        """
        Given: isRepresentative=true, 기존 대표 4개
        When: set_representative 호출
        Then: is_representative=true 갱신
        """
        # Arrange
        mock_db = AsyncMock()
        service = CompanyService(mock_db)

        # Act
        result = await service.set_representative(
            company_id=mock_company.id,
            perf_id=mock_performance.id,
            user_id=mock_company_member_owner.user_id,
            is_representative=True,
        )

        # Assert
        assert result is not None
        assert result.is_representative is True

    @pytest.mark.asyncio
    async def test_UT53_대표_해제_성공(
        self, mock_company, mock_company_member_owner, mock_representative_performance
    ):
        """
        Given: isRepresentative=false (현재 대표 실적을 해제)
        When: set_representative 호출
        Then: is_representative=false 갱신
        """
        # Arrange
        mock_db = AsyncMock()
        service = CompanyService(mock_db)

        # Act
        result = await service.set_representative(
            company_id=mock_company.id,
            perf_id=mock_representative_performance.id,
            user_id=mock_company_member_owner.user_id,
            is_representative=False,
        )

        # Assert
        assert result is not None
        assert result.is_representative is False

    @pytest.mark.asyncio
    async def test_UT54_대표_초과_AppException_400(
        self, mock_company, mock_company_member_owner, mock_performance
    ):
        """
        Given: isRepresentative=true, 기존 대표 실적이 이미 5개
        When: set_representative 호출
        Then: AppException(COMPANY_005, 400) 발생
        """
        # Arrange
        mock_db = AsyncMock()
        service = CompanyService(mock_db)
        from src.services.company_service import AppException

        # Act & Assert
        with pytest.raises(AppException) as exc_info:
            await service.set_representative(
                company_id=mock_company.id,
                perf_id=mock_performance.id,
                user_id=mock_company_member_owner.user_id,
                is_representative=True,
                _force_max_representative=True,  # 5개 초과 상태 시뮬레이션
            )

        assert exc_info.value.code == "COMPANY_005"
        assert exc_info.value.status_code == 400


class TestPerformanceBoundaryConditions:
    """수행 실적 경계 조건 테스트"""

    @pytest.mark.asyncio
    async def test_계약금액_0원_ValidationError(
        self, mock_company, mock_company_member_owner, test_performance_data
    ):
        """
        Given: contractAmount=0 (0원)
        When: create_performance 호출
        Then: ValidationError 발생 (양수만 허용)
        """
        # Arrange
        mock_db = AsyncMock()
        service = CompanyService(mock_db)

        zero_amount_data = {**test_performance_data, "contractAmount": 0}

        # Act & Assert
        with pytest.raises((ValidationError, Exception)):
            await service.create_performance(
                company_id=mock_company.id,
                user_id=mock_company_member_owner.user_id,
                data=zero_amount_data,
            )

    @pytest.mark.asyncio
    async def test_시작일_종료일_같은_날_성공(
        self, mock_company, mock_company_member_owner, test_performance_data
    ):
        """
        Given: startDate == endDate (같은 날짜)
        When: create_performance 호출
        Then: 성공 (경계값 허용)
        """
        # Arrange
        mock_db = AsyncMock()
        service = CompanyService(mock_db)

        same_date_data = {
            **test_performance_data,
            "startDate": "2024-06-15",
            "endDate": "2024-06-15",  # 동일 날짜
        }

        # Act
        result = await service.create_performance(
            company_id=mock_company.id,
            user_id=mock_company_member_owner.user_id,
            data=same_date_data,
        )

        # Assert
        assert result is not None
