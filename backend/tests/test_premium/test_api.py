from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from uuid import uuid4
from datetime import datetime
import pytest

from app.api.premium import router
import app.api.premium as premium_api
from app.core.database import get_db

test_app = FastAPI()
test_app.include_router(router, prefix="/api/v1/premium")
client = TestClient(test_app)


@pytest.fixture
def mock_db():
    return MagicMock()


def test_calculate_valid_worker(mock_db):
    test_app.dependency_overrides[get_db] = lambda: mock_db
    try:
        worker_id = str(uuid4())

        original_build_feature_vector = premium_api._build_feature_vector
        original_calculate_premium = premium_api.calculate_premium
        premium_api._build_feature_vector = MagicMock(
            return_value={
                "season_flag": "NE_monsoon",
                "delivery_baseline_30d": 120.0,
                "income_baseline_weekly": 4500.0,
                "open_meteo_7d_precip_probability": 0.4,
                "activity_consistency_score": 0.75,
                "historical_claim_rate_zone": 0.08,
                "tenure_discount_factor": 0.92,
            }
        )
        premium_api.calculate_premium = MagicMock(
            return_value={
                "premium_amount": 89.0,
                "model_used": "glm",
                "recency_multiplier": 1.0,
                "shap_top3": ["வெள்ள அபாய மண்டலம் (+₹12.0)"],
                "affordability_capped": False,
            }
        )

        mock_worker = MagicMock()
        mock_worker.id = worker_id
        mock_worker.enrollment_week = 3
        mock_worker.flood_hazard_tier = "medium"
        mock_worker.zone_cluster_id = 5
        mock_worker.platform = "zomato"
        mock_worker.language_preference = "tamil"

        mock_policy = MagicMock()
        mock_policy.id = str(uuid4())
        mock_policy.worker_id = worker_id

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.side_effect = [mock_worker, mock_policy]

        response = client.post("/api/v1/premium/calculate", json={"worker_id": worker_id})
        assert response.status_code == 200
        data = response.json()
        assert "premium_amount" in data
        assert "model_used" in data
        assert "tamil_explanation" in data
        assert data["model_used"] == "glm"
    finally:
        premium_api._build_feature_vector = original_build_feature_vector
        premium_api.calculate_premium = original_calculate_premium
        test_app.dependency_overrides.clear()


def test_calculate_unknown_worker(mock_db):
    test_app.dependency_overrides[get_db] = lambda: mock_db
    try:
        worker_id = str(uuid4())

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None

        response = client.post("/api/v1/premium/calculate", json={"worker_id": worker_id})
        assert response.status_code == 404
        assert response.json()["detail"] == "Worker not found"
    finally:
        test_app.dependency_overrides.clear()


def test_calculate_no_policy(mock_db):
    test_app.dependency_overrides[get_db] = lambda: mock_db
    try:
        worker_id = str(uuid4())

        mock_worker = MagicMock()
        mock_worker.id = worker_id
        mock_worker.enrollment_week = 5
        mock_worker.flood_hazard_tier = "medium"
        mock_worker.zone_cluster_id = 5
        mock_worker.platform = "zomato"
        mock_worker.language_preference = "tamil"

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        # first call returns worker, second (policy) returns None
        mock_filter.first.side_effect = [mock_worker, None]

        response = client.post("/api/v1/premium/calculate", json={"worker_id": worker_id})
        assert response.status_code == 404
        assert response.json()["detail"] == "Policy not found for worker"
    finally:
        test_app.dependency_overrides.clear()


def test_history_valid_worker(mock_db):
    test_app.dependency_overrides[get_db] = lambda: mock_db
    try:
        worker_id = str(uuid4())

        mock_worker = MagicMock()
        mock_worker.id = worker_id

        mock_policy = MagicMock()
        mock_policy.coverage_week_number = 1
        mock_policy.weekly_premium_amount = 75.0
        mock_policy.model_used = "glm"
        mock_policy.shap_explanation_json = {}
        mock_policy.updated_at = datetime.now()

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = mock_worker

        mock_order = MagicMock()
        mock_filter.order_by.return_value = mock_order
        mock_order.all.return_value = [mock_policy]

        response = client.get(f"/api/v1/premium/history/{worker_id}")
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert len(data["history"]) == 1
    finally:
        test_app.dependency_overrides.clear()


def test_history_unknown_worker(mock_db):
    test_app.dependency_overrides[get_db] = lambda: mock_db
    try:
        worker_id = str(uuid4())

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None

        response = client.get(f"/api/v1/premium/history/{worker_id}")
        assert response.status_code == 404
        assert response.json()["detail"] == "Worker not found"
    finally:
        test_app.dependency_overrides.clear()


def test_renew_valid_worker(mock_db):
    test_app.dependency_overrides[get_db] = lambda: mock_db
    try:
        worker_id = str(uuid4())

        original_build_feature_vector = premium_api._build_feature_vector
        original_calculate_premium = premium_api.calculate_premium
        premium_api._build_feature_vector = MagicMock(
            return_value={
                "season_flag": "NE_monsoon",
                "delivery_baseline_30d": 130.0,
                "income_baseline_weekly": 4800.0,
                "open_meteo_7d_precip_probability": 0.45,
                "activity_consistency_score": 0.8,
                "historical_claim_rate_zone": 0.07,
                "tenure_discount_factor": 0.9,
            }
        )
        premium_api.calculate_premium = MagicMock(
            return_value={
                "premium_amount": 95.0,
                "model_used": "lgbm",
                "recency_multiplier": 1.0,
                "shap_top3": ["வெள்ள அபாய மண்டலம் (+₹15.0)"],
                "affordability_capped": False,
            }
        )

        mock_worker = MagicMock()
        mock_worker.id = worker_id
        mock_worker.enrollment_week = 6
        mock_worker.flood_hazard_tier = "medium"
        mock_worker.zone_cluster_id = 5
        mock_worker.platform = "zomato"
        mock_worker.language_preference = "tamil"

        mock_policy = MagicMock()
        mock_policy.id = str(uuid4())
        mock_policy.worker_id = worker_id

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.side_effect = [mock_worker, mock_policy]

        response = client.post(
            "/api/v1/premium/renew",
            json={"worker_id": worker_id},
            headers={"X-Admin-Key": "gigshield-admin"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "premium_amount" in data
        assert data["model_used"] == "lgbm"
        assert "tamil_explanation" in data
    finally:
        premium_api._build_feature_vector = original_build_feature_vector
        premium_api.calculate_premium = original_calculate_premium
        test_app.dependency_overrides.clear()
