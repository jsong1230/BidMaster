"""F-03 제안서 생성 테스트"""
import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4, UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.models.bid import Bid
from src.models.company import Company
from src.models.proposal import Proposal
from src.models.proposal_section import ProposalSection
from src.services.proposal_service import ProposalService
from src.core.exceptions import NotFoundError, PermissionError, ValidationError


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
        hashed_password="hashed_password",
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.fixture
async def test_company(db_session: AsyncSession, test_user: User) -> Company:
    """테스트용 회사"""
    company = Company(
        id=uuid4(),
        user_id=UUID(str(test_user.id)),
        name="테스트 회사",
        business_number="123-45-67890",
        description="테스트 회사 설명",
        business_areas=["IT", "소프트웨어"],
        certifications=["ISO 9001"],
    )
    db_session.add(company)
    await db_session.flush()
    return company


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
    )
    db_session.add(bid)
    await db_session.flush()
    return bid


class TestProposalService:
    """제안서 서비스 테스트"""

    @pytest.mark.asyncio
    async def test_create_proposal(
        self,
        proposal_service: ProposalService,
        test_user: User,
        test_bid: Bid,
    ):
        """제안서 생성 테스트"""
        user_id = UUID(str(test_user.id))
        bid_id = UUID(str(test_bid.id))

        proposal = await proposal_service.create_proposal(
            user_id=user_id,
            bid_id=bid_id,
            title="테스트 제안서",
        )

        assert proposal.id is not None
        assert proposal.user_id == user_id
        assert proposal.bid_id == bid_id
        assert proposal.title == "테스트 제안서"
        assert proposal.status == "draft"
        assert proposal.version == 1

    @pytest.mark.asyncio
    async def test_create_proposal_with_company(
        self,
        proposal_service: ProposalService,
        test_user: User,
        test_bid: Bid,
        test_company: Company,
    ):
        """회사 정보와 함께 제안서 생성 테스트"""
        user_id = UUID(str(test_user.id))
        bid_id = UUID(str(test_bid.id))
        company_id = UUID(str(test_company.id))

        proposal = await proposal_service.create_proposal(
            user_id=user_id,
            bid_id=bid_id,
            company_id=company_id,
        )

        assert proposal.company_id == company_id

    @pytest.mark.asyncio
    async def test_create_proposal_duplicate_fails(
        self,
        proposal_service: ProposalService,
        test_user: User,
        test_bid: Bid,
    ):
        """동일 공고에 대한 중복 제안서 생성 실패 테스트"""
        user_id = UUID(str(test_user.id))
        bid_id = UUID(str(test_bid.id))

        # 첫 번째 제안서 생성
        await proposal_service.create_proposal(user_id=user_id, bid_id=bid_id)

        # 두 번째 제안서 생성 시도
        with pytest.raises(ValidationError) as exc_info:
            await proposal_service.create_proposal(user_id=user_id, bid_id=bid_id)

        assert exc_info.value.code == "PROPOSAL_003"

    @pytest.mark.asyncio
    async def test_get_proposals(
        self,
        proposal_service: ProposalService,
        test_user: User,
        test_bid: Bid,
    ):
        """제안서 목록 조회 테스트"""
        user_id = UUID(str(test_user.id))
        bid_id = UUID(str(test_bid.id))

        # 제안서 3개 생성
        for i in range(3):
            await proposal_service.create_proposal(
                user_id=user_id,
                bid_id=bid_id,
                title=f"제안서 {i+1}",
            )

        proposals, total = await proposal_service.get_proposals(user_id=user_id)

        assert total == 3
        assert len(proposals) == 3

    @pytest.mark.asyncio
    async def test_get_proposals_with_status_filter(
        self,
        proposal_service: ProposalService,
        test_user: User,
        test_bid: Bid,
    ):
        """상태 필터로 제안서 목록 조회 테스트"""
        user_id = UUID(str(test_user.id))
        bid_id = UUID(str(test_bid.id))

        proposal = await proposal_service.create_proposal(user_id=user_id, bid_id=bid_id)
        await proposal_service.update_status(proposal.id, user_id, "ready")

        # draft 상태만 조회
        draft_proposals, draft_total = await proposal_service.get_proposals(
            user_id=user_id, status="draft"
        )
        assert draft_total == 0

        # ready 상태만 조회
        ready_proposals, ready_total = await proposal_service.get_proposals(
            user_id=user_id, status="ready"
        )
        assert ready_total == 1

    @pytest.mark.asyncio
    async def test_get_proposal(
        self,
        proposal_service: ProposalService,
        test_user: User,
        test_bid: Bid,
    ):
        """제안서 상세 조회 테스트"""
        user_id = UUID(str(test_user.id))
        bid_id = UUID(str(test_bid.id))

        created = await proposal_service.create_proposal(user_id=user_id, bid_id=bid_id)
        proposal = await proposal_service.get_proposal(created.id, user_id)

        assert proposal.id == created.id
        assert proposal.title == created.title
        # 섹션 확인
        assert len(proposal.sections) == 6  # SECTION_DEFINITIONS 기본 6개 섹션

    @pytest.mark.asyncio
    async def test_get_proposal_other_user_fails(
        self,
        proposal_service: ProposalService,
        test_user: User,
        test_bid: Bid,
    ):
        """다른 사용자의 제안서 조회 시 권한 에러"""
        user_id = UUID(str(test_user.id))
        bid_id = UUID(str(test_bid.id))

        proposal = await proposal_service.create_proposal(user_id=user_id, bid_id=bid_id)
        other_user_id = uuid4()

        with pytest.raises(PermissionError):
            await proposal_service.get_proposal(proposal.id, other_user_id)

    @pytest.mark.asyncio
    async def test_update_proposal(
        self,
        proposal_service: ProposalService,
        test_user: User,
        test_bid: Bid,
    ):
        """제안서 수정 테스트"""
        user_id = UUID(str(test_user.id))
        bid_id = UUID(str(test_bid.id))

        proposal = await proposal_service.create_proposal(user_id=user_id, bid_id=bid_id)
        updated = await proposal_service.update_proposal(
            proposal_id=proposal.id,
            user_id=user_id,
            title="수정된 제목",
            evaluation_checklist={"item1": True},
        )

        assert updated.title == "수정된 제목"
        assert updated.evaluation_checklist == {"item1": True}

    @pytest.mark.asyncio
    async def test_update_section(
        self,
        proposal_service: ProposalService,
        test_user: User,
        test_bid: Bid,
    ):
        """섹션 수정 테스트"""
        user_id = UUID(str(test_user.id))
        bid_id = UUID(str(test_bid.id))

        proposal = await proposal_service.create_proposal(user_id=user_id, bid_id=bid_id)
        section = await proposal_service.update_section(
            proposal_id=proposal.id,
            section_key="overview",
            user_id=user_id,
            content="사업 개요 내용입니다.",
        )

        assert section.content == "사업 개요 내용입니다."
        assert section.is_ai_generated is False  # 수동 수정 시 False

    @pytest.mark.asyncio
    async def test_create_version(
        self,
        proposal_service: ProposalService,
        test_user: User,
        test_bid: Bid,
    ):
        """버전 생성 테스트"""
        user_id = UUID(str(test_user.id))
        bid_id = UUID(str(test_bid.id))

        proposal = await proposal_service.create_proposal(user_id=user_id, bid_id=bid_id)

        # 섹션 내용 추가
        await proposal_service.update_section(
            proposal_id=proposal.id,
            section_key="overview",
            user_id=user_id,
            content="버전 1 내용",
        )

        # 버전 생성
        version = await proposal_service.create_version(proposal.id, user_id)

        assert version.version_number == 1
        assert "sections" in version.snapshot
        assert proposal.version == 2  # 버전 증가

    @pytest.mark.asyncio
    async def test_restore_version(
        self,
        proposal_service: ProposalService,
        test_user: User,
        test_bid: Bid,
    ):
        """버전 복원 테스트"""
        user_id = UUID(str(test_user.id))
        bid_id = UUID(str(test_bid.id))

        proposal = await proposal_service.create_proposal(user_id=user_id, bid_id=bid_id)

        # 섹션 내용 추가 후 버전 1 생성
        await proposal_service.update_section(
            proposal_id=proposal.id,
            section_key="overview",
            user_id=user_id,
            content="버전 1 내용",
        )
        await proposal_service.create_version(proposal.id, user_id)

        # 섹션 내용 수정
        await proposal_service.update_section(
            proposal_id=proposal.id,
            section_key="overview",
            user_id=user_id,
            content="버전 2 내용",
        )

        # 버전 1로 복원
        restored = await proposal_service.restore_version(proposal.id, 1, user_id)

        # 복원된 내용 확인
        proposal = await proposal_service.get_proposal(proposal.id, user_id)
        overview_section = next(s for s in proposal.sections if s.section_key == "overview")
        assert overview_section.content == "버전 1 내용"

    @pytest.mark.asyncio
    async def test_update_status(
        self,
        proposal_service: ProposalService,
        test_user: User,
        test_bid: Bid,
    ):
        """상태 변경 테스트"""
        user_id = UUID(str(test_user.id))
        bid_id = UUID(str(test_bid.id))

        proposal = await proposal_service.create_proposal(user_id=user_id, bid_id=bid_id)

        # generating으로 변경
        updated = await proposal_service.update_status(proposal.id, user_id, "generating")
        assert updated.status == "generating"

        # ready로 변경
        updated = await proposal_service.update_status(proposal.id, user_id, "ready")
        assert updated.status == "ready"
        assert updated.generated_at is not None

        # submitted로 변경
        updated = await proposal_service.update_status(proposal.id, user_id, "submitted")
        assert updated.status == "submitted"
        assert updated.submitted_at is not None

    @pytest.mark.asyncio
    async def test_update_status_invalid_fails(
        self,
        proposal_service: ProposalService,
        test_user: User,
        test_bid: Bid,
    ):
        """유효하지 않은 상태 변경 실패 테스트"""
        user_id = UUID(str(test_user.id))
        bid_id = UUID(str(test_bid.id))

        proposal = await proposal_service.create_proposal(user_id=user_id, bid_id=bid_id)

        with pytest.raises(ValidationError):
            await proposal_service.update_status(proposal.id, user_id, "invalid_status")

    @pytest.mark.asyncio
    async def test_delete_proposal(
        self,
        proposal_service: ProposalService,
        test_user: User,
        test_bid: Bid,
    ):
        """제안서 삭제 테스트"""
        user_id = UUID(str(test_user.id))
        bid_id = UUID(str(test_bid.id))

        proposal = await proposal_service.create_proposal(user_id=user_id, bid_id=bid_id)
        await proposal_service.delete_proposal(proposal.id, user_id)

        # 삭제된 제안서는 조회되지 않음
        with pytest.raises(NotFoundError):
            await proposal_service.get_proposal(proposal.id, user_id)

    @pytest.mark.asyncio
    async def test_proposal_not_found_error(
        self,
        proposal_service: ProposalService,
        test_user: User,
    ):
        """존재하지 않는 제안서 조회 시 에러"""
        user_id = UUID(str(test_user.id))

        with pytest.raises(NotFoundError):
            await proposal_service.get_proposal(uuid4(), user_id)


