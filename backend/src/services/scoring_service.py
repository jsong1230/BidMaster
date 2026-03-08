"""낙찰 가능성 스코어링 서비스"""
import logging
from collections import Counter
from datetime import date, datetime, timezone
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------
# 인메모리 낙찰 이력 저장소 + 시드 데이터
# ----------------------------------------------------------------

SAMPLE_WIN_HISTORY: list[dict[str, Any]] = [
    {
        "bid_number": "20260201001-00",
        "winner_name": "(주)가나다소프트",
        "winner_business_number": "1234567890",
        "winning_price": 420_000_000,
        "bid_rate": 0.8920,
        "winning_date": "2026-02-15",
        "_organization": "행정안전부",
        "_category": "정보화",
        "_bid_type": "일반경쟁",
    },
    {
        "bid_number": "20260201002-00",
        "winner_name": "(주)라마바시스템",
        "winner_business_number": "9876543210",
        "winning_price": 380_000_000,
        "bid_rate": 0.8750,
        "winning_date": "2026-02-10",
        "_organization": "행정안전부",
        "_category": "정보화",
        "_bid_type": "일반경쟁",
    },
    {
        "bid_number": "20260115001-00",
        "winner_name": "(주)사아자테크",
        "winner_business_number": "5555555555",
        "winning_price": 250_000_000,
        "bid_rate": 0.9100,
        "winning_date": "2026-01-20",
        "_organization": "국토교통부",
        "_category": "건설",
        "_bid_type": "제한경쟁",
    },
]

# 인메모리 낙찰 이력 저장소 (시드 데이터로 초기화)
_BID_WIN_HISTORY: list[dict[str, Any]] = list(SAMPLE_WIN_HISTORY)

# 스코어링 결과 캐시 (키: "{user_id}:{bid_id}")
_SCORING_CACHE: dict[str, Any] = {}


def _reset_scoring_store() -> None:
    """테스트 격리용 저장소 초기화"""
    _SCORING_CACHE.clear()
    _BID_WIN_HISTORY.clear()
    _BID_WIN_HISTORY.extend(SAMPLE_WIN_HISTORY)


