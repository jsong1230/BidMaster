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


# ============================================================
# F-05 제안서 편집기 스키마
# ============================================================


class AutoSaveSectionItem(BaseModel):
    """자동 저장 섹션 아이템"""

    section_key: str = Field(..., alias="sectionKey", description="섹션 키")
    content: str = Field(..., description="HTML 콘텐츠")
    word_count: int | None = Field(None, alias="wordCount", description="단어 수")

    model_config = {"populate_by_name": True}


class AutoSaveRequest(BaseModel):
    """자동 저장 요청 스키마"""

    sections: list[AutoSaveSectionItem] = Field(..., description="저장할 섹션 목록")


class AutoSaveResponse(BaseModel):
    """자동 저장 응답 스키마"""

    saved_at: datetime = Field(..., alias="savedAt", description="저장 시각")
    word_count: int = Field(..., alias="wordCount", description="총 단어 수")

    model_config = {"populate_by_name": True}


class ValidationWarning(BaseModel):
    """검증 경고"""

    type: str = Field(..., description="경고 타입 (required_field, page_limit, evaluation_incomplete)")
    section: str | None = Field(None, description="관련 섹션 키")
    message: str = Field(..., description="경고 메시지")
    current: int | None = Field(None, description="현재 값")
    limit: int | None = Field(None, description="제한 값")


class SectionStats(BaseModel):
    """섹션 통계"""

    section_key: str = Field(..., alias="sectionKey")
    word_count: int = Field(..., alias="wordCount")
    is_empty: bool = Field(..., alias="isEmpty")

    model_config = {"populate_by_name": True}


class ValidationStats(BaseModel):
    """검증 통계"""

    total_word_count: int = Field(..., alias="totalWordCount")
    estimated_pages: int = Field(..., alias="estimatedPages")
    section_stats: list[SectionStats] = Field(..., alias="sectionStats")

    model_config = {"populate_by_name": True}


class ValidationRequest(BaseModel):
    """검증 요청 스키마"""

    page_limit: int | None = Field(None, alias="pageLimit", description="페이지 제한")

    model_config = {"populate_by_name": True}


class ValidationResponse(BaseModel):
    """검증 응답 스키마"""

    is_valid: bool = Field(..., alias="isValid", description="검증 통과 여부")
    warnings: list[ValidationWarning] = Field(default_factory=list, description="경고 목록")
    stats: ValidationStats = Field(..., description="통계")

    model_config = {"populate_by_name": True}


class ChecklistItem(BaseModel):
    """평가 체크리스트 아이템"""

    checked: bool = Field(..., description="체크 여부")
    weight: int = Field(..., ge=0, le=100, description="가중치")


class ChecklistUpdateRequest(BaseModel):
    """평가 체크리스트 업데이트 요청"""

    checklist: dict[str, ChecklistItem] = Field(..., description="체크리스트")


class ChecklistUpdateResponse(BaseModel):
    """평가 체크리스트 업데이트 응답"""

    checklist: dict[str, ChecklistItem] = Field(..., description="업데이트된 체크리스트")
    achievement_rate: int = Field(..., alias="achievementRate", ge=0, le=100, description="달성률")
    updated_at: datetime = Field(..., alias="updatedAt")

    model_config = {"populate_by_name": True}
