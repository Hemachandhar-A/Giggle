from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ClaimSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    claim_id: UUID
    claim_date: datetime | None = None
    total_payout_amount: float
    total_paid_amount: float | None = None
    fraud_score: float
    fraud_routing: str
    status: str


class ClaimDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    claim_id: UUID
    worker_id: UUID
    trigger_event_id: UUID
    policy_id: UUID
    claim_date: datetime | None = None
    cascade_day: int
    deliveries_completed: int
    base_loss_amount: float
    slab_delta_amount: float
    monthly_proximity_amount: float
    peak_multiplier_applied: bool
    total_payout_amount: float
    fraud_score: float
    fraud_routing: str
    status: str
    zone_claim_match: bool | None = None
    activity_7d_score: float | None = None


class ClaimResolveRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    resolution: Literal["approve", "reject"]


class ClaimResolveResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    claim_id: UUID
    status: str
    paid_before: float
    total_payout_amount: float
    remaining_payout_attempted: float
    payout_triggered: bool
