"""투찰 전략 분석 서비스"""
import math
from datetime import datetime, timezone
from typing import Any, Optional

import numpy as np

from src.core.exceptions import AppException
from src.schemas.strategy import (
    RecommendedRange,
    RecommendedRanges,
    SimulationResult,
    StrategyReport,
    StrategyResult,
    WinRateDistribution,
)


# ----------------------------------------------------------------
# 인메모리 낙찰 이력 샘플 데이터 (F-02 미완료 시 자체 사용)
# ----------------------------------------------------------------

SAMPLE_WIN_HISTORY: list[dict[str, Any]] = [
    {
        "bid_number": "20260115001-00",
        "winner_name": "(주)가나다소프트",
        "winner_business_number": "1234500001",
        "winning_price": 414_000_000,
        "bid_rate": 0.9200,
        "winning_date": "2026-01-20",
        "_organization": "행정안전부",
        "_category": "정보화",
        "_bid_type": "일반경쟁",
        "_contract_method": "적격심사",
    },
    {
        "bid_number": "20260110002-00",
        "winner_name": "(주)라마바소프트",
        "winner_business_number": "1234500002",
        "winning_price": 400_500_000,
        "bid_rate": 0.8900,
        "winning_date": "2026-01-15",
        "_organization": "행정안전부",
        "_category": "정보화",
        "_bid_type": "일반경쟁",
        "_contract_method": "적격심사",
    },
    {
        "bid_number": "20260105003-00",
        "winner_name": "(주)사아자IT",
        "winner_business_number": "1234500003",
        "winning_price": 391_500_000,
        "bid_rate": 0.8700,
        "winning_date": "2026-01-10",
        "_organization": "교육부",
        "_category": "정보화",
        "_bid_type": "일반경쟁",
        "_contract_method": "적격심사",
    },
    {
        "bid_number": "20251220001-00",
        "winner_name": "(주)차카타소프트",
        "winner_business_number": "1234500004",
        "winning_price": 418_500_000,
        "bid_rate": 0.9300,
        "winning_date": "2025-12-25",
        "_organization": "과학기술정보통신부",
        "_category": "정보화",
        "_bid_type": "일반경쟁",
        "_contract_method": "적격심사",
    },
    {
        "bid_number": "20251215002-00",
        "winner_name": "(주)파하소프트",
        "winner_business_number": "1234500005",
        "winning_price": 382_500_000,
        "bid_rate": 0.8500,
        "winning_date": "2025-12-20",
        "_organization": "행정안전부",
        "_category": "정보화",
        "_bid_type": "일반경쟁",
        "_contract_method": "적격심사",
    },
    # 최저가 샘플
    {
        "bid_number": "20260120001-00",
        "winner_name": "(주)최저가IT",
        "winner_business_number": "9876500001",
        "winning_price": 174_000_000,
        "bid_rate": 0.8700,
        "winning_date": "2026-01-25",
        "_organization": "조달청",
        "_category": "정보화",
        "_bid_type": "일반경쟁",
        "_contract_method": "최저가",
    },
    {
        "bid_number": "20260115002-00",
        "winner_name": "(주)저가시스템",
        "winner_business_number": "9876500002",
        "winning_price": 166_000_000,
        "bid_rate": 0.8300,
        "winning_date": "2026-01-20",
        "_organization": "조달청",
        "_category": "정보화",
        "_bid_type": "일반경쟁",
        "_contract_method": "최저가",
    },
    {
        "bid_number": "20260110003-00",
        "winner_name": "(주)경쟁IT",
        "winner_business_number": "9876500003",
        "winning_price": 178_000_000,
        "bid_rate": 0.8900,
        "winning_date": "2026-01-15",
        "_organization": "환경부",
        "_category": "정보화",
        "_bid_type": "일반경쟁",
        "_contract_method": "최저가",
    },
    # 추가 데이터 (design.md ADDITIONAL_WIN_HISTORY)
    {
        "bid_number": "20260120001-00",
        "winner_name": "(주)차카타소프트",
        "winner_business_number": "1111111111",
        "winning_price": 460_000_000,
        "bid_rate": 0.9200,
        "winning_date": "2026-01-25",
        "_organization": "행정안전부",
        "_category": "정보화",
        "_bid_type": "일반경쟁",
        "_contract_method": "적격심사",
    },
    {
        "bid_number": "20260110001-00",
        "winner_name": "(주)파하소프트",
        "winner_business_number": "2222222222",
        "winning_price": 180_000_000,
        "bid_rate": 0.8500,
        "winning_date": "2026-01-15",
        "_organization": "조달청",
        "_category": "정보화",
        "_bid_type": "일반경쟁",
        "_contract_method": "최저가",
    },
]


