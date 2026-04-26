from pydantic import BaseModel
from typing import List
from uuid import UUID
from datetime import datetime

class PremiumCalculateRequest(BaseModel):
    worker_id: UUID

class PremiumCalculateResponse(BaseModel):
    premium_amount: float
    model_used: str
    recency_multiplier: float
    shap_top3: List[str]
    affordability_capped: bool
    tamil_explanation: str

class PremiumHistoryItem(BaseModel):
    week_number: int
    premium_amount: float
    model_used: str
    shap_explanation_json: list | dict | None
    calculated_at: datetime

class PremiumHistoryResponse(BaseModel):
    worker_id: UUID
    history: List[PremiumHistoryItem]

class PremiumRenewRequest(BaseModel):
    worker_id: UUID
