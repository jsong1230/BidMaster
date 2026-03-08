"""
공고 API 통합 테스트

test-spec.md 기준:
- GET /api/v1/bids — 공고 목록 조회 (페이지네이션, 필터, 정렬)
- GET /api/v1/bids/{id} — 공고 상세 조회
- GET /api/v1/bids/matched — 매칭 공고 목록
- GET /api/v1/bids/{id}/matches — 공고별 매칭 결과
- POST /api/v1/bids/collect — 수동 수집 트리거

RED 상태: 구현 전이므로 MockApp 엔드포인트가 501 반환 (테스트 FAIL)
"""
import pytest
from uuid import uuid4
from httpx import AsyncClient, ASGITransport

from tests.conftest import MockApp


# ============================================================
# 통합 테스트용 Mock App — bids 라우터 포함
# ============================================================

class BidsMockApp(MockApp):
    """공고 관련 엔드포인트가 포함된 Mock App"""

    def __init__(self):
        super().__init__()
        from fastapi import Request
        from fastapi.responses import JSONResponse

        @self.get("/api/v1/bids")
        async def mock_list_bids(request: Request):
            return JSONResponse(
                status_code=501,
                content={
                    "success": False,
                    "error": {"code": "NOT_IMPLEMENTED", "message": "Not implemented yet"}
                }
            )

        @self.get("/api/v1/bids/matched")
        async def mock_list_matched_bids(request: Request):
            return JSONResponse(
                status_code=501,
                content={
                    "success": False,
                    "error": {"code": "NOT_IMPLEMENTED", "message": "Not implemented yet"}
                }
            )

        @self.get("/api/v1/bids/{bid_id}")
        async def mock_get_bid(bid_id: str, request: Request):
            return JSONResponse(
                status_code=501,
                content={
                    "success": False,
                    "error": {"code": "NOT_IMPLEMENTED", "message": "Not implemented yet"}
                }
            )

        @self.get("/api/v1/bids/{bid_id}/matches")
        async def mock_get_bid_matches(bid_id: str, request: Request):
            return JSONResponse(
                status_code=501,
                content={
                    "success": False,
                    "error": {"code": "NOT_IMPLEMENTED", "message": "Not implemented yet"}
                }
            )

        @self.post("/api/v1/bids/collect")
        async def mock_collect_bids(request: Request):
            return JSONResponse(
                status_code=501,
                content={
                    "success": False,
                    "error": {"code": "NOT_IMPLEMENTED", "message": "Not implemented yet"}
                }
            )


bids_app = BidsMockApp()

SAMPLE_TOKEN = "Bearer test-token-owner"
MEMBER_TOKEN = "Bearer test-token-member"
SAMPLE_BID_ID = str(uuid4())


