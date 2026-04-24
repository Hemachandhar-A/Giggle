import logging
import os
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy import func
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.models.worker import WorkerProfile
from app.models.policy import Policy
from app.models.audit import AuditEvent
from app.models.delivery import DeliveryHistory
from app.models.zone import ZoneCluster
from app.models.claims import Claim
from app.schemas.premium import (
    PremiumCalculateRequest, 
    PremiumCalculateResponse,
    PremiumRenewRequest,
    PremiumHistoryResponse,
    PremiumHistoryItem
)
from app.ml.inference import calculate_premium, compute_activity_consistency_score

logger = logging.getLogger(__name__)

router = APIRouter()

EXPECTED_ADMIN_KEY = os.getenv("ADMIN_KEY") or os.getenv("X_ADMIN_KEY") or "gigshield-admin"


def _require_admin_key(x_admin_key: str | None) -> None:
    if not x_admin_key or x_admin_key != EXPECTED_ADMIN_KEY:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


def _fetch_open_meteo_precip_probability(lat: float, lon: float) -> float:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "precipitation_probability_max",
        "timezone": "Asia/Kolkata",
        "forecast_days": 7,
    }
    try:
        response = httpx.get(url, params=params, timeout=10.0)
        response.raise_for_status()
        values = response.json().get("daily", {}).get("precipitation_probability_max", [])
        if not values:
            raise ValueError("No daily precipitation_probability_max values")
        return max(0.0, min(1.0, float(sum(values) / len(values)) / 100.0))
    except Exception as e:
        logger.warning("Open-Meteo call failed for (%s, %s): %s. Using default 0.3", lat, lon, e)
        return 0.3


def _build_feature_vector(worker: WorkerProfile, db: Session) -> dict:
    now_utc = datetime.now(timezone.utc)
    since_30d = now_utc - timedelta(days=30)
    since_52w = now_utc - timedelta(weeks=52)

    delivery_baseline_30d_raw = (
        db.query(func.coalesce(func.sum(DeliveryHistory.deliveries_count), 0))
        .filter(
            DeliveryHistory.worker_id == worker.id,
            DeliveryHistory.recorded_at >= since_30d,
        )
        .scalar()
    )
    delivery_baseline_30d = float(delivery_baseline_30d_raw or 0.0)

    zone = db.query(ZoneCluster).filter(ZoneCluster.id == worker.zone_cluster_id).first()
    zone_rate_mid = float(zone.zone_rate_mid) if zone and zone.zone_rate_mid is not None else 18.0
    income_baseline_weekly = float((delivery_baseline_30d * zone_rate_mid / 30.0) * 7.0)

    if zone and zone.centroid_lat is not None and zone.centroid_lon is not None:
        open_meteo_7d_precip_probability = _fetch_open_meteo_precip_probability(
            float(zone.centroid_lat), float(zone.centroid_lon)
        )
    else:
        logger.warning("Zone centroid not found for zone_cluster_id=%s. Using precip default 0.3", worker.zone_cluster_id)
        open_meteo_7d_precip_probability = 0.3

    weekly_rows = (
        db.query(
            func.date_trunc("week", DeliveryHistory.recorded_at).label("week_start"),
            func.sum(DeliveryHistory.deliveries_count).label("weekly_total"),
        )
        .filter(DeliveryHistory.worker_id == worker.id)
        .group_by(func.date_trunc("week", DeliveryHistory.recorded_at))
        .order_by(func.date_trunc("week", DeliveryHistory.recorded_at).desc())
        .limit(8)
        .all()
    )
    weekly_delivery_counts = [float(row.weekly_total or 0.0) for row in reversed(weekly_rows)]
    activity_consistency_score = compute_activity_consistency_score(weekly_delivery_counts)

    claims_count_raw = (
        db.query(func.count(Claim.id))
        .join(WorkerProfile, Claim.worker_id == WorkerProfile.id)
        .filter(
            WorkerProfile.zone_cluster_id == worker.zone_cluster_id,
            Claim.claim_date >= since_52w,
        )
        .scalar()
    )
    claims_count = int(claims_count_raw or 0)

    active_workers_raw = (
        db.query(func.count(WorkerProfile.id))
        .filter(
            WorkerProfile.zone_cluster_id == worker.zone_cluster_id,
            WorkerProfile.is_active.is_(True),
        )
        .scalar()
    )
    active_workers = int(active_workers_raw or 0)

    if claims_count < 10 or active_workers == 0:
        historical_claim_rate_zone = 0.05
    else:
        historical_claim_rate_zone = float(claims_count / active_workers)

    tenure_discount_factor = 1.0 - (0.15 * min(int(worker.enrollment_week), 26) / 26.0)
    tenure_discount_factor = float(max(0.85, min(1.0, tenure_discount_factor)))

    return {
        "season_flag": get_current_season(),
        "delivery_baseline_30d": delivery_baseline_30d,
        "income_baseline_weekly": income_baseline_weekly,
        "open_meteo_7d_precip_probability": open_meteo_7d_precip_probability,
        "activity_consistency_score": activity_consistency_score,
        "historical_claim_rate_zone": historical_claim_rate_zone,
        "tenure_discount_factor": tenure_discount_factor,
    }

def get_current_season() -> str:
    """Determine the season based on the current month."""
    month = datetime.now().month
    if 6 <= month <= 9:
        return 'SW_monsoon'
    elif 10 <= month <= 12:
        return 'NE_monsoon'
    elif 3 <= month <= 5:
        return 'heat'
    else:  # 1 <= month <= 2
        return 'dry'

