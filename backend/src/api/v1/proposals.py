"""제안서 API (F-03) - SSE 스트리밍 지원"""
import json
import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.exceptions import NotFoundError, PermissionError
from src.models.proposal_section import SECTION_DEFINITIONS
from src.schemas.proposal import (
    ExportRequest,
    GenerateProposalRequest,
    GenerateSectionRequest,
    ProposalCreate,
    ProposalDetailResponse,
    ProposalSectionResponse,
    ProposalSectionUpdate,
    ProposalUpdate,
)
from src.services.proposal_generator_service import ProposalGeneratorService
from src.services.proposal_service import ProposalService

logger = logging.getLogger(__name__)
router = APIRouter()


def get_current_user_id(request: Request) -> UUID:
    """현재 사용자 ID 추출 (임시)"""
    user_id = request.state.user_id if hasattr(request.state, "user_id") else None
    if not user_id:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    return UUID(str(user_id))


# ============================================================
# 제안서 목록/상세
# ============================================================


@router.get("", response_model=dict)
async def list_proposals(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    bid_id: UUID | None = Query(None),
    sort_by: str = Query("updated_at"),
    sort_order: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
):
    """제안서 목록 조회"""
    user_id = get_current_user_id(request)
    service = ProposalService(db)

    proposals, total = await service.get_proposals(
        user_id=user_id,
        page=page,
        page_size=page_size,
        status=status,
        bid_id=bid_id,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    items = []
    for p in proposals:
        items.append({
            "id": str(p.id),
            "bidId": str(p.bid_id),
            "bidTitle": p.bid.title if p.bid else None,
            "title": p.title,
            "status": p.status,
            "version": p.version,
            "pageCount": p.page_count,
            "wordCount": p.word_count,
            "createdAt": p.created_at.isoformat(),
            "updatedAt": p.updated_at.isoformat(),
        })

    return {
        "success": True,
        "data": {
            "items": items,
            "meta": {
                "page": page,
                "pageSize": page_size,
                "total": total,
                "totalPages": (total + page_size - 1) // page_size,
            },
        },
    }


@router.get("/{proposal_id}", response_model=dict)
async def get_proposal(
    proposal_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """제안서 상세 조회"""
    user_id = get_current_user_id(request)
    service = ProposalService(db)

    proposal = await service.get_proposal(proposal_id, user_id)

    sections = []
    for s in proposal.sections:
        sections.append({
            "id": str(s.id),
            "sectionKey": s.section_key,
            "title": s.title,
            "order": s.order,
            "content": s.content,
            "metadata": s.section_metadata,
            "isAiGenerated": s.is_ai_generated,
            "wordCount": s.word_count,
            "createdAt": s.created_at.isoformat(),
            "updatedAt": s.updated_at.isoformat(),
        })

    versions = []
    for v in proposal.versions:
        versions.append({
            "id": str(v.id),
            "versionNumber": v.version_number,
            "createdAt": v.created_at.isoformat(),
        })

    return {
        "success": True,
        "data": {
            "id": str(proposal.id),
            "userId": str(proposal.user_id),
            "bidId": str(proposal.bid_id),
            "companyId": str(proposal.company_id) if proposal.company_id else None,
            "title": proposal.title,
            "status": proposal.status,
            "version": proposal.version,
            "evaluationChecklist": proposal.evaluation_checklist,
            "pageCount": proposal.page_count,
            "wordCount": proposal.word_count,
            "generatedAt": proposal.generated_at.isoformat() if proposal.generated_at else None,
            "submittedAt": proposal.submitted_at.isoformat() if proposal.submitted_at else None,
            "createdAt": proposal.created_at.isoformat(),
            "updatedAt": proposal.updated_at.isoformat(),
            "sections": sections,
            "versions": versions,
        },
    }


# ============================================================
# 제안서 생성/수정/삭제
# ============================================================


@router.post("", response_model=dict)
async def create_proposal(
    request: Request,
    data: ProposalCreate,
    db: AsyncSession = Depends(get_db),
):
    """빈 제안서 생성 (초안)"""
    user_id = get_current_user_id(request)
    service = ProposalService(db)

    proposal = await service.create_proposal(
        user_id=user_id,
        bid_id=data.bid_id,
        title=data.title,
        company_id=data.company_id,
    )

    await db.commit()

    return {
        "success": True,
        "data": {
            "id": str(proposal.id),
            "title": proposal.title,
            "status": proposal.status,
            "createdAt": proposal.created_at.isoformat(),
        },
        "message": "제안서가 생성되었습니다.",
    }


@router.patch("/{proposal_id}", response_model=dict)
async def update_proposal(
    proposal_id: UUID,
    request: Request,
    data: ProposalUpdate,
    db: AsyncSession = Depends(get_db),
):
    """제안서 기본 정보 수정"""
    user_id = get_current_user_id(request)
    service = ProposalService(db)

    proposal = await service.update_proposal(
        proposal_id=proposal_id,
        user_id=user_id,
        title=data.title,
        evaluation_checklist=data.evaluation_checklist,
    )

    await db.commit()

    return {
        "success": True,
        "data": {
            "id": str(proposal.id),
            "title": proposal.title,
            "updatedAt": proposal.updated_at.isoformat(),
        },
    }


@router.delete("/{proposal_id}", response_model=dict)
async def delete_proposal(
    proposal_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """제안서 삭제"""
    user_id = get_current_user_id(request)
    service = ProposalService(db)

    await service.delete_proposal(proposal_id, user_id)
    await db.commit()

    return {
        "success": True,
        "message": "제안서가 삭제되었습니다.",
    }


# ============================================================
# 섹션 관리
# ============================================================


@router.patch("/{proposal_id}/sections/{section_key}", response_model=dict)
async def update_section(
    proposal_id: UUID,
    section_key: str,
    request: Request,
    data: ProposalSectionUpdate,
    db: AsyncSession = Depends(get_db),
):
    """섹션 내용 수정"""
    user_id = get_current_user_id(request)
    service = ProposalService(db)

    section = await service.update_section(
        proposal_id=proposal_id,
        section_key=section_key,
        user_id=user_id,
        content=data.content,
        title=data.title,
        metadata=data.section_metadata,
    )

    await db.commit()

    return {
        "success": True,
        "data": {
            "sectionKey": section.section_key,
            "title": section.title,
            "wordCount": section.word_count,
            "updatedAt": section.updated_at.isoformat(),
        },
    }


# ============================================================
# AI 생성 (SSE 스트리밍)
# ============================================================


@router.post("/{proposal_id}/generate", response_class=StreamingResponse)
async def generate_proposal_content(
    proposal_id: UUID,
    request: Request,
    data: GenerateProposalRequest | None = None,
    db: AsyncSession = Depends(get_db),
):
    """제안서 AI 생성 (SSE 스트리밍)"""
    user_id = get_current_user_id(request)

    async def event_generator():
        generator_service = ProposalGeneratorService(db)
        section_keys = data.sections if data and data.sections else None

        try:
            async for event in generator_service.generate_proposal(
                proposal_id=proposal_id,
                user_id=user_id,
                section_keys=section_keys,
            ):
                event_data = json.dumps(event["data"], ensure_ascii=False)
                yield f"event: {event['event']}\ndata: {event_data}\n\n"

            await db.commit()

        except NotFoundError as e:
            yield f"event: error\ndata: {json.dumps({'code': e.code, 'message': e.message})}\n\n"
        except PermissionError as e:
            yield f"event: error\ndata: {json.dumps({'code': e.code, 'message': e.message})}\n\n"
        except Exception as e:
            logger.error(f"[제안서] 생성 실패: {e}")
            yield f"event: error\ndata: {json.dumps({'code': 'AI_001', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{proposal_id}/sections/{section_key}/regenerate", response_model=dict)
async def regenerate_section(
    proposal_id: UUID,
    section_key: str,
    request: Request,
    data: GenerateSectionRequest | None = None,
    db: AsyncSession = Depends(get_db),
):
    """개별 섹션 재생성"""
    user_id = get_current_user_id(request)
    generator_service = ProposalGeneratorService(db)

    context = data.context if data else None

    result = await generator_service.generate_single_section(
        proposal_id=proposal_id,
        section_key=section_key,
        user_id=user_id,
        context=context,
    )

    await db.commit()

    return {
        "success": True,
        "data": result,
    }


# ============================================================
# 버전 관리
# ============================================================


@router.post("/{proposal_id}/versions", response_model=dict)
async def create_version(
    proposal_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """현재 상태 버전 저장"""
    user_id = get_current_user_id(request)
    service = ProposalService(db)

    version = await service.create_version(proposal_id, user_id)
    await db.commit()

    return {
        "success": True,
        "data": {
            "id": str(version.id),
            "versionNumber": version.version_number,
            "createdAt": version.created_at.isoformat(),
        },
        "message": f"버전 {version.version_number}이 저장되었습니다.",
    }


@router.post("/{proposal_id}/versions/{version_number}/restore", response_model=dict)
async def restore_version(
    proposal_id: UUID,
    version_number: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """특정 버전으로 복원"""
    user_id = get_current_user_id(request)
    service = ProposalService(db)

    proposal = await service.restore_version(
        proposal_id=proposal_id,
        version_number=version_number,
        user_id=user_id,
    )
    await db.commit()

    return {
        "success": True,
        "data": {
            "id": str(proposal.id),
            "version": proposal.version,
        },
        "message": f"버전 {version_number}으로 복원되었습니다.",
    }


@router.get("/{proposal_id}/versions/{version_number}", response_model=dict)
async def get_version(
    proposal_id: UUID,
    version_number: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """특정 버전 상세 조회"""
    user_id = get_current_user_id(request)
    service = ProposalService(db)

    await service.get_proposal(proposal_id, user_id, include_sections=False)

    from sqlalchemy import select
    from src.models.proposal_version import ProposalVersion

    stmt = select(ProposalVersion).where(
        ProposalVersion.proposal_id == proposal_id,
        ProposalVersion.version_number == version_number,
    )
    result = await db.execute(stmt)
    version = result.scalar_one_or_none()

    if not version:
        raise HTTPException(status_code=404, detail="버전을 찾을 수 없습니다.")

    return {
        "success": True,
        "data": {
            "id": str(version.id),
            "versionNumber": version.version_number,
            "snapshot": version.snapshot,
            "createdAt": version.created_at.isoformat(),
        },
    }


# ============================================================
# 상태 관리
# ============================================================


@router.post("/{proposal_id}/submit", response_model=dict)
async def submit_proposal(
    proposal_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """제안서 제출 처리"""
    user_id = get_current_user_id(request)
    service = ProposalService(db)

    proposal = await service.update_status(proposal_id, user_id, "submitted")
    await db.commit()

    return {
        "success": True,
        "data": {
            "id": str(proposal.id),
            "status": proposal.status,
            "submittedAt": proposal.submitted_at.isoformat() if proposal.submitted_at else None,
        },
        "message": "제안서가 제출되었습니다.",
    }


# ============================================================
# 내보내기 (스텁)
# ============================================================


@router.post("/{proposal_id}/export", response_model=dict)
async def export_proposal(
    proposal_id: UUID,
    request: Request,
    data: ExportRequest,
    db: AsyncSession = Depends(get_db),
):
    """제안서 내보내기 (PDF/DOCX/HWP)"""
    user_id = get_current_user_id(request)
    service = ProposalService(db)

    proposal = await service.get_proposal(proposal_id, user_id)

    return {
        "success": True,
        "data": {
            "downloadUrl": f"/api/v1/proposals/{proposal_id}/download?format={data.format}",
            "fileName": f"{proposal.title}.{data.format}",
            "format": data.format,
            "expiresAt": "2026-03-13T00:00:00Z",
        },
        "message": f"{data.format.upper()} 파일 생성이 요청되었습니다.",
    }
