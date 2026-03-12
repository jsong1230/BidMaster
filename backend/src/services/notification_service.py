"""알림 통합 서비스 (F-10)"""
import asyncio
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.core.exceptions import NotFoundError, PermissionError
from src.models.bid import Bid
from src.models.notification import Notification
from src.models.notification_setting import NotificationSetting
from src.models.user import User
from src.models.user_bid_match import UserBidMatch
from src.services.email_sender import EmailSender
from src.services.kakao_sender import KakaoAlimtalkSender

logger = logging.getLogger(__name__)

# 알림 유형 상수
NOTIFICATION_TYPES = ["bid_matched", "deadline", "bid_result", "proposal_ready"]


class NotificationService:
    """알림 통합 서비스"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.settings = get_settings()
        self.email_sender = EmailSender()
        self.kakao_sender = KakaoAlimtalkSender()

    # ============================================================
    # 알림 발송 메서드
    # ============================================================

    async def send_notification(
        self,
        user_id: UUID,
        notification_type: str,
        title: str,
        content: str,
        data: dict[str, Any] | None = None,
    ) -> Notification:
        """
        알림 발송 메인 플로우

        1. notification_settings 조회 (사용자 설정 확인)
        2. in_app 알림 레코드 생성 (notifications 테이블)
        3. email_enabled이면 이메일 발송 (백그라운드)
        4. kakao_enabled이면 카카오 알림톡 발송 (백그라운드)

        Returns: 생성된 Notification 레코드
        """
        # 사용자 설정 조회
        setting = await self._get_or_create_setting(user_id, notification_type)

        # 인앱 알림 생성
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            title=title,
            content=content,
            data=data or {},
            is_read=False,
            channel="in_app",
        )
        self.db.add(notification)
        await self.db.flush()

        # 백그라운드로 이메일/카카오 발송
        user = await self._get_user(user_id)

        if setting.email_enabled and user.email:
            asyncio.create_task(
                self._send_email_notification(
                    str(user.email),
                    notification_type,
                    title,
                    data or {},
                )
            )

        if setting.kakao_enabled and user.phone:
            asyncio.create_task(
                self._send_kakao_notification(
                    str(user.phone),
                    notification_type,
                    data or {},
                )
            )

        logger.info(f"[알림] 생성 완료: user={user_id}, type={notification_type}")
        return notification

    async def send_bid_match_notification(
        self,
        user_id: UUID | str,
        bid_id: UUID | str,
        score: float,
    ) -> None:
        """
        매칭 알림 발송 (기존 스텁 인터페이스 유지)

        - BidMatchService에서 호출하는 기존 인터페이스와 동일
        - 내부적으로 send_notification() 호출
        - bid 정보 조회하여 title/content 생성
        """
        user_uuid = UUID(str(user_id)) if isinstance(user_id, str) else user_id
        bid_uuid = UUID(str(bid_id)) if isinstance(bid_id, str) else bid_id

        # 공고 정보 조회
        bid = await self._get_bid(bid_uuid)
        if not bid:
            logger.warning(f"[알림] 공고 없음: bid={bid_id}")
            return

        # 추천 등급 판단
        recommendation = "recommended" if score >= 80 else "consider"

        title = f"새로운 매칭 공고: {bid.title}"
        content = f"{bid.title} 공고가 매칭되었습니다. (적합도: {score:.0f}점)"

        await self.send_notification(
            user_id=user_uuid,
            notification_type="bid_matched",
            title=title,
            content=content,
            data={
                "bidId": str(bid_uuid),
                "bidTitle": bid.title,
                "score": score,
                "recommendation": recommendation,
            },
        )

    async def send_deadline_notifications(self) -> int:
        """
        마감 임박 알림 일괄 발송 (스케줄러에서 호출)

        1. user_bid_matches에서 참여 중 상태 조회
        2. 마감일이 D-3 또는 D-1인 공고 필터링
        3. 해당 사용자들에게 알림 발송

        Returns: 발송된 알림 수
        """
        # D-N 계산
        days_list = [
            int(d.strip()) for d in self.settings.deadline_notification_days.split(",")
        ]
        today = date.today()
        target_dates = [today + timedelta(days=d) for d in days_list]

        # 마감 임박 공고 + 참여 중인 사용자 조회
        stmt = (
            select(UserBidMatch, Bid)
            .join(Bid, UserBidMatch.bid_id == Bid.id)
            .where(
                UserBidMatch.status.in_(["interested", "participating"]),
                func.date(Bid.deadline).in_(target_dates),
                Bid.status == "open",
            )
        )
        result = await self.db.execute(stmt)
        matches = result.all()

        sent_count = 0
        for match, bid in matches:
            # 중복 알림 체크 (당일 동일 알림 이미 발송?)
            if await self._check_duplicate_deadline_notification(
                match.user_id, bid.id, today
            ):
                continue

            days_left = (bid.deadline.date() - today).days
            title = f"마감 임박: {bid.title} (D-{days_left})"
            content = f"{bid.title} 공고가 {days_left}일 후 마감됩니다."

            await self.send_notification(
                user_id=match.user_id,
                notification_type="deadline",
                title=title,
                content=content,
                data={
                    "bidId": str(bid.id),
                    "bidTitle": bid.title,
                    "deadline": bid.deadline.isoformat(),
                    "daysLeft": days_left,
                },
            )
            sent_count += 1

        logger.info(f"[알림] 마감 임박 알림 발송 완료: {sent_count}건")
        return sent_count

    async def send_bid_result_notification(
        self,
        user_id: UUID,
        bid_id: UUID,
        is_winner: bool,
        winning_price: int | None = None,
    ) -> None:
        """
        낙찰/실패 결과 알림 발송

        - user_bid_tracking에서 결과 등록 시 호출
        - is_winner에 따라 제목/내용 분기
        """
        bid = await self._get_bid(bid_id)
        if not bid:
            logger.warning(f"[알림] 공고 없음: bid={bid_id}")
            return

        if is_winner:
            title = f"낙찰 결과: {bid.title}"
            content = f"축하합니다! {bid.title} 공고에 낙찰되었습니다."
        else:
            title = f"낙찰 결과: {bid.title}"
            content = f"아쉽게도 {bid.title} 공고에 낙찰되지 않았습니다."

        await self.send_notification(
            user_id=user_id,
            notification_type="bid_result",
            title=title,
            content=content,
            data={
                "bidId": str(bid_id),
                "bidTitle": bid.title,
                "isWinner": is_winner,
                "winningPrice": winning_price,
            },
        )

    async def send_proposal_ready_notification(
        self,
        user_id: UUID,
        proposal_id: UUID,
        proposal_title: str,
        bid_id: UUID,
    ) -> None:
        """
        제안서 생성 완료 알림 발송

        - ProposalService에서 AI 제안서 생성 완료 시 호출
        """
        bid = await self._get_bid(bid_id)
        bid_title = bid.title if bid else "알 수 없는 공고"

        title = f"제안서 생성 완료: {proposal_title}"
        content = f"'{proposal_title}' 제안서 생성이 완료되었습니다."

        await self.send_notification(
            user_id=user_id,
            notification_type="proposal_ready",
            title=title,
            content=content,
            data={
                "proposalId": str(proposal_id),
                "proposalTitle": proposal_title,
                "bidId": str(bid_id),
                "bidTitle": bid_title,
            },
        )

    async def send_admin_alert(self, message: str) -> None:
        """
        관리자 알림 발송 (기존 스텁 인터페이스 유지)

        - 시스템 오류, 수집 실패 등 관리자 대상 알림
        - 이메일로 발송
        """
        logger.warning(f"[관리자 알림] {message}")
        # TODO: 관리자 이메일 목록 설정 후 발송

    # ============================================================
    # 알림 조회 메서드
    # ============================================================

    async def get_notifications(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        is_read: bool | None = None,
        notification_type: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Notification], int]:
        """
        알림 목록 조회

        Returns: (알림 목록, 전체 건수)
        """
        # 기본 쿼리
        stmt = select(Notification).where(Notification.user_id == user_id)

        # 필터링
        if is_read is not None:
            stmt = stmt.where(Notification.is_read == is_read)
        if notification_type:
            stmt = stmt.where(Notification.type == notification_type)

        # 정렬
        order_col = getattr(Notification, sort_by, Notification.created_at)
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
        notifications = list(result.scalars().all())

        return notifications, total

    async def get_unread_count(self, user_id: UUID) -> int:
        """안읽은 알림 수 조회"""
        stmt = select(func.count()).where(
            Notification.user_id == user_id,
            Notification.is_read == False,
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    # ============================================================
    # 알림 읽음 처리 메서드
    # ============================================================

    async def mark_as_read(
        self, notification_id: UUID, user_id: UUID
    ) -> Notification:
        """
        단일 알림 읽음 처리

        - 본인의 알림이 아니면 PERMISSION_002 에러
        """
        notification = await self._get_notification(notification_id)

        if not notification:
            raise NotFoundError(
                code="NOTIFICATION_001",
                message="알림을 찾을 수 없습니다.",
            )

        if notification.user_id != user_id:
            raise PermissionError(
                code="PERMISSION_002",
                message="리소스 소유자가 아닙니다.",
            )

        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.now(timezone.utc)
            await self.db.flush()

        return notification

    async def mark_all_as_read(self, user_id: UUID) -> int:
        """전체 읽음 처리, Returns: 업데이트된 건수"""
        stmt = (
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read == False,
            )
            .values(is_read=True, read_at=datetime.now(timezone.utc))
            .returning(Notification.id)
        )
        result = await self.db.execute(stmt)
        updated_ids = list(result.scalars().all())
        return len(updated_ids)

    # ============================================================
    # 알림 설정 메서드
    # ============================================================

    async def get_settings(self, user_id: UUID) -> list[NotificationSetting]:
        """알림 설정 조회 (없으면 기본값 생성)"""
        settings = []

        for notification_type in NOTIFICATION_TYPES:
            setting = await self._get_or_create_setting(user_id, notification_type)
            settings.append(setting)

        return settings

    async def update_settings(
        self,
        user_id: UUID,
        settings_data: list[dict],
    ) -> int:
        """알림 설정 변경, Returns: 업데이트된 건수"""
        updated_count = 0

        for data in settings_data:
            notification_type = data.get("notification_type")
            if notification_type not in NOTIFICATION_TYPES:
                continue

            setting = await self._get_or_create_setting(user_id, notification_type)
            setting.email_enabled = data.get("email_enabled", setting.email_enabled)
            setting.kakao_enabled = data.get("kakao_enabled", setting.kakao_enabled)
            setting.push_enabled = data.get("push_enabled", setting.push_enabled)
            updated_count += 1

        await self.db.flush()
        return updated_count

    # ============================================================
    # 내부 메서드
    # ============================================================

    async def _get_user(self, user_id: UUID) -> User:
        """사용자 조회"""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError(code="USER_001", message="사용자를 찾을 수 없습니다.")
        return user

    async def _get_bid(self, bid_id: UUID) -> Bid | None:
        """공고 조회"""
        stmt = select(Bid).where(Bid.id == bid_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_notification(
        self, notification_id: UUID
    ) -> Notification | None:
        """알림 조회"""
        stmt = select(Notification).where(Notification.id == notification_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_or_create_setting(
        self, user_id: UUID, notification_type: str
    ) -> NotificationSetting:
        """알림 설정 조회 또는 생성"""
        stmt = select(NotificationSetting).where(
            NotificationSetting.user_id == user_id,
            NotificationSetting.notification_type == notification_type,
        )
        result = await self.db.execute(stmt)
        setting = result.scalar_one_or_none()

        if not setting:
            setting = NotificationSetting(
                user_id=user_id,
                notification_type=notification_type,
                email_enabled=True,
                kakao_enabled=False,
                push_enabled=True,
            )
            self.db.add(setting)
            await self.db.flush()

        return setting

    async def _check_duplicate_deadline_notification(
        self, user_id: UUID, bid_id: UUID, check_date: date
    ) -> bool:
        """마감 임박 중복 알림 체크"""
        stmt = select(func.count()).where(
            Notification.user_id == user_id,
            Notification.type == "deadline",
            func.date(Notification.created_at) == check_date,
            Notification.data["bidId"].astext == str(bid_id),
        )
        result = await self.db.execute(stmt)
        count = result.scalar() or 0
        return count > 0

    async def _send_email_notification(
        self,
        to_email: str,
        notification_type: str,
        title: str,
        data: dict[str, Any],
    ) -> None:
        """이메일 알림 발송 (백그라운드)"""
        try:
            template_map = {
                "bid_matched": "bid_matched.html",
                "deadline": "deadline.html",
                "bid_result": "bid_result.html",
                "proposal_ready": "proposal_ready.html",
            }
            template_name = template_map.get(notification_type, "base.html")

            context = {
                "app_url": self.settings.frontend_url,
                **data,
            }

            await self.email_sender.send_with_template(
                to_email=to_email,
                subject=title,
                template_name=template_name,
                context=context,
            )
        except Exception as e:
            logger.error(f"[이메일] 발송 실패: {to_email} - {e}")

    async def _send_kakao_notification(
        self,
        phone: str,
        notification_type: str,
        data: dict[str, Any],
    ) -> None:
        """카카오 알림톡 발송 (백그라운드)"""
        try:
            # TODO: 템플릿 코드 매핑
            template_code = f"BID_{notification_type.upper()}"
            await self.kakao_sender.send(phone, template_code, data)
        except Exception as e:
            logger.error(f"[카카오] 발송 실패: {phone} - {e}")
