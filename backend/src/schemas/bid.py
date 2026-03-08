"""공고 관련 Pydantic 스키마"""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class BidAttachmentSchema(BaseModel):
    """첨부파일 스키마"""
    id: str
    filename: str
    file_type: str
    file_url: str
    has_extracted_text: bool


class BidListItem(BaseModel):
    """공고 목록 아이템 스키마"""
    id: str
    bid_number: str
    title: str
    organization: str
    region: Optional[str] = None
    category: Optional[str] = None
    bid_type: Optional[str] = None
    contract_method: Optional[str] = None
    budget: Optional[Decimal] = None
    announcement_date: Optional[date] = None
    deadline: datetime
    status: str
    attachment_count: int = 0
    crawled_at: Optional[datetime] = None


class BidDetail(BaseModel):
    """공고 상세 스키마"""
    id: str
    bid_number: str
    title: str
    description: Optional[str] = None
    organization: str
    region: Optional[str] = None
    category: Optional[str] = None
    bid_type: Optional[str] = None
    contract_method: Optional[str] = None
    budget: Optional[Decimal] = None
    estimated_price: Optional[Decimal] = None
    announcement_date: Optional[date] = None
    deadline: datetime
    open_date: Optional[datetime] = None
    status: str
    scoring_criteria: Optional[dict] = None
    attachments: list[BidAttachmentSchema] = []
    crawled_at: Optional[datetime] = None
    created_at: datetime


class BidListResponse(BaseModel):
    """공고 목록 응답 스키마"""
    items: list[BidListItem]


class BidQuery(BaseModel):
    """공고 조회 파라미터 스키마"""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    status: Optional[str] = None
    keyword: Optional[str] = None
    region: Optional[str] = None
    category: Optional[str] = None
    bid_type: Optional[str] = None
    min_budget: Optional[Decimal] = None
    max_budget: Optional[Decimal] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    sort_by: str = "deadline"
    sort_order: str = "asc"

    # 유효한 상태값
    VALID_STATUS = {"open", "closed", "awarded", "cancelled"}
    VALID_SORT_BY = {"deadline", "announcementDate", "budget", "createdAt"}
    VALID_SORT_ORDER = {"asc", "desc"}