class BiddingStrategyService:
    """투찰 전략 분석 서비스"""

    # 적격심사 기본 구간 (예정가격 대비 비율)
    # 인수조건: 예산 88~95% 구간 추천
    QUALIFICATION_RANGES = {
        "safe": (0.92, 0.95),
        "moderate": (0.90, 0.92),
        "aggressive": (0.88, 0.90),
    }

    # 최저가 통계 기반 시그마 계수
    LOWEST_PRICE_SIGMA = {
        "safe": (0.0, 0.5),        # mean ~ mean - 0.5*std
        "moderate": (0.5, 1.0),    # mean - 0.5*std ~ mean - 1.0*std
        "aggressive": (1.0, 2.0),  # mean - 1.0*std ~ mean - 2.0*std
    }

    # 계약 방식별 기본 분포 (유사 공고 데이터 없을 때)
    DEFAULT_DISTRIBUTIONS = {
        "적격심사": {"mean": 0.91, "std": 0.03, "median": 0.91, "q25": 0.89, "q75": 0.93, "minRate": 0.86, "maxRate": 0.95, "sampleCount": 0},
        "최저가": {"mean": 0.87, "std": 0.04, "median": 0.87, "q25": 0.84, "q75": 0.90, "minRate": 0.80, "maxRate": 0.95, "sampleCount": 0},
    }

    def __init__(self, db: Any):
        self.db = db

    async def analyze_strategy(self, bid_id: str) -> StrategyResult:
        """
        투찰 전략 분석

        1. 공고 정보 조회
        2. 유사 공고 낙찰 이력 조회
        3. 낙찰가율 분포 계산 (numpy)
        4. contract_method에 따른 추천 투찰가 범위 산출
        5. 전략 리포트 생성

        Raises:
            AppException: BID_001(404), STRATEGY_001(500)
        """
        bid = await self._get_bid(bid_id)
        if bid is None:
            raise AppException("BID_001", "공고를 찾을 수 없습니다.", 404)

        try:
            # 유사 공고 낙찰 이력 조회
            win_history = await self._get_similar_win_history(bid)

            # 낙찰가율 분포 계산
            bid_rates = [h.bid_rate if hasattr(h, "bid_rate") else h.get("bid_rate", 0) for h in win_history]
            distribution = self._calculate_distribution(bid_rates)

            # 예정가격 추출
            estimated_price = self._get_estimated_price(bid)

            contract_method = getattr(bid, "contract_method", None) or bid.get("contractMethod") if isinstance(bid, dict) else getattr(bid, "contract_method", None)
            if not contract_method:
                contract_method = "적격심사"

            # 추천 범위 계산
            if contract_method == "최저가":
                if distribution is None:
                    # 기본 분포 사용
                    fallback_dist = dict(self.DEFAULT_DISTRIBUTIONS["최저가"])
                    ranges = self._calculate_ranges_lowest_price(estimated_price or 0, fallback_dist)
                    distribution = None  # 리포트용으로 None 유지
                else:
                    ranges = self._calculate_ranges_lowest_price(estimated_price or 0, distribution)
            else:
                ranges = self._calculate_ranges_qualification(estimated_price or 0, distribution)

            # 각 구간별 낙찰 확률 추정
            effective_dist = distribution or self.DEFAULT_DISTRIBUTIONS.get(contract_method, self.DEFAULT_DISTRIBUTIONS["적격심사"])
            for level in ["safe", "moderate", "aggressive"]:
                mid_rate = (ranges[level]["minRate"] + ranges[level]["maxRate"]) / 2
                prob = self._estimate_win_probability(mid_rate, effective_dist, contract_method)
                ranges[level]["winProbability"] = prob

            # 전략 리포트 생성
            report = self._generate_strategy_report(bid, distribution, ranges)

            # 결과 구성을 위한 분포 (None이면 기본값 사용)
            final_dist = distribution or self.DEFAULT_DISTRIBUTIONS.get(contract_method, self.DEFAULT_DISTRIBUTIONS["적격심사"])

            # 구간 레이블 추가
            level_labels = {
                "safe": "낮은 리스크 (안전)",
                "moderate": "중간 리스크 (적정)",
                "aggressive": "높은 리스크 (공격적)",
            }
            level_descriptions = {
                "safe": "안전한 구간으로 낙찰 가능성이 높습니다.",
                "moderate": "적정 구간으로 수익과 낙찰 가능성의 균형입니다.",
                "aggressive": "공격적 구간으로 수익은 높지만 낙찰 가능성이 낮습니다.",
            }

            recommended_ranges = RecommendedRanges(
                safe=RecommendedRange(
                    label=level_labels["safe"],
                    description=level_descriptions["safe"],
                    **ranges["safe"],
                ),
                moderate=RecommendedRange(
                    label=level_labels["moderate"],
                    description=level_descriptions["moderate"],
                    **ranges["moderate"],
                ),
                aggressive=RecommendedRange(
                    label=level_labels["aggressive"],
                    description=level_descriptions["aggressive"],
                    **ranges["aggressive"],
                ),
            )

            bid_title = getattr(bid, "title", None) or (bid.get("title") if isinstance(bid, dict) else "")
            budget_val = getattr(bid, "budget", None) or (bid.get("budget") if isinstance(bid, dict) else None)

            return StrategyResult(
                bidId=bid_id,
                bidTitle=bid_title or "",
                contractMethod=contract_method,
                estimatedPrice=estimated_price,
                budget=budget_val,
                winRateDistribution=WinRateDistribution(**final_dist),
                recommendedRanges=recommended_ranges,
                strategyReport=StrategyReport(**report),
                analyzedAt=datetime.now(timezone.utc).isoformat(),
            )

        except AppException:
            raise
        except Exception as exc:
            raise AppException("STRATEGY_001", "투찰 전략 분석 중 오류가 발생했습니다.", 500) from exc

    async def simulate(self, bid_id: str, bid_price: int) -> SimulationResult:
        """
        투찰가 시뮬레이션

        1. 공고 정보 조회 + 예정가격 확인
        2. bid_rate 계산 (bid_price / estimated_price)
        3. 유사 공고 bid_rate 분포에서 백분위 계산
        4. 낙찰 확률 추정
        5. 리스크 레벨 판정

        Raises:
            AppException: BID_001(404), STRATEGY_002(422)
        """
        bid = await self._get_bid(bid_id)
        if bid is None:
            raise AppException("BID_001", "공고를 찾을 수 없습니다.", 404)

        estimated_price = self._get_estimated_price(bid)
        if estimated_price is None:
            raise AppException("STRATEGY_002", "예정가격 정보가 없어 투찰가를 추천할 수 없습니다.", 422)

        contract_method = getattr(bid, "contract_method", None) or (bid.get("contractMethod") if isinstance(bid, dict) else None)
        if not contract_method:
            contract_method = "적격심사"

        # bid_rate 계산
        if estimated_price == 0:
            bid_rate = 0.0
        else:
            bid_rate = round(bid_price / estimated_price, 4)

        # 유사 공고 이력 및 분포
        win_history = await self._get_similar_win_history(bid)
        bid_rates = [h.bid_rate if hasattr(h, "bid_rate") else h.get("bid_rate", 0) for h in win_history]
        distribution = self._calculate_distribution(bid_rates)

        effective_dist = distribution or self.DEFAULT_DISTRIBUTIONS.get(contract_method, self.DEFAULT_DISTRIBUTIONS["적격심사"])

        # 추천 범위 계산 (리스크 판정용)
        if contract_method == "최저가":
            ranges = self._calculate_ranges_lowest_price(estimated_price, effective_dist)
        else:
            ranges = self._calculate_ranges_qualification(estimated_price, distribution)

        # 낙찰 확률 및 리스크 판정
        win_probability = self._estimate_win_probability(bid_rate, effective_dist, contract_method)
        risk_level, risk_label = self._determine_risk_level(bid_rate, ranges)

        # 비교 분석 생성
        comparison = self._build_comparison(bid_rate, ranges)

        # 분석 텍스트 생성
        mean_rate = effective_dist["mean"]
        analysis = (
            f"입력 금액은 예정가격의 {bid_rate * 100:.1f}%로, "
            f"유사 공고 평균({mean_rate * 100:.1f}%) 대비 "
            f"{'높은' if bid_rate > mean_rate else '낮은'} 수준입니다. "
            f"낙찰 가능성은 약 {win_probability}%로 추정됩니다."
        )

        return SimulationResult(
            bidId=bid_id,
            inputPrice=bid_price,
            bidRate=bid_rate,
            winProbability=win_probability,
            riskLevel=risk_level,
            riskLabel=risk_label,
            analysis=analysis,
            comparisonWithRecommended=comparison,
        )

    def _calculate_distribution(self, bid_rates: list[float]) -> Optional[dict]:
        """
        numpy 기반 낙찰가율 분포 계산

        Returns: {mean, std, median, q25, q75, minRate, maxRate, sampleCount}
        빈 배열이면 None 반환
        """
        if not bid_rates:
            return None

        arr = np.array(bid_rates, dtype=float)
        return {
            "mean": round(float(np.mean(arr)), 6),
            "std": round(float(np.std(arr)), 6),
            "median": round(float(np.median(arr)), 6),
            "q25": round(float(np.percentile(arr, 25)), 6),
            "q75": round(float(np.percentile(arr, 75)), 6),
            "minRate": round(float(np.min(arr)), 6),
            "maxRate": round(float(np.max(arr)), 6),
            "sampleCount": len(bid_rates),
        }

    def _calculate_ranges_qualification(
        self,
        estimated_price: int,
        distribution: Optional[dict],
    ) -> dict:
        """
        적격심사 투찰가 추천 범위 계산

        - 유사 공고 데이터 있으면 실데이터 기반
        - 없으면 기본 구간 (86~95%) 사용
        """
        if distribution is not None:
            # 실데이터 기반: q25~q75 구간 활용
            mean = distribution["mean"]
            std = distribution["std"]
            median = distribution["median"]
            q25 = distribution["q25"]
            q75 = distribution["q75"]
            min_r = distribution["minRate"]

            # 안전 구간: median ~ 최대 0.95
            safe_min_rate = round(max(median, 0.89), 4)
            safe_max_rate = round(min(q75, 0.95), 4)
            if safe_min_rate > safe_max_rate:
                safe_min_rate, safe_max_rate = safe_max_rate, safe_min_rate

            # 적정 구간: q25 ~ median
            moderate_min_rate = round(max(q25, 0.86), 4)
            moderate_max_rate = round(safe_min_rate, 4)

            # 공격적 구간: min ~ q25
            aggressive_min_rate = round(max(min_r, 0.80), 4)
            aggressive_max_rate = round(moderate_min_rate, 4)

        else:
            # 기본 구간 사용
            safe_min_rate, safe_max_rate = self.QUALIFICATION_RANGES["safe"]
            moderate_min_rate, moderate_max_rate = self.QUALIFICATION_RANGES["moderate"]
            aggressive_min_rate, aggressive_max_rate = self.QUALIFICATION_RANGES["aggressive"]

        def make_range(min_r: float, max_r: float) -> dict:
            return {
                "minRate": round(min_r, 4),
                "maxRate": round(max_r, 4),
                "minPrice": int(estimated_price * min_r),
                "maxPrice": int(estimated_price * max_r),
                "winProbability": 50,  # 이후 덮어씀
            }

        return {
            "safe": make_range(safe_min_rate, safe_max_rate),
            "moderate": make_range(moderate_min_rate, moderate_max_rate),
            "aggressive": make_range(aggressive_min_rate, aggressive_max_rate),
        }

    def _calculate_ranges_lowest_price(
        self,
        estimated_price: int,
        distribution: dict,
    ) -> dict:
        """
        최저가 투찰가 추천 범위 계산

        - 평균/표준편차 기반 시그마 구간
        - safe: mean - 0.5*std ~ mean
        - moderate: mean - 1.0*std ~ mean - 0.5*std
        - aggressive: mean - 2.0*std ~ mean - 1.0*std
        """
        mean = distribution["mean"]
        std = distribution["std"]

        def make_range(sigma_low: float, sigma_high: float) -> dict:
            # 최저가는 낮을수록 유리하므로 min이 아래
            min_r = round(mean - sigma_high * std, 4)
            max_r = round(mean - sigma_low * std, 4)
            # 0 미만 방지
            min_r = max(min_r, 0.0)
            max_r = max(max_r, 0.0)
            return {
                "minRate": min_r,
                "maxRate": max_r,
                "minPrice": int(estimated_price * min_r),
                "maxPrice": int(estimated_price * max_r),
                "winProbability": 50,  # 이후 덮어씀
            }

        safe_sigma = self.LOWEST_PRICE_SIGMA["safe"]
        moderate_sigma = self.LOWEST_PRICE_SIGMA["moderate"]
        aggressive_sigma = self.LOWEST_PRICE_SIGMA["aggressive"]

        return {
            "safe": make_range(*safe_sigma),
            "moderate": make_range(*moderate_sigma),
            "aggressive": make_range(*aggressive_sigma),
        }

    def _estimate_win_probability(
        self,
        bid_rate: float,
        distribution: Optional[dict],
        contract_method: str,
    ) -> int:
        """
        낙찰 확률 추정 (0~100%)

        적격심사: 정규분포 CDF 기반 (적정 구간 = 높은 확률)
        최저가: 백분위 기반 (낮을수록 유리)
        분포 없으면 기본 확률 50%
        """
        if distribution is None:
            return 50

        mean = distribution["mean"]
        std = distribution["std"]

        if contract_method == "최저가":
            # 최저가: bid_rate가 낮을수록 유리
            # 분포 평균 대비 얼마나 낮은지 기반
            if std <= 0:
                # std=0이면 mean과 같으면 50%, 낮으면 높은 확률
                if bid_rate <= mean:
                    prob = 75
                else:
                    prob = 25
            else:
                # bid_rate의 분포 내 백분위 계산 (낮을수록 유리)
                z = (bid_rate - mean) / std
                # 정규분포 CDF (낮은 값 = 낮은 percentile = 유리)
                cdf = 0.5 * (1 + math.erf(z / math.sqrt(2)))
                # 낮을수록 유리: win_prob = (1 - percentile) * 100
                prob = int(round((1 - cdf) * 100))
        else:
            # 적격심사: 적정 구간 중심부일수록 유리
            # 정규분포 확률밀도 기반 (mean 주변이 가장 높음)
            if std <= 0:
                if abs(bid_rate - mean) < 0.01:
                    prob = 70
                else:
                    prob = 30
            else:
                # 정규분포 PDF를 확률로 변환
                # mean±1sigma 구간에서 최대 확률
                z = (bid_rate - mean) / std
                # 덤핑(너무 낮음) 또는 과도하게 높음 → 낮은 확률
                # z=0이 가장 유리 (mean과 동일)
                # 확률 = max(10, 100 * exp(-z^2 / 2))
                pdf_factor = math.exp(-(z ** 2) / 2)
                prob = int(round(max(10, min(90, pdf_factor * 85))))

        return max(0, min(100, prob))

    def _determine_risk_level(
        self, bid_rate: float, ranges: dict
    ) -> tuple[str, str]:
        """
        리스크 레벨 판정

        Returns: (risk_level, risk_label)
        """
        level_labels = {
            "safe": "낮은 리스크",
            "moderate": "중간 리스크",
            "aggressive": "높은 리스크",
        }

        for level in ["safe", "moderate", "aggressive"]:
            r = ranges[level]
            if r["minRate"] <= bid_rate <= r["maxRate"]:
                return level, level_labels[level]

        # 구간 외 판정
        safe_max = ranges["safe"]["maxRate"]
        aggressive_min = ranges["aggressive"]["minRate"]

        if bid_rate > safe_max:
            return "over_safe", "구간 초과 (매우 높음)"
        elif bid_rate < aggressive_min:
            return "extreme", "구간 미달 (매우 낮음)"
        else:
            return "moderate", "중간 리스크"

    def _generate_strategy_report(
        self,
        bid: Any,
        distribution: Optional[dict],
        ranges: dict,
    ) -> dict:
        """
        전략 리포트 생성

        - 계약 방식별 전략 설명
        - 시장 인사이트
        - 리스크 요인
        - 추천 사항
        """
        contract_method = getattr(bid, "contract_method", None) or (bid.get("contractMethod") if isinstance(bid, dict) else None)
        if not contract_method:
            contract_method = "적격심사"

        if contract_method == "최저가":
            contract_strategy = (
                "최저가 낙찰 방식으로 순수 가격 경쟁이 이루어집니다. "
                "경쟁사 대비 낮은 가격을 제시하는 것이 핵심 전략입니다."
            )
        else:
            contract_strategy = (
                "적격심사 방식으로 기술력과 가격의 종합 평가가 이루어집니다. "
                "예정가격 대비 89~95% 구간이 유리합니다."
            )

        if distribution is None or distribution.get("sampleCount", 0) == 0:
            market_insight = (
                "유사 공고 데이터가 부족하여 일반적인 통계 기반으로 추천합니다. "
                "실제 시장 데이터가 축적되면 더 정확한 분석이 가능합니다."
            )
        else:
            sample_count = distribution["sampleCount"]
            mean_pct = distribution["mean"] * 100
            market_insight = (
                f"유사 공고 {sample_count}건 분석 결과 평균 낙찰가율 {mean_pct:.1f}%입니다."
            )

        risk_factors = [
            "경쟁 업체 수 추정 (보통 수준)",
            "예산 규모 대비 시장 경쟁도 분석 필요",
        ]

        if distribution and distribution.get("sampleCount", 0) > 0:
            recommendations = [
                f"투찰가는 예정가격의 {ranges['safe']['minRate'] * 100:.0f}~{ranges['safe']['maxRate'] * 100:.0f}% 구간을 권장합니다.",
                "기술 제안서 품질에 집중하여 기술 점수를 극대화하세요." if contract_method != "최저가" else "최저 비용 구조를 확보하여 경쟁력 있는 가격을 제시하세요.",
            ]
        else:
            recommendations = [
                "데이터 부족으로 인해 일반적인 기준을 적용합니다. 유사 사업 이력 분석을 권장합니다.",
                f"투찰가는 예정가격의 {ranges['safe']['minRate'] * 100:.0f}~{ranges['safe']['maxRate'] * 100:.0f}% 구간을 권장합니다.",
            ]

        return {
            "contractMethodStrategy": contract_strategy,
            "marketInsight": market_insight,
            "riskFactors": risk_factors,
            "recommendations": recommendations,
        }

    async def _get_similar_win_history(self, bid: Any) -> list[Any]:
        """
        유사 공고 낙찰 이력 조회

        조건: 동일 category + contract_method, 최근 1년
        인메모리 store 우선, DB 폴백
        """
        category = getattr(bid, "category", None) or (bid.get("category") if isinstance(bid, dict) else None)
        contract_method = getattr(bid, "contract_method", None) or (bid.get("contractMethod") if isinstance(bid, dict) else None)

        # 인메모리 샘플에서 유사 공고 필터링
        similar = [
            h for h in SAMPLE_WIN_HISTORY
            if (category is None or h.get("_category") == category)
            and (contract_method is None or h.get("_contract_method") == contract_method)
        ]

        if similar:
            # dict를 속성 접근 가능한 객체로 변환
            class WinHistoryItem:
                def __init__(self, data: dict):
                    for k, v in data.items():
                        setattr(self, k.lstrip("_"), v)
                        setattr(self, k, v)

            return [WinHistoryItem(h) for h in similar]

        return []

    def _get_estimated_price(self, bid: Any) -> Optional[int]:
        """
        예정가격 추출

        우선순위: estimated_price > budget
        둘 다 없으면 None
        """
        if isinstance(bid, dict):
            estimated = bid.get("estimatedPrice") or bid.get("estimated_price")
            budget = bid.get("budget")
        else:
            estimated = getattr(bid, "estimated_price", None)
            budget = getattr(bid, "budget", None)

        if estimated is not None:
            return int(estimated)
        if budget is not None:
            return int(budget)
        return None

    async def _get_bid(self, bid_id: str) -> Optional[Any]:
        """
        공고 조회 (인메모리 스토어 사용)

        실제 DB 사용 시 self.db로 교체
        """
        # 인메모리 스토어에서 조회 (bids.py의 _SAMPLE_BIDS 참조)
        try:
            from src.api.v1.bids import _SAMPLE_BIDS
            bid = _SAMPLE_BIDS.get(bid_id)
            if bid is not None:
                return bid
        except ImportError:
            pass

        return None

    def _build_comparison(self, bid_rate: float, ranges: dict) -> dict[str, str]:
        """
        추천 범위 대비 비교 텍스트 생성

        Returns: {safe: "...", moderate: "...", aggressive: "..."}
        """
        comparison = {}
        for level in ["safe", "moderate", "aggressive"]:
            r = ranges[level]
            min_r = r["minRate"]
            max_r = r["maxRate"]

            if min_r <= bid_rate <= max_r:
                comparison[level] = "추천 범위 내"
            elif bid_rate > max_r:
                comparison[level] = "추천 범위 초과"
            else:
                comparison[level] = "추천 범위 미달"

        return comparison
