"""F-05 제안서 편집기 - 서비스 계층 테스트"""
import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4, UUID
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.models.bid import Bid
from src.models.proposal import Proposal
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
    )
    db_session.add(bid)
    await db_session.flush()
    return bid


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


class TestProposalEditorService:
    """제안서 편집기 서비스 테스트"""

    @pytest.mark.asyncio
    async def test_auto_save_section_success(
        self,
        proposal_service: ProposalService,
        test_proposal: Proposal,
        test_user: User,
    ):
        """섹션 자동 저장 성공 테스트"""
        user_id = UUID(str(test_user.id))
        proposal_id = test_proposal.id

        result = await proposal_service.auto_save_sections(
            proposal_id=proposal_id,
            user_id=user_id,
            sections_data=[
                {
                    "section_key": "overview",
                    "content": "<p>자동 저장된 내용</p>",
                }
            ],
        )

        assert "saved_at" in result
        assert "word_count" in result
        assert isinstance(result["word_count"], int)

    @pytest.mark.asyncio
    async def test_auto_save_section_word_count_recalculated(
        self,
        proposal_service: ProposalService,
        test_proposal: Proposal,
        test_user: User,
    ):
        """섹션 자동 저장 시 word_count 재계산 테스트"""
        user_id = UUID(str(test_user.id))
        proposal_id = test_proposal.id

        # HTML 콘텐츠로 저장
        result = await proposal_service.auto_save_sections(
            proposal_id=proposal_id,
            user_id=user_id,
            sections_data=[
                {
                    "section_key": "overview",
                    "content": "<p>테스트 내용입니다.</p>",
                }
            ],
        )

        # 단어 수 계산 확인 (서비스에서 계산)
        assert result["word_count"] > 0

    @pytest.mark.asyncio
    async def test_auto_save_multiple_sections(
        self,
        proposal_service: ProposalService,
        test_proposal: Proposal,
        test_user: User,
    ):
        """여러 섹션 자동 저장 테스트"""
        user_id = UUID(str(test_user.id))
        proposal_id = test_proposal.id

        result = await proposal_service.auto_save_sections(
            proposal_id=proposal_id,
            user_id=user_id,
            sections_data=[
                {
                    "section_key": "overview",
                    "content": "<p>사업 개요</p>",
                },
                {
                    "section_key": "technical",
                    "content": "<p>기술 제안</p>",
                },
                {
                    "section_key": "price",
                    "content": "<p>가격 제안</p>",
                },
            ],
        )

        # 총 단어 수 확인
        assert result["word_count"] > 0

        # 제안서 조회로 확인
        proposal = await proposal_service.get_proposal(proposal_id, user_id)
        section_map = {s.section_key: s for s in proposal.sections}
        assert "<p>사업 개요</p>" in section_map["overview"].content
        assert "<p>기술 제안</p>" in section_map["technical"].content
        assert "<p>가격 제안</p>" in section_map["price"].content

    @pytest.mark.asyncio
    async def test_auto_save_updates_metadata(
        self,
        proposal_service: ProposalService,
        test_proposal: Proposal,
        test_user: User,
    ):
        """자동 저장 시 섹션 메타데이터 업데이트 테스트"""
        user_id = UUID(str(test_user.id))
        proposal_id = test_proposal.id

        await proposal_service.auto_save_sections(
            proposal_id=proposal_id,
            user_id=user_id,
            sections_data=[
                {
                    "section_key": "overview",
                    "content": "<p>내용</p>",
                }
            ],
        )

        proposal = await proposal_service.get_proposal(proposal_id, user_id)
        overview_section = next(s for s in proposal.sections if s.section_key == "overview")

        metadata = overview_section.section_metadata
        assert metadata is not None
        assert "lastEditedBy" in metadata
        assert metadata["lastEditedBy"] == str(user_id)
        assert "editCount" in metadata
        assert metadata["editCount"] >= 1
        assert "lastEditAt" in metadata
        assert "format" in metadata
        assert metadata["format"] == "html"

    @pytest.mark.asyncio
    async def test_auto_save_proposal_not_found_fails(
        self,
        proposal_service: ProposalService,
        test_user: User,
    ):
        """존재하지 않는 제안서 자동 저장 실패 테스트"""
        user_id = UUID(str(test_user.id))
        non_existent_id = uuid4()

        with pytest.raises(NotFoundError):
            await proposal_service.auto_save_sections(
                proposal_id=non_existent_id,
                user_id=user_id,
                sections_data=[
                    {
                        "section_key": "overview",
                        "content": "<p>내용</p>",
                    }
                ],
            )

    @pytest.mark.asyncio
    async def test_validate_proposal_empty_section_fails(
        self,
        proposal_service: ProposalService,
        test_proposal: Proposal,
        test_user: User,
    ):
        """필수 섹션 비어있음 검증 실패 테스트"""
        user_id = UUID(str(test_user.id))
        proposal_id = test_proposal.id

        # overview 섹션 비워둠
        await proposal_service.update_section(
            proposal_id=proposal_id,
            section_key="overview",
            user_id=user_id,
            content="",
        )

        result = await proposal_service.validate_proposal(proposal_id, user_id)

        assert result["is_valid"] is False
        required_warnings = [w for w in result["warnings"] if w["type"] == "required_field"]
        assert len(required_warnings) > 0
        assert any(w["section"] == "overview" for w in required_warnings)

    @pytest.mark.asyncio
    async def test_validate_proposal_page_limit_exceeded_fails(
        self,
        proposal_service: ProposalService,
        test_proposal: Proposal,
        test_user: User,
    ):
        """페이지 제한 초과 검증 실패 테스트"""
        user_id = UUID(str(test_user.id))
        proposal_id = test_proposal.id

        # 매우 긴 내용으로 채움
        long_content = "<p>내용</p>" * 12000  # 약 40페이지
        await proposal_service.update_section(
            proposal_id=proposal_id,
            section_key="technical",
            user_id=user_id,
            content=long_content,
        )

        result = await proposal_service.validate_proposal(proposal_id, user_id, page_limit=10)

        assert result["is_valid"] is False
        page_warnings = [w for w in result["warnings"] if w["type"] == "page_limit"]
        assert len(page_warnings) > 0
        assert page_warnings[0]["current"] > page_warnings[0]["limit"]

    @pytest.mark.asyncio
    async def test_validate_proposal_success(
        self,
        proposal_service: ProposalService,
        test_proposal: Proposal,
        test_user: User,
    ):
        """모든 검증 통과 테스트"""
        user_id = UUID(str(test_user.id))
        proposal_id = test_proposal.id

        # 모든 필수 섹션 채움
        for section_key in ["overview", "technical"]:
            await proposal_service.update_section(
                proposal_id=proposal_id,
                section_key=section_key,
                user_id=user_id,
                content=f"<p>{section_key} 내용입니다.</p>" * 10,
            )

        # 평가 체크리스트 설정 (달성률 100%)
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

        result = await proposal_service.validate_proposal(proposal_id, user_id, page_limit=30)

        assert result["is_valid"] is True
        assert len(result["warnings"]) == 0

    @pytest.mark.asyncio
    async def test_update_evaluation_checklist(
        self,
        proposal_service: ProposalService,
        test_proposal: Proposal,
        test_user: User,
    ):
        """평가 체크리스트 업데이트 테스트"""
        user_id = UUID(str(test_user.id))
        proposal_id = test_proposal.id

        checklist = {
            "technical_capability": {"checked": True, "weight": 30},
            "price_competitiveness": {"checked": True, "weight": 25},
        }

        result = await proposal_service.update_evaluation_checklist(
            proposal_id=proposal_id,
            user_id=user_id,
            checklist=checklist,
        )

        assert "checklist" in result
        assert "achievement_rate" in result
        assert result["achievement_rate"] == 100  # (30 + 25) / 55 * 100

    @pytest.mark.asyncio
    async def test_update_evaluation_checklist_merges_existing(
        self,
        proposal_service: ProposalService,
        test_proposal: Proposal,
        test_user: User,
    ):
        """기존 체크리스트와 병합 테스트"""
        user_id = UUID(str(test_user.id))
        proposal_id = test_proposal.id

        # 첫 번째 업데이트
        await proposal_service.update_evaluation_checklist(
            proposal_id=proposal_id,
            user_id=user_id,
            checklist={
                "technical_capability": {"checked": True, "weight": 30},
                "price_competitiveness": {"checked": True, "weight": 25},
            },
        )

        # 두 번째 업데이트 (일부 항목만)
        result = await proposal_service.update_evaluation_checklist(
            proposal_id=proposal_id,
            user_id=user_id,
            checklist={
                "past_performance": {"checked": True, "weight": 20},
            },
        )

        # 병합 결과 확인
        assert result["checklist"]["technical_capability"]["checked"] is True
        assert result["checklist"]["price_competitiveness"]["checked"] is True
        assert result["checklist"]["past_performance"]["checked"] is True

    @pytest.mark.asyncio
    async def test_calculate_word_count_korean(
        self,
        proposal_service: ProposalService,
    ):
        """한글 단어 수 계산 테스트"""
        content = "<p>안녕하세요 테스트입니다</p>"
        word_count = proposal_service._calculate_word_count(content)
        # "안녕하세요" 5 + "테스트입니다" 6 = 11
        assert word_count == 11

    @pytest.mark.asyncio
    async def test_calculate_word_count_english(
        self,
        proposal_service: ProposalService,
    ):
        """영어 단어 수 계산 테스트"""
        content = "<p>Hello World Test</p>"
        word_count = proposal_service._calculate_word_count(content)
        # 3단어
        assert word_count == 3

    @pytest.mark.asyncio
    async def test_calculate_word_count_mixed(
        self,
        proposal_service: ProposalService,
    ):
        """한글+영어 혼합 단어 수 계산 테스트"""
        content = "<p>Hello 안녕하세요</p>"
        word_count = proposal_service._calculate_word_count(content)
        # "Hello" 1 + "안녕하세요" 5 = 6
        assert word_count == 6

    @pytest.mark.asyncio
    async def test_calculate_word_count_html_tags_ignored(
        self,
        proposal_service: ProposalService,
    ):
        """HTML 태그 무시 단어 수 계산 테스트"""
        content = "<h1>제목</h1><p>내용입니다</p>"
        word_count = proposal_service._calculate_word_count(content)
        # "제목" 2 + "내용입니다" 5 = 7
        assert word_count == 7

    @pytest.mark.asyncio
    async def test_calculate_evaluation_rate(
        self,
        proposal_service: ProposalService,
    ):
        """평가 항목 달성률 계산 테스트"""
        checklist = {
            "item1": {"checked": True, "weight": 30},
            "item2": {"checked": True, "weight": 20},
            "item3": {"checked": False, "weight": 25},
            "item4": {"checked": False, "weight": 25},
        }

        rate = proposal_service._calculate_evaluation_rate(checklist)

        # 체크된 가중치: 30 + 20 = 50
        # 전체 가중치: 100
        # 달성률: 50%
        assert rate == 50

    @pytest.mark.asyncio
    async def test_calculate_evaluation_rate_empty_checklist(
        self,
        proposal_service: ProposalService,
    ):
        """빈 체크리스트 달성률 계산 테스트"""
        rate = proposal_service._calculate_evaluation_rate({})
        assert rate == 0

    @pytest.mark.asyncio
    async def test_calculate_evaluation_rate_none_checklist(
        self,
        proposal_service: ProposalService,
    ):
        """null 체크리스트 달성률 계산 테스트"""
        rate = proposal_service._calculate_evaluation_rate(None)
        assert rate == 0
