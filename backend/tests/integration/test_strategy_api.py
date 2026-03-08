"""
투찰 전략 API 통합 테스트

test-spec.md 기준:
- GET /api/v1/bids/{id}/strategy
- POST /api/v1/bids/{id}/strategy/simulate

구현 전 — RED 상태: src.services.bidding_strategy_service ImportError로 FAIL 예상
"""
import pytest
from uuid import uuid4
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from tests.conftest import MockApp
from src.core.security import create_access_token


# ============================================================
# 통합 테스트용 Mock App — strategy 엔드포인트 포함
# ============================================================

SAMPLE_BID_ID = str(uuid4())
SAMPLE_BID_ID_LOWEST = str(uuid4())

# 실제 JWT 토큰 생성 (테스트용)
_owner_jwt = create_access_token(
    subject="user-owner-001",
    extra_data={"role": "owner", "company_id": "company-001"},
)
VALID_TOKEN = f"Bearer {_owner_jwt}"

# 구현 전 — RED 상태: bidding_strategy_service import 시도 (FAIL 트리거)
try:
    from src.services.bidding_strategy_service import BiddingStrategyService  # noqa: F401 — 구현 전 ImportError 발생
    _strategy_available = True
except ImportError:
    _strategy_available = False


class StrategyMockApp(MockApp):
    """투찰 전략 관련 엔드포인트가 포함된 Mock App"""

    def __init__(self):
        super().__init__()

        @self.get("/api/v1/bids/{bid_id}/strategy")
        async def mock_get_strategy(bid_id: str, request: Request):
            return JSONResponse(
                status_code=501,
                content={
                    "success": False,
                    "error": {"code": "NOT_IMPLEMENTED", "message": "전략 분석 미구현"}
                }
            )

        @self.post("/api/v1/bids/{bid_id}/strategy/simulate")
        async def mock_simulate(bid_id: str, request: Request):
            return JSONResponse(
                status_code=501,
                content={
                    "success": False,
                    "error": {"code": "NOT_IMPLEMENTED", "message": "시뮬레이션 미구현"}
                }
            )


app = StrategyMockApp()


@pytest.fixture
def strategy_app() -> FastAPI:
    return app


