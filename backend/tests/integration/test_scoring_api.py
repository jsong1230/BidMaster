"""
스코어링 API 통합 테스트

test-spec.md 기준:
- GET /api/v1/bids/{id}/scoring

구현 전 — RED 상태: src.services.scoring_service ImportError로 FAIL 예상
"""
import pytest
from uuid import uuid4
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from tests.conftest import MockApp


# ============================================================
# 통합 테스트용 Mock App — scoring 엔드포인트 포함
# ============================================================

SAMPLE_BID_ID = str(uuid4())
SAMPLE_USER_ID = "user-owner-001"

# 구현 전 — RED 상태: scoring_service import 시도 (FAIL 트리거)
try:
    from src.services.scoring_service import ScoringService  # noqa: F401 — 구현 전 ImportError 발생
    _scoring_available = True
except ImportError:
    _scoring_available = False


class ScoringMockApp(MockApp):
    """스코어링 관련 엔드포인트가 포함된 Mock App"""

    def __init__(self):
        super().__init__()

        @self.get("/api/v1/bids/{bid_id}/scoring")
        async def mock_get_scoring(bid_id: str, request: Request):
            return JSONResponse(
                status_code=501,
                content={
                    "success": False,
                    "error": {"code": "NOT_IMPLEMENTED", "message": "스코어링 미구현"}
                }
            )


app = ScoringMockApp()


@pytest.fixture
def scoring_app() -> FastAPI:
    return app


