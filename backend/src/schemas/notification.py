"""알림 관련 스키마 (F-10)"""
from datetime import datetime
from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# 알림 유형
NotificationType = Literal["bid_matched", "deadline", "bid_result", "proposal_ready"]

# 알림 채널
NotificationChannel = Literal["in_app", "email", "kakao"]

# 알림 유형 라벨
NOTIFICATION_TYPE_LABELS: dict[str, str] = {
    "bid_matched": "매칭 공고 알림",
    "deadline": "마감 임박 알림",
    "bid_result": "낙찰 결과 알림",
    "proposal_ready": "제안서 생성 완료 알림",
}


class CamelCaseResponse(BaseModel):
    """camelCase JSON 응답 기본 클래스"""
    model_config = ConfigDict(
        alias_generator=lambda x: ''.join(
            word.capitalize() if i > 0 else word.lower()
            for i, word in enumerate(x.split('_'))
        ),
        populate_by_name=True,
    )


class NotificationResponse(CamelCaseResponse):
    """알림 응답"""
    id: UUID
    type: str
    title: str
    content: str
    data: dict[str, Any] = Field(default_factory=dict)
    is_read: bool
    channel: str
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    created_at: datetime


class NotificationListResponse(CamelCaseResponse):
    """알림 목록 응답"""
    items: list[NotificationResponse]


class NotificationListMeta(CamelCaseResponse):
    """알림 목록 메타"""
    page: int
    page_size: int
    total: int
    total_pages: int


class UnreadCountResponse(CamelCaseResponse):
    """안읽은 알림 수 응답"""
    unread_count: int


class MarkReadResponse(CamelCaseResponse):
    """읽음 처리 응답"""
    id: UUID
    is_read: bool
    read_at: datetime


class MarkAllReadResponse(CamelCaseResponse):
    """전체 읽음 처리 응답"""
    updated_count: int


class NotificationSettingResponse(CamelCaseResponse):
    """알림 설정 응답"""
    notification_type: str
    label: str
    email_enabled: bool
    kakao_enabled: bool
    push_enabled: bool


class NotificationSettingsResponse(CamelCaseResponse):
    """알림 설정목록 응답"""
    settings: list[NotificationSettingResponse]


class NotificationSettingUpdate(BaseModel):
    """알림 설정 변경 항목"""
    notification_type: str
    email_enabled: bool
    kakao_enabled: bool
    push_enabled: bool

    @field_validator("notification_type")
    @classmethod
    def validate_notification_type(cls, v: str) -> str:
        """알림 유형 검증"""
        valid_types = ["bid_matched", "deadline", "bid_result", "proposal_ready"]
        if v not in valid_types:
            raise ValueError(f"유효하지 않은 알림 유형입니다: {v}")
        return v


class NotificationSettingsUpdateRequest(BaseModel):
    """알림 설정 변경 요청"""
    settings: list[NotificationSettingUpdate] = Field(..., min_length=1)


class NotificationSettingsUpdateResponse(CamelCaseResponse):
    """알림 설정 변경 응답"""
    updated_count: int
