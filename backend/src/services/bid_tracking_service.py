"""입찰 추적 서비스 (F-06)"""
import logging
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.core.exceptions import NotFoundError
from src.models.bid import Bid
from src.models.user_bid_tracking import UserBidTracking

logger = logging.getLogger(__name__)


class BidTrackingService:
    """입찰 추적 CRUD 서비스"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def upsert_tracking(
        self,
        user_id: UUID,
        bid_id: UUID,
        status: str,
        my_bid_price: int | None,
        notes: str | None,
    ) -> tuple[UserBidTracking, bool]:
        """
        추적 생성 또는 업데이트 (Upsert)

        Returns:
            (UserBidTracking, is_created): 레코드와 신규 생성 여부
        """
        now = datetime.now(timezone.utc)

        # 기존 레코드 조회
        stmt = select(UserBidTracking).where(
            UserBidTracking.user_id == user_id,
            UserBidTracking.bid_id == bid_id,
        )
        result = await self.db.execute(stmt)
        tracking = result.scalar_one_or_none()

        is_created = tracking is None

        if is_created:
            tracking = UserBidTracking(
                user_id=user_id,
                bid_id=bid_id,
            )
            self.db.add(tracking)

        # 공통 필드 업데이트
        tracking.status = status
        if my_bid_price is not None:
            tracking.my_bid_price = Decimal(my_bid_price)
        if notes is not None:
            tracking.notes = notes
        tracking.updated_at = now

        # 상태에 따른 자동 필드 설정
        if status == "submitted":
            if tracking.submitted_at is None or not is_created:
                tracking.submitted_at = now

        elif status == "won":
            tracking.is_winner = True
            tracking.result_at = now

        elif status == "lost":
            tracking.is_winner = False
            tracking.result_at = now

        await self.db.flush()

        logger.info(
            "[추적] %s: user=%s, bid=%s, status=%s",
            "생성" if is_created else "업데이트",
            user_id,
            bid_id,
            status,
        )

        return tracking, is_created

    async def get_tracking(
        self, user_id: UUID, bid_id: UUID
    ) -> UserBidTracking | None:
        """추적 레코드 조회"""
        stmt = select(UserBidTracking).where(
            UserBidTracking.user_id == user_id,
            UserBidTracking.bid_id == bid_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_trackings(
        self,
        user_id: UUID,
        status: str | None = None,
    ) -> list[UserBidTracking]:
        """사용자의 전체 추적 목록 조회 (상태 필터 선택)"""
        stmt = select(UserBidTracking).where(UserBidTracking.user_id == user_id)

        if status is not None:
            stmt = stmt.where(UserBidTracking.status == status)

        stmt = stmt.order_by(UserBidTracking.updated_at.desc())

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_win_history(
        self,
        user_id: UUID,
        page: int,
        page_size: int,
        filters: dict,
    ) -> tuple[list[dict], int]:
        """
        낙찰 이력 조회 (is_winner=True)

        Returns:
            (items, total): 이력 목록과 전체 건수
        """
        from src.models.bid import Bid

        # 기본 쿼리 (is_winner=True인 추적 레코드)
        stmt = (
            select(UserBidTracking, Bid)
            .join(Bid, UserBidTracking.bid_id == Bid.id)
            .where(
                UserBidTracking.user_id == user_id,
                UserBidTracking.is_winner == True,
            )
        )

        # 날짜 범위 필터
        start_date = filters.get("start_date")
        end_date = filters.get("end_date")
        if start_date:
            stmt = stmt.where(UserBidTracking.result_at >= start_date)
        if end_date:
            stmt = stmt.where(UserBidTracking.result_at <= end_date)

        # 정렬
        sort_by = filters.get("sort_by", "result_at")
        sort_order = filters.get("sort_order", "desc")

        if sort_by == "my_bid_price":
            order_col = UserBidTracking.my_bid_price
        else:
            order_col = UserBidTracking.result_at

        if sort_order == "desc":
            stmt = stmt.order_by(order_col.desc().nulls_last())
        else:
            stmt = stmt.order_by(order_col.asc().nulls_last())

        # 전체 건수
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar() or 0

        # 페이지네이션
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        result = await self.db.execute(stmt)
        rows = result.all()

        items = []
        for tracking, bid in rows:
            # bid_rate 계산 (budget이 0이면 None)
            bid_rate: float | None = None
            if bid.budget and int(bid.budget) > 0 and tracking.my_bid_price is not None:
                bid_rate = float(tracking.my_bid_price) / float(bid.budget)

            items.append({
                "tracking_id": tracking.id,
                "bid_id": bid.id,
                "title": bid.title,
                "organization": bid.organization,
                "budget": int(bid.budget) if bid.budget is not None else None,
                "my_bid_price": int(tracking.my_bid_price) if tracking.my_bid_price is not None else None,
                "bid_rate": round(bid_rate, 4) if bid_rate is not None else None,
                "is_winner": tracking.is_winner,
                "result_at": tracking.result_at,
                "submitted_at": tracking.submitted_at,
            })

        return items, total
