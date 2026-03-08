"""APScheduler 스케줄러 설정 및 작업 함수"""
import logging

import httpx

logger = logging.getLogger(__name__)

# 수집 잠금 키 (Redis SETNX)
COLLECTION_LOCK_KEY = "bid_collection:lock"
COLLECTION_LOCK_TTL = 600  # 10분


async def scheduled_collect_bids() -> None:
    """
    스케줄러에서 호출하는 공고 수집 함수

    실행 순서:
    1. 공고 수집 (BidCollectorService)
    2. 첨부파일 파싱 (BidParserService)
    3. 매칭 분석 (BidMatchService)
    """
    from src.core.database import AsyncSessionLocal
    from src.services.bid_collector_service import BidCollectorService
    from src.services.bid_parser_service import BidParserService
    from src.services.bid_match_service import BidMatchService

    logger.info("[스케줄러] 공고 자동 수집 시작")

    try:
        async with AsyncSessionLocal() as db:
            async with httpx.AsyncClient(timeout=30.0) as client:
                collector = BidCollectorService(db, client)
                parser = BidParserService(client)
                matcher = BidMatchService(db)

                # 1. 공고 수집
                result = await collector.collect_bids()
                logger.info(
                    f"[스케줄러] 수집 완료: 신규={result.new_count}, "
                    f"실패={result.failed_count}"
                )

                # 2. 신규 공고 첨부파일 파싱
                for bid_id in result.new_bid_ids:
                    attachments = await collector._save_attachments(bid_id, [])
                    await parser.parse_all_for_bid(bid_id, attachments)

                # 3. 매칭 분석 (신규 공고에 대해서만)
                if result.new_bid_ids:
                    match_count = await matcher.analyze_new_bids_for_all_users(
                        result.new_bid_ids
                    )
                    logger.info(f"[스케줄러] 매칭 분석 완료: {match_count}건")

                await db.commit()

    except Exception as e:
        logger.error(f"[스케줄러] 공고 수집 오류: {e}")


async def acquire_collection_lock(redis: "Any") -> bool:
    """수집 잠금 획득 (Redis SETNX)"""
    try:
        return await redis.set(COLLECTION_LOCK_KEY, "1", nx=True, ex=COLLECTION_LOCK_TTL)
    except Exception as e:
        logger.warning(f"Redis 잠금 획득 실패: {e}")
        return True  # Redis 없으면 잠금 없이 진행


async def release_collection_lock(redis: "Any") -> None:
    """수집 잠금 해제"""
    try:
        await redis.delete(COLLECTION_LOCK_KEY)
    except Exception as e:
        logger.warning(f"Redis 잠금 해제 실패: {e}")


def create_scheduler() -> "AsyncIOScheduler":
    """APScheduler 인스턴스 생성"""
    from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore[import]
    from apscheduler.triggers.cron import CronTrigger  # type: ignore[import]

    from src.config import get_settings
    settings = get_settings()

    scheduler = AsyncIOScheduler(timezone="Asia/Seoul")

    if settings.scheduler_enabled:
        scheduler.add_job(
            scheduled_collect_bids,
            CronTrigger(
                hour=settings.collection_schedule_hours,
                minute=0,
                timezone="Asia/Seoul",
            ),
            id="bid_collection",
            name="공고 자동 수집",
            replace_existing=True,
            max_instances=1,  # 동시 실행 방지
        )
        logger.info(
            f"[스케줄러] 공고 수집 스케줄 등록: {settings.collection_schedule_hours}시 KST"
        )

    return scheduler


# Any 타입 힌트 임포트 (런타임 이전에 평가되지 않도록)
from typing import Any  # noqa: E402
