import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from app.core.database import get_db
from app.models.worker import WorkerProfile
from app.models.policy import Policy
from app.models.audit import AuditEvent
from app.schemas.premium import (
    PremiumCalculateRequest, 
    PremiumCalculateResponse,
    PremiumRenewRequest,
    PremiumHistoryResponse,
    PremiumHistoryItem
)
from app.ml.inference import calculate_premium

logger = logging.getLogger(__name__)

router = APIRouter()

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

        inference_result = calculate_premium(
            enrollment_week=worker.enrollment_week,
            flood_hazard_zone_tier=worker.flood_hazard_tier,
            zone_cluster_id=worker.zone_cluster_id,
            platform=worker.platform,
            season_flag=get_current_season(),
            delivery_baseline_30d=0.0,
            income_baseline_weekly=4000.0, # TODO: query delivery_history for real value
            open_meteo_7d_precip_probability=0.0,
            activity_consistency_score=0.5,
            tenure_discount_factor=1.0,
            historical_claim_rate_zone=0.0,
            language=worker.language_preference
        )

        model_used = inference_result["model_used"]
        shap_top3 = inference_result.get("shap_top3", [])
        
        default_tamil_explanation = "உங்கள் பிரீமியம் கணக்கிடப்பட்டது"
        if model_used in ['stub', 'glm']:
            tamil_explanation = default_tamil_explanation
        elif model_used == 'lgbm':
            if shap_top3 and len(shap_top3) > 0:
                tamil_explanation = shap_top3[0]
            else:
                tamil_explanation = default_tamil_explanation
        else:
            tamil_explanation = default_tamil_explanation
            
        inference_result["tamil_explanation"] = tamil_explanation

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
            
        # The prompt specifies "order by calculated_at desc". Since Policy has created_at and updated_at,
        # we map calculated_at to updated_at.
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
def renew_premium_endpoint(request: PremiumRenewRequest, db: Session = Depends(get_db)):
    """Renew premium for a worker."""
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

        inference_result = calculate_premium(
            enrollment_week=worker.enrollment_week,
            flood_hazard_zone_tier=worker.flood_hazard_tier,
            zone_cluster_id=worker.zone_cluster_id,
            platform=worker.platform,
            season_flag=get_current_season(),
            delivery_baseline_30d=0.0,
            income_baseline_weekly=4000.0, # TODO: query delivery_history for real value
            open_meteo_7d_precip_probability=0.0,
            activity_consistency_score=0.5,
            tenure_discount_factor=1.0,
            historical_claim_rate_zone=0.0,
            language=worker.language_preference
        )

        model_used = inference_result["model_used"]
        shap_top3 = inference_result.get("shap_top3", [])
        
        default_tamil_explanation = "உங்கள் பிரீமியம் கணக்கிடப்பட்டது"
        if model_used in ['stub', 'glm']:
            tamil_explanation = default_tamil_explanation
        elif model_used == 'lgbm':
            if shap_top3 and len(shap_top3) > 0:
                tamil_explanation = shap_top3[0]
            else:
                tamil_explanation = default_tamil_explanation
        else:
            tamil_explanation = default_tamil_explanation
            
        inference_result["tamil_explanation"] = tamil_explanation

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
