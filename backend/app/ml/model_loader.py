"""Model loader logic. Includes a stub for calculate_premium."""

def load_models() -> None:
    """Stub for loading .joblib models at startup."""
    pass

def calculate_premium(
    enrollment_week: int,
    flood_hazard_zone_tier: str,
    zone_cluster_id: int,
    platform: str,
    season_flag: str,
    delivery_baseline_30d: float,
    income_baseline_weekly: float,
    open_meteo_7d_precip_probability: float,
    activity_consistency_score: float,
    tenure_discount_factor: float,
    historical_claim_rate_zone: float,
    language: str
) -> dict:
    """Stub implementation of calculate_premium."""
    return {
        "premium_amount": 75.0,
        "model_used": "stub",
        "recency_multiplier": 1.0,
        "shap_top3": ["வெள்ள அபாய மண்டலம் (+₹75.0)"],
        "affordability_capped": False
    }
