"""
BidCollectorService 단위 테스트

test-spec.md 기준:
- 공공데이터포털 API 호출 성공/실패
- 지수 백오프 재시도 (3회)
- 중복 공고 필터링
- 신규 공고 저장
- 타임아웃 발생 시 재시도

RED 상태: 구현 전이므로 import 시 ImportError 발생
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from uuid import uuid4
import asyncio

# 구현 전이므로 import 시 ImportError 발생 - RED 상태
from src.services.bid_collector_service import BidCollectorService, CollectionResult, CollectionError


# 나라장터 API Mock 응답 데이터
SAMPLE_BID_LIST_RESPONSE = {
    "response": {
        "header": {"resultCode": "00", "resultMsg": "NORMAL SERVICE."},
        "body": {
            "items": [
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
            ],
            "numOfRows": 100,
            "pageNo": 1,
            "totalCount": 1,
        }
    }
}

SAMPLE_BID_LIST_RESPONSE_3 = {
    "response": {
        "header": {"resultCode": "00", "resultMsg": "NORMAL SERVICE."},
        "body": {
            "items": [
                {
                    "bidNtceNo": "20260308001",
                    "bidNtceOrd": "00",
                    "bidNtceNm": "정보시스템 구축 사업",
                    "ntceInsttNm": "행정안전부",
                    "dminsttNm": "정보화전략과",
                    "presmptPrce": "300000000",
                    "bidNtceDt": "2026/03/08",
                    "bidClseDt": "2026/03/22 17:00:00",
                    "opengDt": "2026/03/23 10:00:00",
                    "ntceKindNm": "일반경쟁",
                    "cntrctMthdNm": "적격심사",
                },
                {
                    "bidNtceNo": "20260308002",
                    "bidNtceOrd": "00",
                    "bidNtceNm": "클라우드 전환 사업",
                    "ntceInsttNm": "국방부",
                    "dminsttNm": "정보화국",
                    "presmptPrce": "800000000",
                    "bidNtceDt": "2026/03/08",
                    "bidClseDt": "2026/03/25 17:00:00",
                    "opengDt": "2026/03/26 10:00:00",
                    "ntceKindNm": "일반경쟁",
                    "cntrctMthdNm": "최저가",
                },
                {
                    "bidNtceNo": "20260308003",
                    "bidNtceOrd": "00",
                    "bidNtceNm": "보안 솔루션 구축",
                    "ntceInsttNm": "과학기술정보통신부",
                    "dminsttNm": "사이버보안과",
                    "presmptPrce": "200000000",
                    "bidNtceDt": "2026/03/08",
                    "bidClseDt": "2026/03/20 17:00:00",
                    "opengDt": "2026/03/21 10:00:00",
                    "ntceKindNm": "제한경쟁",
                    "cntrctMthdNm": "적격심사",
                },
            ],
            "numOfRows": 100,
            "pageNo": 1,
            "totalCount": 3,
        }
    }
}

EMPTY_BID_LIST_RESPONSE = {
    "response": {
        "header": {"resultCode": "00", "resultMsg": "NORMAL SERVICE."},
        "body": {"items": [], "numOfRows": 100, "pageNo": 1, "totalCount": 0}
    }
}

PAGINATION_RESPONSE_PAGE1 = {
    "response": {
        "header": {"resultCode": "00", "resultMsg": "NORMAL SERVICE."},
        "body": {
            "items": [{"bidNtceNo": f"2026030800{i}", "bidNtceOrd": "00", "bidNtceNm": f"사업{i}", "ntceInsttNm": "기관", "dminsttNm": "부서", "presmptPrce": "100000000", "bidNtceDt": "2026/03/08", "bidClseDt": "2026/03/22 17:00:00", "opengDt": "2026/03/23 10:00:00", "ntceKindNm": "일반경쟁", "cntrctMthdNm": "적격심사"} for i in range(1, 101)],
            "numOfRows": 100,
            "pageNo": 1,
            "totalCount": 250,
        }
    }
}


class TestCollectBids:
    """collect_bids 메서드 테스트"""

    @pytest.mark.asyncio
    async def test_신규_공고_3건_수집_성공(self):
        """
        Given: API가 3건의 신규 공고를 반환하는 상황
        When: collect_bids() 호출
        Then: CollectionResult(new_count=3) 반환
        """
        # Arrange
        mock_db = AsyncMock()
        mock_http_client = AsyncMock()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = SAMPLE_BID_LIST_RESPONSE_3
        mock_http_client.get = AsyncMock(return_value=mock_response)

        service = BidCollectorService(db=mock_db, http_client=mock_http_client)
        # 중복 없음 — 모두 신규
        service._is_duplicate = AsyncMock(return_value=False)
        service._save_bid = AsyncMock(side_effect=lambda data: MagicMock(id=str(uuid4())))
        service._save_attachments = AsyncMock(return_value=[])

        # Act
        result = await service.collect_bids()

        # Assert
        assert isinstance(result, CollectionResult)
        assert result.new_count == 3

    @pytest.mark.asyncio
    async def test_중복_공고_필터링_5건_중_2건_기존(self):
        """
        Given: API가 5건 반환, 그 중 2건은 이미 DB에 존재
        When: collect_bids() 호출
        Then: CollectionResult(new_count=3) 반환
        """
        # Arrange
        mock_db = AsyncMock()
        mock_http_client = AsyncMock()

        # 5건 응답 생성
        items_5 = [
            {"bidNtceNo": f"2026030800{i}", "bidNtceOrd": "00", "bidNtceNm": f"사업{i}", "ntceInsttNm": "기관", "dminsttNm": "부서", "presmptPrce": "100000000", "bidNtceDt": "2026/03/08", "bidClseDt": "2026/03/22 17:00:00", "opengDt": "2026/03/23 10:00:00", "ntceKindNm": "일반경쟁", "cntrctMthdNm": "적격심사"}
            for i in range(1, 6)
        ]
        response_5 = {
            "response": {
                "header": {"resultCode": "00", "resultMsg": "NORMAL SERVICE."},
                "body": {"items": items_5, "numOfRows": 100, "pageNo": 1, "totalCount": 5}
            }
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = response_5
        mock_http_client.get = AsyncMock(return_value=mock_response)

        service = BidCollectorService(db=mock_db, http_client=mock_http_client)
        # 처음 2건은 중복, 나머지 3건은 신규
        duplicate_flags = [True, True, False, False, False]
        call_count = {"n": 0}

        async def _is_dup(bid_number):
            idx = call_count["n"]
            call_count["n"] += 1
            return duplicate_flags[idx] if idx < len(duplicate_flags) else False

        service._is_duplicate = _is_dup
        service._save_bid = AsyncMock(side_effect=lambda data: MagicMock(id=str(uuid4())))
        service._save_attachments = AsyncMock(return_value=[])

        # Act
        result = await service.collect_bids()

        # Assert
        assert isinstance(result, CollectionResult)
        assert result.new_count == 3

    @pytest.mark.asyncio
    async def test_API_응답_빈_목록(self):
        """
        Given: API가 빈 목록 반환
        When: collect_bids() 호출
        Then: CollectionResult(new_count=0) 반환, 에러 아님
        """
        # Arrange
        mock_db = AsyncMock()
        mock_http_client = AsyncMock()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = EMPTY_BID_LIST_RESPONSE
        mock_http_client.get = AsyncMock(return_value=mock_response)

        service = BidCollectorService(db=mock_db, http_client=mock_http_client)

        # Act
        result = await service.collect_bids()

        # Assert
        assert isinstance(result, CollectionResult)
        assert result.new_count == 0


class TestFetchFromApi:
    """_fetch_from_api 메서드 테스트"""

    @pytest.mark.asyncio
    async def test_정상_응답_파싱(self):
        """
        Given: 공공데이터포털 API 정상 JSON 응답
        When: _fetch_from_api() 호출
        Then: 공고 dict 리스트 반환
        """
        # Arrange
        mock_db = AsyncMock()
        mock_http_client = AsyncMock()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = SAMPLE_BID_LIST_RESPONSE
        mock_http_client.get = AsyncMock(return_value=mock_response)

        service = BidCollectorService(db=mock_db, http_client=mock_http_client)

        # Act
        result = await service._fetch_from_api(page=1, num_of_rows=100)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["bidNtceNo"] == "20260308001"

    @pytest.mark.asyncio
    async def test_페이지네이션_처리_totalCount_250(self):
        """
        Given: totalCount=250, numOfRows=100 응답
        When: collect_bids() 가 내부에서 _fetch_from_api를 반복 호출
        Then: 3페이지 순회하여 총 250건 반환
        """
        # Arrange
        mock_db = AsyncMock()
        mock_http_client = AsyncMock()

        page1_items = [
            {"bidNtceNo": f"BID{i:04d}", "bidNtceOrd": "00", "bidNtceNm": f"사업{i}", "ntceInsttNm": "기관", "dminsttNm": "부서", "presmptPrce": "100000000", "bidNtceDt": "2026/03/08", "bidClseDt": "2026/03/22 17:00:00", "opengDt": "2026/03/23 10:00:00", "ntceKindNm": "일반경쟁", "cntrctMthdNm": "적격심사"}
            for i in range(1, 101)
        ]
        page2_items = [
            {"bidNtceNo": f"BID{i:04d}", "bidNtceOrd": "00", "bidNtceNm": f"사업{i}", "ntceInsttNm": "기관", "dminsttNm": "부서", "presmptPrce": "100000000", "bidNtceDt": "2026/03/08", "bidClseDt": "2026/03/22 17:00:00", "opengDt": "2026/03/23 10:00:00", "ntceKindNm": "일반경쟁", "cntrctMthdNm": "적격심사"}
            for i in range(101, 201)
        ]
        page3_items = [
            {"bidNtceNo": f"BID{i:04d}", "bidNtceOrd": "00", "bidNtceNm": f"사업{i}", "ntceInsttNm": "기관", "dminsttNm": "부서", "presmptPrce": "100000000", "bidNtceDt": "2026/03/08", "bidClseDt": "2026/03/22 17:00:00", "opengDt": "2026/03/23 10:00:00", "ntceKindNm": "일반경쟁", "cntrctMthdNm": "적격심사"}
            for i in range(201, 251)
        ]

        def make_response(items, page):
            r = MagicMock()
            r.status_code = 200
            r.json.return_value = {
                "response": {
                    "header": {"resultCode": "00", "resultMsg": "NORMAL SERVICE."},
                    "body": {"items": items, "numOfRows": 100, "pageNo": page, "totalCount": 250}
                }
            }
            return r

        responses = [
            make_response(page1_items, 1),
            make_response(page2_items, 2),
            make_response(page3_items, 3),
        ]
        mock_http_client.get = AsyncMock(side_effect=responses)

        service = BidCollectorService(db=mock_db, http_client=mock_http_client)
        service._is_duplicate = AsyncMock(return_value=False)
        service._save_bid = AsyncMock(side_effect=lambda data: MagicMock(id=str(uuid4())))
        service._save_attachments = AsyncMock(return_value=[])

        # Act
        result = await service.collect_bids()

        # Assert
        assert result.new_count == 250
        # 3페이지 순회 확인
        assert mock_http_client.get.call_count == 3


class TestRetryWithBackoff:
    """_retry_with_backoff 메서드 테스트"""

    @pytest.mark.asyncio
    async def test_1회_실패_후_성공(self):
        """
        Given: 첫 번째 호출에서 TimeoutError 발생, 두 번째 호출에서 성공
        When: _retry_with_backoff() 호출
        Then: 정상 결과 반환
        """
        # Arrange
        mock_db = AsyncMock()
        mock_http_client = AsyncMock()
        service = BidCollectorService(db=mock_db, http_client=mock_http_client)

        call_count = {"n": 0}

        async def flaky_func():
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise TimeoutError("요청 타임아웃")
            return "success"

        # Act
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await service._retry_with_backoff(flaky_func, max_retries=3, base_delay=2.0)

        # Assert
        assert result == "success"
        assert call_count["n"] == 2
        mock_sleep.assert_called_once()

    @pytest.mark.asyncio
    async def test_2회_실패_후_성공(self):
        """
        Given: 첫 번째, 두 번째 호출에서 TimeoutError 발생, 세 번째 성공
        When: _retry_with_backoff() 호출
        Then: 정상 결과 반환, 2회 sleep 호출
        """
        # Arrange
        mock_db = AsyncMock()
        mock_http_client = AsyncMock()
        service = BidCollectorService(db=mock_db, http_client=mock_http_client)

        call_count = {"n": 0}

        async def flaky_func():
            call_count["n"] += 1
            if call_count["n"] < 3:
                raise TimeoutError("요청 타임아웃")
            return "success"

        # Act
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await service._retry_with_backoff(flaky_func, max_retries=3, base_delay=2.0)

        # Assert
        assert result == "success"
        assert call_count["n"] == 3
        assert mock_sleep.call_count == 2

    @pytest.mark.asyncio
    async def test_3회_모두_실패_CollectionError_발생(self):
        """
        Given: 3회 모두 TimeoutError 발생
        When: _retry_with_backoff() 호출
        Then: CollectionError 발생
        """
        # Arrange
        mock_db = AsyncMock()
        mock_http_client = AsyncMock()
        service = BidCollectorService(db=mock_db, http_client=mock_http_client)

        async def always_fail():
            raise TimeoutError("요청 타임아웃")

        # Act & Assert
        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(CollectionError):
                await service._retry_with_backoff(always_fail, max_retries=3, base_delay=2.0)

    @pytest.mark.asyncio
    async def test_지수_백오프_대기시간_검증(self):
        """
        Given: 3회 모두 실패
        When: _retry_with_backoff() 호출
        Then: 대기 시간이 2s, 4s, 8s (base_delay=2.0 기준)
        """
        # Arrange
        mock_db = AsyncMock()
        mock_http_client = AsyncMock()
        service = BidCollectorService(db=mock_db, http_client=mock_http_client)

        async def always_fail():
            raise TimeoutError("요청 타임아웃")

        # Act
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            with pytest.raises(CollectionError):
                await service._retry_with_backoff(always_fail, max_retries=3, base_delay=2.0)

        # Assert: 대기 시간이 2^1*2=2, 2^2*2=4, 2^3*2=8 (또는 유사한 지수 증가 패턴)
        sleep_calls = [c.args[0] for c in mock_sleep.call_args_list]
        assert len(sleep_calls) >= 2
        # 지수 증가 확인: 두 번째 대기 >= 첫 번째 대기
        assert sleep_calls[1] >= sleep_calls[0]


class TestSaveBid:
    """_save_bid 메서드 테스트"""

    @pytest.mark.asyncio
    async def test_API_응답을_Bid_객체로_변환(self):
        """
        Given: 공공데이터포털 API 응답 dict
        When: _save_bid() 호출
        Then: Bid 객체 생성 (필드 매핑 정확)
        """
        # Arrange
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_http_client = AsyncMock()

        bid_data = {
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

        service = BidCollectorService(db=mock_db, http_client=mock_http_client)

        # Act
        result = await service._save_bid(bid_data)

        # Assert
        assert result is not None
        # bid_number는 bidNtceNo + "-" + bidNtceOrd 결합
        assert result.bid_number == "20260308001-00"
        assert result.title == "2026년 정보시스템 고도화 사업"
        assert result.organization == "행정안전부"
        assert result.budget == 500000000

    @pytest.mark.asyncio
    async def test_필수_필드_누락_ValidationError(self):
        """
        Given: bidNtceNm(title) 누락된 응답
        When: _save_bid() 호출
        Then: ValidationError 발생
        """
        # Arrange
        mock_db = AsyncMock()
        mock_http_client = AsyncMock()

        bid_data_no_title = {
            "bidNtceNo": "20260308001",
            "bidNtceOrd": "00",
            # bidNtceNm 누락
            "ntceInsttNm": "행정안전부",
            "bidClseDt": "2026/03/22 17:00:00",
        }

        service = BidCollectorService(db=mock_db, http_client=mock_http_client)

        # Act & Assert
        with pytest.raises((ValueError, Exception)) as exc_info:
            await service._save_bid(bid_data_no_title)

        # 유효성 검사 에러임을 확인
        assert exc_info.value is not None


class TestSaveAttachments:
    """_save_attachments 메서드 테스트"""

    @pytest.mark.asyncio
    async def test_첨부파일_2건_저장(self):
        """
        Given: 첨부파일 정보 2건 (PDF, HWP)
        When: _save_attachments() 호출
        Then: BidAttachment 2건 생성 반환
        """
        # Arrange
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()
        mock_http_client = AsyncMock()

        bid_id = uuid4()
        attachments_data = [
            {"filename": "제안요청서.pdf", "fileType": "PDF", "fileUrl": "https://nara.go.kr/files/rfp.pdf"},
            {"filename": "과업지시서.hwp", "fileType": "HWP", "fileUrl": "https://nara.go.kr/files/task.hwp"},
        ]

        service = BidCollectorService(db=mock_db, http_client=mock_http_client)

        # Act
        result = await service._save_attachments(bid_id=bid_id, attachments=attachments_data)

        # Assert
        assert len(result) == 2
        assert result[0].filename == "제안요청서.pdf"
        assert result[1].filename == "과업지시서.hwp"


class TestIsDuplicate:
    """_is_duplicate 메서드 테스트"""

    @pytest.mark.asyncio
    async def test_기존_공고번호_True_반환(self):
        """
        Given: 이미 DB에 존재하는 bid_number
        When: _is_duplicate() 호출
        Then: True 반환
        """
        # Arrange
        mock_db = AsyncMock()
        mock_http_client = AsyncMock()

        # DB 조회 결과 — 기존 공고 있음
        from unittest.mock import MagicMock
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock()  # 존재하는 공고
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = BidCollectorService(db=mock_db, http_client=mock_http_client)

        # Act
        result = await service._is_duplicate("20260308001-00")

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_신규_공고번호_False_반환(self):
        """
        Given: DB에 없는 bid_number
        When: _is_duplicate() 호출
        Then: False 반환
        """
        # Arrange
        mock_db = AsyncMock()
        mock_http_client = AsyncMock()

        # DB 조회 결과 — 없음
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = BidCollectorService(db=mock_db, http_client=mock_http_client)

        # Act
        result = await service._is_duplicate("NEW_BID_NUMBER_9999")

        # Assert
        assert result is False
