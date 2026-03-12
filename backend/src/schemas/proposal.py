"""제안서 스키마 (F-03)"""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from src.models.proposal_section import SECTION_DEFINITIONS


# ============================================================
# 섹션 스키마
# ============================================================


class ProposalSectionBase(BaseModel):
    """섹션 기본 스키마"""

    section_key: str = Field(..., description="섹션 키")
    title: str = Field(..., description="섹션 제목")
    content: str | None = Field(None, description="섹션 내용")
    section_metadata: dict[str, Any] | None = Field(
        None, alias="metadata", description="섹션 메타데이터"
    )

    model_config = {
        "populate_by_name": True,
    }


class ProposalSectionCreate(ProposalSectionBase):
    """섹션 생성 스키마"""

    pass


class ProposalSectionUpdate(BaseModel):
    """섹션 수정 스키마"""

    title: str | None = None
    content: str | None = None
    section_metadata: dict[str, Any] | None = Field(None, alias="metadata")


class ProposalSectionResponse(ProposalSectionBase):
    """섹션 응답 스키마"""

    id: UUID
    proposal_id: UUID
    order: int
    is_ai_generated: bool
    word_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


# ============================================================
# 버전 스키마
# ============================================================


class ProposalVersionResponse(BaseModel):
    """버전 응답 스키마"""

    id: UUID
    proposal_id: UUID
    version_number: int
    snapshot: dict[str, Any]
    created_by: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================
# 제안서 스키마
# ============================================================


class ProposalBase(BaseModel):
    """제안서 기본 스키마"""

    title: str = Field(..., max_length=300, description="제안서 제목")
    company_id: UUID | None = Field(None, description="회사 ID")


class ProposalCreate(ProposalBase):
    """제안서 생성 스키마"""

    bid_id: UUID = Field(..., description="입찰 공고 ID")


class ProposalUpdate(BaseModel):
    """제안서 수정 스키마"""

    title: str | None = Field(None, max_length=300)
    evaluation_checklist: dict[str, Any] | None = None


class ProposalResponse(BaseModel):
    """제안서 응답 스키마"""

    id: UUID
    user_id: UUID = Field(alias="userId")
    bid_id: UUID = Field(alias="bidId")
    company_id: UUID | None = Field(None, alias="companyId")
    title: str
    status: str
    version: int
    evaluation_checklist: dict[str, Any] | None = Field(None, alias="evaluationChecklist")
    page_count: int = Field(alias="pageCount")
    word_count: int = Field(alias="wordCount")
    generated_at: datetime | None = Field(None, alias="generatedAt")
    submitted_at: datetime | None = Field(None, alias="submittedAt")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class ProposalDetailResponse(ProposalResponse):
    """제안서 상세 응답 스키마"""

    sections: list[ProposalSectionResponse] = []
    versions: list[ProposalVersionResponse] = []


class ProposalListResponse(BaseModel):
    """제안서 목록 응답 스키마"""

    id: UUID
    bid_id: UUID = Field(alias="bidId")
    title: str
    status: str
    version: int
    page_count: int = Field(alias="pageCount")
    word_count: int = Field(alias="wordCount")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    # 조인 필드
    bid_title: str | None = Field(None, alias="bidTitle")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


# ============================================================
# 제안서 생성 요청/응답
# ============================================================


class GenerateProposalRequest(BaseModel):
    """제안서 생성 요청 스키마"""

    bid_id: UUID = Field(..., description="입찰 공고 ID")
    company_id: UUID | None = Field(None, description="회사 ID (없으면 사용자 기본 회사 사용)")
    title: str | None = Field(None, max_length=300, description="제안서 제목 (없으면 공고명 사용)")
    sections: list[str] | None = Field(
        None,
        description="생성할 섹션 키 목록 (없으면 전체 섹션 생성)",
    )


class GenerateSectionRequest(BaseModel):
    """개별 섹션 생성 요청 스키마"""

    section_key: str = Field(..., description="섹션 키")
    context: dict[str, Any] | None = Field(None, description="추가 컨텍스트")


class GenerateSectionResponse(BaseModel):
    """개별 섹션 생성 응답 스키마"""

    section_key: str = Field(alias="sectionKey")
    title: str
    content: str
    word_count: int = Field(alias="wordCount")

    model_config = {"populate_by_name": True}


# ============================================================
# AI 스트리밍 이벤트
# ============================================================


class SSEEvent(BaseModel):
    """SSE 이벤트 스키마"""

    event: str
    data: dict[str, Any]


class ProposalGenerationProgress(BaseModel):
    """제안서 생성 진행 상황"""

    proposal_id: UUID = Field(alias="proposalId")
    status: str
    current_section: str | None = Field(None, alias="currentSection")
    completed_sections: int = Field(0, alias="completedSections")
    total_sections: int = Field(0, alias="totalSections")
    message: str | None = None

    model_config = {"populate_by_name": True}


# ============================================================
# 목록 조회 파라미터
# ============================================================


class ProposalListParams(BaseModel):
    """제안서 목록 조회 파라미터"""

    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    status: str | None = None
    bid_id: UUID | None = None
    sort_by: str = Field("updated_at", pattern="^(created_at|updated_at|title|status)$")
    sort_order: str = Field("desc", pattern="^(asc|desc)$")


# ============================================================
# 내보내기 스키마
# ============================================================


class ExportRequest(BaseModel):
    """내보내기 요청 스키마"""

    format: str = Field(
        ...,
        pattern="^(pdf|docx|hwp)$",
        description="내보내기 형식",
    )
    include_version: bool = Field(
        False,
        description="버전 정보 포함 여부",
    )


class ExportResponse(BaseModel):
    """내보내기 응답 스키마"""

    download_url: str = Field(alias="downloadUrl")
    file_name: str = Field(alias="fileName")
    format: str
    expires_at: datetime = Field(alias="expiresAt")

    model_config = {"populate_by_name": True}


# ============================================================
# 상수
# ============================================================


PROPOSAL_STATUSES = ["draft", "generating", "ready", "submitted"]

ALL_SECTION_KEYS = list(SECTION_DEFINITIONS.keys())
