"""공고 수집 서비스 - 공공데이터포털 나라장터 API 연동"""
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable
from uuid import UUID, uuid4

import httpx

logger = logging.getLogger(__name__)

# 나라장터 API 설정
NARA_API_BASE_URL = "https://apis.data.go.kr/1230000/BidPublicInfoService04"
NARA_API_ENDPOINT = "getBidPblancListInfoServc"

# 샘플 데이터 (API 키 없을 때 폴백)
SAMPLE_BID_DATA = [
    {
        "bidNtceNo": "20260308001",
        "bidNtceOrd": "00",
        "bidNtceNm": "2026년 정보시스템 고도화 사업",
        "ntceInsttNm": "행정안전부",
        "dminsttNm": "정보화전략과",
        "presmptPrce": "500000000",
        "bidNtceDt": "2026/03/08",
        "bidClseDt": "2026/03/22 17:00:00",
        "opengDt": "2026/03/23 10:00:00",
        "ntceKindNm": "일반경쟁",
        "cntrctMthdNm": "적격심사",
    }
]


class CollectionError(Exception):
    """공고 수집 오류"""
    def __init__(self, message: str, cause: Exception | None = None):
        self.message = message
        self.cause = cause
        super().__init__(message)


@dataclass
class CollectionResult:
    """공고 수집 결과"""
    new_count: int = 0
    updated_count: int = 0
    failed_count: int = 0
    errors: list[str] = field(default_factory=list)
    new_bid_ids: list[UUID] = field(default_factory=list)


# 인메모리 저장소 (MVP 패턴)
_bids: dict[str, Any] = {}
_attachments: dict[str, Any] = {}


def _reset_store() -> None:
    """테스트 격리용 저장소 초기화"""
    _bids.clear()
    _attachments.clear()


class BidObject:
    """공고 데이터 객체 (인메모리)"""
    def __init__(self, **kwargs: Any):
        for k, v in kwargs.items():
            setattr(self, k, v)


class BidAttachmentObject:
    """첨부파일 데이터 객체 (인메모리)"""
    def __init__(self, **kwargs: Any):
        for k, v in kwargs.items():
            setattr(self, k, v)