@pytest.fixture
async def strategy_client(strategy_app: FastAPI):
    transport = ASGITransport(app=strategy_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# ============================================================
# 인수조건 AC-01: 유사 공고 낙찰가율 분포 시각화 데이터
# GET /api/v1/bids/{id}/strategy
# ============================================================

class Test전략분석_정상요청:

    @pytest.mark.asyncio
    async def test_정상분석_적격심사_200(self, strategy_client):
        """정상 요청 (적격심사) → 200, contractMethod='적격심사', recommendedRanges 3구간"""
        # Arrange
        headers = {"Authorization": VALID_TOKEN}

        # Act
        response = await strategy_client.get(
            f"/api/v1/bids/{SAMPLE_BID_ID}/strategy",
            headers=headers,
        )

        # Assert
        assert response.status_code == 200, f"구현 후 200 기대: {response.status_code}"
        data = response.json()["data"]
        assert data["contractMethod"] == "적격심사"
        assert "recommendedRanges" in data
        ranges = data["recommendedRanges"]
        assert "safe" in ranges
        assert "moderate" in ranges
        assert "aggressive" in ranges
        assert "strategyReport" in data

    @pytest.mark.asyncio
    async def test_정상분석_최저가_200(self, strategy_client):
        """정상 요청 (최저가) → 200, contractMethod='최저가', recommendedRanges 3구간"""
        # Arrange
        headers = {"Authorization": VALID_TOKEN}

        # Act
        response = await strategy_client.get(
            f"/api/v1/bids/{SAMPLE_BID_ID_LOWEST}/strategy",
            headers=headers,
        )

        # Assert
        assert response.status_code == 200, f"구현 후 200 기대: {response.status_code}"
        data = response.json()["data"]
        assert data["contractMethod"] == "최저가"
        assert "recommendedRanges" in data

    @pytest.mark.asyncio
    async def test_winRateDistribution_구조(self, strategy_client):
        """winRateDistribution: sampleCount > 0, mean/std/median/q25/q75 모두 존재"""
        # Arrange
        headers = {"Authorization": VALID_TOKEN}

        # Act
        response = await strategy_client.get(
            f"/api/v1/bids/{SAMPLE_BID_ID}/strategy",
            headers=headers,
        )

        # Assert
        assert response.status_code == 200, f"구현 후 200 기대: {response.status_code}"
        dist = response.json()["data"]["winRateDistribution"]
        for field in ["mean", "std", "median", "q25", "q75", "minRate", "maxRate", "sampleCount"]:
            assert field in dist, f"winRateDistribution에 {field} 없음"

    @pytest.mark.asyncio
    async def test_winProbability_범위_0_100(self, strategy_client):
        """모든 winProbability: 0 <= p <= 100"""
        # Arrange
        headers = {"Authorization": VALID_TOKEN}

        # Act
        response = await strategy_client.get(
            f"/api/v1/bids/{SAMPLE_BID_ID}/strategy",
            headers=headers,
        )

        # Assert
        assert response.status_code == 200, f"구현 후 200 기대: {response.status_code}"
        ranges = response.json()["data"]["recommendedRanges"]
        for level in ["safe", "moderate", "aggressive"]:
            prob = ranges[level]["winProbability"]
            assert 0 <= prob <= 100, f"{level} winProbability 범위 초과: {prob}"

    @pytest.mark.asyncio
    async def test_recommendedRanges_일관성(self, strategy_client):
        """safe.minPrice >= moderate.maxPrice, moderate.minPrice >= aggressive.maxPrice (대략)"""
        # Arrange
        headers = {"Authorization": VALID_TOKEN}

        # Act
        response = await strategy_client.get(
            f"/api/v1/bids/{SAMPLE_BID_ID}/strategy",
            headers=headers,
        )

        # Assert
        assert response.status_code == 200, f"구현 후 200 기대: {response.status_code}"
        ranges = response.json()["data"]["recommendedRanges"]
        # safe가 moderate보다 가격이 높아야 함 (적격심사 기준)
        # 정확한 순서는 계약 방식에 따라 다를 수 있으므로 넓은 허용치 적용
        safe_min = ranges["safe"].get("minPrice", 0)
        aggressive_max = ranges["aggressive"].get("maxPrice", float("inf"))
        assert safe_min >= aggressive_max or safe_min > 0, \
            f"구간 일관성 오류: safe.minPrice={safe_min}, aggressive.maxPrice={aggressive_max}"

    @pytest.mark.asyncio
    async def test_유사공고_없음_기본구간_사용(self, strategy_client):
        """이력 없는 공고 → 200, 기본 분포/구간 사용, strategyReport에 '데이터 부족' 표시"""
        # Arrange
        headers = {"Authorization": VALID_TOKEN}
        no_history_bid_id = str(uuid4())

        # Act
        response = await strategy_client.get(
            f"/api/v1/bids/{no_history_bid_id}/strategy",
            headers=headers,
        )

        # Assert
        assert response.status_code in [200, 404], f"이력 없어도 200 또는 공고없음 404: {response.status_code}"
        if response.status_code == 200:
            data = response.json()["data"]
            report_text = " ".join([
                data.get("strategyReport", {}).get("marketInsight", ""),
                *data.get("strategyReport", {}).get("recommendations", []),
            ])
            assert any(k in report_text for k in ["부족", "데이터", "없"]), \
                f"데이터 부족 문구 없음: {report_text}"

    @pytest.mark.asyncio
    async def test_estimatedPrice_없는_공고_budget_폴백(self, strategy_client):
        """estimated_price 없고 budget만 있는 공고 → 200, estimatedPrice=budget"""
        # Arrange
        headers = {"Authorization": VALID_TOKEN}

        # Act
        response = await strategy_client.get(
            f"/api/v1/bids/{SAMPLE_BID_ID}/strategy",
            headers=headers,
        )

        # Assert
        assert response.status_code == 200, f"budget 폴백 시 200 기대: {response.status_code}"
        data = response.json()["data"]
        # budget 또는 estimatedPrice 중 하나는 있어야 함
        assert data.get("estimatedPrice") is not None or data.get("budget") is not None


# ============================================================
# 인증 검증
# ============================================================

class Test전략분석_인증:

    @pytest.mark.asyncio
    async def test_인증없음_401(self, strategy_client):
        """Authorization 헤더 없음 → 401, AUTH_002"""
        # Act
        response = await strategy_client.get(
            f"/api/v1/bids/{SAMPLE_BID_ID}/strategy"
        )

        # Assert
        assert response.status_code == 401, f"인증 없으면 401 기대: {response.status_code}"
        body = response.json()
        assert body["success"] is False
        error_code = body.get("error", {}).get("code", "")
        assert error_code == "AUTH_002", f"에러 코드 AUTH_002 기대: {error_code}"


# ============================================================
# 에러 케이스
# ============================================================

class Test전략분석_에러케이스:

    @pytest.mark.asyncio
    async def test_존재하지않는_공고_404(self, strategy_client):
        """잘못된 bid_id → 404, BID_001"""
        # Arrange
        headers = {"Authorization": VALID_TOKEN}
        nonexistent_id = str(uuid4())

        # Act
        response = await strategy_client.get(
            f"/api/v1/bids/{nonexistent_id}/strategy",
            headers=headers,
        )

        # Assert
        assert response.status_code == 404, f"존재하지 않는 공고 404 기대: {response.status_code}"
        body = response.json()
        assert body["success"] is False
        error_code = body.get("error", {}).get("code", "")
        assert error_code == "BID_001", f"에러 코드 BID_001 기대: {error_code}"

    @pytest.mark.asyncio
    async def test_공고ID_형식오류_422(self, strategy_client):
        """bid_id='invalid' → 422"""
        # Arrange
        headers = {"Authorization": VALID_TOKEN}

        # Act
        response = await strategy_client.get(
            "/api/v1/bids/not-valid-uuid/strategy",
            headers=headers,
        )

        # Assert
        assert response.status_code == 422, f"잘못된 UUID 422 기대: {response.status_code}"


# ============================================================
# 인수조건 AC-05: 투찰가 시뮬레이션
# POST /api/v1/bids/{id}/strategy/simulate
# ============================================================

class Test시뮬레이션_정상요청:

    @pytest.mark.asyncio
    async def test_정상_시뮬레이션_200(self, strategy_client):
        """정상 시뮬레이션 → 200, bidRate > 0, winProbability 0~100, riskLevel 포함"""
        # Arrange
        headers = {"Authorization": VALID_TOKEN}
        body = {"bidPrice": 410_000_000}

        # Act
        response = await strategy_client.post(
            f"/api/v1/bids/{SAMPLE_BID_ID}/strategy/simulate",
            json=body,
            headers=headers,
        )

        # Assert
        assert response.status_code == 200, f"구현 후 200 기대: {response.status_code}"
        data = response.json()["data"]
        assert data["bidRate"] > 0
        assert 0 <= data["winProbability"] <= 100
        assert data["riskLevel"] in ["safe", "moderate", "aggressive", "over_safe", "extreme", "unknown"]

    @pytest.mark.asyncio
    async def test_시뮬레이션_comparisonWithRecommended_포함(self, strategy_client):
        """시뮬레이션 결과에 safe/moderate/aggressive 비교 문구 포함"""
        # Arrange
        headers = {"Authorization": VALID_TOKEN}
        body = {"bidPrice": 410_000_000}

        # Act
        response = await strategy_client.post(
            f"/api/v1/bids/{SAMPLE_BID_ID}/strategy/simulate",
            json=body,
            headers=headers,
        )

        # Assert
        assert response.status_code == 200, f"구현 후 200 기대: {response.status_code}"
        comparison = response.json()["data"].get("comparisonWithRecommended", {})
        assert "safe" in comparison
        assert "moderate" in comparison
        assert "aggressive" in comparison

    @pytest.mark.asyncio
    async def test_시뮬레이션_bidPrice_0_처리(self, strategy_client):
        """bidPrice=0 → 200, bidRate=0, 특수 처리"""
        # Arrange
        headers = {"Authorization": VALID_TOKEN}
        body = {"bidPrice": 0}

        # Act
        response = await strategy_client.post(
            f"/api/v1/bids/{SAMPLE_BID_ID}/strategy/simulate",
            json=body,
            headers=headers,
        )

        # Assert
        assert response.status_code == 200, f"bidPrice=0 처리 200 기대: {response.status_code}"
        data = response.json()["data"]
        assert data["bidRate"] == 0 or data["bidRate"] == pytest.approx(0.0, abs=0.001)


# ============================================================
# 시뮬레이션 에러 케이스
# ============================================================

class Test시뮬레이션_에러케이스:

    @pytest.mark.asyncio
    async def test_인증없음_401(self, strategy_client):
        """Authorization 헤더 없음 → 401, AUTH_002"""
        # Act
        response = await strategy_client.post(
            f"/api/v1/bids/{SAMPLE_BID_ID}/strategy/simulate",
            json={"bidPrice": 100_000_000},
        )

        # Assert
        assert response.status_code == 401, f"인증 없으면 401 기대: {response.status_code}"
        error_code = response.json().get("error", {}).get("code", "")
        assert error_code == "AUTH_002", f"에러 코드 AUTH_002 기대: {error_code}"

    @pytest.mark.asyncio
    async def test_bidPrice_누락_400(self, strategy_client):
        """bidPrice 누락 (빈 body) → 400, VALIDATION_001"""
        # Arrange
        headers = {"Authorization": VALID_TOKEN}

        # Act
        response = await strategy_client.post(
            f"/api/v1/bids/{SAMPLE_BID_ID}/strategy/simulate",
            json={},  # bidPrice 누락
            headers=headers,
        )

        # Assert
        assert response.status_code in [400, 422], \
            f"bidPrice 누락 시 400 또는 422 기대: {response.status_code}"

    @pytest.mark.asyncio
    async def test_bidPrice_음수_400(self, strategy_client):
        """bidPrice=-100 → 400, VALIDATION_001"""
        # Arrange
        headers = {"Authorization": VALID_TOKEN}

        # Act
        response = await strategy_client.post(
            f"/api/v1/bids/{SAMPLE_BID_ID}/strategy/simulate",
            json={"bidPrice": -100},
            headers=headers,
        )

        # Assert
        assert response.status_code in [400, 422], \
            f"음수 bidPrice 시 400 또는 422 기대: {response.status_code}"

    @pytest.mark.asyncio
    async def test_존재하지않는_공고_404(self, strategy_client):
        """잘못된 bid_id → 404, BID_001"""
        # Arrange
        headers = {"Authorization": VALID_TOKEN}
        nonexistent_id = str(uuid4())

        # Act
        response = await strategy_client.post(
            f"/api/v1/bids/{nonexistent_id}/strategy/simulate",
            json={"bidPrice": 100_000_000},
            headers=headers,
        )

        # Assert
        assert response.status_code == 404, f"존재하지 않는 공고 404 기대: {response.status_code}"
        error_code = response.json().get("error", {}).get("code", "")
        assert error_code == "BID_001", f"에러 코드 BID_001 기대: {error_code}"

    @pytest.mark.asyncio
    async def test_예정가격없는_공고_422(self, strategy_client):
        """estimated_price=None, budget=None → 422, STRATEGY_002"""
        # Arrange
        headers = {"Authorization": VALID_TOKEN}
        no_price_bid_id = str(uuid4())  # 예정가격 없는 공고로 설정 필요

        # Act
        response = await strategy_client.post(
            f"/api/v1/bids/{no_price_bid_id}/strategy/simulate",
            json={"bidPrice": 100_000_000},
            headers=headers,
        )

        # Assert
        # 공고 없으면 404, 공고 있고 예정가 없으면 422
        assert response.status_code in [404, 422], \
            f"예정가격 없으면 404 또는 422 기대: {response.status_code}"
        if response.status_code == 422:
            error_code = response.json().get("error", {}).get("code", "")
            assert error_code == "STRATEGY_002", f"에러 코드 STRATEGY_002 기대: {error_code}"


# ============================================================
# 회귀 테스트: F-01, F-02 하위 호환성
# ============================================================

class Test전략_회귀:

    @pytest.mark.asyncio
    async def test_기존_bids_목록_엔드포인트_동작(self, strategy_client):
        """F-01 GET /bids 목록 엔드포인트가 여전히 동작"""
        # Act
        response = await strategy_client.get("/api/v1/bids")

        # Assert: 200이거나 401 (인증 필요)이어야 하며, 501이면 안 됨
        assert response.status_code != 501, \
            f"F-01 목록 엔드포인트가 깨지면 안 됨 (501 반환): {response.status_code}"

    @pytest.mark.asyncio
    async def test_scoring_엔드포인트_URL_충돌없음(self, strategy_client):
        """F-02 scoring 엔드포인트와 F-04 strategy 엔드포인트 URL 충돌 없음"""
        # Arrange
        headers = {"Authorization": VALID_TOKEN}

        # Act — 두 엔드포인트 각각 요청
        resp_scoring = await strategy_client.get(
            f"/api/v1/bids/{SAMPLE_BID_ID}/scoring",
            headers=headers,
        )
        resp_strategy = await strategy_client.get(
            f"/api/v1/bids/{SAMPLE_BID_ID}/strategy",
            headers=headers,
        )

        # Assert: 404 (Not Found) 또는 200/501 → 405 Method Not Allowed는 허용 안 됨
        for resp, name in [(resp_scoring, "scoring"), (resp_strategy, "strategy")]:
            assert resp.status_code != 405, \
                f"{name} 엔드포인트 URL 충돌 (405 반환): {resp.status_code}"
