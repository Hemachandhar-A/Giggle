# Model artifacts are loaded here at import time. Stubs active until Person 2A pushes .joblib files to Git LFS.

def calculate_premium(
    enrollment_week: int,
    flood_hazard_zone_tier: int,
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
    # Compute recency_multiplier
    if enrollment_week <= 2:
        recency_multiplier = 1.5
    elif enrollment_week <= 4:
        recency_multiplier = 1.25
    else:
        recency_multiplier = 1.0

    # Model selection and raw premium fallback
    if enrollment_week < 5:
        model_used = 'glm'
        raw_premium = 75.0  # TODO: load glm_m1.joblib
        shap_top3 = []
    else:
        model_used = 'lgbm'
        raw_premium = 75.0  # TODO: load lgbm_m2.joblib
        shap_top3 = ["வெள்ள அபாய மண்டலம் உங்கள் பிரீமியத்தை பாதிக்கிறது"] * 3

    # Adjust premium
    adjusted = raw_premium * recency_multiplier

    # Apply affordability cap
    affordability_cap = income_baseline_weekly * 0.025
    capped = min(adjusted, affordability_cap)

    # Floor and ceiling bounds
    final = max(49.0, min(capped, 149.0))

    # Flag
    affordability_capped = (capped < adjusted)

    return {
        "premium_amount": round(final, 2),
        "model_used": model_used,
        "recency_multiplier": float(recency_multiplier),
        "shap_top3": shap_top3,
        "affordability_capped": affordability_capped
    }