@router.post("/calculate", response_model=PremiumCalculateResponse)
def calculate_premium_endpoint(request: PremiumCalculateRequest, db: Session = Depends(get_db)):
    """Calculate premium for a worker."""
    try:
        worker = db.query(WorkerProfile).filter(WorkerProfile.id == request.worker_id).first()
        if not worker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker not found"
            )
            
        policy = db.query(Policy).filter(Policy.worker_id == request.worker_id).first()
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Policy not found for worker"
            )

        features = _build_feature_vector(worker, db)

        inference_result = calculate_premium(
            enrollment_week=worker.enrollment_week,
            flood_hazard_zone_tier=worker.flood_hazard_tier,
            zone_cluster_id=worker.zone_cluster_id,
            platform=worker.platform,
            season_flag=features["season_flag"],
            delivery_baseline_30d=features["delivery_baseline_30d"],
            income_baseline_weekly=features["income_baseline_weekly"],
            open_meteo_7d_precip_probability=features["open_meteo_7d_precip_probability"],
            activity_consistency_score=features["activity_consistency_score"],
            tenure_discount_factor=features["tenure_discount_factor"],
            historical_claim_rate_zone=features["historical_claim_rate_zone"],
            language=worker.language_preference,
            clean_claim_weeks=policy.clean_claim_weeks or 0,
        )

        # Update policy table
        policy.weekly_premium_amount = inference_result["premium_amount"]
        policy.model_used = inference_result["model_used"]
        policy.shap_explanation_json = inference_result["shap_top3"]
        db.add(policy)

        audit_event = AuditEvent(
            event_type="premium_calculated",
            entity_id=policy.id,
            entity_type="policy",
            payload={
                "worker_id": str(worker.id),
                "premium_amount": float(inference_result["premium_amount"]),
                "model_used": inference_result["model_used"],
                "recency_multiplier": float(inference_result["recency_multiplier"]),
                "affordability_capped": inference_result["affordability_capped"]
            },
            actor="system"
        )
        db.add(audit_event)
        
        db.commit()

        return PremiumCalculateResponse(**inference_result)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Database or calculation error in /calculate")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/history/{worker_id}", response_model=PremiumHistoryResponse)
def get_premium_history(worker_id: UUID, db: Session = Depends(get_db)):
    """Get premium history for a worker."""
    try:
        worker = db.query(WorkerProfile).filter(WorkerProfile.id == worker_id).first()
        if not worker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker not found"
            )
            
        policies = db.query(Policy).filter(Policy.worker_id == worker_id).order_by(Policy.updated_at.desc()).all()
        
        history_items = []
        for p in policies:
            history_items.append(
                PremiumHistoryItem(
                    week_number=p.coverage_week_number,
                    premium_amount=float(p.weekly_premium_amount) if p.weekly_premium_amount is not None else 0.0,
                    model_used=p.model_used or "stub",
                    shap_explanation_json=p.shap_explanation_json,
                    calculated_at=p.updated_at
                )
            )
            
        return PremiumHistoryResponse(worker_id=worker_id, history=history_items)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Database error in /history")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/renew", response_model=PremiumCalculateResponse)
def renew_premium_endpoint(
    request: PremiumRenewRequest,
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
    db: Session = Depends(get_db),
):
    """Renew premium for a worker."""
    try:
        _require_admin_key(x_admin_key)

        worker = db.query(WorkerProfile).filter(WorkerProfile.id == request.worker_id).first()
        if not worker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker not found"
            )
            
        policy = db.query(Policy).filter(Policy.worker_id == request.worker_id).first()
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Policy not found for worker"
            )

        features = _build_feature_vector(worker, db)

        inference_result = calculate_premium(
            enrollment_week=worker.enrollment_week,
            flood_hazard_zone_tier=worker.flood_hazard_tier,
            zone_cluster_id=worker.zone_cluster_id,
            platform=worker.platform,
            season_flag=features["season_flag"],
            delivery_baseline_30d=features["delivery_baseline_30d"],
            income_baseline_weekly=features["income_baseline_weekly"],
            open_meteo_7d_precip_probability=features["open_meteo_7d_precip_probability"],
            activity_consistency_score=features["activity_consistency_score"],
            tenure_discount_factor=features["tenure_discount_factor"],
            historical_claim_rate_zone=features["historical_claim_rate_zone"],
            language=worker.language_preference,
            clean_claim_weeks=policy.clean_claim_weeks or 0,
        )

        # Update policy table
        policy.weekly_premium_amount = inference_result["premium_amount"]
        policy.model_used = inference_result["model_used"]
        policy.shap_explanation_json = inference_result["shap_top3"]
        db.add(policy)

        # Write audit event
        audit_event = AuditEvent(
            event_type="premium_calculated",
            entity_id=policy.id,
            entity_type="policy",
            payload={
                "worker_id": str(worker.id),
                "premium_amount": float(inference_result["premium_amount"]),
                "model_used": inference_result["model_used"],
                "recency_multiplier": float(inference_result["recency_multiplier"]),
                "affordability_capped": inference_result["affordability_capped"]
            },
            actor="system"
        )
        db.add(audit_event)
        
        db.commit()

        return PremiumCalculateResponse(**inference_result)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Database or calculation error in /renew")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
