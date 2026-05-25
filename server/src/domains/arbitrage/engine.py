"""
Arbitrage Engine - core calculation logic.

For each card, compares normalized prices between buy/sell markets and
calculates: gross spread, platform fees, shipping, net profit, ROI,
and a confidence score based on data volume and recency.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import math


@dataclass
class PriceDataPoint:
    price_gbp: float
    sold_at: datetime
    condition: str
    market_id: uuid.UUID


@dataclass
class ArbitrageResult:
    card_id: uuid.UUID
    buy_market_id: uuid.UUID
    sell_market_id: uuid.UUID
    buy_price_gbp: float
    sell_price_gbp: float
    gross_spread_gbp: float
    platform_fees_gbp: float
    shipping_cost_gbp: float
    import_duties_gbp: float
    net_profit_gbp: float
    roi_percent: float
    confidence_score: float
    volume_score: float
    data_points_used: int
    expires_at: datetime


def _recency_weight(sold_at: datetime, now: datetime) -> float:
    """Older sales get less weight. Decays over 30 days."""
    age_days = max(0, (now - sold_at).total_seconds() / 86400)
    return math.exp(-age_days / 30)


def _median(values: List[float]) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    mid = len(s) // 2
    return s[mid] if len(s) % 2 else (s[mid - 1] + s[mid]) / 2


def weighted_avg_price(data_points: List[PriceDataPoint], now: datetime, is_uk_market: bool = False) -> float:
    """Recency-weighted average price from data points. For UK markets, simple average of last 3 sales is used."""
    if not data_points:
        return 0.0

    # Filter out cheap outliers (e.g. proxy cards/code cards under 30% of maximum price in batch)
    max_price = max(dp.price_gbp for dp in data_points)
    if max_price > 0:
        data_points = [dp for dp in data_points if dp.price_gbp >= 0.3 * max_price]
        if not data_points:
            return 0.0

    if is_uk_market:
        # Sort by sold_at descending (latest sales first)
        sorted_dps = sorted(data_points, key=lambda dp: dp.sold_at, reverse=True)
        last_3 = sorted_dps[:3]
        return sum(dp.price_gbp for dp in last_3) / len(last_3)

    weights = [_recency_weight(dp.sold_at, now) for dp in data_points]
    total_weight = sum(weights)
    if total_weight == 0:
        return _median([dp.price_gbp for dp in data_points])
    return sum(dp.price_gbp * w for dp, w in zip(data_points, weights)) / total_weight


def calculate_confidence(
    buy_points: List[PriceDataPoint],
    sell_points: List[PriceDataPoint],
    now: datetime,
) -> float:
    """
    Confidence score 0–1 based on:
    - Volume (more data = higher confidence)
    - Recency (recent sales = higher confidence)
    - Price consistency (low variance = higher confidence)
    """
    volume_score = min(1.0, (len(buy_points) + len(sell_points)) / 20)

    all_ages = [
        (now - dp.sold_at).total_seconds() / 86400
        for dp in (buy_points + sell_points)
        if dp.sold_at
    ]
    recency_score = math.exp(-min(all_ages, default=30) / 14) if all_ages else 0.3

    prices = [dp.price_gbp for dp in (buy_points + sell_points)]
    if len(prices) > 1:
        mean = sum(prices) / len(prices)
        variance = sum((p - mean) ** 2 for p in prices) / len(prices)
        cv = (variance ** 0.5) / mean if mean > 0 else 1.0
        consistency_score = max(0.0, 1.0 - min(cv, 1.0))
    else:
        consistency_score = 0.5

    return round(
        0.4 * volume_score + 0.35 * recency_score + 0.25 * consistency_score, 3
    )


def calculate_arbitrage(
    card_id: uuid.UUID,
    buy_market_id: uuid.UUID,
    sell_market_id: uuid.UUID,
    buy_data_points: List[PriceDataPoint],
    sell_data_points: List[PriceDataPoint],
    buy_fee_percent: float,
    sell_fee_percent: float,
    shipping_cost_gbp: float,
    import_duties_gbp: float = 0.0,
    is_buy_uk: bool = False,
    is_sell_uk: bool = False,
) -> Optional[ArbitrageResult]:
    """
    Core arbitrage calculation. Returns None if not profitable enough.
    """
    now = datetime.now(timezone.utc)
    all_points = len(buy_data_points) + len(sell_data_points)
    if all_points < 2:
        return None

    buy_price = weighted_avg_price(buy_data_points, now, is_uk_market=is_buy_uk)
    sell_price = weighted_avg_price(sell_data_points, now, is_uk_market=is_sell_uk)

    if buy_price <= 0 or sell_price <= 0:
        return None

    gross_spread = sell_price - buy_price
    # Platform fee applies on the sell side (eBay final value fee)
    platform_fees = sell_price * (sell_fee_percent / 100)
    net_profit = gross_spread - platform_fees - shipping_cost_gbp - import_duties_gbp
    roi = (net_profit / buy_price) * 100 if buy_price > 0 else 0

    confidence = calculate_confidence(buy_data_points, sell_data_points, now)
    volume_score = min(1.0, all_points / 10)

    return ArbitrageResult(
        card_id=card_id,
        buy_market_id=buy_market_id,
        sell_market_id=sell_market_id,
        buy_price_gbp=round(buy_price, 2),
        sell_price_gbp=round(sell_price, 2),
        gross_spread_gbp=round(gross_spread, 2),
        platform_fees_gbp=round(platform_fees, 2),
        shipping_cost_gbp=round(shipping_cost_gbp, 2),
        import_duties_gbp=round(import_duties_gbp, 2),
        net_profit_gbp=round(net_profit, 2),
        roi_percent=round(roi, 2),
        confidence_score=confidence,
        volume_score=volume_score,
        data_points_used=all_points,
        expires_at=now + timedelta(hours=6),
    )
