"""알림 서비스 (F-10에서 실제 구현, 현재 스텁)"""
import logging
from uuid import UUID

logger = logging.getLogger(__name__)


class NotificationService:
    """알림 서비스 스텁 - F-10에서 실제 구현 예정"""

    async def send_bid_match_notification(
        self,
        user_id: UUID | str,
        bid_id: UUID | str,
        score: float,
    ) -> None:
        """
        매칭 알림 발송 (스텁: 로그만 기록)

        F-10에서 이메일/슬랙 알림으로 고도화 예정
        """
        logger.info(f"[알림 스텁] user={user_id}, bid={bid_id}, score={score}")

    async def send_admin_alert(self, message: str) -> None:
        """
        관리자 알림 발송 (스텁: 로그만 기록)

        F-10에서 슬랙/이메일 알림으로 고도화 예정
        """
        logger.warning(f"[관리자 알림 스텁] {message}")