class ScoringService:
    """낙찰 가능성 스코어링 서비스"""

    # 가중치 설정
    WEIGHTS: dict[str, float] = {
        "suitability": 0.30,
        "competition": 0.25,
        "capability": 0.30,
        "market": 0.15,
    }

    # 추천 등급 기준
    RECOMMENDATION_THRESHOLDS: dict[str, int] = {
        "strongly_recommended": 80,
        "recommended": 60,
        "neutral": 40,
        # 40 미만: not_recommended
    }

    def __init__(self, db: Any):
        self.db = db
        self.bid_match_service: Any | None = None

    async def score(
        self,
        user_id: str,
        bid_id: str,
        company: Any = None,
    ) -> dict[str, Any]:
        """
        종합 스코어링 실행 (lazy evaluation + 인메모리 캐시)

        1. 캐시 확인 (이미 분석된 경우 캐시 반환)
        2. 사용자 회사 + 공고 정보 조회
        3. 4개 항목 점수 계산
        4. 가중합 총점 계산
        5. 추천 등급 결정
        6. user_bid_matches 갱신
        7. 결과 캐시 저장

        Args:
            company: 이미 조회된 회사 객체를 주입할 경우 사용 (None이면 내부에서 조회)
        Returns: ScoringResult 딕셔너리
        Raises:
            AppException: COMPANY_001(404), BID_001(404), SCORING_001(500)
        """
        from src.core.exceptions import AppException

        cache_key = f"{user_id}:{bid_id}"

        # 캐시 확인
        if cache_key in _SCORING_CACHE:
            return _SCORING_CACHE[cache_key]

        # 회사 조회 (주입된 company 없으면 내부 조회)
        if company is None:
            company = await self._get_user_company(user_id)
        if company is None:
            raise AppException("COMPANY_001", "회사를 찾을 수 없습니다.", 404)

        # 공고 조회
        bid = await self._get_bid(bid_id)
        if bid is None:
            raise AppException("BID_001", "공고를 찾을 수 없습니다.", 404)

        try:
            # 관련 데이터 조회
            performances = await self._get_company_performances(str(getattr(company, "id", "")))
            certifications = await self._get_company_certifications(str(getattr(company, "id", "")))

            # 4개 항목 점수 계산
            suitability_score, suitability_factors = await self._calculate_suitability(user_id, bid_id)
            competition_score, competition_factors = await self._calculate_competition(bid)
            capability_score, capability_factors = await self._calculate_capability(
                company, performances, certifications, bid
            )
            market_score, market_factors = await self._calculate_market(bid, performances)

            # 가중합 총점
            scores = {
                "suitability": suitability_score,
                "competition": competition_score,
                "capability": capability_score,
                "market": market_score,
            }
            total = self._compute_total(scores)

            # 추천 등급 결정
            details_dict = {
                "suitability": {"score": suitability_score, "factors": suitability_factors},
                "competition": {"score": competition_score, "factors": competition_factors},
                "capability": {"score": capability_score, "factors": capability_factors},
                "market": {"score": market_score, "factors": market_factors},
            }
            recommendation, label, reason = self._determine_recommendation(total, details_dict)

            # 경쟁사 통계 + 유사 공고 통계
            competitor_stats = await self._get_competitor_stats(bid)
            similar_bid_stats = await self._get_similar_bid_stats(bid)

            # user_bid_matches 갱신
            await self._update_match_scores(
                user_id, bid_id, scores, recommendation, reason
            )

            analyzed_at = datetime.now(timezone.utc).isoformat()
            result_id = str(uuid4())

            result = {
                "id": result_id,
                "bidId": bid_id,
                "userId": user_id,
                "scores": {
                    "suitability": suitability_score,
                    "competition": competition_score,
                    "capability": capability_score,
                    "market": market_score,
                    "total": total,
                },
                "weights": {
                    "suitability": self.WEIGHTS["suitability"],
                    "competition": self.WEIGHTS["competition"],
                    "capability": self.WEIGHTS["capability"],
                    "market": self.WEIGHTS["market"],
                },
                "recommendation": recommendation,
                "recommendationLabel": label,
                "recommendationReason": reason,
                "details": details_dict,
                "competitorStats": competitor_stats,
                "similarBidStats": similar_bid_stats,
                "analyzedAt": analyzed_at,
            }

            # 캐시 저장
            _SCORING_CACHE[cache_key] = result
            return result

        except AppException:
            raise
        except Exception as e:
            logger.error(f"스코어링 오류 (user={user_id}, bid={bid_id}): {e}")
            raise AppException("SCORING_001", "스코어링 분석 중 오류가 발생했습니다.", 500)

    async def _calculate_suitability(
        self, user_id: str, bid_id: str
    ) -> tuple[float, list[str]]:
        """
        적합도 점수 산출 (TF-IDF 기반, BidMatchService 위임)

        Returns: (score, factors)
        """
        try:
            if self.bid_match_service is None:
                from src.services.bid_match_service import BidMatchService
                self.bid_match_service = BidMatchService(db=self.db)

            match_result = await self.bid_match_service.analyze_match(user_id, bid_id)
            score = float(getattr(match_result, "suitability_score", 60.0))
            factors = [
                f"키워드 유사도 기반 적합도 점수: {score:.1f}점",
            ]
            return score, factors
        except Exception:
            # BidMatchService 실패 시 기본값 60.0
            return 60.0, ["적합도 분석 기본값 적용 (60.0점)"]

    async def _calculate_competition(
        self, bid: Any
    ) -> tuple[float, list[str]]:
        """
        경쟁 강도 점수 산출

        1. 유사 공고 조건: organization + category + bid_type
        2. bid_win_history에서 낙찰 이력 조회
        3. 고유 낙찰자 수 -> 경쟁 업체 수 추정
        4. 경쟁 역점수 계산

        Returns: (score, factors)
        """
        organization = getattr(bid, "organization", None) or ""
        category = getattr(bid, "category", None) or ""
        bid_type = getattr(bid, "bid_type", None) or ""

        history = await self._get_win_history(
            organization=organization or None,
            category=category or None,
            bid_type=bid_type or None,
        )

        if not history:
            factors = [
                "유사 공고 낙찰 데이터 없음 — 기본값 적용",
            ]
            return 50.0, factors

        # 고유 낙찰자 수 집계
        unique_winners = set(
            h.get("winner_business_number", "") or h.get("winner_name", "")
            for h in history
        )
        competitor_count = len(unique_winners)

        # 경쟁 강도 raw = min(competitor_count / 10, 1.0)
        raw = min(competitor_count / 10.0, 1.0)
        score = round((1.0 - raw) * 100.0, 1)

        # 경쟁 강도 수준 텍스트
        if raw < 0.3:
            intensity = "낮음"
        elif raw < 0.7:
            intensity = "보통"
        else:
            intensity = "높음"

        factors = [
            f"유사 공고 낙찰 이력: {len(history)}건",
            f"추정 경쟁 업체 수: {competitor_count}개사",
            f"경쟁 강도: {intensity}",
        ]
        return score, factors

    async def _calculate_capability(
        self,
        company: Any,
        performances: list[Any],
        certifications: list[Any],
        bid: Any,
    ) -> tuple[float, list[str]]:
        """
        역량 점수 산출

        1. 실적 점수 (40%): 건수, 유사실적, 대표실적
        2. 인증 점수 (30%): 건수, 유효성
        3. 규모 점수 (30%): 기업 규모, 금액 적합성

        Returns: (score, factors)
        """
        factors: list[str] = []

        # callable이 전달된 경우 호출하여 실제 데이터 획득 (테스트 fixture 직접 전달 방어)
        if callable(performances) and not isinstance(performances, list):
            performances = performances()
        if callable(certifications) and not isinstance(certifications, list):
            certifications = certifications()
        if performances is None:
            performances = []
        if certifications is None:
            certifications = []

        # ── 실적 점수 (40%) ──
        perf_count = len(performances)
        perf_base = min(perf_count / 10.0, 1.0) * 100.0

        # 유사 실적 보너스
        organization = str(getattr(bid, "organization", "") or "").lower()
        has_same_org = False
        has_representative = False
        for perf in performances:
            client = str(getattr(perf, "client_name", "") or "").lower()
            if organization and organization in client:
                has_same_org = True
            if getattr(perf, "is_representative", False):
                has_representative = True

        perf_bonus = 0.0
        if has_same_org:
            perf_bonus += 20.0
        if has_representative:
            perf_bonus += 10.0

        perf_score = min(100.0, perf_base + perf_bonus)
        factors.append(f"수행 실적: {perf_count}건 ({'양호' if perf_count >= 5 else '보통' if perf_count >= 2 else '부족'})")

        # ── 인증 점수 (30%) ──
        today = date.today()
        valid_certs: list[Any] = []
        for cert in certifications:
            expiry_str = getattr(cert, "expiry_date", None)
            if expiry_str:
                try:
                    if isinstance(expiry_str, str):
                        expiry = date.fromisoformat(expiry_str[:10])
                    elif isinstance(expiry_str, date):
                        expiry = expiry_str
                    else:
                        expiry = date.fromisoformat(str(expiry_str)[:10])
                    if expiry >= today:
                        valid_certs.append(cert)
                except (ValueError, TypeError):
                    pass
            else:
                # 만료일 없으면 유효한 것으로 처리
                valid_certs.append(cert)

        cert_count = len(valid_certs)
        cert_score = min(cert_count / 5.0, 1.0) * 100.0

        cert_names = [getattr(c, "name", "") for c in valid_certs[:3]]
        if cert_names:
            factors.append(f"보유 인증: {', '.join(cert_names)}")
        else:
            factors.append("보유 인증: 없음")

        # ── 규모 점수 (30%) ──
        scale = str(getattr(company, "scale", "") or "").lower()
        scale_map = {"large": 100.0, "medium": 70.0, "small": 40.0}
        scale_score = scale_map.get(scale, 40.0)
        scale_label = {"large": "대기업", "medium": "중견기업", "small": "소기업"}.get(scale, "소기업")
        factors.append(f"회사 규모: {scale_label}")

        # 가중합
        capability_score = round(
            perf_score * 0.40 + cert_score * 0.30 + scale_score * 0.30,
            1,
        )
        return capability_score, factors

    async def _calculate_market(
        self,
        bid: Any,
        performances: list[Any],
    ) -> tuple[float, list[str]]:
        """
        시장 환경 점수 산출

        1. 예산 적합성 (50%): 회사 평균 수행금액 대비 비율
        2. 계약 방식 적합성 (30%)
        3. 시기 점수 (20%): 마감까지 남은 기간

        Returns: (score, factors)
        """
        factors: list[str] = []

        # ── 예산 적합성 (50%) ──
        budget = float(getattr(bid, "budget", 0) or 0)

        if performances:
            amounts = [float(getattr(p, "contract_amount", 0) or 0) for p in performances]
            avg_amount = sum(amounts) / len(amounts) if amounts else 0.0
        else:
            avg_amount = 0.0

        if avg_amount > 0 and budget > 0:
            ratio = budget / avg_amount
            if 0.5 <= ratio <= 2.0:
                budget_score = 100.0
                budget_label = f"적정 (회사 평균 수행금액 대비 {ratio:.1f}배)"
            elif ratio < 0.5:
                # 예산이 너무 작음
                budget_score = max(0.0, 50.0 - (0.5 - ratio) * 50.0)
                budget_label = f"예산 과소 (회사 평균 수행금액 대비 {ratio:.1f}배)"
            else:
                # 예산이 너무 큼 (ratio > 2.0)
                budget_score = max(0.0, 100.0 - (ratio - 2.0) * 20.0)
                budget_score = min(budget_score, 70.0)
                budget_label = f"예산 과대 (회사 평균 수행금액 대비 {ratio:.1f}배)"
            factors.append(f"예산 적합성: {budget_label}")
        else:
            budget_score = 50.0  # 데이터 없을 때 기본값
            factors.append("예산 적합성: 기본값 적용 (수행 실적 없음)")

        # ── 계약 방식 적합성 (30%) ──
        contract_method = str(getattr(bid, "contract_method", "") or "").strip()
        if "적격" in contract_method:
            contract_score = 70.0
            factors.append(f"계약 방식: 적격심사 (유리)")
        elif "최저" in contract_method:
            contract_score = 50.0
            factors.append(f"계약 방식: 최저가 (가격 경쟁)")
        else:
            contract_score = 60.0
            factors.append(f"계약 방식: {contract_method or '일반'}")

        # ── 시기 점수 (20%) ──
        deadline = getattr(bid, "deadline", None)
        if deadline is not None:
            now = datetime.now(timezone.utc)
            if isinstance(deadline, datetime):
                if deadline.tzinfo is None:
                    deadline = deadline.replace(tzinfo=timezone.utc)
                days_left = (deadline - now).days
            else:
                days_left = 7  # 기본값
        else:
            days_left = 7  # 기본값

        if days_left >= 7:
            timing_score = 80.0
            factors.append(f"마감 여유: {days_left}일 (충분)")
        elif days_left >= 3:
            timing_score = 60.0
            factors.append(f"마감 여유: {days_left}일 (보통)")
        else:
            timing_score = 40.0
            factors.append(f"마감 여유: {days_left}일 (부족)")

        # 가중합
        market_score = round(
            budget_score * 0.50 + contract_score * 0.30 + timing_score * 0.20,
            1,
        )
        return market_score, factors

    def _compute_total(self, scores: dict[str, float]) -> float:
        """가중합 총점 계산 (0~100 클램핑)"""
        total = (
            scores.get("suitability", 0.0) * self.WEIGHTS["suitability"]
            + scores.get("competition", 0.0) * self.WEIGHTS["competition"]
            + scores.get("capability", 0.0) * self.WEIGHTS["capability"]
            + scores.get("market", 0.0) * self.WEIGHTS["market"]
        )
        return round(max(0.0, min(100.0, total)), 2)

    def _determine_recommendation(
        self, total_score: float, details: dict[str, Any]
    ) -> tuple[str, str, str]:
        """
        추천 등급 + 라벨 + 사유 결정

        Returns: (recommendation_code, label, reason)
        """
        if total_score >= self.RECOMMENDATION_THRESHOLDS["strongly_recommended"]:
            code = "strongly_recommended"
            label = "강력추천"
            reason = (
                f"높은 낙찰 가능성이 예상됩니다. (총점: {total_score:.1f}점) "
                "회사 역량과 공고 분야가 탁월하게 일치하며, 경쟁 강도가 낮습니다. 적극 참여를 권장합니다."
            )
        elif total_score >= self.RECOMMENDATION_THRESHOLDS["recommended"]:
            code = "recommended"
            label = "추천"
            reason = (
                f"회사 역량과 공고 분야가 잘 일치하며, 경쟁 강도가 보통 수준입니다. "
                f"(총점: {total_score:.1f}점) 참여를 추천합니다."
            )
        elif total_score >= self.RECOMMENDATION_THRESHOLDS["neutral"]:
            code = "neutral"
            label = "보류"
            reason = (
                f"참여 가능성은 있으나 신중한 검토가 필요합니다. "
                f"(총점: {total_score:.1f}점) 일부 역량 보완 후 참여를 검토하세요."
            )
        else:
            code = "not_recommended"
            label = "비추천"
            reason = (
                f"낙찰 가능성이 낮습니다. (총점: {total_score:.1f}점) "
                "회사 역량과 공고 요건 간 불일치가 크며, 다른 공고를 검토하는 것을 권장합니다."
            )

        return code, label, reason

    async def _get_competitor_stats(self, bid: Any) -> dict[str, Any]:
        """
        경쟁사 통계 조회

        유사 공고 낙찰 이력에서 주요 경쟁사 리스트 추출

        Returns: {estimatedCompetitors, topCompetitors}
        """
        organization = getattr(bid, "organization", None) or ""
        category = getattr(bid, "category", None) or ""
        bid_type = getattr(bid, "bid_type", None) or ""

        history = await self._get_win_history(
            organization=organization or None,
            category=category or None,
            bid_type=bid_type or None,
        )

        if not history:
            return {"estimatedCompetitors": 0, "topCompetitors": []}

        # 낙찰자별 낙찰 횟수 집계
        winner_counts: Counter = Counter()
        winner_names: dict[str, str] = {}
        for h in history:
            biz_num = h.get("winner_business_number") or h.get("winner_name", "")
            name = h.get("winner_name", "")
            winner_counts[biz_num] += 1
            winner_names[biz_num] = name

        estimated = len(winner_counts)
        top_competitors = [
            {"name": winner_names[biz_num], "winCount": count}
            for biz_num, count in winner_counts.most_common(5)
        ]

        return {
            "estimatedCompetitors": estimated,
            "topCompetitors": top_competitors,
        }

    async def _get_similar_bid_stats(self, bid: Any) -> dict[str, Any]:
        """
        유사 공고 낙찰 통계

        Returns: {totalCount, avgWinRate, avgWinningPrice}
        """
        organization = getattr(bid, "organization", None) or ""
        category = getattr(bid, "category", None) or ""
        bid_type = getattr(bid, "bid_type", None) or ""

        history = await self._get_win_history(
            organization=organization or None,
            category=category or None,
            bid_type=bid_type or None,
        )

        if not history:
            return {"totalCount": 0, "avgWinRate": None, "avgWinningPrice": None}

        total = len(history)

        # 낙찰율 평균
        rates = [float(h["bid_rate"]) for h in history if h.get("bid_rate") is not None]
        avg_win_rate = sum(rates) / len(rates) if rates else None

        # 낙찰가 평균
        prices = [float(h["winning_price"]) for h in history if h.get("winning_price") is not None]
        avg_winning_price = sum(prices) / len(prices) if prices else None

        return {
            "totalCount": total,
            "avgWinRate": round(avg_win_rate, 4) if avg_win_rate is not None else None,
            "avgWinningPrice": round(avg_winning_price, 0) if avg_winning_price is not None else None,
        }

    async def _get_win_history(
        self,
        organization: str | None = None,
        category: str | None = None,
        bid_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        bid_win_history 조회 (인메모리 + DB 폴백)

        조건에 맞는 낙찰 이력 반환 (OR 조건: organization 또는 category 일치)
        """
        result: list[dict[str, Any]] = []

        # 인메모리 검색 (OR 조건)
        for h in _BID_WIN_HISTORY:
            org_match = organization and h.get("_organization") == organization
            cat_match = category and h.get("_category") == category
            type_match = bid_type and h.get("_bid_type") == bid_type

            if org_match or cat_match or type_match:
                result.append(h)

        if result:
            return result

        # DB 폴백 (연결 실패 시 빈 리스트 반환)
        try:
            from sqlalchemy import text
            conditions: list[str] = []
            params: dict[str, str] = {}

            if organization:
                conditions.append("b.organization = :org")
                params["org"] = organization
            if category:
                conditions.append("b.category = :cat")
                params["cat"] = category

            if not conditions:
                return []

            where_clause = " OR ".join(conditions)
            rows = await self.db.execute(
                text(f"""
                    SELECT wh.*, b.organization AS _organization, b.category AS _category,
                           b.bid_type AS _bid_type
                    FROM bid_win_history wh
                    JOIN bids b ON b.bid_number = wh.bid_number
                    WHERE {where_clause}
                    ORDER BY wh.winning_date DESC
                    LIMIT 50
                """),
                params,
            )
            return [dict(r._mapping) for r in rows.fetchall()]
        except Exception:
            return []

    async def _update_match_scores(
        self,
        user_id: str,
        bid_id: str,
        scores: dict[str, float],
        recommendation: str,
        reason: str,
    ) -> None:
        """user_bid_matches 테이블 갱신 (인메모리 + DB)"""
        from src.services.bid_match_service import _BID_MATCHES, UserBidMatchResult

        match_key = f"{user_id}:{bid_id}"
        now = datetime.now(timezone.utc)

        # 인메모리 갱신
        existing = _BID_MATCHES.get(match_key)
        if existing is not None:
            existing.competition_score = scores.get("competition", 0.0)
            existing.capability_score = scores.get("capability", 0.0)
            existing.market_score = scores.get("market", 0.0)
            existing.suitability_score = scores.get("suitability", 0.0)
            total = (
                scores.get("suitability", 0.0) * self.WEIGHTS["suitability"]
                + scores.get("competition", 0.0) * self.WEIGHTS["competition"]
                + scores.get("capability", 0.0) * self.WEIGHTS["capability"]
                + scores.get("market", 0.0) * self.WEIGHTS["market"]
            )
            existing.total_score = round(max(0.0, min(100.0, total)), 2)
            existing.recommendation = recommendation
            existing.recommendation_reason = reason
            existing.analyzed_at = now

        # DB 갱신 시도
        try:
            from sqlalchemy import text
            total_score = (
                scores.get("suitability", 0.0) * self.WEIGHTS["suitability"]
                + scores.get("competition", 0.0) * self.WEIGHTS["competition"]
                + scores.get("capability", 0.0) * self.WEIGHTS["capability"]
                + scores.get("market", 0.0) * self.WEIGHTS["market"]
            )
            await self.db.execute(
                text("""
                    UPDATE user_bid_matches
                    SET suitability_score = :suit, competition_score = :comp,
                        capability_score = :cap, market_score = :mkt,
                        total_score = :total, recommendation = :rec,
                        recommendation_reason = :reason, analyzed_at = :analyzed_at,
                        updated_at = :updated_at
                    WHERE user_id = :uid AND bid_id = :bid_id
                """),
                {
                    "suit": scores.get("suitability", 0.0),
                    "comp": scores.get("competition", 0.0),
                    "cap": scores.get("capability", 0.0),
                    "mkt": scores.get("market", 0.0),
                    "total": round(max(0.0, min(100.0, total_score)), 2),
                    "rec": recommendation,
                    "reason": reason,
                    "analyzed_at": now,
                    "updated_at": now,
                    "uid": user_id,
                    "bid_id": bid_id,
                },
            )
        except Exception:
            pass

    # ----------------------------------------------------------------
    # 데이터 접근 헬퍼
    # ----------------------------------------------------------------

    async def _get_user_company(self, user_id: str) -> Any | None:
        """사용자 소속 회사 조회"""
        # company_service 인메모리 저장소 먼저 조회
        try:
            from src.services.company_service import _get_user_company_from_store
            company = _get_user_company_from_store(user_id)
            if company is not None:
                return company
        except (ImportError, AttributeError):
            pass

        # DB 조회 시도
        try:
            from sqlalchemy import text
            result = await self.db.execute(
                text("""
                    SELECT c.* FROM companies c
                    JOIN users u ON u.company_id = c.id
                    WHERE u.id = :uid AND c.deleted_at IS NULL
                """),
                {"uid": user_id},
            )
            row = result.fetchone()
            return row
        except Exception:
            return None

    async def _get_bid(self, bid_id: str) -> Any | None:
        """공고 조회"""
        # bids.py 인메모리 저장소 먼저 조회
        try:
            from src.api.v1.bids import _SAMPLE_BIDS
            bid_dict = _SAMPLE_BIDS.get(bid_id)
            if bid_dict is not None:
                return _DictBid(bid_dict)
        except ImportError:
            pass

        # DB 조회
        try:
            from sqlalchemy import select
            from src.models.bid import Bid
            result = await self.db.execute(
                select(Bid).where(Bid.id == bid_id)
            )
            return result.scalar_one_or_none()
        except Exception:
            return None

    async def _get_company_performances(self, company_id: str) -> list[Any]:
        """회사 수행 실적 조회"""
        try:
            from src.services.company_service import _get_company_performances_from_store
            return _get_company_performances_from_store(company_id)
        except (ImportError, AttributeError):
            pass

        try:
            from sqlalchemy import text
            result = await self.db.execute(
                text("SELECT * FROM performances WHERE company_id = :cid AND deleted_at IS NULL"),
                {"cid": company_id},
            )
            return list(result.fetchall())
        except Exception:
            return []

    async def _get_company_certifications(self, company_id: str) -> list[Any]:
        """회사 보유 인증 조회"""
        try:
            from src.services.company_service import _get_company_certifications_from_store
            return _get_company_certifications_from_store(company_id)
        except (ImportError, AttributeError):
            pass

        try:
            from sqlalchemy import text
            result = await self.db.execute(
                text("SELECT * FROM certifications WHERE company_id = :cid AND deleted_at IS NULL"),
                {"cid": company_id},
            )
            return list(result.fetchall())
        except Exception:
            return []


class _DictBid:
    """딕셔너리를 공고 객체처럼 접근하기 위한 어댑터"""

    def __init__(self, data: dict[str, Any]):
        self._data = data

    def __getattr__(self, name: str) -> Any:
        # camelCase → snake_case 변환 매핑
        key_map = {
            "organization": "organization",
            "category": "category",
            "bid_type": "bidType",
            "contract_method": "contractMethod",
            "budget": "budget",
            "deadline": "deadline",
            "title": "title",
            "description": "description",
            "id": "id",
        }
        key = key_map.get(name, name)
        val = self._data.get(key)
        if val is None:
            val = self._data.get(name)
        return val
