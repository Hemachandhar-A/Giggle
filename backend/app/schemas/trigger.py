from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TriggerZoneStatus(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    zone_cluster_id: int
    status: Literal["active", "recovering", "none"]
    trigger_event_id: UUID | None = None
    trigger_type: str | None = None
    composite_score: float | None = None
    triggered_at: datetime | None = None
    sources_confirmed: int = 0


class TriggerSimulateRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    zone_cluster_id: int = Field(..., ge=1)
    trigger_type: str
    duration_hours: float = Field(..., gt=0)


class TriggerSimulateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    trigger_event_id: UUID
    zone_cluster_id: int
    trigger_type: str
    duration_hours: float
    payout_task_enqueued: bool


class ActiveTrigger(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    trigger_event_id: UUID
    zone_cluster_id: int
    zone_centroid_lat: float | None = None
    zone_centroid_lon: float | None = None
    status: str
    trigger_type: str
    composite_score: float
    sources_confirmed: int
    triggered_at: datetime
    current_cascade_day: int


class TriggerHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    trigger_event_id: UUID
    zone_cluster_id: int
    trigger_type: str
    status: str
    triggered_at: datetime
    composite_score: float
    sources_confirmed: int
    payout_count: int
