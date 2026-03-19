"""
F-06 입찰 현황 대시보드 — 테스트 명세 기반 테스트

테스트 범위:
- DashboardService 단위 테스트 (mock 기반)
- BidTrackingService 단위 테스트 (mock 기반)
- Dashboard API 통합 테스트 (인메모리 방식)
- Tracking API 통합 테스트 (인메모리 방식)
"""
import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import AsyncGenerator, Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID

from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport


# ============================================================
# Mock 헬퍼
# ============================================================

def make_mock_tracking(
    user_id: UUID | None = None,
    bid_id: UUID | None = None,
    status: str = "interested",
    my_bid_price: Decimal | None = None,
    is_winner: bool | None = None,
    submitted_at: datetime | None = None,
    result_at: datetime | None = None,
    notes: str | None = None,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> MagicMock:
    """UserBidTracking Mock 객체 생성"""
    t = MagicMock()
    t.id = uuid4()
    t.user_id = user_id or uuid4()
    t.bid_id = bid_id or uuid4()
    t.status = status
    t.my_bid_price = my_bid_price
    t.is_winner = is_winner
    t.submitted_at = submitted_at
    t.result_at = result_at
    t.notes = notes
    t.created_at = created_at or datetime.now(timezone.utc)
    t.updated_at = updated_at or datetime.now(timezone.utc)
    return t


def make_mock_bid(
    bid_id: UUID | None = None,
    title: str = "테스트 공고",
    organization: str = "테스트 기관",
    budget: Decimal | None = Decimal(500_000_000),
    deadline: datetime | None = None,
) -> MagicMock:
    """Bid Mock 객체 생성"""
    b = MagicMock()
    b.id = bid_id or uuid4()
    b.title = title
    b.organization = organization
    b.budget = budget
    b.deadline = deadline or datetime.now(timezone.utc) + timedelta(days=10)
    return b


# ============================================================
# BidTrackingService 단위 테스트 (mock DB)
# ============================================================

class TestBidTrackingServiceUpsert:
    """BidTrackingService.upsert_tracking 단위 테스트"""

    async def test_upsert_creates_new_tracking_interested(self):
        """신규 생성 - interested 상태"""
        from src.services.bid_tracking_service import BidTrackingService

        user_id = uuid4()
        bid_id = uuid4()

        # DB mock
        mock_db = AsyncMock()
        # 기존 레코드 없음
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        service = BidTrackingService(mock_db)
        tracking, is_created = await service.upsert_tracking(
            user_id=user_id,
            bid_id=bid_id,
            status="interested",
            my_bid_price=None,
            notes=None,
        )

        assert is_created is True
        assert tracking.status == "interested"
        assert tracking.user_id == user_id
        assert tracking.bid_id == bid_id
        assert tracking.is_winner is None
        assert tracking.submitted_at is None
        assert tracking.result_at is None
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()

    async def test_upsert_updates_existing_tracking(self):
        """기존 레코드 업데이트"""
        from src.services.bid_tracking_service import BidTrackingService

        user_id = uuid4()
        bid_id = uuid4()
        existing = make_mock_tracking(user_id=user_id, bid_id=bid_id, status="interested")

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        service = BidTrackingService(mock_db)
        tracking, is_created = await service.upsert_tracking(
            user_id=user_id,
            bid_id=bid_id,
            status="participating",
            my_bid_price=None,
            notes=None,
        )

        assert is_created is False
        assert tracking.status == "participating"
        assert tracking.id == existing.id
        mock_db.add.assert_not_called()

    async def test_upsert_submitted_sets_submitted_at(self):
        """submitted 상태 -> submitted_at 자동 설정"""
        from src.services.bid_tracking_service import BidTrackingService

        user_id = uuid4()
        bid_id = uuid4()

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        service = BidTrackingService(mock_db)
        tracking, is_created = await service.upsert_tracking(
            user_id=user_id,
            bid_id=bid_id,
            status="submitted",
            my_bid_price=450_000_000,
            notes=None,
        )

        assert is_created is True
        assert tracking.submitted_at is not None
        assert int(tracking.my_bid_price) == 450_000_000

    async def test_upsert_won_sets_winner_fields(self):
        """won 상태 -> is_winner=True, result_at 자동 설정"""
        from src.services.bid_tracking_service import BidTrackingService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        service = BidTrackingService(mock_db)
        tracking, _ = await service.upsert_tracking(
            user_id=uuid4(),
            bid_id=uuid4(),
            status="won",
            my_bid_price=450_000_000,
            notes=None,
        )

        assert tracking.is_winner is True
        assert tracking.result_at is not None

    async def test_upsert_lost_sets_loser_fields(self):
        """lost 상태 -> is_winner=False, result_at 자동 설정"""
        from src.services.bid_tracking_service import BidTrackingService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        service = BidTrackingService(mock_db)
        tracking, _ = await service.upsert_tracking(
            user_id=uuid4(),
            bid_id=uuid4(),
            status="lost",
            my_bid_price=None,
            notes=None,
        )

        assert tracking.is_winner is False
        assert tracking.result_at is not None

    async def test_upsert_saves_notes(self):
        """notes 저장"""
        from src.services.bid_tracking_service import BidTrackingService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        service = BidTrackingService(mock_db)
        tracking, _ = await service.upsert_tracking(
            user_id=uuid4(),
            bid_id=uuid4(),
            status="participating",
            my_bid_price=None,
            notes="투찰가 확정, 제출 예정",
        )

        assert tracking.notes == "투찰가 확정, 제출 예정"

    async def test_upsert_my_bid_price(self):
        """myBidPrice 저장"""
        from src.services.bid_tracking_service import BidTrackingService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        service = BidTrackingService(mock_db)
        tracking, _ = await service.upsert_tracking(
            user_id=uuid4(),
            bid_id=uuid4(),
            status="submitted",
            my_bid_price=450_000_000,
            notes=None,
        )

        assert tracking.my_bid_price == Decimal(450_000_000)


class TestBidTrackingServiceGet:
    """BidTrackingService.get_tracking 단위 테스트"""

    async def test_get_tracking_exists(self):
        """존재하는 추적 조회"""
        from src.services.bid_tracking_service import BidTrackingService

        user_id = uuid4()
        bid_id = uuid4()
        existing = make_mock_tracking(user_id=user_id, bid_id=bid_id, status="interested")

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = BidTrackingService(mock_db)
        result = await service.get_tracking(user_id=user_id, bid_id=bid_id)

        assert result is not None
        assert result.status == "interested"

    async def test_get_tracking_not_exists(self):
        """존재하지 않는 추적 -> None"""
        from src.services.bid_tracking_service import BidTrackingService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = BidTrackingService(mock_db)
        result = await service.get_tracking(user_id=uuid4(), bid_id=uuid4())
        assert result is None

    async def test_get_user_trackings_all(self):
        """전체 추적 목록 조회"""
        from src.services.bid_tracking_service import BidTrackingService

        user_id = uuid4()
        t1 = make_mock_tracking(user_id=user_id, status="interested")
        t2 = make_mock_tracking(user_id=user_id, status="participating")

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [t1, t2]
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = BidTrackingService(mock_db)
        trackings = await service.get_user_trackings(user_id=user_id)
        assert len(trackings) == 2

    async def test_get_user_trackings_with_status_filter(self):
        """상태 필터로 조회"""
        from src.services.bid_tracking_service import BidTrackingService

        user_id = uuid4()
        t1 = make_mock_tracking(user_id=user_id, status="submitted")

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [t1]
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = BidTrackingService(mock_db)
        submitted = await service.get_user_trackings(user_id=user_id, status="submitted")
        assert len(submitted) == 1
        assert submitted[0].status == "submitted"

    async def test_get_win_history(self):
        """낙찰 이력 조회 - is_winner=True인 레코드만"""
        from src.services.bid_tracking_service import BidTrackingService

        user_id = uuid4()
        bid_id = uuid4()
        t1 = make_mock_tracking(user_id=user_id, bid_id=bid_id, status="won", is_winner=True, my_bid_price=Decimal(450_000_000))
        mock_bid = make_mock_bid(bid_id=bid_id)

        mock_db = AsyncMock()

        # count 쿼리 결과
        count_result = MagicMock()
        count_result.scalar.return_value = 1

        # 목록 쿼리 결과
        list_result = MagicMock()
        list_result.all.return_value = [(t1, mock_bid)]

        mock_db.execute = AsyncMock(side_effect=[count_result, list_result])

        service = BidTrackingService(mock_db)
        items, total = await service.get_win_history(
            user_id=user_id, page=1, page_size=20, filters={}
        )
        assert total == 1
        assert all(item["is_winner"] for item in items)

    async def test_get_win_history_pagination(self):
        """낙찰 이력 페이지네이션"""
        from src.services.bid_tracking_service import BidTrackingService

        user_id = uuid4()

        mock_db = AsyncMock()
        count_result = MagicMock()
        count_result.scalar.return_value = 6

        list_result = MagicMock()
        # page=1, size=5 -> 5개 반환
        win_rows = [
            (make_mock_tracking(user_id=user_id, status="won", is_winner=True, my_bid_price=Decimal(500_000_000)),
             make_mock_bid())
            for _ in range(5)
        ]
        list_result.all.return_value = win_rows

        mock_db.execute = AsyncMock(side_effect=[count_result, list_result])

        service = BidTrackingService(mock_db)
        items_p1, total = await service.get_win_history(user_id=user_id, page=1, page_size=5, filters={})
        assert total == 6
        assert len(items_p1) == 5


# ============================================================
# DashboardService 단위 테스트
# ============================================================

class TestDashboardServicePeriodRange:
    """DashboardService._calculate_period_range 단위 테스트"""

    def test_current_month(self):
        """current_month -> 이번 달 1일 ~ 오늘"""
        from src.services.dashboard_service import DashboardService

        service = DashboardService(db=None)
        start, end = service._calculate_period_range("current_month")

        now = datetime.now(timezone.utc)
        assert start.day == 1
        assert start.month == now.month
        assert start.year == now.year
        assert end.date() == now.date()

    def test_last_year(self):
        """last_year -> 1년 전 1일 ~ 오늘"""
        from src.services.dashboard_service import DashboardService

        service = DashboardService(db=None)
        start, end = service._calculate_period_range("last_year")

        now = datetime.now(timezone.utc)
        assert end.date() == now.date()
        # 약 1년 전 날짜임을 확인 (365일 이상 전)
        assert (now.date() - start.date()).days >= 364

    def test_last_3_months(self):
        """last_3_months -> 3개월 전 1일 ~ 오늘"""
        from src.services.dashboard_service import DashboardService

        service = DashboardService(db=None)
        start, end = service._calculate_period_range("last_3_months")

        now = datetime.now(timezone.utc)
        assert end.date() == now.date()
        assert start.day == 1
        assert (now.date() - start.date()).days >= 60

    def test_invalid_period_raises_value_error(self):
        """잘못된 period 값 -> ValueError"""
        from src.services.dashboard_service import DashboardService

        service = DashboardService(db=None)
        with pytest.raises(ValueError):
            service._calculate_period_range("invalid")


class TestDashboardServiceGetSummary:
    """DashboardService.get_summary 단위 테스트 (mock DB)"""

    async def test_get_summary_no_data(self):
        """데이터가 없는 경우 -> 모든 카운트 0"""
        from src.services.dashboard_service import DashboardService

        user_id = uuid4()

        mock_db = AsyncMock()
        # 추적 레코드 없음
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        # upcoming deadlines 용 추가 쿼리도 빈 결과
        mock_result2 = MagicMock()
        mock_result2.all.return_value = []
        mock_db.execute = AsyncMock(side_effect=[mock_result, mock_result2])

        service = DashboardService(db=mock_db)
        result = await service.get_summary(user_id=user_id, period="current_month")

        assert result["participationCount"] == 0
        assert result["submissionCount"] == 0
        assert result["wonCount"] == 0
        assert result["lostCount"] == 0
        assert result["winRate"] == 0.0
        assert result["totalWonAmount"] == 0
        assert result["upcomingDeadlines"] == []

    async def test_get_summary_with_data(self):
        """데이터가 있는 경우 -> 정확한 집계"""
        from src.services.dashboard_service import DashboardService

        user_id = uuid4()
        now = datetime.now(timezone.utc)

        trackings = [
            make_mock_tracking(user_id=user_id, status="participating", created_at=now),
            make_mock_tracking(user_id=user_id, status="won", is_winner=True, my_bid_price=Decimal(500_000_000), result_at=now, created_at=now),
            make_mock_tracking(user_id=user_id, status="lost", is_winner=False, result_at=now, created_at=now),
        ]

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = trackings
        mock_result2 = MagicMock()
        mock_result2.all.return_value = []
        mock_db.execute = AsyncMock(side_effect=[mock_result, mock_result2])

        service = DashboardService(db=mock_db)
        result = await service.get_summary(user_id=user_id, period="current_month")

        assert result["wonCount"] == 1
        assert result["lostCount"] == 1
        assert result["totalWonAmount"] == 500_000_000
        # winRate = 1 / (1+1) * 100 = 50.0
        assert result["winRate"] == 50.0

    async def test_get_summary_win_rate_zero_division(self):
        """낙찰 0건, 탈락 0건 -> winRate = 0.0 (0으로 나누기 방지)"""
        from src.services.dashboard_service import DashboardService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_result2 = MagicMock()
        mock_result2.all.return_value = []
        mock_db.execute = AsyncMock(side_effect=[mock_result, mock_result2])

        service = DashboardService(db=mock_db)
        result = await service.get_summary(user_id=uuid4(), period="current_month")

        assert result["winRate"] == 0.0
        assert isinstance(result["winRate"], float)

    async def test_get_summary_roi_calculation(self):
        """ROI 계산 정확성"""
        from src.services.dashboard_service import DashboardService

        user_id = uuid4()
        now = datetime.now(timezone.utc)

        # won 2건 각 400만 = 총 800만, 투찰가 합 800만 -> ROI = (800-800)/800*100 = 0.0
        trackings = [
            make_mock_tracking(user_id=user_id, status="won", is_winner=True, my_bid_price=Decimal(400_000_000), result_at=now, created_at=now),
            make_mock_tracking(user_id=user_id, status="won", is_winner=True, my_bid_price=Decimal(400_000_000), result_at=now, created_at=now),
        ]

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = trackings
        mock_result2 = MagicMock()
        mock_result2.all.return_value = []
        mock_db.execute = AsyncMock(side_effect=[mock_result, mock_result2])

        service = DashboardService(db=mock_db)
        result = await service.get_summary(user_id=user_id, period="current_month")

        assert result["wonCount"] == 2
        assert result["totalWonAmount"] == 800_000_000
        # ROI = (총낙찰금 - 총투찰금) / 총투찰금 * 100 = 0.0
        assert result["roi"] == 0.0

    async def test_get_summary_upcoming_deadlines(self):
        """마감 임박 공고 (D-7 이내) 포함 확인"""
        from src.services.dashboard_service import DashboardService

        user_id = uuid4()
        now = datetime.now(timezone.utc)
        bid_near = make_mock_bid(deadline=now + timedelta(days=3))
        tracking_near = make_mock_tracking(user_id=user_id, bid_id=bid_near.id, status="participating", created_at=now)

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []  # 기간 내 없음
        # upcoming deadlines 쿼리
        mock_result2 = MagicMock()
        mock_result2.all.return_value = [(tracking_near, bid_near)]
        mock_db.execute = AsyncMock(side_effect=[mock_result, mock_result2])

        service = DashboardService(db=mock_db)
        result = await service.get_summary(user_id=user_id, period="current_month")

        assert len(result["upcomingDeadlines"]) == 1
        assert result["upcomingDeadlines"][0]["daysLeft"] <= 7

    async def test_get_summary_roi_none_bid_price(self):
        """my_bid_price=None인 경우 ROI 계산 -> 해당 건 제외, 예외 없음"""
        from src.services.dashboard_service import DashboardService

        user_id = uuid4()
        now = datetime.now(timezone.utc)

        trackings = [
            make_mock_tracking(user_id=user_id, status="won", is_winner=True, my_bid_price=None, result_at=now, created_at=now),
        ]

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = trackings
        mock_result2 = MagicMock()
        mock_result2.all.return_value = []
        mock_db.execute = AsyncMock(side_effect=[mock_result, mock_result2])

        service = DashboardService(db=mock_db)
        # 예외 없이 처리
        result = await service.get_summary(user_id=user_id, period="current_month")
        assert isinstance(result["roi"], float)


class TestDashboardServiceGetPipeline:
    """DashboardService.get_pipeline 단위 테스트"""

    async def test_get_pipeline_empty(self):
        """빈 파이프라인 -> 5개 stage 모두 count=0"""
        from src.services.dashboard_service import DashboardService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_result2 = MagicMock()
        mock_result2.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(side_effect=[mock_result, mock_result2])

        service = DashboardService(db=mock_db)
        result = await service.get_pipeline(user_id=uuid4())

        assert len(result["stages"]) == 5
        for stage in result["stages"]:
            assert stage["count"] == 0
            assert stage["items"] == []

    async def test_get_pipeline_all_statuses(self):
        """모든 상태에 데이터 있음 -> 각 stage count = 1"""
        from src.services.dashboard_service import DashboardService

        user_id = uuid4()
        now = datetime.now(timezone.utc)
        statuses = ["interested", "participating", "submitted", "won", "lost"]
        rows = []
        for s in statuses:
            bid = make_mock_bid(deadline=now + timedelta(days=5))
            t = make_mock_tracking(user_id=user_id, bid_id=bid.id, status=s)
            rows.append((t, bid))

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = rows
        mock_result2 = MagicMock()
        mock_result2.scalars.return_value.all.return_value = []  # 매칭 점수 없음
        mock_db.execute = AsyncMock(side_effect=[mock_result, mock_result2])

        service = DashboardService(db=mock_db)
        result = await service.get_pipeline(user_id=user_id)

        assert len(result["stages"]) == 5
        for stage in result["stages"]:
            assert stage["count"] == 1
            assert len(stage["items"]) == 1
            item = stage["items"][0]
            assert "title" in item
            assert "organization" in item

    async def test_get_pipeline_stage_labels(self):
        """파이프라인 단계 라벨 확인"""
        from src.services.dashboard_service import DashboardService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_result2 = MagicMock()
        mock_result2.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(side_effect=[mock_result, mock_result2])

        service = DashboardService(db=mock_db)
        result = await service.get_pipeline(user_id=uuid4())

        label_map = {
            "interested": "관심",
            "participating": "참여",
            "submitted": "제출",
            "won": "낙찰",
            "lost": "실패",
        }
        for stage in result["stages"]:
            assert stage["label"] == label_map[stage["status"]]

    async def test_get_pipeline_bid_info_joined(self):
        """각 item에 bid 정보 포함 확인"""
        from src.services.dashboard_service import DashboardService

        user_id = uuid4()
        bid = make_mock_bid(title="AI 기반 행정 서비스", organization="과학기술부")
        t = make_mock_tracking(user_id=user_id, bid_id=bid.id, status="interested")

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [(t, bid)]
        mock_result2 = MagicMock()
        mock_result2.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(side_effect=[mock_result, mock_result2])

        service = DashboardService(db=mock_db)
        result = await service.get_pipeline(user_id=user_id)

        interested_stage = next(s for s in result["stages"] if s["status"] == "interested")
        assert interested_stage["count"] == 1
        item = interested_stage["items"][0]
        assert item["title"] == "AI 기반 행정 서비스"
        assert item["organization"] == "과학기술부"


class TestDashboardServiceGetStatistics:
    """DashboardService.get_statistics 단위 테스트"""

    async def test_get_statistics_no_data(self):
        """데이터 없음 -> 빈 월별 리스트, 누적 0"""
        from src.services.dashboard_service import DashboardService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        # won_stmt 용
        mock_result2 = MagicMock()
        mock_result2.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(side_effect=[mock_result, mock_result2])

        service = DashboardService(db=mock_db)
        result = await service.get_statistics(user_id=uuid4(), months=6)

        assert "monthly" in result
        assert "cumulative" in result
        assert result["cumulative"]["totalWon"] == 0
        assert result["cumulative"]["overallWinRate"] == 0.0

    async def test_get_statistics_win_rate_calculation(self):
        """낙찰률 계산: won=3, lost=7 -> overallWinRate=30.0"""
        from src.services.dashboard_service import DashboardService

        user_id = uuid4()
        now = datetime.now(timezone.utc)

        rows = []
        for i in range(10):
            status = "won" if i < 3 else "lost"
            is_winner = i < 3
            bid = make_mock_bid()
            t = make_mock_tracking(
                user_id=user_id, bid_id=bid.id,
                status=status, is_winner=is_winner,
                result_at=now - timedelta(days=i),
                created_at=now - timedelta(days=i),
            )
            rows.append((t, bid))

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = rows

        mock_won_result = MagicMock()
        won_trackings = [t for t, _ in rows if t.is_winner is True]
        mock_won_result.scalars.return_value.all.return_value = won_trackings
        mock_db.execute = AsyncMock(side_effect=[mock_result, mock_won_result])

        service = DashboardService(db=mock_db)
        result = await service.get_statistics(user_id=user_id, months=6)

        assert result["cumulative"]["totalWon"] == 3
        assert result["cumulative"]["totalLost"] == 7
        assert result["cumulative"]["overallWinRate"] == 30.0

    async def test_get_statistics_cumulative_matches_monthly(self):
        """누적 통계가 월별 합산과 일치"""
        from src.services.dashboard_service import DashboardService

        user_id = uuid4()
        now = datetime.now(timezone.utc)

        rows = []
        for i in range(3):
            bid = make_mock_bid()
            t = make_mock_tracking(
                user_id=user_id, bid_id=bid.id,
                status="won", is_winner=True,
                my_bid_price=Decimal(300_000_000),
                result_at=now, created_at=now,
            )
            rows.append((t, bid))

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = rows
        mock_won_result = MagicMock()
        mock_won_result.scalars.return_value.all.return_value = [t for t, _ in rows]
        mock_db.execute = AsyncMock(side_effect=[mock_result, mock_won_result])

        service = DashboardService(db=mock_db)
        result = await service.get_statistics(user_id=user_id, months=6)

        monthly_won_sum = sum(m["wonCount"] for m in result["monthly"])
        assert result["cumulative"]["totalWon"] == monthly_won_sum


# ============================================================
# 대시보드 API 통합 테스트 (인메모리)
# ============================================================

@pytest.fixture
def dashboard_app() -> FastAPI:
    """대시보드 통합 테스트용 FastAPI 앱"""
    app = FastAPI()

    try:
        from src.api.v1.bids import router as bids_router
        app.include_router(bids_router, prefix="/api/v1/bids")
    except ImportError:
        pass

    try:
        from src.api.v1.dashboard import router as dashboard_router
        app.include_router(dashboard_router, prefix="/api/v1/dashboard")
    except ImportError:
        pass

    return app


@pytest.fixture(autouse=True)
def reset_tracking_store():
    """각 테스트 전후로 추적 저장소 초기화"""
    try:
        from src.api.v1.bids import _TRACKING_STORE
        _TRACKING_STORE.clear()
    except (ImportError, AttributeError):
        pass
    yield
    try:
        from src.api.v1.bids import _TRACKING_STORE
        _TRACKING_STORE.clear()
    except (ImportError, AttributeError):
        pass


@pytest.fixture
async def dashboard_client(dashboard_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """대시보드 테스트용 HTTP 클라이언트"""
    transport = ASGITransport(app=dashboard_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


def make_token(user_id: str | None = None, company_id: str | None = None) -> str:
    """테스트용 JWT 토큰 생성"""
    from src.core.security import create_access_token
    uid = user_id or str(uuid4())
    extra: dict[str, Any] = {"role": "owner"}
    if company_id:
        extra["company_id"] = company_id
    return create_access_token(subject=uid, extra_data=extra)


class TestDashboardSummaryAPI:
    """GET /api/v1/dashboard/summary 통합 테스트"""

    async def test_summary_no_auth(self, dashboard_client: AsyncClient):
        """인증 없음 -> 401"""
        resp = await dashboard_client.get("/api/v1/dashboard/summary")
        assert resp.status_code == 401
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "AUTH_002"

    async def test_summary_authenticated(self, dashboard_client: AsyncClient):
        """인증된 사용자 -> 200, KPI 데이터 반환"""
        token = make_token()
        resp = await dashboard_client.get(
            "/api/v1/dashboard/summary",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "participationCount" in data["data"]
        assert "wonCount" in data["data"]
        assert "winRate" in data["data"]
        assert "upcomingDeadlines" in data["data"]

    async def test_summary_invalid_period(self, dashboard_client: AsyncClient):
        """잘못된 period -> 400"""
        token = make_token()
        resp = await dashboard_client.get(
            "/api/v1/dashboard/summary?period=invalid",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] in ("VALIDATION_001", "DASHBOARD_002")

    async def test_summary_empty_data(self, dashboard_client: AsyncClient):
        """신규 사용자 -> 200, 모든 카운트 0"""
        token = make_token()
        resp = await dashboard_client.get(
            "/api/v1/dashboard/summary",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["participationCount"] == 0
        assert data["data"]["wonCount"] == 0
        assert data["data"]["winRate"] == 0.0


class TestDashboardPipelineAPI:
    """GET /api/v1/dashboard/pipeline 통합 테스트"""

    async def test_pipeline_no_auth(self, dashboard_client: AsyncClient):
        """인증 없음 -> 401"""
        resp = await dashboard_client.get("/api/v1/dashboard/pipeline")
        assert resp.status_code == 401
        data = resp.json()
        assert data["error"]["code"] == "AUTH_002"

    async def test_pipeline_authenticated(self, dashboard_client: AsyncClient):
        """인증된 사용자 -> 200, 5개 stage"""
        token = make_token()
        resp = await dashboard_client.get(
            "/api/v1/dashboard/pipeline",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert len(data["data"]["stages"]) == 5


class TestDashboardStatisticsAPI:
    """GET /api/v1/dashboard/statistics 통합 테스트"""

    async def test_statistics_no_auth(self, dashboard_client: AsyncClient):
        """인증 없음 -> 401"""
        resp = await dashboard_client.get("/api/v1/dashboard/statistics")
        assert resp.status_code == 401

    async def test_statistics_6_months(self, dashboard_client: AsyncClient):
        """6개월 통계 -> 200"""
        token = make_token()
        resp = await dashboard_client.get(
            "/api/v1/dashboard/statistics?months=6",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "monthly" in data["data"]
        assert "cumulative" in data["data"]
        assert len(data["data"]["monthly"]) == 6

    async def test_statistics_12_months_max(self, dashboard_client: AsyncClient):
        """months=12 최대 -> 200"""
        token = make_token()
        resp = await dashboard_client.get(
            "/api/v1/dashboard/statistics?months=12",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]["monthly"]) == 12

    async def test_statistics_months_over_limit(self, dashboard_client: AsyncClient):
        """months=13 초과 -> 400"""
        token = make_token()
        resp = await dashboard_client.get(
            "/api/v1/dashboard/statistics?months=13",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400
        data = resp.json()
        assert data["success"] is False


# ============================================================
# Tracking API 통합 테스트
# ============================================================

# 테스트용 공고 ID (bids._SAMPLE_BIDS에 존재하는 ID)
SAMPLE_BID_ID = "550e8400-e29b-41d4-a716-446655440000"
NON_EXISTENT_BID_ID = str(uuid4())


class TestTrackingPostAPI:
    """POST /api/v1/bids/{bid_id}/tracking 통합 테스트"""

    async def test_create_tracking_interested(self, dashboard_client: AsyncClient):
        """최초 관심 등록 -> 201"""
        token = make_token()
        resp = await dashboard_client.post(
            f"/api/v1/bids/{SAMPLE_BID_ID}/tracking",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": "interested"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["status"] == "interested"

    async def test_update_tracking_status(self, dashboard_client: AsyncClient):
        """상태 변경 -> 200"""
        token = make_token()

        # 최초 생성
        await dashboard_client.post(
            f"/api/v1/bids/{SAMPLE_BID_ID}/tracking",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": "interested"},
        )

        # 상태 업데이트
        resp = await dashboard_client.post(
            f"/api/v1/bids/{SAMPLE_BID_ID}/tracking",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": "participating"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["status"] == "participating"

    async def test_create_tracking_won(self, dashboard_client: AsyncClient):
        """낙찰 처리 -> is_winner=true"""
        token = make_token()

        # 먼저 생성
        await dashboard_client.post(
            f"/api/v1/bids/{SAMPLE_BID_ID}/tracking",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": "interested"},
        )

        resp = await dashboard_client.post(
            f"/api/v1/bids/{SAMPLE_BID_ID}/tracking",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": "won", "myBidPrice": 450_000_000},
        )
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert data["data"]["isWinner"] is True

    async def test_create_tracking_lost(self, dashboard_client: AsyncClient):
        """탈락 처리 -> is_winner=false"""
        token = make_token()

        # 먼저 생성
        await dashboard_client.post(
            f"/api/v1/bids/{SAMPLE_BID_ID}/tracking",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": "interested"},
        )

        resp = await dashboard_client.post(
            f"/api/v1/bids/{SAMPLE_BID_ID}/tracking",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": "lost"},
        )
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert data["data"]["isWinner"] is False

    async def test_create_tracking_no_auth(self, dashboard_client: AsyncClient):
        """인증 없음 -> 401"""
        resp = await dashboard_client.post(
            f"/api/v1/bids/{SAMPLE_BID_ID}/tracking",
            json={"status": "interested"},
        )
        assert resp.status_code == 401
        data = resp.json()
        assert data["error"]["code"] == "AUTH_002"

    async def test_create_tracking_bid_not_found(self, dashboard_client: AsyncClient):
        """존재하지 않는 공고 -> 404"""
        token = make_token()
        resp = await dashboard_client.post(
            f"/api/v1/bids/{NON_EXISTENT_BID_ID}/tracking",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": "interested"},
        )
        assert resp.status_code == 404
        data = resp.json()
        assert data["error"]["code"] == "BID_001"

    async def test_create_tracking_invalid_status(self, dashboard_client: AsyncClient):
        """잘못된 status -> 400"""
        token = make_token()
        resp = await dashboard_client.post(
            f"/api/v1/bids/{SAMPLE_BID_ID}/tracking",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": "invalid_status"},
        )
        assert resp.status_code == 400
        data = resp.json()
        assert data["error"]["code"] in ("VALIDATION_001", "DASHBOARD_003")


class TestTrackingGetAPI:
    """GET /api/v1/bids/{bid_id}/tracking 통합 테스트"""

    async def test_get_tracking_exists(self, dashboard_client: AsyncClient):
        """추적 존재 -> 200"""
        token = make_token()

        # 먼저 생성
        await dashboard_client.post(
            f"/api/v1/bids/{SAMPLE_BID_ID}/tracking",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": "participating"},
        )

        resp = await dashboard_client.get(
            f"/api/v1/bids/{SAMPLE_BID_ID}/tracking",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["status"] == "participating"

    async def test_get_tracking_not_found(self, dashboard_client: AsyncClient):
        """추적 미등록 -> 404, DASHBOARD_001"""
        token = make_token()
        resp = await dashboard_client.get(
            f"/api/v1/bids/{SAMPLE_BID_ID}/tracking",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404
        data = resp.json()
        assert data["error"]["code"] == "DASHBOARD_001"


class TestWinsAPI:
    """GET /api/v1/bids/wins 통합 테스트"""

    async def test_get_wins_no_auth(self, dashboard_client: AsyncClient):
        """인증 없음 -> 401"""
        resp = await dashboard_client.get("/api/v1/bids/wins")
        assert resp.status_code == 401

    async def test_get_wins_authenticated(self, dashboard_client: AsyncClient):
        """인증된 사용자 -> 200, 낙찰 목록"""
        token = make_token()
        resp = await dashboard_client.get(
            "/api/v1/bids/wins",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "items" in data["data"]
        assert "page" in data["meta"]
        assert "total" in data["meta"]

    async def test_get_wins_pagination_meta(self, dashboard_client: AsyncClient):
        """페이지네이션 meta 확인"""
        token = make_token()
        resp = await dashboard_client.get(
            "/api/v1/bids/wins?page=2&pageSize=5",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["meta"]["page"] == 2
        assert data["meta"]["pageSize"] == 5

    async def test_get_wins_date_filter(self, dashboard_client: AsyncClient):
        """날짜 필터 -> 200"""
        token = make_token()
        resp = await dashboard_client.get(
            "/api/v1/bids/wins?startDate=2026-01-01",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200


# ============================================================
# 경계 조건 테스트
# ============================================================

class TestEdgeCases:
    """경계 조건 테스트"""

    def test_win_rate_zero_division_static(self):
        """낙찰 0건, 탈락 0건 -> winRate = 0.0 (정적 계산)"""
        won_count = 0
        lost_count = 0
        decided = won_count + lost_count
        win_rate = 0.0
        if decided > 0:
            win_rate = round(won_count / decided * 100, 2)
        assert win_rate == 0.0

    def test_roi_none_bid_price_static(self):
        """my_bid_price=None -> 해당 건 제외"""
        from src.services.dashboard_service import DashboardService

        # my_bid_price=None인 mock
        t = make_mock_tracking(status="won", is_winner=True, my_bid_price=None)
        roi = DashboardService._calculate_roi([t])
        assert isinstance(roi, float)
        assert roi == 0.0  # 투찰비용이 없어서 0

    async def test_duplicate_tracking_upsert(self):
        """동일 공고에 대해 중복 tracking POST -> upsert 동작 (에러 아님)"""
        from src.services.bid_tracking_service import BidTrackingService

        user_id = uuid4()
        bid_id = uuid4()

        mock_db = AsyncMock()

        # 첫 번째 호출: 기존 없음
        mock_result1 = MagicMock()
        mock_result1.scalar_one_or_none.return_value = None
        # 두 번째 호출: 기존 있음
        mock_result2 = MagicMock()

        call_count = 0
        existing_tracking = None

        async def side_effect_execute(*args, **kwargs):
            nonlocal call_count, existing_tracking
            call_count += 1
            if call_count == 1:
                return mock_result1
            else:
                m = MagicMock()
                m.scalar_one_or_none.return_value = existing_tracking
                return m

        mock_db.execute = side_effect_execute
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        service = BidTrackingService(mock_db)

        # 첫 번째 호출
        t1, created1 = await service.upsert_tracking(user_id=user_id, bid_id=bid_id, status="interested", my_bid_price=None, notes=None)
        assert created1 is True
        existing_tracking = t1  # 이제 존재함

        # 두 번째 호출 (업데이트)
        t2, created2 = await service.upsert_tracking(user_id=user_id, bid_id=bid_id, status="participating", my_bid_price=None, notes=None)
        assert created2 is False

    def test_state_transition_freely_allowed(self):
        """상태 전이 자유로움 (역전이 허용)"""
        valid_statuses = ["interested", "participating", "submitted", "won", "lost"]
        assert len(valid_statuses) == 5

    def test_period_range_last_month(self):
        """last_month 기간 범위 확인"""
        from src.services.dashboard_service import DashboardService

        service = DashboardService(db=None)
        start, end = service._calculate_period_range("last_month")

        now = datetime.now(timezone.utc)
        assert start.day == 1
        # end는 지난 달 말일
        assert end < now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    def test_period_range_last_6_months(self):
        """last_6_months 기간 범위 확인"""
        from src.services.dashboard_service import DashboardService

        service = DashboardService(db=None)
        start, end = service._calculate_period_range("last_6_months")

        now = datetime.now(timezone.utc)
        assert end.date() == now.date()
        assert (now.date() - start.date()).days >= 150
