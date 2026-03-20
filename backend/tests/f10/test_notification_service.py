"""F-10 알림 시스템 테스트"""
import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4, UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.services.notification_service import NotificationService
from src.core.exceptions import NotFoundError, PermissionError


@pytest.fixture
async def notification_service(db_session: AsyncSession) -> NotificationService:
    """알림 서비스 fixture"""
    return NotificationService(db_session)


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


class TestNotificationService:
    """알림 서비스 테스트"""

    @pytest.mark.asyncio
    async def test_send_notification_creates_in_app_notification(
        self,
        notification_service: NotificationService,
        test_user: User,
    ):
        """인앱 알림 생성 테스트"""
        # Given
        user_id = UUID(str(test_user.id))
        notification = await notification_service.send_notification(
            user_id=user_id,
            notification_type="bid_matched",
            title="새로운 매칭 공고",
            content="테스트 공고가 매칭되었습니다.",
            data={"bidId": str(uuid4()), "score": 85.0},
        )

        # Then
        assert notification.id is not None
        assert notification.user_id == user_id
        assert notification.type == "bid_matched"
        assert notification.title == "새로운 매칭 공고"
        assert notification.is_read is False
        assert notification.channel == "in_app"

    @pytest.mark.asyncio
    async def test_send_bid_match_notification(
        self,
        notification_service: NotificationService,
        test_user: User,
        db_session: AsyncSession,
    ):
        """매칭 알림 발송 테스트"""
        from src.models.bid import Bid

        # Given
        user_id = UUID(str(test_user.id))
        bid = Bid(
            id=uuid4(),
            bid_number="TEST-2026-001",
            title="테스트 공고",
            organization="테스트 기관",
            deadline=datetime.now(timezone.utc) + timedelta(days=7),
            status="open",
        )
        db_session.add(bid)
        await db_session.flush()
        bid_id = UUID(str(bid.id))

        # When
        await notification_service.send_bid_match_notification(
            user_id=user_id,
            bid_id=bid_id,
            score=85.0,
        )

        # Then
        notifications, total = await notification_service.get_notifications(
            user_id=user_id
        )
        assert total == 1
        assert notifications[0].type == "bid_matched"
        assert "85" in notifications[0].content

    @pytest.mark.asyncio
    async def test_get_unread_count(
        self,
        notification_service: NotificationService,
        test_user: User,
    ):
        """안읽은 알림 수 조회 테스트"""
        # Given
        user_id = UUID(str(test_user.id))
        # 알림 3개 생성
        for i in range(3):
            await notification_service.send_notification(
                user_id=user_id,
                notification_type="bid_matched",
                title=f"알림 {i+1}",
                content="테스트",
            )

        # When
        count = await notification_service.get_unread_count(user_id)

        # Then
        assert count == 3

    @pytest.mark.asyncio
    async def test_mark_as_read(
        self,
        notification_service: NotificationService,
        test_user: User,
    ):
        """알림 읽음 처리 테스트"""
        # Given
        user_id = UUID(str(test_user.id))
        notification = await notification_service.send_notification(
            user_id=user_id,
            notification_type="bid_matched",
            title="테스트 알림",
            content="내용",
        )

        # When
        updated = await notification_service.mark_as_read(
            notification_id=notification.id,
            user_id=user_id,
        )

        # Then
        assert updated.is_read is True
        assert updated.read_at is not None

    @pytest.mark.asyncio
    async def test_mark_as_read_other_user_notification_fails(
        self,
        notification_service: NotificationService,
        test_user: User,
    ):
        """다른 사용자의 알림 읽음 처리 시 권한 에러"""
        # Given
        user_id = UUID(str(test_user.id))
        notification = await notification_service.send_notification(
            user_id=user_id,
            notification_type="bid_matched",
            title="테스트 알림",
            content="내용",
        )
        other_user_id = uuid4()

        # When/Then
        with pytest.raises(PermissionError):
            await notification_service.mark_as_read(
                notification_id=notification.id,
                user_id=other_user_id,
            )

    @pytest.mark.asyncio
    async def test_mark_all_as_read(
        self,
        notification_service: NotificationService,
        test_user: User,
    ):
        """전체 읽음 처리 테스트"""
        # Given
        user_id = UUID(str(test_user.id))
        # 5개 알림 생성
        for i in range(5):
            await notification_service.send_notification(
                user_id=user_id,
                notification_type="bid_matched",
                title=f"알림 {i+1}",
                content="테스트",
            )

        # When
        count = await notification_service.mark_all_as_read(user_id)

        # Then
        assert count == 5

        # 안읽은 알림 수 확인
        unread = await notification_service.get_unread_count(user_id)
        assert unread == 0

    @pytest.mark.asyncio
    async def test_get_settings(
        self,
        notification_service: NotificationService,
        test_user: User,
    ):
        """알림 설정 조회 테스트"""
        # Given
        user_id = UUID(str(test_user.id))

        # When
        settings = await notification_service.get_settings(user_id)

        # Then
        assert len(settings) == 4
        notification_types = [s.notification_type for s in settings]
        assert "bid_matched" in notification_types
        assert "deadline" in notification_types
        assert "bid_result" in notification_types
        assert "proposal_ready" in notification_types

    @pytest.mark.asyncio
    async def test_update_settings(
        self,
        notification_service: NotificationService,
        test_user: User,
    ):
        """알림 설정 변경 테스트"""
        # Given
        user_id = UUID(str(test_user.id))
        settings_data = [
            {
                "notification_type": "bid_matched",
                "email_enabled": False,
                "kakao_enabled": True,
                "push_enabled": True,
            },
            {
                "notification_type": "deadline",
                "email_enabled": True,
                "kakao_enabled": False,
                "push_enabled": False,
            },
        ]

        # When
        count = await notification_service.update_settings(
            user_id=user_id,
            settings_data=settings_data,
        )

        # Then
        assert count == 2

        # 변경된 설정 확인
        settings = await notification_service.get_settings(user_id)
        bid_matched_setting = next(
            s for s in settings if s.notification_type == "bid_matched"
        )
        assert bid_matched_setting.email_enabled is False
        assert bid_matched_setting.kakao_enabled is True

        deadline_setting = next(
            s for s in settings if s.notification_type == "deadline"
        )
        assert deadline_setting.push_enabled is False

    @pytest.mark.asyncio
    async def test_notification_not_found_error(
        self,
        notification_service: NotificationService,
        test_user: User,
    ):
        """존재하지 않는 알림 읽음 처리 시 에러"""
        # Given
        user_id = UUID(str(test_user.id))

        # When/Then
        with pytest.raises(NotFoundError):
            await notification_service.mark_as_read(
                notification_id=uuid4(),
                user_id=user_id,
            )


