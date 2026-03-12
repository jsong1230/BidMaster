"""제안서 CRUD 서비스 (F-03)"""
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.exceptions import NotFoundError, PermissionError, ValidationError
from src.models.bid import Bid
from src.models.company import Company
from src.models.proposal import Proposal
from src.models.proposal_section import ProposalSection, SECTION_DEFINITIONS
from src.models.proposal_version import ProposalVersion
from src.models.user import User

logger = logging.getLogger(__name__)


class ProposalService:
    """제안서 CRUD 서비스"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ============================================================
    # 제안서 조회
    # ============================================================

    async def get_proposals(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        bid_id: UUID | None = None,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
    ) -> tuple[list[Proposal], int]:
        """
        제안서 목록 조회

        Returns: (제안서 목록, 전체 건수)
        """
        # 기본 쿼리 (soft delete 제외)
        stmt = (
            select(Proposal)
            .where(Proposal.user_id == user_id, Proposal.deleted_at.is_(None))
            .options(selectinload(Proposal.bid))
        )

        # 필터링
        if status:
            if status not in ["draft", "generating", "ready", "submitted"]:
                raise ValidationError(
                    code="PROPOSAL_001",
                    message="유효하지 않은 상태입니다.",
                )
            stmt = stmt.where(Proposal.status == status)

        if bid_id:
            stmt = stmt.where(Proposal.bid_id == bid_id)

        # 정렬
        order_col = getattr(Proposal, sort_by, Proposal.updated_at)
        if sort_order == "desc":
            stmt = stmt.order_by(order_col.desc())
        else:
            stmt = stmt.order_by(order_col.asc())

        # 전체 건수
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar() or 0

        # 페이지네이션
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        result = await self.db.execute(stmt)
        proposals = list(result.scalars().all())

        return proposals, total

    async def get_proposal(
        self,
        proposal_id: UUID,
        user_id: UUID,
        include_sections: bool = True,
    ) -> Proposal:
        """
        제안서 상세 조회

        Raises: NotFoundError, PermissionError
        """
        stmt = select(Proposal).where(
            Proposal.id == proposal_id,
            Proposal.deleted_at.is_(None),
        )

        if include_sections:
            stmt = stmt.options(
                selectinload(Proposal.sections),
                selectinload(Proposal.versions),
            )

        result = await self.db.execute(stmt)
        proposal = result.scalar_one_or_none()

        if not proposal:
            raise NotFoundError(
                code="PROPOSAL_002",
                message="제안서를 찾을 수 없습니다.",
            )

        if proposal.user_id != user_id:
            raise PermissionError(
                code="PERMISSION_002",
                message="리소스 소유자가 아닙니다.",
            )

        return proposal

    # ============================================================
    # 제안서 생성
    # ============================================================

    async def create_proposal(
        self,
        user_id: UUID,
        bid_id: UUID,
        title: str | None = None,
        company_id: UUID | None = None,
    ) -> Proposal:
        """
        빈 제안서 생성 (초안 상태)

        - 공고 정보를 조회하여 기본 제목 설정
        - 기본 섹션 생성 (내용은 비어있음)
        """
        # 공고 존재 확인
        bid = await self._get_bid(bid_id)
        if not bid:
            raise NotFoundError(
                code="BID_001",
                message="입찰 공고를 찾을 수 없습니다.",
            )

        # 기존 제안서 확인 (동일 공고에 대해)
        existing = await self._get_proposal_by_bid(user_id, bid_id)
        if existing:
            raise ValidationError(
                code="PROPOSAL_003",
                message="이미 해당 공고에 대한 제안서가 존재합니다.",
            )

        # 회사 확인
        if company_id:
            company = await self._get_company(company_id)
            if not company or company.user_id != user_id:
                raise ValidationError(
                    code="COMPANY_001",
                    message="유효하지 않은 회사입니다.",
                )

        # 제안서 생성
        proposal = Proposal(
            user_id=user_id,
            bid_id=bid_id,
            company_id=company_id,
            title=title or bid.title,
            status="draft",
            version=1,
        )
        self.db.add(proposal)
        await self.db.flush()

        # 기본 섹션 생성
        for section_key, section_def in SECTION_DEFINITIONS.items():
            section = ProposalSection(
                proposal_id=proposal.id,
                section_key=section_key,
                title=section_def["title"],
                order=section_def["order"],
                content=None,
                is_ai_generated=False,
            )
            self.db.add(section)

        await self.db.flush()
        logger.info(f"[제안서] 생성 완료: id={proposal.id}, bid={bid_id}")

        return proposal

    # ============================================================
    # 제안서 수정
    # ============================================================

    async def update_proposal(
        self,
        proposal_id: UUID,
        user_id: UUID,
        title: str | None = None,
        evaluation_checklist: dict | None = None,
    ) -> Proposal:
        """제안서 기본 정보 수정"""
        proposal = await self.get_proposal(proposal_id, user_id)

        if title:
            proposal.title = title
        if evaluation_checklist is not None:
            proposal.evaluation_checklist = evaluation_checklist

        proposal.updated_at = datetime.now(timezone.utc)
        await self.db.flush()

        return proposal

    async def update_section(
        self,
        proposal_id: UUID,
        section_key: str,
        user_id: UUID,
        content: str | None = None,
        title: str | None = None,
        metadata: dict | None = None,
    ) -> ProposalSection:
        """섹션 내용 수정"""
        # 제안서 확인
        proposal = await self.get_proposal(proposal_id, user_id)

        # 섹션 조회
        stmt = select(ProposalSection).where(
            ProposalSection.proposal_id == proposal_id,
            ProposalSection.section_key == section_key,
        )
        result = await self.db.execute(stmt)
        section = result.scalar_one_or_none()

        if not section:
            raise NotFoundError(
                code="SECTION_001",
                message="섹션을 찾을 수 없습니다.",
            )

        # 내용 수정
        if content is not None:
            section.content = content
            section.is_ai_generated = False  # 수동 수정 시 AI 생성 플래그 해제

        if title:
            section.title = title
        if metadata is not None:
            section.section_metadata = metadata

        section.updated_at = datetime.now(timezone.utc)

        # 제안서 통계 업데이트
        await self._update_proposal_stats(proposal)

        await self.db.flush()
        return section

    # ============================================================
    # 버전 관리
    # ============================================================

    async def create_version(
        self,
        proposal_id: UUID,
        user_id: UUID,
    ) -> ProposalVersion:
        """현재 상태 스냅샷 버전 생성"""
        proposal = await self.get_proposal(
            proposal_id, user_id, include_sections=True
        )

        # 섹션 데이터 스냅샷
        sections_snapshot = []
        for section in proposal.sections:
            sections_snapshot.append({
                "section_key": section.section_key,
                "title": section.title,
                "order": section.order,
                "content": section.content,
                "section_metadata": section.section_metadata,
                "is_ai_generated": section.is_ai_generated,
            })

        snapshot = {
            "title": proposal.title,
            "version": proposal.version,
            "sections": sections_snapshot,
            "evaluation_checklist": proposal.evaluation_checklist,
            "page_count": proposal.page_count,
            "word_count": proposal.word_count,
        }

        # 버전 생성
        version = ProposalVersion(
            proposal_id=proposal_id,
            version_number=proposal.version,
            snapshot=snapshot,
            created_by=user_id,
        )
        self.db.add(version)

        # 제안서 버전 증가
        proposal.version += 1
        proposal.updated_at = datetime.now(timezone.utc)

        await self.db.flush()
        logger.info(f"[제안서] 버전 생성: proposal={proposal_id}, version={version.version_number}")

        return version

    async def restore_version(
        self,
        proposal_id: UUID,
        version_number: int,
        user_id: UUID,
    ) -> Proposal:
        """특정 버전으로 복원"""
        proposal = await self.get_proposal(proposal_id, user_id)

        # 버전 조회
        stmt = select(ProposalVersion).where(
            ProposalVersion.proposal_id == proposal_id,
            ProposalVersion.version_number == version_number,
        )
        result = await self.db.execute(stmt)
        version = result.scalar_one_or_none()

        if not version:
            raise NotFoundError(
                code="VERSION_001",
                message="해당 버전을 찾을 수 없습니다.",
            )

        # 현재 상태를 새 버전으로 저장
        await self.create_version(proposal_id, user_id)

        # 스냅샷 복원
        snapshot = version.snapshot
        proposal.title = snapshot["title"]
        proposal.evaluation_checklist = snapshot.get("evaluation_checklist")
        proposal.page_count = snapshot.get("page_count", 0)
        proposal.word_count = snapshot.get("word_count", 0)

        # 섹션 복원
        for section_data in snapshot.get("sections", []):
            stmt = select(ProposalSection).where(
                ProposalSection.proposal_id == proposal_id,
                ProposalSection.section_key == section_data["section_key"],
            )
            result = await self.db.execute(stmt)
            section = result.scalar_one_or_none()

            if section:
                section.title = section_data["title"]
                section.content = section_data["content"]
                section.section_metadata = section_data.get("section_metadata")
                section.is_ai_generated = section_data.get("is_ai_generated", True)
                section.updated_at = datetime.now(timezone.utc)

        proposal.updated_at = datetime.now(timezone.utc)
        await self.db.flush()

        logger.info(f"[제안서] 버전 복원: proposal={proposal_id}, version={version_number}")
        return proposal

    # ============================================================
    # 상태 관리
    # ============================================================

    async def update_status(
        self,
        proposal_id: UUID,
        user_id: UUID,
        status: str,
    ) -> Proposal:
        """제안서 상태 변경"""
        if status not in ["draft", "generating", "ready", "submitted"]:
            raise ValidationError(
                code="PROPOSAL_001",
                message="유효하지 않은 상태입니다.",
            )

        proposal = await self.get_proposal(proposal_id, user_id)
        old_status = proposal.status
        proposal.status = status

        # 상태별 추가 처리
        if status == "ready" and not proposal.generated_at:
            proposal.generated_at = datetime.now(timezone.utc)

        if status == "submitted" and not proposal.submitted_at:
            proposal.submitted_at = datetime.now(timezone.utc)

        proposal.updated_at = datetime.now(timezone.utc)
        await self.db.flush()

        logger.info(f"[제안서] 상태 변경: proposal={proposal_id}, {old_status} -> {status}")
        return proposal

    # ============================================================
    # 삭제
    # ============================================================

    async def delete_proposal(
        self,
        proposal_id: UUID,
        user_id: UUID,
    ) -> None:
        """제안서 소프트 삭제"""
        proposal = await self.get_proposal(proposal_id, user_id)
        proposal.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()

        logger.info(f"[제안서] 삭제 완료: id={proposal_id}")

    # ============================================================
    # 내부 메서드
    # ============================================================

    async def _get_bid(self, bid_id: UUID) -> Bid | None:
        """공고 조회"""
        stmt = select(Bid).where(Bid.id == bid_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_company(self, company_id: UUID) -> Company | None:
        """회사 조회"""
        stmt = select(Company).where(Company.id == company_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_proposal_by_bid(
        self, user_id: UUID, bid_id: UUID
    ) -> Proposal | None:
        """공고별 제안서 조회"""
        stmt = select(Proposal).where(
            Proposal.user_id == user_id,
            Proposal.bid_id == bid_id,
            Proposal.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _update_proposal_stats(self, proposal: Proposal) -> None:
        """제안서 통계(글자수 등) 업데이트"""
        total_words = 0
        for section in proposal.sections:
            if section.content:
                total_words += len(section.content)

        proposal.word_count = total_words
        # 페이지 수는 약 2000자당 1페이지로 계산
        proposal.page_count = max(1, total_words // 2000)

    async def _get_user(self, user_id: UUID) -> User | None:
        """사용자 조회"""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