@pytest.fixture
async def bids_client():
    """공고 API 테스트용 HTTP 클라이언트"""
    transport = ASGITransport(app=bids_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# ============================================================
# GET /api/v1/bids — 공고 목록 조회 테스트
# ============================================================

class TestGetBidsList:
    """GET /api/v1/bids 통합 테스트"""

    @pytest.mark.asyncio
    async def test_공고_목록_조회_기본(self, bids_client):
        """
        Given: 인증 토큰
        When: GET /api/v1/bids
        Then: 200 OK, items 배열, meta 포함
        """
        # Act
        response = await bids_client.get(
            "/api/v1/bids",
            headers={"Authorization": SAMPLE_TOKEN}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "items" in data["data"]
        assert "meta" in data
        assert "page" in data["meta"]
        assert "pageSize" in data["meta"]
        assert "total" in data["meta"]
        assert "totalPages" in data["meta"]

    @pytest.mark.asyncio
    async def test_페이지네이션_page2_pageSize10(self, bids_client):
        """
        Given: page=2, pageSize=10 파라미터
        When: GET /api/v1/bids?page=2&pageSize=10
        Then: 200 OK, meta.page=2, meta.pageSize=10
        """
        # Act
        response = await bids_client.get(
            "/api/v1/bids",
            params={"page": 2, "pageSize": 10},
            headers={"Authorization": SAMPLE_TOKEN}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["meta"]["page"] == 2
        assert data["meta"]["pageSize"] == 10

    @pytest.mark.asyncio
    async def test_status_필터_open(self, bids_client):
        """
        Given: status=open 파라미터
        When: GET /api/v1/bids?status=open
        Then: 200 OK, 모든 items의 status="open"
        """
        # Act
        response = await bids_client.get(
            "/api/v1/bids",
            params={"status": "open"},
            headers={"Authorization": SAMPLE_TOKEN}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        for item in data["data"]["items"]:
            assert item["status"] == "open"

    @pytest.mark.asyncio
    async def test_keyword_검색_정보시스템(self, bids_client):
        """
        Given: keyword=정보시스템 파라미터
        When: GET /api/v1/bids?keyword=정보시스템
        Then: 200 OK, 제목/기관에 키워드 포함
        """
        # Act
        response = await bids_client.get(
            "/api/v1/bids",
            params={"keyword": "정보시스템"},
            headers={"Authorization": SAMPLE_TOKEN}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        for item in data["data"]["items"]:
            assert "정보시스템" in item["title"] or "정보시스템" in item.get("organization", "")

    @pytest.mark.asyncio
    async def test_region_필터_서울(self, bids_client):
        """
        Given: region=서울 파라미터
        When: GET /api/v1/bids?region=서울
        Then: 200 OK, 모든 items의 region="서울"
        """
        # Act
        response = await bids_client.get(
            "/api/v1/bids",
            params={"region": "서울"},
            headers={"Authorization": SAMPLE_TOKEN}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        for item in data["data"]["items"]:
            assert item.get("region") == "서울"

    @pytest.mark.asyncio
    async def test_budget_범위_필터(self, bids_client):
        """
        Given: minBudget=100000000, maxBudget=500000000
        When: GET /api/v1/bids?minBudget=100000000&maxBudget=500000000
        Then: 200 OK, 예산 범위 내 공고만 반환
        """
        # Act
        response = await bids_client.get(
            "/api/v1/bids",
            params={"minBudget": 100000000, "maxBudget": 500000000},
            headers={"Authorization": SAMPLE_TOKEN}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        for item in data["data"]["items"]:
            if item.get("budget") is not None:
                assert 100000000 <= item["budget"] <= 500000000

    @pytest.mark.asyncio
    async def test_날짜_범위_필터(self, bids_client):
        """
        Given: startDate=2026-03-01, endDate=2026-03-31
        When: GET /api/v1/bids?startDate=2026-03-01&endDate=2026-03-31
        Then: 200 OK, 해당 기간 공고 반환
        """
        # Act
        response = await bids_client.get(
            "/api/v1/bids",
            params={"startDate": "2026-03-01", "endDate": "2026-03-31"},
            headers={"Authorization": SAMPLE_TOKEN}
        )

        # Assert
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_정렬_budget_내림차순(self, bids_client):
        """
        Given: sortBy=budget, sortOrder=desc
        When: GET /api/v1/bids?sortBy=budget&sortOrder=desc
        Then: 200 OK, budget 내림차순 정렬
        """
        # Act
        response = await bids_client.get(
            "/api/v1/bids",
            params={"sortBy": "budget", "sortOrder": "desc"},
            headers={"Authorization": SAMPLE_TOKEN}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        items = data["data"]["items"]
        if len(items) >= 2:
            budgets = [item["budget"] for item in items if item.get("budget") is not None]
            assert budgets == sorted(budgets, reverse=True)

    @pytest.mark.asyncio
    async def test_인증_없음_401_AUTH_002(self, bids_client):
        """
        Given: 인증 토큰 없음
        When: GET /api/v1/bids
        Then: 401 Unauthorized, AUTH_002
        """
        # Act
        response = await bids_client.get("/api/v1/bids")

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "AUTH_002"

    @pytest.mark.asyncio
    async def test_잘못된_status_값_400_VALIDATION_001(self, bids_client):
        """
        Given: 잘못된 status 값 (예: "invalid_status")
        When: GET /api/v1/bids?status=invalid_status
        Then: 400, VALIDATION_001
        """
        # Act
        response = await bids_client.get(
            "/api/v1/bids",
            params={"status": "invalid_status"},
            headers={"Authorization": SAMPLE_TOKEN}
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_001"

    @pytest.mark.asyncio
    async def test_pageSize_100_초과시_100으로_제한(self, bids_client):
        """
        Given: pageSize=200 (최대값 100 초과)
        When: GET /api/v1/bids?pageSize=200
        Then: 200 OK, meta.pageSize=100 (자동 제한)
        """
        # Act
        response = await bids_client.get(
            "/api/v1/bids",
            params={"pageSize": 200},
            headers={"Authorization": SAMPLE_TOKEN}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["meta"]["pageSize"] <= 100


# ============================================================
# GET /api/v1/bids/{id} — 공고 상세 조회 테스트
# ============================================================

class TestGetBidDetail:
    """GET /api/v1/bids/{id} 통합 테스트"""

    @pytest.mark.asyncio
    async def test_공고_상세_조회_성공(self, bids_client):
        """
        Given: 존재하는 bid_id
        When: GET /api/v1/bids/{id}
        Then: 200 OK, 공고 상세 + attachments 반환
        """
        # Act
        response = await bids_client.get(
            f"/api/v1/bids/{SAMPLE_BID_ID}",
            headers={"Authorization": SAMPLE_TOKEN}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "id" in data["data"]
        assert "bidNumber" in data["data"]
        assert "title" in data["data"]
        assert "organization" in data["data"]
        assert "attachments" in data["data"]

    @pytest.mark.asyncio
    async def test_존재하지_않는_공고_404_BID_001(self, bids_client):
        """
        Given: DB에 없는 bid_id
        When: GET /api/v1/bids/{id}
        Then: 404 Not Found, BID_001
        """
        non_existent_id = str(uuid4())

        # Act
        response = await bids_client.get(
            f"/api/v1/bids/{non_existent_id}",
            headers={"Authorization": SAMPLE_TOKEN}
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "BID_001"

    @pytest.mark.asyncio
    async def test_UUID_아닌_bid_id_422(self, bids_client):
        """
        Given: UUID 형식이 아닌 bid_id
        When: GET /api/v1/bids/not-a-uuid
        Then: 422 Unprocessable Entity (FastAPI 자동 처리)
        """
        # Act
        response = await bids_client.get(
            "/api/v1/bids/not-a-valid-uuid",
            headers={"Authorization": SAMPLE_TOKEN}
        )

        # Assert
        assert response.status_code == 422


# ============================================================
# GET /api/v1/bids/{id}/matches — 공고별 매칭 결과 조회 테스트
# ============================================================

class TestGetBidMatches:
    """GET /api/v1/bids/{id}/matches 통합 테스트"""

    @pytest.mark.asyncio
    async def test_매칭_결과_조회_기존_결과(self, bids_client):
        """
        Given: 이미 매칭 분석된 bid_id
        When: GET /api/v1/bids/{id}/matches
        Then: 200 OK, 매칭 점수 포함 응답
        """
        # Act
        response = await bids_client.get(
            f"/api/v1/bids/{SAMPLE_BID_ID}/matches",
            headers={"Authorization": SAMPLE_TOKEN}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "totalScore" in data["data"]
        assert "recommendation" in data["data"]
        assert "suitabilityScore" in data["data"]

    @pytest.mark.asyncio
    async def test_매칭_결과_조회_신규_분석(self, bids_client):
        """
        Given: 매칭 분석이 없는 bid_id (lazy evaluation)
        When: GET /api/v1/bids/{id}/matches
        Then: 200 OK, 새로 분석된 매칭 결과
        """
        new_bid_id = str(uuid4())

        # Act
        response = await bids_client.get(
            f"/api/v1/bids/{new_bid_id}/matches",
            headers={"Authorization": SAMPLE_TOKEN}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_회사_미등록_사용자_404_COMPANY_001(self, bids_client):
        """
        Given: company_id=NULL인 사용자 (회사 미소속)
        When: GET /api/v1/bids/{id}/matches
        Then: 404 Not Found, COMPANY_001
        """
        # Act — company 없는 사용자 토큰으로 요청
        response = await bids_client.get(
            f"/api/v1/bids/{SAMPLE_BID_ID}/matches",
            headers={"Authorization": "Bearer test-token-no-company"}
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "COMPANY_001"

    @pytest.mark.asyncio
    async def test_존재하지_않는_공고_매칭_404_BID_001(self, bids_client):
        """
        Given: 존재하지 않는 bid_id로 매칭 조회
        When: GET /api/v1/bids/{id}/matches
        Then: 404 Not Found, BID_001
        """
        non_existent_id = str(uuid4())

        # Act
        response = await bids_client.get(
            f"/api/v1/bids/{non_existent_id}/matches",
            headers={"Authorization": SAMPLE_TOKEN}
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "BID_001"


# ============================================================
# GET /api/v1/bids/matched — 매칭 공고 목록 조회 테스트
# ============================================================

class TestGetMatchedBids:
    """GET /api/v1/bids/matched 통합 테스트"""

    @pytest.mark.asyncio
    async def test_매칭_공고_목록_조회_기본(self, bids_client):
        """
        Given: 인증 토큰, 회사 등록 사용자
        When: GET /api/v1/bids/matched
        Then: 200 OK, totalScore 내림차순 정렬
        """
        # Act
        response = await bids_client.get(
            "/api/v1/bids/matched",
            headers={"Authorization": SAMPLE_TOKEN}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "items" in data["data"]
        items = data["data"]["items"]
        if len(items) >= 2:
            scores = [item["totalScore"] for item in items]
            assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_minScore_70_필터(self, bids_client):
        """
        Given: minScore=70 파라미터
        When: GET /api/v1/bids/matched?minScore=70
        Then: 200 OK, 모든 totalScore >= 70
        """
        # Act
        response = await bids_client.get(
            "/api/v1/bids/matched",
            params={"minScore": 70},
            headers={"Authorization": SAMPLE_TOKEN}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        for item in data["data"]["items"]:
            assert item["totalScore"] >= 70

    @pytest.mark.asyncio
    async def test_recommendation_recommended_필터(self, bids_client):
        """
        Given: recommendation=recommended 파라미터
        When: GET /api/v1/bids/matched?recommendation=recommended
        Then: 200 OK, 모든 recommendation="recommended"
        """
        # Act
        response = await bids_client.get(
            "/api/v1/bids/matched",
            params={"recommendation": "recommended"},
            headers={"Authorization": SAMPLE_TOKEN}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        for item in data["data"]["items"]:
            assert item["recommendation"] == "recommended"

    @pytest.mark.asyncio
    async def test_회사_미등록_사용자_404_COMPANY_001(self, bids_client):
        """
        Given: company_id=NULL인 사용자
        When: GET /api/v1/bids/matched
        Then: 404, COMPANY_001
        """
        # Act
        response = await bids_client.get(
            "/api/v1/bids/matched",
            headers={"Authorization": "Bearer test-token-no-company"}
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "COMPANY_001"


# ============================================================
# POST /api/v1/bids/collect — 수동 수집 트리거 테스트
# ============================================================

class TestPostBidsCollect:
    """POST /api/v1/bids/collect 통합 테스트"""

    @pytest.mark.asyncio
    async def test_수동_수집_owner_권한_202(self, bids_client):
        """
        Given: owner 역할 토큰
        When: POST /api/v1/bids/collect
        Then: 202 Accepted, 수집 시작 메시지
        """
        # Act
        response = await bids_client.post(
            "/api/v1/bids/collect",
            headers={"Authorization": SAMPLE_TOKEN}
        )

        # Assert
        assert response.status_code == 202
        data = response.json()
        assert data["success"] is True
        assert "message" in data["data"]
        assert "triggeredAt" in data["data"]

    @pytest.mark.asyncio
    async def test_수동_수집_권한_없음_403_PERMISSION_001(self, bids_client):
        """
        Given: member 역할 토큰 (owner 아님)
        When: POST /api/v1/bids/collect
        Then: 403 Forbidden, PERMISSION_001
        """
        # Act
        response = await bids_client.post(
            "/api/v1/bids/collect",
            headers={"Authorization": MEMBER_TOKEN}
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "PERMISSION_001"

    @pytest.mark.asyncio
    async def test_수집_이미_진행중_409_BID_004(self, bids_client):
        """
        Given: Redis 잠금 상태 — 다른 수집이 진행 중
        When: POST /api/v1/bids/collect
        Then: 409 Conflict, BID_004
        """
        # Act — 두 번째 요청 (잠금 상태에서)
        response = await bids_client.post(
            "/api/v1/bids/collect",
            headers={"Authorization": SAMPLE_TOKEN},
            params={"_simulate_lock": "true"}  # 테스트용 잠금 시뮬레이션
        )

        # Assert
        assert response.status_code == 409
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "BID_004"

    @pytest.mark.asyncio
    async def test_인증_없음_401(self, bids_client):
        """
        Given: 토큰 없음
        When: POST /api/v1/bids/collect
        Then: 401 Unauthorized
        """
        # Act
        response = await bids_client.post("/api/v1/bids/collect")

        # Assert
        assert response.status_code == 401
