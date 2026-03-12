"""알림 API 엔드포인트 (F-10)"""
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.dependencies import get_current_user
from src.core.responses import success_response
from src.models.user import User
from src.schemas.notification import (
    MarkAllReadResponse,
    MarkReadResponse,
    NotificationListMeta,
    NotificationListResponse,
    NotificationResponse,
    NotificationSettingsResponse,
    NotificationSettingsUpdateRequest,
    NotificationSettingsUpdateResponse,
    UnreadCountResponse,
)
from src.services.notification_service import NotificationService

router = APIRouter()


@router.get("", response_model=Any)
async def list_notifications(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    is_read: Annotated[bool | None, Query()] = None,
    type: Annotated[str | None, Query(alias="type")] = None,
    sort_by: Annotated[str, Query()] = "createdAt",
    sort_order: Annotated[str, Query(regex="^(asc|desc)$")] = "desc",
):
    """
    알림 목록 조회

    페이지네이션, 필터링, 정렬 지원
    """
    # snake_case 변환
    sort_by_map = {
        "createdAt": "created_at",
        "sentAt": "sent_at",
    }
    db_sort_by = sort_by_map.get(sort_by, "created_at")

    service = NotificationService(db)
    notifications, total = await service.get_notifications(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        is_read=is_read,
        notification_type=type,
        sort_by=db_sort_by,
        sort_order=sort_order,
    )

    items = [NotificationResponse.model_validate(n) for n in notifications]

    return success_response(
        data=NotificationListResponse(items=items).model_dump(by_alias=True),
        meta=NotificationListMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=(total + page_size - 1) // page_size,
        ).model_dump(by_alias=True),
    )


@router.get("/unread-count", response_model=Any)
async def get_unread_count(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    안읽은 알림 수 조회

    프론트엔드 헤더 뱃지용
    """
    service = NotificationService(db)
    count = await service.get_unread_count(current_user.id)

    return success_response(
        data=UnreadCountResponse(unread_count=count).model_dump(by_alias=True)
    )


@router.patch("/{notification_id}/read", response_model=Any)
async def mark_as_read(
    notification_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    알림 읽음 처리

    특정 알림을 읽음으로 표시
    """
    service = NotificationService(db)
    notification = await service.mark_as_read(notification_id, current_user.id)

    return success_response(
        data=MarkReadResponse(
            id=notification.id,
            is_read=notification.is_read,
            read_at=notification.read_at,
        ).model_dump(by_alias=True)
    )


@router.post("/read-all", response_model=Any)
async def mark_all_as_read(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    전체 읽음 처리

    현재 사용자의 모든 안읽은 알림을 읽음으로 표시
    """
    service = NotificationService(db)
    count = await service.mark_all_as_read(current_user.id)

    return success_response(
        data=MarkAllReadResponse(updated_count=count).model_dump(by_alias=True)
    )


@router.get("/settings", response_model=Any)
async def get_settings(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    알림 설정 조회

    사용자별 알림 유형 설정
    """
    from src.schemas.notification import (
        NOTIFICATION_TYPE_LABELS,
        NotificationSettingResponse,
    )

    service = NotificationService(db)
    settings = await service.get_settings(current_user.id)

    settings_response = []
    for setting in settings:
        settings_response.append(
            NotificationSettingResponse(
                notification_type=setting.notification_type,
                label=NOTIFICATION_TYPE_LABELS.get(
                    setting.notification_type, setting.notification_type
                ),
                email_enabled=setting.email_enabled,
                kakao_enabled=setting.kakao_enabled,
                push_enabled=setting.push_enabled,
            )
        )

    return success_response(
        data=NotificationSettingsResponse(
            settings=settings_response
        ).model_dump(by_alias=True)
    )


@router.put("/settings", response_model=Any)
async def update_settings(
    request: NotificationSettingsUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    알림 설정 변경

    알림 유형별 채널 on/off 설정
    """
    service = NotificationService(db)
    settings_data = [s.model_dump() for s in request.settings]
    count = await service.update_settings(current_user.id, settings_data)

    return success_response(
        data=NotificationSettingsUpdateResponse(
            updated_count=count
        ).model_dump(by_alias=True)
    )