class TestProposalAPI:
    """제안서 API 테스트"""

    @pytest.mark.asyncio
    async def test_list_proposals_api(
        self,
        client,
        auth_headers,
        proposal_service: ProposalService,
        test_user: User,
        test_bid: Bid,
    ):
        """제안서 목록 API 테스트"""
        user_id = UUID(str(test_user.id))
        bid_id = UUID(str(test_bid.id))

        for i in range(3):
            await proposal_service.create_proposal(
                user_id=user_id,
                bid_id=bid_id,
                title=f"제안서 {i+1}",
            )

        response = await client.get(
            "/api/v1/proposals",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["items"]) == 3
        assert data["meta"]["total"] == 3

    @pytest.mark.asyncio
    async def test_get_proposal_api(
        self,
        client,
        auth_headers,
        proposal_service: ProposalService,
        test_user: User,
        test_bid: Bid,
    ):
        """제안서 상세 API 테스트"""
        user_id = UUID(str(test_user.id))
        bid_id = UUID(str(test_bid.id))

        proposal = await proposal_service.create_proposal(user_id=user_id, bid_id=bid_id)

        response = await client.get(
            f"/api/v1/proposals/{proposal.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == str(proposal.id)

    @pytest.mark.asyncio
    async def test_create_proposal_api(
        self,
        client,
        auth_headers,
        test_bid: Bid,
    ):
        """제안서 생성 API 테스트"""
        response = await client.post(
            "/api/v1/proposals",
            headers=auth_headers,
            json={
                "bidId": str(test_bid.id),
                "title": "API 테스트 제안서",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["title"] == "API 테스트 제안서"
        assert data["data"]["status"] == "draft"

    @pytest.mark.asyncio
    async def test_update_section_api(
        self,
        client,
        auth_headers,
        proposal_service: ProposalService,
        test_user: User,
        test_bid: Bid,
    ):
        """섹션 수정 API 테스트"""
        user_id = UUID(str(test_user.id))
        bid_id = UUID(str(test_bid.id))

        proposal = await proposal_service.create_proposal(user_id=user_id, bid_id=bid_id)

        response = await client.patch(
            f"/api/v1/proposals/{proposal.id}/sections/overview",
            headers=auth_headers,
            json={
                "content": "수정된 섹션 내용입니다.",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["content"] == "수정된 섹션 내용입니다."