class BidCollectorService:
    """공고 수집 서비스 - 나라장터 공공데이터포털 API 연동"""

    def __init__(self, db: Any, http_client: httpx.AsyncClient):
        self.db = db
        self.http_client = http_client

        # 설정
        try:
            from src.config import get_settings
            settings = get_settings()
            self._api_key = getattr(settings, "nara_api_key", "")
            self._base_url = getattr(settings, "nara_api_base_url", NARA_API_BASE_URL)
            self._page_size = getattr(settings, "collection_page_size", 100)
            self._max_retries = getattr(settings, "collection_retry_max", 3)
            self._base_delay = getattr(settings, "collection_retry_base_delay", 2.0)
        except Exception:
            self._api_key = ""
            self._base_url = NARA_API_BASE_URL
            self._page_size = 100
            self._max_retries = 3
            self._base_delay = 2.0

    async def collect_bids(self) -> CollectionResult:
        """
        공고 수집 메인 플로우

        1. 공공데이터포털 API 호출 (입찰공고목록 조회, 페이지네이션)
        2. 중복 공고 필터링 (bid_number 기준)
        3. 신규 공고 저장
        4. 첨부파일 정보 저장
        """
        result = CollectionResult()
        page = 1
        total_count: int | None = None

        while True:
            try:
                # API 호출
                response = await self.http_client.get(
                    f"{self._base_url}/{NARA_API_ENDPOINT}",
                    params={
                        "ServiceKey": self._api_key,
                        "numOfRows": self._page_size,
                        "pageNo": page,
                        "type": "json",
                    },
                )
                data = response.json()
                body = data.get("response", {}).get("body", {})
                items: list[dict[str, Any]] = body.get("items", [])

                # totalCount 초기화
                if total_count is None:
                    total_count = int(body.get("totalCount", 0))

                if not items:
                    break

                # 각 공고 처리
                for item in items:
                    bid_number = f"{item.get('bidNtceNo', '')}-{item.get('bidNtceOrd', '00')}"
                    try:
                        # 중복 확인
                        if await self._is_duplicate(bid_number):
                            continue

                        # 저장
                        bid = await self._save_bid(item)
                        result.new_count += 1
                        result.new_bid_ids.append(bid.id if not isinstance(bid.id, UUID) else bid.id)

                        # 첨부파일 저장 (API 응답에 첨부파일 정보가 있으면)
                        attachments_data = item.get("attachments", [])
                        await self._save_attachments(bid.id, attachments_data)

                    except (ValueError, KeyError, AttributeError) as e:
                        result.failed_count += 1
                        result.errors.append(str(e))

                # 페이지네이션 확인
                fetched_count = page * self._page_size
                if total_count is not None and fetched_count >= total_count:
                    break
                page += 1

            except Exception as e:
                result.failed_count += 1
                result.errors.append(str(e))
                break

        return result

    async def _fetch_from_api(self, page: int = 1, num_of_rows: int = 100) -> list[dict[str, Any]]:
        """
        공공데이터포털 나라장터 입찰공고 API 호출

        Returns:
            공고 dict 리스트
        """
        params: dict[str, Any] = {
            "ServiceKey": self._api_key,
            "numOfRows": num_of_rows,
            "pageNo": page,
            "type": "json",
        }

        response = await self.http_client.get(
            f"{self._base_url}/{NARA_API_ENDPOINT}",
            params=params,
        )

        data = response.json()
        body = data.get("response", {}).get("body", {})
        items = body.get("items", [])
        return items if isinstance(items, list) else []

    async def _retry_with_backoff(
        self,
        func: Callable,
        max_retries: int = 3,
        base_delay: float = 2.0,
    ) -> Any:
        """
        지수 백오프 재시도 로직 (AC-05)

        - 1차: base_delay * 2^0 = 2초 대기 후 재시도
        - 2차: base_delay * 2^1 = 4초 대기 후 재시도
        - 3차: base_delay * 2^2 = 8초 대기 후 재시도
        - 3회 모두 실패: CollectionError 발생
        """
        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                return await func()
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    # 지수 백오프: base_delay * 2^attempt
                    delay = base_delay * (2 ** attempt)
                    logger.warning(
                        f"재시도 {attempt + 1}/{max_retries}: {e}. {delay}초 후 재시도..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"최대 재시도 횟수 {max_retries}회 초과: {e}")

        raise CollectionError(
            f"최대 재시도 횟수({max_retries}회) 초과: {last_error}",
            cause=last_error,
        )

    async def _save_bid(self, bid_data: dict[str, Any]) -> Any:
        """
        API 응답 dict -> Bid 객체 변환 및 저장

        Raises:
            ValueError: 필수 필드(title, deadline) 누락 시
        """
        # 필수 필드 검증
        title = bid_data.get("bidNtceNm")
        if not title:
            raise ValueError("공고명(bidNtceNm)이 누락되었습니다.")

        deadline_str = bid_data.get("bidClseDt")
        if not deadline_str:
            raise ValueError("마감일시(bidClseDt)가 누락되었습니다.")

        # bid_number 조합
        bid_number = f"{bid_data.get('bidNtceNo', '')}-{bid_data.get('bidNtceOrd', '00')}"

        # 날짜/시간 파싱
        deadline = _parse_datetime(deadline_str)
        open_date_str = bid_data.get("opengDt")
        open_date = _parse_datetime(open_date_str) if open_date_str else None

        announcement_date_str = bid_data.get("bidNtceDt")
        announcement_date = _parse_date(announcement_date_str) if announcement_date_str else None

        # 예산 파싱
        budget_str = bid_data.get("presmptPrce")
        budget: int | None = None
        if budget_str:
            try:
                budget = int(budget_str)
            except (ValueError, TypeError):
                budget = None

        now = datetime.now(timezone.utc)
        bid_id = uuid4()

        # DB 저장 시도 (연결 가능 시)
        try:
            from src.models.bid import Bid
            bid = Bid(
                id=bid_id,
                bid_number=bid_number,
                title=title,
                organization=bid_data.get("ntceInsttNm", ""),
                category=bid_data.get("dminsttNm"),
                bid_type=bid_data.get("ntceKindNm"),
                contract_method=bid_data.get("cntrctMthdNm"),
                budget=budget,
                announcement_date=announcement_date,
                deadline=deadline,
                open_date=open_date,
                status="open",
                crawled_at=now,
                created_at=now,
                updated_at=now,
            )
            self.db.add(bid)
            await self.db.flush()
            await self.db.refresh(bid)
            # 인메모리 저장소에도 등록
            _bids[bid_number] = bid
            return bid
        except Exception:
            pass

        # 인메모리 저장 폴백
        bid = BidObject(
            id=bid_id,
            bid_number=bid_number,
            title=title,
            organization=bid_data.get("ntceInsttNm", ""),
            category=bid_data.get("dminsttNm"),
            bid_type=bid_data.get("ntceKindNm"),
            contract_method=bid_data.get("cntrctMthdNm"),
            budget=budget,
            announcement_date=announcement_date,
            deadline=deadline,
            open_date=open_date,
            status="open",
            crawled_at=now,
            created_at=now,
            updated_at=now,
        )
        _bids[bid_number] = bid
        return bid

    async def _save_attachments(
        self,
        bid_id: UUID | Any,
        attachments: list[dict[str, Any]],
    ) -> list[Any]:
        """
        첨부파일 정보 저장

        Returns:
            저장된 BidAttachment 목록
        """
        result_list: list[Any] = []
        now = datetime.now(timezone.utc)

        for attachment_data in attachments:
            attachment_id = uuid4()
            filename = attachment_data.get("filename", "")
            file_type = attachment_data.get("fileType", "")
            file_url = attachment_data.get("fileUrl", "")

            # DB 저장 시도
            try:
                from src.models.bid_attachment import BidAttachment
                attachment = BidAttachment(
                    id=attachment_id,
                    bid_id=bid_id,
                    filename=filename,
                    file_type=file_type,
                    file_url=file_url,
                    created_at=now,
                )
                self.db.add(attachment)
                await self.db.flush()
                result_list.append(attachment)
                continue
            except Exception:
                pass

            # 인메모리 폴백
            attachment = BidAttachmentObject(
                id=attachment_id,
                bid_id=bid_id,
                filename=filename,
                file_type=file_type,
                file_url=file_url,
                extracted_text=None,
                created_at=now,
            )
            _attachments[str(attachment_id)] = attachment
            result_list.append(attachment)

        return result_list

    async def _is_duplicate(self, bid_number: str) -> bool:
        """
        bid_number 기준 중복 공고 확인

        Returns:
            True: 이미 존재하는 공고
            False: 신규 공고
        """
        # 인메모리 먼저 확인
        if bid_number in _bids:
            return True

        # DB 조회 시도
        try:
            from sqlalchemy import select
            from src.models.bid import Bid
            result = await self.db.execute(
                select(Bid).where(Bid.bid_number == bid_number)
            )
            existing = result.scalar_one_or_none()
            return existing is not None
        except Exception:
            pass

        return False


# ----------------------------------------------------------------
# 날짜/시간 파싱 헬퍼
# ----------------------------------------------------------------

def _parse_datetime(value: str | None) -> datetime:
    """나라장터 API 날짜시간 포맷 파싱 (예: '2026/03/22 17:00:00')"""
    if not value:
        raise ValueError(f"날짜시간 값이 없습니다: {value}")

    # 여러 포맷 시도
    formats = [
        "%Y/%m/%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(value.strip(), fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    raise ValueError(f"날짜시간 파싱 실패: {value}")


def _parse_date(value: str | None) -> "date | None":
    """나라장터 API 날짜 포맷 파싱 (예: '2026/03/08')"""
    from datetime import date
    if not value:
        return None

    formats = [
        "%Y/%m/%d",
        "%Y-%m-%d",
        "%Y/%m/%d %H:%M:%S",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(value.strip()[:10], fmt[:8])
            return dt.date()
        except ValueError:
            continue

    # 공백으로 분리 후 날짜 부분만
    try:
        date_part = value.strip().split(" ")[0]
        for sep in ["/", "-"]:
            if sep in date_part:
                parts = date_part.split(sep)
                if len(parts) == 3:
                    return date(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        pass

    return None
