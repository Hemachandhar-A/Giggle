"""Worker profile GET and PATCH endpoints for user-facing profile page."""

from __future__ import annotations

from uuid import UUID
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.audit import AuditEvent
from app.models.worker import WorkerProfile
from app.models.zone import ZoneCluster

router = APIRouter(prefix="/api/v1/worker", tags=["worker"])

ZONE_NAMES = {
    1: "North Chennai", 2: "Perambur", 3: "T. Nagar", 4: "Anna Nagar",
    5: "Adyar", 6: "Kodambakkam", 7: "Velachery", 8: "Mylapore",
    9: "Tambaram", 10: "Porur", 11: "Chromepet", 12: "Ambattur",
}


class WorkerProfileResponse(BaseModel):
    worker_id: UUID
    platform: str
    partner_id: str
    pincode: int
    flood_hazard_tier: str
    zone_cluster_id: int
    zone_name: str
    upi_vpa: str
    language_preference: str
    enrollment_date: datetime
    enrollment_week: int
    upi_mandate_active: bool
    is_active: bool


class WorkerUpdateRequest(BaseModel):
    upi_vpa: str | None = None
    language_preference: str | None = None
    pincode: int | None = None


@router.get("/{worker_id}", response_model=WorkerProfileResponse)
def get_worker_profile(worker_id: UUID, db: Session = Depends(get_db)) -> WorkerProfileResponse:
    worker = db.query(WorkerProfile).filter_by(id=worker_id).first()
    if worker is None:
        raise HTTPException(status_code=404, detail="Worker not found")

    zone_name = ZONE_NAMES.get(int(worker.zone_cluster_id), f"Zone {worker.zone_cluster_id}")

    enroll = worker.enrollment_date
    if enroll and enroll.tzinfo is None:
        enroll = enroll.replace(tzinfo=timezone.utc)

    return WorkerProfileResponse(
        worker_id=worker.id,
        platform=str(worker.platform),
        partner_id=str(worker.partner_id),
        pincode=int(worker.pincode),
        flood_hazard_tier=str(worker.flood_hazard_tier),
        zone_cluster_id=int(worker.zone_cluster_id),
        zone_name=zone_name,
        upi_vpa=str(worker.upi_vpa),
        language_preference=str(worker.language_preference),
        enrollment_date=enroll,
        enrollment_week=int(worker.enrollment_week),
        upi_mandate_active=bool(worker.upi_mandate_active),
        is_active=bool(worker.is_active),
    )


@router.patch("/{worker_id}", response_model=WorkerProfileResponse)
def update_worker_profile(
    worker_id: UUID,
    payload: WorkerUpdateRequest,
    db: Session = Depends(get_db),
) -> WorkerProfileResponse:
    worker = db.query(WorkerProfile).filter_by(id=worker_id).first()
    if worker is None:
        raise HTTPException(status_code=404, detail="Worker not found")

    changes: dict = {}

    if payload.upi_vpa is not None:
        stripped = payload.upi_vpa.strip()
        if "@" not in stripped or len(stripped) < 5:
            raise HTTPException(status_code=422, detail="Invalid UPI VPA format")
        worker.upi_vpa = stripped
        changes["upi_vpa"] = stripped

    if payload.language_preference is not None:
        if payload.language_preference not in ("en", "ta", "hi"):
            raise HTTPException(status_code=422, detail="language must be en, ta, or hi")
        worker.language_preference = payload.language_preference
        changes["language_preference"] = payload.language_preference

    if payload.pincode is not None:
        worker.pincode = payload.pincode
        changes["pincode"] = payload.pincode

    if changes:
        db.add(AuditEvent(
            event_type="worker_profile_updated",
            entity_id=worker.id,
            entity_type="worker",
            payload={"worker_id": str(worker_id), "changes": changes},
            actor="worker",
        ))
        db.commit()

    zone_name = ZONE_NAMES.get(int(worker.zone_cluster_id), f"Zone {worker.zone_cluster_id}")
    enroll = worker.enrollment_date
    if enroll and enroll.tzinfo is None:
        enroll = enroll.replace(tzinfo=timezone.utc)

    return WorkerProfileResponse(
        worker_id=worker.id,
        platform=str(worker.platform),
        partner_id=str(worker.partner_id),
        pincode=int(worker.pincode),
        flood_hazard_tier=str(worker.flood_hazard_tier),
        zone_cluster_id=int(worker.zone_cluster_id),
        zone_name=zone_name,
        upi_vpa=str(worker.upi_vpa),
        language_preference=str(worker.language_preference),
        enrollment_date=enroll,
        enrollment_week=int(worker.enrollment_week),
        upi_mandate_active=bool(worker.upi_mandate_active),
        is_active=bool(worker.is_active),
    )