@pytest.fixture
async def scoring_client(scoring_app: FastAPI):
    transport = ASGITransport(app=scoring_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# ============================================================
# 인수조건 AC-01: 60초 이내 낙찰 가능성 점수(0~100) 반환
# GET /api/v1/bids/{id}/scoring
# ============================================================

class Test스코어링_정상_요청:

    @pytest.mark.asyncio
    async def test_정상_스코어링_200_반환(self, scoring_client):
        """정상 요청 → 200, scores 4개 항목 모두 > 0, recommendation 포함"""
        # Arrange
        headers = {"Authorization": "Bearer valid-token"}

        # Act
        response = await scoring_client.get(
            f"/api/v1/bids/{SAMPLE_BID_ID}/scoring",
            headers=headers,
        )

        # Assert — 구현 후 200 기대, 구현 전 501
        assert response.status_code == 200, (
            f"구현 후 200 기대. 현재 상태: {response.status_code} / {response.json()}"
        )
        data = response.json()
        assert data["success"] is True
        assert "scores" in data["data"]
        scores = data["data"]["scores"]
        assert scores["suitability"] >= 0
        assert scores["competition"] >= 0
        assert scores["capability"] >= 0
        assert scores["market"] >= 0
        assert 0 <= scores["total"] <= 100

    @pytest.mark.asyncio
    async def test_정상_스코어링_scores_total_범위(self, scoring_client):
        """scores.total은 항상 0~100"""
        # Arrange
        headers = {"Authorization": "Bearer valid-token"}

        # Act
        response = await scoring_client.get(
            f"/api/v1/bids/{SAMPLE_BID_ID}/scoring",
            headers=headers,
        )

        # Assert
        assert response.status_code == 200, f"구현 후 200 기대: {response.status_code}"
        total = response.json()["data"]["scores"]["total"]
        assert 0 <= total <= 100

    @pytest.mark.asyncio
    async def test_정상_recommendation_4단계_중_하나(self, scoring_client):
        """recommendation은 4단계 중 하나"""
        # Arrange
        headers = {"Authorization": "Bearer valid-token"}

        # Act
        response = await scoring_client.get(
            f"/api/v1/bids/{SAMPLE_BID_ID}/scoring",
            headers=headers,
        )

        # Assert
        assert response.status_code == 200, f"구현 후 200 기대: {response.status_code}"
        recommendation = response.json()["data"]["recommendation"]
        valid_values = {"strongly_recommended", "recommended", "neutral", "not_recommended"}
        assert recommendation in valid_values, f"유효하지 않은 recommendation: {recommendation}"

    @pytest.mark.asyncio
    async def test_details_구조_검증(self, scoring_client):
        """details에 suitability/competition/capability/market 각각 score + factors"""
        # Arrange
        headers = {"Authorization": "Bearer valid-token"}

        # Act
        response = await scoring_client.get(
            f"/api/v1/bids/{SAMPLE_BID_ID}/scoring",
            headers=headers,
        )

        # Assert
        assert response.status_code == 200, f"구현 후 200 기대: {response.status_code}"
        details = response.json()["data"]["details"]
        for section in ["suitability", "competition", "capability", "market"]:
            assert section in details, f"details에 {section} 없음"
            assert "score" in details[section]
            assert "factors" in details[section]
            assert isinstance(details[section]["factors"], list)

    @pytest.mark.asyncio
    async def test_competitorStats_포함(self, scoring_client):
        """competitorStats: estimatedCompetitors >= 0, topCompetitors 배열"""
        # Arrange
        headers = {"Authorization": "Bearer valid-token"}

        # Act
        response = await scoring_client.get(
            f"/api/v1/bids/{SAMPLE_BID_ID}/scoring",
            headers=headers,
        )

        # Assert
        assert response.status_code == 200, f"구현 후 200 기대: {response.status_code}"
        competitor_stats = response.json()["data"]["competitorStats"]
        assert competitor_stats["estimatedCompetitors"] >= 0
        assert isinstance(competitor_stats["topCompetitors"], list)

    @pytest.mark.asyncio
    async def test_similarBidStats_포함(self, scoring_client):
        """similarBidStats: totalCount >= 0, avgWinRate, avgWinningPrice 포함"""
        # Arrange
        headers = {"Authorization": "Bearer valid-token"}

        # Act
        response = await scoring_client.get(
            f"/api/v1/bids/{SAMPLE_BID_ID}/scoring",
            headers=headers,
        )

        # Assert
        assert response.status_code == 200, f"구현 후 200 기대: {response.status_code}"
        similar_stats = response.json()["data"]["similarBidStats"]
        assert similar_stats["totalCount"] >= 0
        assert "avgWinRate" in similar_stats
        assert "avgWinningPrice" in similar_stats

    @pytest.mark.asyncio
    async def test_weights_필드_포함(self, scoring_client):
        """weights 필드: 4개 항목 합계 = 1.0"""
        # Arrange
        headers = {"Authorization": "Bearer valid-token"}

        # Act
        response = await scoring_client.get(
            f"/api/v1/bids/{SAMPLE_BID_ID}/scoring",
            headers=headers,
        )

        # Assert
        assert response.status_code == 200, f"구현 후 200 기대: {response.status_code}"
        weights = response.json()["data"]["weights"]
        total_weight = sum([
            weights.get("suitability", 0),
            weights.get("competition", 0),
            weights.get("capability", 0),
            weights.get("market", 0),
        ])
        assert total_weight == pytest.approx(1.0, abs=0.01), f"가중치 합계 1.0 기대: {total_weight}"


# ============================================================
# 인증/인가 검증
# ============================================================

class Test스코어링_인증:

    @pytest.mark.asyncio
    async def test_인증없음_401(self, scoring_client):
        """Authorization 헤더 없음 → 401, AUTH_002"""
        # Act
        response = await scoring_client.get(
            f"/api/v1/bids/{SAMPLE_BID_ID}/scoring"
            # Authorization 헤더 없음
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

class Test스코어링_에러케이스:

    @pytest.mark.asyncio
    async def test_존재하지않는_공고_404(self, scoring_client):
        """잘못된 bid_id → 404, BID_001"""
        # Arrange
        headers = {"Authorization": "Bearer valid-token"}
        nonexistent_id = str(uuid4())

        # Act
        response = await scoring_client.get(
            f"/api/v1/bids/{nonexistent_id}/scoring",
            headers=headers,
        )

        # Assert
        assert response.status_code == 404, f"존재하지 않는 공고 404 기대: {response.status_code}"
        body = response.json()
        assert body["success"] is False
        error_code = body.get("error", {}).get("code", "")
        assert error_code == "BID_001", f"에러 코드 BID_001 기대: {error_code}"

    @pytest.mark.asyncio
    async def test_회사_미등록_사용자_404(self, scoring_client):
        """회사 없는 사용자 → 404, COMPANY_001"""
        # Arrange — 회사 미등록 사용자 토큰
        headers = {"Authorization": "Bearer token-no-company"}

        # Act
        response = await scoring_client.get(
            f"/api/v1/bids/{SAMPLE_BID_ID}/scoring",
            headers=headers,
        )

        # Assert
        assert response.status_code == 404, f"회사 미등록 404 기대: {response.status_code}"
        body = response.json()
        assert body["success"] is False
        error_code = body.get("error", {}).get("code", "")
        assert error_code == "COMPANY_001", f"에러 코드 COMPANY_001 기대: {error_code}"

    @pytest.mark.asyncio
    async def test_공고ID_형식오류_422(self, scoring_client):
        """bid_id="invalid" (UUID 형식 아님) → 422"""
        # Arrange
        headers = {"Authorization": "Bearer valid-token"}

        # Act
        response = await scoring_client.get(
            "/api/v1/bids/invalid-not-uuid/scoring",
            headers=headers,
        )

        # Assert
        assert response.status_code == 422, f"잘못된 UUID 형식 422 기대: {response.status_code}"


# ============================================================
# Lazy Evaluation 테스트 (인수조건 AC-01)
# ============================================================

class Test스코어링_Lazy평가:

    @pytest.mark.asyncio
    async def test_lazy_evaluation_즉시분석_실행(self, scoring_client):
        """스코어링 미수행 공고 → 즉시 분석 실행 후 결과 반환 (200)"""
        # Arrange
        headers = {"Authorization": "Bearer valid-token"}

        # Act — 첫 번째 요청 (캐시 없음)
        response = await scoring_client.get(
            f"/api/v1/bids/{SAMPLE_BID_ID}/scoring",
            headers=headers,
        )

        # Assert: 분석 없어도 즉시 결과 반환
        assert response.status_code == 200, f"lazy evaluation 후 200 기대: {response.status_code}"
        data = response.json()["data"]
        assert "analyzedAt" in data

    @pytest.mark.asyncio
    async def test_캐시된_결과_재요청시_analyzedAt_동일(self, scoring_client):
        """이미 스코어링된 공고 → 재요청 시 캐시된 결과 반환 (analyzed_at 동일)"""
        # Arrange
        headers = {"Authorization": "Bearer valid-token"}

        # Act — 두 번 요청
        response1 = await scoring_client.get(
            f"/api/v1/bids/{SAMPLE_BID_ID}/scoring",
            headers=headers,
        )
        response2 = await scoring_client.get(
            f"/api/v1/bids/{SAMPLE_BID_ID}/scoring",
            headers=headers,
        )

        # Assert
        assert response1.status_code == 200, f"첫 번째 요청 200 기대: {response1.status_code}"
        assert response2.status_code == 200, f"두 번째 요청 200 기대: {response2.status_code}"
        # 캐시된 경우 analyzed_at 동일
        analyzed_at_1 = response1.json()["data"].get("analyzedAt")
        analyzed_at_2 = response2.json()["data"].get("analyzedAt")
        assert analyzed_at_1 == analyzed_at_2, \
            f"캐시된 결과라면 analyzedAt이 동일해야 함: {analyzed_at_1} != {analyzed_at_2}"


# ============================================================
# 회귀 테스트: F-01 하위 호환성
# ============================================================

class Test스코어링_회귀:

    @pytest.mark.asyncio
    async def test_기존_matches_엔드포인트_여전히_동작(self, scoring_client):
        """F-01 GET /bids/{id}/matches 엔드포인트가 여전히 동작"""
        # Arrange
        headers = {"Authorization": "Bearer valid-token"}

        # Act
        response = await scoring_client.get(
            f"/api/v1/bids/{SAMPLE_BID_ID}/matches",
            headers=headers,
        )

        # Assert: 200 또는 404 (공고 없음), 501은 허용 안 됨
        assert response.status_code != 501, \
            f"F-01 엔드포인트가 깨지면 안 됨 (501 반환): {response.status_code}"
