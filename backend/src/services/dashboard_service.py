"""대시보드 서비스 (F-06)"""
import json
import logging
from calendar import monthrange
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Callable
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.bid import Bid
from src.models.user_bid_match import UserBidMatch
from src.models.user_bid_tracking import UserBidTracking

logger = logging.getLogger(__name__)

# 파이프라인 단계 레이블
PIPELINE_STAGE_LABELS: dict[str, str] = {
    "interested": "관심",
    "participating": "참여",
    "submitted": "제출",
    "won": "낙찰",
    "lost": "실패",
}

PIPELINE_STAGE_ORDER = ["interested", "participating", "submitted", "won", "lost"]

# 유효한 기간 값
VALID_PERIODS = frozenset(["current_month", "last_month", "last_3_months", "last_6_months", "last_year"])


class DashboardService:
    """대시보드 집계 서비스"""

    def __init__(self, db: AsyncSession | None, redis: Any | None = None) -> None:
        self.db = db
        self.redis = redis

    # ============================================================
    # 퍼블릭 메서드
    # ============================================================

    async def get_summary(self, user_id: UUID, period: str) -> dict[str, Any]:
        """
        KPI 요약 데이터 조회

        1. 기간 내 user_bid_tracking 집계
        2. ROI 계산
        3. 마감 임박 공고 (D-7 이내)
        4. Redis 캐싱 (30초 TTL)
        """
        cache_key = f"dashboard:summary:{user_id}:{period}"

        # Redis 캐시 조회
        cached = await self._get_cache(cache_key)
        if cached is not None:
            return cached

        # 기간 계산
        start_date, end_date = self._calculate_period_range(period)

        # 기간 내 추적 레코드 조회
        stmt = select(UserBidTracking).where(
            UserBidTracking.user_id == user_id,
            UserBidTracking.created_at >= start_date,
            UserBidTracking.created_at <= end_date,
        )
        result = await self.db.execute(stmt)
        trackings = list(result.scalars().all())

        # 상태별 집계
        participation_count = len([
            t for t in trackings
            if t.status in ("participating", "submitted", "won", "lost")
        ])
        submission_count = len([
            t for t in trackings
            if t.status in ("submitted", "won", "lost")
        ])
        won_count = len([t for t in trackings if t.is_winner is True])
        lost_count = len([t for t in trackings if t.is_winner is False and t.status == "lost"])
        pending_count = len([
            t for t in trackings
            if t.status in ("interested", "participating", "submitted")
        ])

        # 낙찰 금액 집계
        won_trackings = [t for t in trackings if t.is_winner is True and t.my_bid_price is not None]
        total_won_amount = sum(int(t.my_bid_price) for t in won_trackings)
        average_won_amount = total_won_amount / len(won_trackings) if won_trackings else 0.0

        # 낙찰률 (0으로 나누기 방지)
        win_rate = 0.0
        decided = won_count + lost_count
        if decided > 0:
            win_rate = round(won_count / decided * 100, 2)

        # ROI 계산 (my_bid_price가 있는 낙찰 건만 포함)
        roi = self._calculate_roi(won_trackings)

        # 마감 임박 공고 (D-7 이내, status in interested/participating)
        upcoming_deadlines = await self._get_upcoming_deadlines(user_id)

        # 기간 레이블 (YYYY-MM 형식)
        period_label = start_date.strftime("%Y-%m")

        data: dict[str, Any] = {
            "period": period_label,
            "participationCount": participation_count,
            "submissionCount": submission_count,
            "wonCount": won_count,
            "lostCount": lost_count,
            "pendingCount": pending_count,
            "totalWonAmount": total_won_amount,
            "winRate": win_rate,
            "averageWonAmount": average_won_amount,
            "roi": roi,
            "upcomingDeadlines": upcoming_deadlines,
        }

        # 응답 스키마 호환용 snake_case 키도 포함
        result_data: dict[str, Any] = {
            **data,
            "participation_count": participation_count,
            "submission_count": submission_count,
            "won_count": won_count,
            "lost_count": lost_count,
            "pending_count": pending_count,
            "total_won_amount": total_won_amount,
            "win_rate": win_rate,
            "average_won_amount": average_won_amount,
            "upcoming_deadlines": upcoming_deadlines,
        }

        # Redis 캐시 저장 (30초 TTL)
        await self._set_cache(cache_key, result_data, ttl=30)

        return result_data

    async def get_pipeline(self, user_id: UUID) -> dict[str, Any]:
        """
        파이프라인 단계별 데이터 조회

        1. user_bid_tracking + bids JOIN
        2. status별 그룹화
        3. 각 단계 내 deadline ASC 정렬
        """
        cache_key = f"dashboard:pipeline:{user_id}"

        cached = await self._get_cache(cache_key)
        if cached is not None:
            return cached

        # 모든 추적 레코드 + 공고 정보 JOIN
        stmt = (
            select(UserBidTracking, Bid)
            .join(Bid, UserBidTracking.bid_id == Bid.id)
            .where(UserBidTracking.user_id == user_id)
            .order_by(Bid.deadline.asc().nulls_last())
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        # 매칭 점수 조회 (있는 경우)
        bid_ids = [bid.id for _, bid in rows]
        score_map: dict[UUID, float] = {}

        if bid_ids:
            score_stmt = select(UserBidMatch).where(
                UserBidMatch.user_id == user_id,
                UserBidMatch.bid_id.in_(bid_ids),
            )
            score_result = await self.db.execute(score_stmt)
            for match in score_result.scalars().all():
                score_map[match.bid_id] = match.total_score

        # status별 그룹화
        stages_map: dict[str, list[dict]] = {s: [] for s in PIPELINE_STAGE_ORDER}
        now = datetime.now(timezone.utc)

        for tracking, bid in rows:
            if tracking.status not in stages_map:
                continue

            days_left: int | None = None
            if bid.deadline:
                delta = bid.deadline.replace(tzinfo=timezone.utc) - now if bid.deadline.tzinfo is None else bid.deadline - now
                days_left = max(0, delta.days)

            item = {
                "trackingId": str(tracking.id),
                "tracking_id": tracking.id,
                "bidId": str(bid.id),
                "bid_id": bid.id,
                "title": bid.title,
                "organization": bid.organization,
                "budget": int(bid.budget) if bid.budget is not None else None,
                "deadline": bid.deadline,
                "daysLeft": days_left,
                "days_left": days_left,
                "totalScore": score_map.get(bid.id),
                "total_score": score_map.get(bid.id),
                "updatedAt": tracking.updated_at,
                "updated_at": tracking.updated_at,
            }
            stages_map[tracking.status].append(item)

        stages = [
            {
                "status": status,
                "label": PIPELINE_STAGE_LABELS[status],
                "count": len(items),
                "items": items,
            }
            for status in PIPELINE_STAGE_ORDER
            for items in [stages_map[status]]
        ]

        result_data: dict[str, Any] = {"stages": stages}

        await self._set_cache(cache_key, result_data, ttl=30)
        return result_data

    async def get_statistics(self, user_id: UUID, months: int) -> dict[str, Any]:
        """
        월별 성과 통계 조회

        1. 최근 N개월간 user_bid_tracking 데이터 집계
        2. 월별: 참여수, 제출수, 낙찰수, 탈락수, 낙찰률, 총 낙찰금액
        3. 누적 통계
        """
        cache_key = f"dashboard:statistics:{user_id}:{months}"

        cached = await self._get_cache(cache_key)
        if cached is not None:
            return cached

        now = datetime.now(timezone.utc)
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(
            days=30 * (months - 1)
        )
        # 정확한 N개월 전 1일로 조정
        start_year = now.year
        start_month = now.month - months + 1
        while start_month <= 0:
            start_month += 12
            start_year -= 1
        start_date = datetime(start_year, start_month, 1, tzinfo=timezone.utc)

        # 추적 레코드 조회 (기간 내)
        stmt = (
            select(UserBidTracking, Bid)
            .join(Bid, UserBidTracking.bid_id == Bid.id)
            .where(
                UserBidTracking.user_id == user_id,
                UserBidTracking.created_at >= start_date,
            )
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        # 월별 집계를 위한 딕셔너리 초기화
        monthly_data: dict[str, dict] = {}

        # 조회 기간의 각 월 초기화
        for i in range(months):
            year = now.year
            month = now.month - i
            while month <= 0:
                month += 12
                year -= 1
            month_key = f"{year:04d}-{month:02d}"
            monthly_data[month_key] = {
                "month": month_key,
                "participation_count": 0,
                "submission_count": 0,
                "won_count": 0,
                "lost_count": 0,
                "total_won_amount": 0,
                "bid_price_sum": 0,
                "bid_price_count": 0,
            }

        # 데이터 집계
        for tracking, bid in rows:
            # 기준 날짜: created_at 기준 월
            ref_dt = tracking.created_at
            if ref_dt.tzinfo is None:
                ref_dt = ref_dt.replace(tzinfo=timezone.utc)
            month_key = ref_dt.strftime("%Y-%m")

            if month_key not in monthly_data:
                continue

            md = monthly_data[month_key]

            if tracking.status in ("participating", "submitted", "won", "lost"):
                md["participation_count"] += 1
            if tracking.status in ("submitted", "won", "lost"):
                md["submission_count"] += 1
            if tracking.is_winner is True:
                md["won_count"] += 1
                if tracking.my_bid_price is not None:
                    md["total_won_amount"] += int(tracking.my_bid_price)
            if tracking.is_winner is False and tracking.status == "lost":
                md["lost_count"] += 1

            # bid_rate 계산용
            if tracking.my_bid_price is not None and bid.budget and int(bid.budget) > 0:
                md["bid_price_sum"] += float(tracking.my_bid_price) / float(bid.budget)
                md["bid_price_count"] += 1

        # 월별 통계 목록 (최신 월부터)
        monthly_list = []
        for i in range(months):
            year = now.year
            month = now.month - i
            while month <= 0:
                month += 12
                year -= 1
            month_key = f"{year:04d}-{month:02d}"
            md = monthly_data.get(month_key, {})

            won_c = md.get("won_count", 0)
            lost_c = md.get("lost_count", 0)
            decided = won_c + lost_c
            win_rate = round(won_c / decided * 100, 2) if decided > 0 else 0.0

            bp_count = md.get("bid_price_count", 0)
            avg_bid_rate = round(md.get("bid_price_sum", 0) / bp_count, 4) if bp_count > 0 else None

            monthly_list.append({
                "month": month_key,
                "participationCount": md.get("participation_count", 0),
                "participation_count": md.get("participation_count", 0),
                "submissionCount": md.get("submission_count", 0),
                "submission_count": md.get("submission_count", 0),
                "wonCount": won_c,
                "won_count": won_c,
                "lostCount": lost_c,
                "lost_count": lost_c,
                "winRate": win_rate,
                "win_rate": win_rate,
                "totalWonAmount": md.get("total_won_amount", 0),
                "total_won_amount": md.get("total_won_amount", 0),
                "averageBidRate": avg_bid_rate,
                "average_bid_rate": avg_bid_rate,
            })

        # 누적 통계
        total_participation = sum(m["participation_count"] for m in monthly_list)
        total_submission = sum(m["submission_count"] for m in monthly_list)
        total_won = sum(m["won_count"] for m in monthly_list)
        total_lost = sum(m["lost_count"] for m in monthly_list)
        total_won_amount = sum(m["total_won_amount"] for m in monthly_list)

        decided_total = total_won + total_lost
        overall_win_rate = round(total_won / decided_total * 100, 2) if decided_total > 0 else 0.0
        average_won_amount = total_won_amount / total_won if total_won > 0 else 0.0

        # overall ROI 계산
        won_stmt = select(UserBidTracking).where(
            UserBidTracking.user_id == user_id,
            UserBidTracking.is_winner == True,
            UserBidTracking.created_at >= start_date,
        )
        won_result = await self.db.execute(won_stmt)
        won_trackings = list(won_result.scalars().all())
        overall_roi = self._calculate_roi(won_trackings)

        cumulative = {
            "totalParticipation": total_participation,
            "total_participation": total_participation,
            "totalSubmission": total_submission,
            "total_submission": total_submission,
            "totalWon": total_won,
            "total_won": total_won,
            "totalLost": total_lost,
            "total_lost": total_lost,
            "overallWinRate": overall_win_rate,
            "overall_win_rate": overall_win_rate,
            "totalWonAmount": total_won_amount,
            "total_won_amount": total_won_amount,
            "averageWonAmount": average_won_amount,
            "average_won_amount": average_won_amount,
            "overallRoi": overall_roi,
            "overall_roi": overall_roi,
        }

        result_data: dict[str, Any] = {
            "monthly": monthly_list,
            "cumulative": cumulative,
        }

        await self._set_cache(cache_key, result_data, ttl=300)
        return result_data

    def _calculate_period_range(self, period: str) -> tuple[datetime, datetime]:
        """
        기간 문자열 -> 시작일/종료일 변환

        Args:
            period: current_month, last_month, last_3_months, last_6_months, last_year

        Returns:
            (start_date, end_date) tuple

        Raises:
            ValueError: 알 수 없는 기간 값
        """
        if period not in VALID_PERIODS:
            raise ValueError(f"유효하지 않은 기간 값입니다: {period}. 허용값: {', '.join(sorted(VALID_PERIODS))}")

        now = datetime.now(timezone.utc)

        if period == "current_month":
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end = now

        elif period == "last_month":
            first_of_current = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            last_of_last = first_of_current - timedelta(seconds=1)
            start = last_of_last.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end = last_of_last

        elif period == "last_3_months":
            start = self._months_ago(now, 3)
            end = now

        elif period == "last_6_months":
            start = self._months_ago(now, 6)
            end = now

        elif period == "last_year":
            start = self._months_ago(now, 12)
            end = now

        else:
            raise ValueError(f"유효하지 않은 기간 값입니다: {period}")

        return start, end

    # ============================================================
    # 내부 메서드
    # ============================================================

    @staticmethod
    def _months_ago(dt: datetime, months: int) -> datetime:
        """N개월 전 1일 00:00:00"""
        year = dt.year
        month = dt.month - months
        while month <= 0:
            month += 12
            year -= 1
        return datetime(year, month, 1, tzinfo=timezone.utc)

    @staticmethod
    def _calculate_roi(won_trackings: list[UserBidTracking]) -> float:
        """
        ROI 계산

        ROI = (총 낙찰금액 - 총 투찰비용) / 총 투찰비용 * 100
        my_bid_price가 없는 건은 제외
        투찰비용이 0이면 0.0 반환
        """
        total_won = sum(
            int(t.my_bid_price) for t in won_trackings
            if t.my_bid_price is not None
        )
        total_bid = total_won  # MVP: 투찰비용 = 낙찰금액 합계

        if total_bid == 0:
            return 0.0

        return round((total_won - total_bid) / total_bid * 100, 2)

    async def _get_upcoming_deadlines(self, user_id: UUID) -> list[dict]:
        """D-7 이내 마감 임박 공고 (interested, participating 상태)"""
        now = datetime.now(timezone.utc)
        deadline_threshold = now + timedelta(days=7)

        stmt = (
            select(UserBidTracking, Bid)
            .join(Bid, UserBidTracking.bid_id == Bid.id)
            .where(
                UserBidTracking.user_id == user_id,
                UserBidTracking.status.in_(["interested", "participating"]),
                Bid.deadline <= deadline_threshold,
                Bid.deadline >= now,
            )
            .order_by(Bid.deadline.asc())
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        deadlines = []
        for tracking, bid in rows:
            deadline_dt = bid.deadline
            if deadline_dt.tzinfo is None:
                deadline_dt = deadline_dt.replace(tzinfo=timezone.utc)
            days_left = max(0, (deadline_dt - now).days)

            deadlines.append({
                "bidId": str(bid.id),
                "bid_id": bid.id,
                "title": bid.title,
                "deadline": deadline_dt,
                "daysLeft": days_left,
                "days_left": days_left,
                "trackingStatus": tracking.status,
                "tracking_status": tracking.status,
            })

        return deadlines

    async def _get_cache(self, key: str) -> dict | None:
        """Redis 캐시 조회 (없으면 None)"""
        if self.redis is None:
            return None
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.warning("[캐시] 조회 실패: %s - %s", key, e)
        return None

    async def _set_cache(self, key: str, data: dict, ttl: int = 30) -> None:
        """Redis 캐시 저장"""
        if self.redis is None:
            return
        try:
            await self.redis.setex(key, ttl, json.dumps(data, default=str))
        except Exception as e:
            logger.warning("[캐시] 저장 실패: %s - %s", key, e)

    async def invalidate_user_cache(self, user_id: UUID) -> None:
        """사용자의 대시보드 캐시 무효화"""
        if self.redis is None:
            return
        try:
            keys = [
                f"dashboard:pipeline:{user_id}",
            ]
            # summary는 패턴 삭제 필요 (period별로 다름)
            for period in VALID_PERIODS:
                keys.append(f"dashboard:summary:{user_id}:{period}")

            for key in keys:
                await self.redis.delete(key)
        except Exception as e:
            logger.warning("[캐시] 무효화 실패: user=%s - %s", user_id, e)
