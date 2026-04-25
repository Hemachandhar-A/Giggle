from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PayoutHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    payout_event_id: UUID
    claim_id: UUID
    amount: float
    status: str
    razorpay_payout_id: str | None = None
    initiated_at: datetime | None = None
    completed_at: datetime | None = None


class RazorpayWebhookPayload(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event: str
    payload: dict
