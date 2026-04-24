"""
Loss-ratio simulation helper for Person 2 premium data generation.
Section 3.4: weekly premium target from actuarial assumptions.
"""

from __future__ import annotations

import numpy as np

BASE_LOSS_DELIVERIES = 7
BASE_LOSS_PER_DELIVERY = 18.0
BASE_LOSS = BASE_LOSS_DELIVERIES * BASE_LOSS_PER_DELIVERY  # 126.0
SLAB_PROBABILITY = 0.40
SLAB_BONUS_VALUE = 120.0
SLAB_DELTA = SLAB_PROBABILITY * SLAB_BONUS_VALUE  # 48.0
BASE_PAYOUT_PER_DISRUPTION_DAY = BASE_LOSS + SLAB_DELTA  # 174.0
CLIMATE_ADJUSTMENT_FACTOR = 1.1
TARGET_LOSS_RATIO = 0.65
WEEKLY_PREMIUM_FLOOR = 49.0
WEEKLY_PREMIUM_CEILING = 149.0
RAIN_SCALE_MIN = 5.0
RAIN_SCALE_MAX = 30.0

FLOOD_TIER_MULTIPLIERS = {"low": 1.0, "medium": 1.5, "high": 2.0}
SEASON_MULTIPLIERS = {"NE_monsoon": 1.4, "SW_monsoon": 1.2, "heat": 1.1, "dry": 0.8}


def compute_weekly_premium_target(
    avg_heavy_rain_days_yr: float,
    flood_tier_numeric: int,
    season_flag: str,
) -> float:
    """Return the capped weekly premium target from the document's loss-ratio logic."""
    if flood_tier_numeric not in (1, 2, 3):
        raise ValueError(f"flood_tier_numeric must be 1, 2, or 3; got {flood_tier_numeric}")
    if season_flag not in SEASON_MULTIPLIERS:
        raise ValueError(f"season_flag must be one of {sorted(SEASON_MULTIPLIERS)}; got {season_flag}")

    tier_name = {1: "low", 2: "medium", 3: "high"}[flood_tier_numeric]

    rain_normalized = (float(avg_heavy_rain_days_yr) - RAIN_SCALE_MIN) / (RAIN_SCALE_MAX - RAIN_SCALE_MIN)
    rain_normalized = max(0.0, min(1.0, rain_normalized))
    rain_multiplier = 1.0 + (0.2 * rain_normalized)

    raw_payout = BASE_PAYOUT_PER_DISRUPTION_DAY * FLOOD_TIER_MULTIPLIERS[tier_name] * rain_multiplier
    adjusted_payout = raw_payout * CLIMATE_ADJUSTMENT_FACTOR
    annual_target = adjusted_payout / TARGET_LOSS_RATIO
    weekly_premium = (annual_target / 52.0) * SEASON_MULTIPLIERS[season_flag]
    return float(np.clip(weekly_premium, WEEKLY_PREMIUM_FLOOR, WEEKLY_PREMIUM_CEILING))
