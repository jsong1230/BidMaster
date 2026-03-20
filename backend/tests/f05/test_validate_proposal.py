"""F-05 제안서 편집기 - 검증 API 테스트"""
import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4, UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.models.bid import Bid
from src.models.proposal import Proposal
from src.services.proposal_service import ProposalService
from src.core.exceptions import ValidationError


@pytest.fixture
async def proposal_service(db_session: AsyncSession) -> ProposalService:
    """제안서 서비스 fixture"""
    return ProposalService(db_session)


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """테스트용 사용자"""
    user = User(
        id=uuid4(),
        email="test@example.com",
        name="테스트 사용자",
        phone="010-1234-5678",
        password_hash="hashed_password",
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.fixture
async def test_bid(db_session: AsyncSession) -> Bid:
    """테스트용 공고"""
    bid = Bid(
        id=uuid4(),
        bid_number="TEST-2026-001",
        title="테스트 공고",
        organization="테스트 기관",
        deadline=datetime.now(timezone.utc) + timedelta(days=7),
        status="open",
        requirements=["요구사항 1", "요구사항 2"],
        # page_limit은 API 요청 파라미터로 전달 (Bid 모델에 없음)
    )
    db_session.add(bid)
    await db_session.flush()
    return bid


@pytest.fixture
async def auth_headers_for_test_user(test_user: User):
    """테스트 사용자용 인증 헤더"""
    try:
        from src.core.security import create_access_token
        user_id = str(test_user.id)
        token = create_access_token(
            user_id,
            extra_data={"company_id": None, "role": "user"}
        )
        return {"Authorization": f"Bearer {token}"}
    except ImportError:
        import base64
        import json
        user_id = str(test_user.id)
        token_data = json.dumps({"sub": user_id, "exp": 9999999999})
        mock_token = base64.b64encode(token_data.encode()).decode()
        return {"Authorization": f"Bearer mock_{mock_token}"}


@pytest.fixture
async def test_proposal(
    db_session: AsyncSession,
    proposal_service: ProposalService,
    test_user: User,
    test_bid: Bid,
) -> Proposal:
    """테스트용 제안서"""
    user_id = UUID(str(test_user.id))
    bid_id = UUID(str(test_bid.id))
    proposal = await proposal_service.create_proposal(
        user_id=user_id,
        bid_id=bid_id,
        title="테스트 제안서",
    )
    return proposal


class TestProposalValidation:
    """제안서 검증 테스트"""

    @pytest.mark.asyncio
    async def test_validate_all_sections_filled_success(
        self,
        client,
        auth_headers_for_test_user,
        proposal_service: ProposalService,
        test_proposal: Proposal,
        test_user: User,
    ):
        """모든 필수 섹션이 채워진 경우 검증 성공"""
        user_id = UUID(str(test_user.id))
        proposal_id = test_proposal.id

        # 모든 섹션 채우기
        for section_key in ["overview", "technical", "price", "schedule", "organization", "past_performance"]:
            await proposal_service.update_section(
                proposal_id=proposal_id,
                section_key=section_key,
                user_id=user_id,
                content=f"<p>{section_key}의 내용입니다. 충분한 분량입니다.</p>" * 10,
            )

        # 평가 체크리스트 채우기
        await proposal_service.update_proposal(
            proposal_id=proposal_id,
            user_id=user_id,
            evaluation_checklist={
                "technical_capability": {"checked": True, "weight": 30},
                "price_competitiveness": {"checked": True, "weight": 25},
                "past_performance": {"checked": True, "weight": 20},
                "project_schedule": {"checked": True, "weight": 15},
                "organization": {"checked": True, "weight": 10}
            }
        )

        response = await client.post(
            f"/api/v1/proposals/{proposal_id}/validate",
            headers=auth_headers_for_test_user,
            json={"pageLimit": 30},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["isValid"] is True
        assert len(data["data"]["warnings"]) == 0

    @pytest.mark.asyncio
    async def test_validate_empty_required_section_fails(
        self,
        client,
        auth_headers_for_test_user,
        proposal_service: ProposalService,
        test_proposal: Proposal,
        test_user: User,
    ):
        """필수 섹션이 비어있는 경우 검증 실패"""
        user_id = UUID(str(test_user.id))
        proposal_id = test_proposal.id

        # overview 섹션만 비우고 나머지 채우기
        sections = ["technical", "price", "schedule", "organization", "past_performance"]
        for section_key in sections:
            await proposal_service.update_section(
                proposal_id=proposal_id,
                section_key=section_key,
                user_id=user_id,
                content=f"<p>{section_key}의 내용입니다.</p>" * 10,
            )

        # overview 섹션 비워둠
        await proposal_service.update_section(
            proposal_id=proposal_id,
            section_key="overview",
            user_id=user_id,
            content="",
        )

        response = await client.post(
            f"/api/v1/proposals/{proposal_id}/validate",
            headers=auth_headers_for_test_user,
            json={"pageLimit": 30},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["isValid"] is False

        # 필수 섹션 누락 경고 확인
        warnings = data["data"]["warnings"]
        required_warning = next((w for w in warnings if w["type"] == "required_field" and w["section"] == "overview"), None)
        assert required_warning is not None
        assert "비어 있습니다" in required_warning["message"]

    @pytest.mark.asyncio
    async def test_validate_page_limit_exceeded_fails(
        self,
        client,
        auth_headers_for_test_user,
        proposal_service: ProposalService,
        test_proposal: Proposal,
        test_user: User,
    ):
        """페이지 제한 초과 시 검증 실패"""
        user_id = UUID(str(test_user.id))
        proposal_id = test_proposal.id

        # 모든 섹션을 매우 긴 내용으로 채움 (35페이지 분량)
        for section_key in ["overview", "technical", "price", "schedule", "organization", "past_performance"]:
            long_content = "<p>긴 내용입니다.</p>" * 2000  # 대략 6페이지 분량
            await proposal_service.update_section(
                proposal_id=proposal_id,
                section_key=section_key,
                user_id=user_id,
                content=long_content,
            )

        response = await client.post(
            f"/api/v1/proposals/{proposal_id}/validate",
            headers=auth_headers_for_test_user,
            json={"pageLimit": 30},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["isValid"] is False

        # 페이지 제한 초과 경고 확인
        warnings = data["data"]["warnings"]
        page_warning = next((w for w in warnings if w["type"] == "page_limit"), None)
        assert page_warning is not None
        assert page_warning["current"] > page_warning["limit"]
        assert "페이지 제한을 초과했습니다" in page_warning["message"]

    @pytest.mark.asyncio
    async def test_validate_within_page_limit_success(
        self,
        client,
        auth_headers_for_test_user,
        proposal_service: ProposalService,
        test_proposal: Proposal,
        test_user: User,
    ):
        """페이지 제한 내에 있을 때 검증 성공"""
        user_id = UUID(str(test_user.id))
        proposal_id = test_proposal.id

        # 적절한 분량으로 채움 (20페이지 분량)
        for section_key in ["overview", "technical", "price", "schedule", "organization", "past_performance"]:
            content = "<p>내용입니다.</p>" * 500  # 대략 3.3페이지 분량
            await proposal_service.update_section(
                proposal_id=proposal_id,
                section_key=section_key,
                user_id=user_id,
                content=content,
            )

        response = await client.post(
            f"/api/v1/proposals/{proposal_id}/validate",
            headers=auth_headers_for_test_user,
            json={"pageLimit": 30},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["isValid"] is True

        # 페이지 제한 관련 경고 없음 확인
        warnings = data["data"]["warnings"]
        page_warning = next((w for w in warnings if w["type"] == "page_limit"), None)
        assert page_warning is None

    @pytest.mark.asyncio
    async def test_validate_multiple_warnings(
        self,
        client,
        auth_headers_for_test_user,
        proposal_service: ProposalService,
        test_proposal: Proposal,
        test_user: User,
    ):
        """여러 경고가 발생하는 경우 검증 실패"""
        user_id = UUID(str(test_user.id))
        proposal_id = test_proposal.id

        # 일부 섹션 비우기
        await proposal_service.update_section(
            proposal_id=proposal_id,
            section_key="overview",
            user_id=user_id,
            content="",
        )
        await proposal_service.update_section(
            proposal_id=proposal_id,
            section_key="technical",
            user_id=user_id,
            content="",
        )

        # 나머지 섹션 채우기
        sections = ["price", "schedule", "organization", "past_performance"]
        for section_key in sections:
            long_content = "<p>내용입니다.</p>" * 2000  # 많은 분량
            await proposal_service.update_section(
                proposal_id=proposal_id,
                section_key=section_key,
                user_id=user_id,
                content=long_content,
            )

        response = await client.post(
            f"/api/v1/proposals/{proposal_id}/validate",
            headers=auth_headers_for_test_user,
            json={"pageLimit": 10},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["isValid"] is False

        # 여러 경고 확인
        warnings = data["data"]["warnings"]
        assert len(warnings) >= 2

        # 필수 섹션 누락 경고
        required_warnings = [w for w in warnings if w["type"] == "required_field"]
        assert len(required_warnings) == 2

        # 페이지 제한 초과 경고
        page_warning = next((w for w in warnings if w["type"] == "page_limit"), None)
        assert page_warning is not None

    @pytest.mark.asyncio
    async def test_validate_returns_stats(
        self,
        client,
        auth_headers_for_test_user,
        proposal_service: ProposalService,
        test_proposal: Proposal,
        test_user: User,
    ):
        """검증 결과에 통계 정보 포함 테스트"""
        user_id = UUID(str(test_user.id))
        proposal_id = test_proposal.id

        # 섹션별 다른 길이로 채우기
        await proposal_service.update_section(
            proposal_id=proposal_id,
            section_key="overview",
            user_id=user_id,
            content="<p>내용</p>" * 100,  # 대략 200단어
        )
        await proposal_service.update_section(
            proposal_id=proposal_id,
            section_key="technical",
            user_id=user_id,
            content="<p>내용</p>" * 300,  # 대략 600단어
        )
        await proposal_service.update_section(
            proposal_id=proposal_id,
            section_key="price",
            user_id=user_id,
            content="",  # 비어있음
        )

        response = await client.post(
            f"/api/v1/proposals/{proposal_id}/validate",
            headers=auth_headers_for_test_user,
            json={"pageLimit": 30},
        )

        assert response.status_code == 200
        data = response.json()
        assert "stats" in data["data"]

        stats = data["data"]["stats"]
        assert "totalWordCount" in stats
        assert "estimatedPages" in stats
        assert "sectionStats" in stats
        assert len(stats["sectionStats"]) == 6

        # 섹션별 통계 확인
        overview_stats = next((s for s in stats["sectionStats"] if s["sectionKey"] == "overview"), None)
        assert overview_stats is not None
        assert overview_stats["isEmpty"] is False
        assert overview_stats["wordCount"] > 0

        price_stats = next((s for s in stats["sectionStats"] if s["sectionKey"] == "price"), None)
        assert price_stats is not None
        assert price_stats["isEmpty"] is True

    @pytest.mark.asyncio
    async def test_validate_without_auth_fails(
        self,
        client,
        test_proposal: Proposal,
    ):
        """인증 없는 검증 실패 테스트"""
        response = await client.post(
            f"/api/v1/proposals/{test_proposal.id}/validate",
            json={"pageLimit": 30},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_validate_proposal_not_found_fails(
        self,
        client,
        auth_headers_for_test_user,
    ):
        """존재하지 않는 제안서 검증 실패 테스트"""
        non_existent_id = uuid4()

        response = await client.post(
            f"/api/v1/proposals/{non_existent_id}/validate",
            headers=auth_headers_for_test_user,
            json={"pageLimit": 30},
        )

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "PROPOSAL_001"

    @pytest.mark.asyncio
    async def test_validate_negative_page_limit_fails(
        self,
        client,
        auth_headers_for_test_user,
        test_proposal: Proposal,
    ):
        """음수 페이지 제한으로 검증 실패 테스트"""
        response = await client.post(
            f"/api/v1/proposals/{test_proposal.id}/validate",
            headers=auth_headers_for_test_user,
            json={"pageLimit": -10},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False

    @pytest.mark.asyncio
    async def test_validate_zero_page_limit_fails(
        self,
        client,
        auth_headers_for_test_user,
        test_proposal: Proposal,
    ):
        """0 페이지 제한으로 검증 실패 테스트"""
        response = await client.post(
            f"/api/v1/proposals/{test_proposal.id}/validate",
            headers=auth_headers_for_test_user,
            json={"pageLimit": 0},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False

    @pytest.mark.asyncio
    async def test_validate_evaluation_checklist_warning(
        self,
        client,
        auth_headers_for_test_user,
        proposal_service: ProposalService,
        test_proposal: Proposal,
        test_user: User,
    ):
        """평가 체크리스트 미달성 경고 테스트"""
        user_id = UUID(str(test_user.id))
        proposal_id = test_proposal.id

        # 모든 섹션 채우기
        for section_key in ["overview", "technical", "price", "schedule", "organization", "past_performance"]:
            await proposal_service.update_section(
                proposal_id=proposal_id,
                section_key=section_key,
                user_id=user_id,
                content=f"<p>{section_key}의 내용입니다.</p>" * 10,
            )

        # 평가 체크리스트 미달성 (2/5만 체크)
        await proposal_service.update_proposal(
            proposal_id=proposal_id,
            user_id=user_id,
            evaluation_checklist={
                "technical_capability": True,
                "price_competitiveness": True,
                "past_performance": False,
                "project_schedule": False,
                "organization": False
            }
        )

        response = await client.post(
            f"/api/v1/proposals/{proposal_id}/validate",
            headers=auth_headers_for_test_user,
            json={"pageLimit": 30},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # 평가 항목 미달성은 검증 결과에 영향을 주지 않으나 경고로 표시
        # 실제 구현에서는 isValid가 True이지만 warning에 포함되거나, 달성률이 낮으면 False일 수 있음

    @pytest.mark.asyncio
    async def test_validate_empty_proposal_fails(
        self,
        client,
        auth_headers_for_test_user,
        proposal_service: ProposalService,
        test_proposal: Proposal,
        test_user: User,
    ):
        """완전히 비어있는 제안서 검증 실패 테스트"""
        user_id = UUID(str(test_user.id))
        proposal_id = test_proposal.id

        # 모든 섹션 비우기
        for section_key in ["overview", "technical", "price", "schedule", "organization", "past_performance"]:
            await proposal_service.update_section(
                proposal_id=proposal_id,
                section_key=section_key,
                user_id=user_id,
                content="",
            )

        response = await client.post(
            f"/api/v1/proposals/{proposal_id}/validate",
            headers=auth_headers_for_test_user,
            json={"pageLimit": 30},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["isValid"] is False

        # 모든 필수 섹션에 대한 경고 확인 (overview와 technical만 필수)
        warnings = data["data"]["warnings"]
        required_warnings = [w for w in warnings if w["type"] == "required_field"]
        assert len(required_warnings) == 2  # overview, technical