class TestNotificationAPI:
    """알림 API 테스트"""

    @pytest.mark.asyncio
    async def test_list_notifications_api(
        self,
        client,
        auth_headers,
        notification_service: NotificationService,
        test_user: User,
    ):
        """알림 목록 API 테스트"""
        # Given
        user_id = UUID(str(test_user.id))
        for i in range(3):
            await notification_service.send_notification(
                user_id=user_id,
                notification_type="bid_matched",
                title=f"알림 {i+1}",
                content="테스트",
            )

        # When
        response = await client.get(
            "/api/v1/notifications",
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["items"]) == 3
        assert data["meta"]["total"] == 3

    @pytest.mark.asyncio
    async def test_unread_count_api(
        self,
        client,
        auth_headers,
        notification_service: NotificationService,
        test_user: User,
    ):
        """안읽은 알림 수 API 테스트"""
        # Given
        user_id = UUID(str(test_user.id))
        await notification_service.send_notification(
            user_id=user_id,
            notification_type="bid_matched",
            title="테스트",
            content="내용",
        )

        # When
        response = await client.get(
            "/api/v1/notifications/unread-count",
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["unreadCount"] >= 1

    @pytest.mark.asyncio
    async def test_mark_as_read_api(
        self,
        client,
        auth_headers,
        notification_service: NotificationService,
        test_user: User,
    ):
        """알림 읽음 처리 API 테스트"""
        # Given
        user_id = UUID(str(test_user.id))
        notification = await notification_service.send_notification(
            user_id=user_id,
            notification_type="bid_matched",
            title="테스트",
            content="내용",
        )

        # When
        response = await client.patch(
            f"/api/v1/notifications/{notification.id}/read",
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["isRead"] is True
        assert data["data"]["readAt"] is not None

    @pytest.mark.asyncio
    async def test_mark_all_as_read_api(
        self,
        client,
        auth_headers,
        notification_service: NotificationService,
        test_user: User,
    ):
        """전체 읽음 처리 API 테스트"""
        # Given
        user_id = UUID(str(test_user.id))
        for i in range(3):
            await notification_service.send_notification(
                user_id=user_id,
                notification_type="bid_matched",
                title=f"알림 {i+1}",
                content="테스트",
            )

        # When
        response = await client.post(
            "/api/v1/notifications/read-all",
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["updatedCount"] == 3

    @pytest.mark.asyncio
    async def test_get_settings_api(
        self,
        client,
        auth_headers,
    ):
        """알림 설정 조회 API 테스트"""
        # When
        response = await client.get(
            "/api/v1/notifications/settings",
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["settings"]) == 4

    @pytest.mark.asyncio
    async def test_update_settings_api(
        self,
        client,
        auth_headers,
    ):
        """알림 설정 변경 API 테스트"""
        # Given
        update_data = {
            "settings": [
                {
                    "notificationType": "bid_matched",
                    "emailEnabled": False,
                    "kakaoEnabled": True,
                    "pushEnabled": True,
                }
            ]
        }

        # When
        response = await client.put(
            "/api/v1/notifications/settings",
            headers=auth_headers,
            json=update_data,
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["updatedCount"] == 1
