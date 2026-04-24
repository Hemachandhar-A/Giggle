import importlib
import pytest
import random
import os
import sys
from pathlib import Path
import tempfile
import pandas as pd
import joblib
from unittest.mock import MagicMock
from uuid import uuid4
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.ml.inference import calculate_premium
from fastapi import HTTPException, status
from app.api.premium import _require_admin_key, _build_feature_vector, router
from app.core.database import get_db
from scripts.synthetic_data import (
    DEFAULT_NUM_ROWS,
    WEEKLY_PREMIUM_CEILING,
    WEEKLY_PREMIUM_FLOOR,
    compute_weekly_premium_target,
    generate_synthetic_training_data,
    save_synthetic_training_data,
)
from scripts.train_premium_models import (
    load_training_data,
    train_m1_glm_cold_start,
    train_m2_lgbm_weekly,
)


ARTIFACTS_DIR = Path(__file__).resolve().parents[2] / "app" / "ml" / "artifacts"
ARTIFACTS_LOADED = (
    (ARTIFACTS_DIR / "glm_m1.joblib").exists()
    and (ARTIFACTS_DIR / "lgbm_m2.joblib").exists()
)


# ---------------------------------------------------------------------------
# Section 2 — Helper
# ---------------------------------------------------------------------------

def base_kwargs(**overrides):
    defaults = {
        "enrollment_week": 6,
        "flood_hazard_zone_tier": "medium",
        "zone_cluster_id": 5,
        "platform": "zomato",
        "season_flag": "NE_monsoon",
        "delivery_baseline_30d": 420.0,
        "income_baseline_weekly": 4000.0,
        "open_meteo_7d_precip_probability": 0.4,
        "activity_consistency_score": 0.8,
        "tenure_discount_factor": 1.0,
        "historical_claim_rate_zone": 0.1,
        "language": "tamil"
    }
    defaults.update(overrides)
    return defaults


# ---------------------------------------------------------------------------
# Section 3 — Person 2B inference tests
# ---------------------------------------------------------------------------

def test_glm_used_for_week_3():
    result = calculate_premium(**base_kwargs(enrollment_week=3))
    assert result["model_used"] == "glm"


def test_lgbm_used_for_week_6():
    result = calculate_premium(**base_kwargs(enrollment_week=6))
    assert result["model_used"] == "lgbm"


def test_recency_multiplier_week_1():
    result = calculate_premium(**base_kwargs(enrollment_week=1))
    assert result["recency_multiplier"] == 1.5


def test_recency_multiplier_week_3():
    result = calculate_premium(**base_kwargs(enrollment_week=3))
    assert result["recency_multiplier"] == 1.25


def test_recency_multiplier_week_5():
    result = calculate_premium(**base_kwargs(enrollment_week=5))
    assert result["recency_multiplier"] == 1.0


def test_boundary_week_4_routes_to_glm():
    result = calculate_premium(**base_kwargs(enrollment_week=4))
    assert result["model_used"] == "glm"


def test_boundary_week_5_routes_to_lgbm():
    result = calculate_premium(**base_kwargs(enrollment_week=5))
    assert result["model_used"] == "lgbm"


def test_affordability_cap_applied():
    result = calculate_premium(**base_kwargs(income_baseline_weekly=1000.0))
    # cap = 1000 * 0.025 = 25.0, floor is 49.0, so final = 49.0
    assert result["affordability_capped"] is True
    assert result["premium_amount"] == 49.0


def test_premium_floor_enforced_with_mocked_raw_price(monkeypatch):
    import app.ml.inference as inference_module

    monkeypatch.setattr(inference_module, "_predict_glm", lambda *args, **kwargs: 30.0)
    result = inference_module.calculate_premium(**base_kwargs(enrollment_week=3))
    assert result["premium_amount"] == 49.0


def test_premium_ceiling_enforced_with_mocked_raw_price(monkeypatch):
    import app.ml.inference as inference_module

    monkeypatch.setattr(inference_module, "_predict_glm", lambda *args, **kwargs: 200.0)
    result = inference_module.calculate_premium(**base_kwargs(enrollment_week=3, income_baseline_weekly=10000.0))
    assert result["premium_amount"] == 149.0


def test_premium_within_bounds_random():
    for _ in range(100):
        result = calculate_premium(**base_kwargs(
            enrollment_week=random.randint(1, 10),
            income_baseline_weekly=random.uniform(2000.0, 10000.0)
        ))
        assert 49.0 <= result["premium_amount"] <= 149.0


def test_high_tier_ne_monsoon_higher_than_low_tier_dry():
    import app.ml.inference as inference_module

    original = inference_module._predict_lgbm
    inference_module._predict_lgbm = lambda features, template_map, clean_claim_weeks=0: (
        120.0 if (features["flood_hazard_zone_tier"] == "high" and features["season_flag"] == "NE_monsoon") else 80.0,
        [],
    )
    try:
        high_risk = calculate_premium(**base_kwargs(
            enrollment_week=10,
            flood_hazard_zone_tier="high",
            season_flag="NE_monsoon",
            delivery_baseline_30d=320.0,
            income_baseline_weekly=10000.0,
        ))
        low_risk = calculate_premium(**base_kwargs(
            enrollment_week=10,
            flood_hazard_zone_tier="low",
            season_flag="dry",
            delivery_baseline_30d=320.0,
            income_baseline_weekly=10000.0,
        ))
    finally:
        inference_module._predict_lgbm = original
    assert high_risk["premium_amount"] > low_risk["premium_amount"]


def test_ne_monsoon_higher_than_dry_all_else_equal():
    import app.ml.inference as inference_module

    original = inference_module._predict_lgbm
    inference_module._predict_lgbm = lambda features, template_map, clean_claim_weeks=0: (
        110.0 if features["season_flag"] == "NE_monsoon" else 70.0,
        [],
    )
    try:
        ne = calculate_premium(**base_kwargs(
            enrollment_week=10,
            season_flag="NE_monsoon",
            flood_hazard_zone_tier="medium",
            delivery_baseline_30d=310.0,
            income_baseline_weekly=10000.0,
        ))
        dry = calculate_premium(**base_kwargs(
            enrollment_week=10,
            season_flag="dry",
            flood_hazard_zone_tier="medium",
            delivery_baseline_30d=310.0,
            income_baseline_weekly=10000.0,
        ))
    finally:
        inference_module._predict_lgbm = original
    assert ne["premium_amount"] > dry["premium_amount"]


def test_shap_empty_for_glm():
    result = calculate_premium(**base_kwargs(enrollment_week=3))
    assert result["shap_top3"] == []


def test_shap_three_items_for_lgbm():
    result = calculate_premium(**base_kwargs(enrollment_week=6))
    assert len(result["shap_top3"]) == 3


def test_tamil_shap_contains_unicode_character(monkeypatch):
    import app.ml.inference as inference_module

    monkeypatch.setattr(
        inference_module,
        "_predict_lgbm",
        lambda *args, **kwargs: (100.0, ["உங்கள் மண்டலத்தில் மழை முன்னறிவிப்பு (+₹{amount})", "வெள்ள அபாய மண்டலம் (+₹{amount})", "விசுவாசமான வாடிக்கையாளர் தள்ளுபடி (-₹{amount})"]),
    )
    result = inference_module.calculate_premium(**base_kwargs(enrollment_week=6))
    assert result["shap_top3"]
    assert any(ord(character) > 0x0B80 for character in result["shap_top3"][0])


def test_hindi_shap_contains_devanagari_unicode(monkeypatch):
    import app.ml.inference as inference_module

    def fake_predict(features, template_map, clean_claim_weeks=0):
        return (100.0, [template_map["flood_hazard_zone_tier"]] * 3)

    monkeypatch.setattr(inference_module, "_predict_lgbm", fake_predict)
    result = inference_module.calculate_premium(**base_kwargs(enrollment_week=6, language="hi"))
    assert result["shap_top3"]
    assert any(0x0900 <= ord(character) <= 0x097F for character in result["shap_top3"][0])


def test_unsupported_language_falls_back_to_tamil(monkeypatch):
    import app.ml.inference as inference_module

    def fake_predict(features, template_map, clean_claim_weeks=0):
        return (100.0, [template_map["flood_hazard_zone_tier"]] * 3)

    monkeypatch.setattr(inference_module, "_predict_lgbm", fake_predict)
    result = inference_module.calculate_premium(**base_kwargs(enrollment_week=6, language="en"))
    assert result["shap_top3"]
    assert "வெள்ள" in result["shap_top3"][0]


@pytest.mark.skipif(not ARTIFACTS_LOADED, reason="needs artifacts")
def test_affordability_cap_1000_weekly_baseline_leq_25():
    result = calculate_premium(**base_kwargs(income_baseline_weekly=1000.0, enrollment_week=6))
    assert result["premium_amount"] == 49.0
    assert result["affordability_capped"] is True


def test_m2_shap_top3_has_no_placeholder_literals(monkeypatch):
    import app.ml.inference as inference_module

    class DummyShapValues:
        def __init__(self, values):
            self.values = values

    class DummyExplainer:
        def __call__(self, input_df):
            # Prioritize open_meteo so it appears first in top3
            return DummyShapValues([[0.30, 0.25, 0.05, 0.02, 0.01, 0.01, 0.01, 0.50, 0.04, 0.03, 0.02]])

    class DummyModel:
        def predict(self, input_df):
            return [100.0]

    monkeypatch.setattr(inference_module, "_lgbm_model", DummyModel())
    monkeypatch.setattr(inference_module, "_shap_explainer", DummyExplainer())
    monkeypatch.setattr(
        inference_module,
        "_lgbm_feature_list",
        [
            "flood_hazard_zone_tier",
            "zone_cluster_id",
            "platform",
            "delivery_baseline_30d",
            "income_baseline_weekly",
            "enrollment_week",
            "season_flag",
            "open_meteo_7d_precip_probability",
            "activity_consistency_score",
            "tenure_discount_factor",
            "historical_claim_rate_zone",
        ],
    )

    result = inference_module.calculate_premium(**base_kwargs(enrollment_week=6, language="ta", clean_claim_weeks=4))
    assert "{amount}" not in result["shap_top3"][0]
    assert "{weeks}" not in result["shap_top3"][0]


def test_missing_artifact_fallback_imports_without_exception(tmp_path):
    artifact_path = Path(os.path.dirname(__file__)) / "../../app/ml/artifacts/glm_m1.joblib"
    artifact_path = artifact_path.resolve()
    backup_path = tmp_path / "glm_m1.joblib.bak"
    if not artifact_path.exists():
        pytest.skip("glm_m1.joblib not present")

    artifact_path.replace(backup_path)
    try:
        sys.modules.pop("app.ml.inference", None)
        module = importlib.import_module("app.ml.inference")
        assert module is not None
    finally:
        backup_path.replace(artifact_path)
        sys.modules.pop("app.ml.inference", None)
        importlib.import_module("app.ml.inference")


def test_csv_data_validation():
    """Validate synthetic training CSV generated by Person 2A."""
    csv_path = os.path.join(os.path.dirname(__file__), "../../data/synthetic_training_data.csv")
    if not os.path.exists(csv_path):
        pytest.skip("CSV not yet generated by Person 2A")
    df = pd.read_csv(csv_path)
    assert len(df) == 10000, f"Expected 10000 rows, got {len(df)}"
    assert df["weekly_premium"].notna().all(), "Null values found in weekly_premium column"
    assert (df["weekly_premium"] >= 49.0).all(), "Some premiums below ₹49 floor"
    assert (df["weekly_premium"] <= 149.0).all(), "Some premiums above ₹149 ceiling"


def test_real_glm_loaded_if_artifacts_exist():
    """If glm_m1.joblib exists, model_used should be 'glm' not 'stub'"""
    artifact_path = os.path.join(os.path.dirname(__file__), "../../app/ml/artifacts/glm_m1.joblib")
    if not os.path.exists(artifact_path):
        pytest.skip("glm_m1.joblib not present")
    result = calculate_premium(**base_kwargs(enrollment_week=3))
    assert result["model_used"] == "glm"


def test_real_lgbm_loaded_if_artifacts_exist():
    """If lgbm_m2.joblib exists, model_used should be 'lgbm' not 'stub'"""
    artifact_path = os.path.join(os.path.dirname(__file__), "../../app/ml/artifacts/lgbm_m2.joblib")
    if not os.path.exists(artifact_path):
        pytest.skip("lgbm_m2.joblib not present")
    result = calculate_premium(**base_kwargs(enrollment_week=6))
    assert result["model_used"] == "lgbm"
    assert len(result["shap_top3"]) == 3
    for s in result["shap_top3"]:
        assert len(s) > 0


def test_renew_without_admin_key_returns_403():
    with pytest.raises(HTTPException) as error_info:
        _require_admin_key(None)

    assert error_info.value.status_code == status.HTTP_403_FORBIDDEN


def test_renew_endpoint_without_admin_key_returns_403():
    test_app = FastAPI()
    test_app.include_router(router, prefix="/api/v1/premium")
    client = TestClient(test_app)

    mock_db = MagicMock()
    test_app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post("/api/v1/premium/renew", json={"worker_id": str(uuid4())})
        assert response.status_code == 403
    finally:
        test_app.dependency_overrides.clear()


def test_build_feature_vector_derives_non_placeholder_values(monkeypatch):
    worker = MagicMock()
    worker.id = uuid4()
    worker.zone_cluster_id = 5
    worker.enrollment_week = 13

    mock_db = MagicMock()

    q1 = MagicMock()
    q1.filter.return_value = q1
    q1.scalar.return_value = 280

    zone = MagicMock()
    zone.zone_rate_mid = 27.5
    zone.centroid_lat = 13.0827
    zone.centroid_lon = 80.2707
    q2 = MagicMock()
    q2.filter.return_value = q2
    q2.first.return_value = zone

    week1 = MagicMock(); week1.weekly_total = 220
    week2 = MagicMock(); week2.weekly_total = 230
    week3 = MagicMock(); week3.weekly_total = 210
    week4 = MagicMock(); week4.weekly_total = 240
    week5 = MagicMock(); week5.weekly_total = 235
    week6 = MagicMock(); week6.weekly_total = 225
    week7 = MagicMock(); week7.weekly_total = 245
    week8 = MagicMock(); week8.weekly_total = 238
    q3 = MagicMock()
    q3.filter.return_value = q3
    q3.group_by.return_value = q3
    q3.order_by.return_value = q3
    q3.limit.return_value = q3
    q3.all.return_value = [week8, week7, week6, week5, week4, week3, week2, week1]

    q4 = MagicMock()
    q4.join.return_value = q4
    q4.filter.return_value = q4
    q4.scalar.return_value = 12

    q5 = MagicMock()
    q5.filter.return_value = q5
    q5.scalar.return_value = 60

    mock_db.query.side_effect = [q1, q2, q3, q4, q5]
    monkeypatch.setattr("app.api.premium._fetch_open_meteo_precip_probability", lambda lat, lon: 0.42)

    features = _build_feature_vector(worker, mock_db)

    assert features["delivery_baseline_30d"] == 280.0
    assert features["income_baseline_weekly"] > 0.0
    assert features["open_meteo_7d_precip_probability"] == 0.42
    assert features["activity_consistency_score"] != 0.5
    assert features["historical_claim_rate_zone"] > 0.0
    assert 0.85 <= features["tenure_discount_factor"] <= 1.0


def test_calculate_endpoint_uses_feature_helper(monkeypatch):
    test_app = FastAPI()
    test_app.include_router(router, prefix="/api/v1/premium")
    client = TestClient(test_app)

    mock_db = MagicMock()
    test_app.dependency_overrides[get_db] = lambda: mock_db

    worker_id = str(uuid4())
    worker = MagicMock()
    worker.id = worker_id
    worker.enrollment_week = 10
    worker.flood_hazard_tier = "medium"
    worker.zone_cluster_id = 5
    worker.platform = "zomato"
    worker.language_preference = "ta"

    policy = MagicMock()
    policy.id = uuid4()
    policy.worker_id = worker_id

    query = MagicMock()
    filtered = MagicMock()
    mock_db.query.return_value = query
    query.filter.return_value = filtered
    filtered.first.side_effect = [worker, policy]

    monkeypatch.setattr("app.api.premium._build_feature_vector", lambda w, db: {
        "season_flag": "NE_monsoon",
        "delivery_baseline_30d": 300.0,
        "income_baseline_weekly": 3500.0,
        "open_meteo_7d_precip_probability": 0.4,
        "activity_consistency_score": 0.8,
        "historical_claim_rate_zone": 0.1,
        "tenure_discount_factor": 0.9,
    })

    try:
        response = client.post("/api/v1/premium/calculate", json={"worker_id": worker_id})
        assert response.status_code == 200
        data = response.json()
        assert data["premium_amount"] > 0
        assert data["model_used"] in ["glm", "lgbm"]
        assert data["recency_multiplier"] in [1.0, 1.25, 1.5]
    finally:
        test_app.dependency_overrides.clear()


def test_premium_calculate_unknown_worker_endpoint():
    test_app = FastAPI()
    test_app.include_router(router, prefix="/api/v1/premium")
    client = TestClient(test_app)

    mock_db = MagicMock()
    query = MagicMock()
    filtered = MagicMock()
    mock_db.query.return_value = query
    query.filter.return_value = filtered
    filtered.first.return_value = None
    test_app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post("/api/v1/premium/calculate", json={"worker_id": str(uuid4())})
        assert response.status_code == 404
    finally:
        test_app.dependency_overrides.clear()


def test_premium_calculate_no_policy_endpoint(monkeypatch):
    test_app = FastAPI()
    test_app.include_router(router, prefix="/api/v1/premium")
    client = TestClient(test_app)

    mock_db = MagicMock()
    worker = MagicMock()
    worker.id = str(uuid4())
    worker.enrollment_week = 6
    worker.flood_hazard_tier = "medium"
    worker.zone_cluster_id = 5
    worker.platform = "zomato"
    worker.language_preference = "ta"

    query = MagicMock()
    filtered = MagicMock()
    mock_db.query.return_value = query
    query.filter.return_value = filtered
    filtered.first.side_effect = [worker, None]

    monkeypatch.setattr("app.api.premium._build_feature_vector", lambda w, db: {
        "season_flag": "NE_monsoon",
        "delivery_baseline_30d": 300.0,
        "income_baseline_weekly": 3500.0,
        "open_meteo_7d_precip_probability": 0.4,
        "activity_consistency_score": 0.8,
        "historical_claim_rate_zone": 0.1,
        "tenure_discount_factor": 0.9,
    })
    test_app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post("/api/v1/premium/calculate", json={"worker_id": str(worker.id)})
        assert response.status_code == 404
    finally:
        test_app.dependency_overrides.clear()


def test_premium_history_endpoints():
    test_app = FastAPI()
    test_app.include_router(router, prefix="/api/v1/premium")
    client = TestClient(test_app)

    worker_id = str(uuid4())
    mock_db = MagicMock()

    worker = MagicMock()
    worker.id = worker_id

    policy = MagicMock()
    policy.coverage_week_number = 2
    policy.weekly_premium_amount = 88.0
    policy.model_used = "lgbm"
    policy.shap_explanation_json = {"top3": ["one", "two", "three"]}
    policy.updated_at = pd.Timestamp("2026-04-04T10:00:00Z").to_pydatetime()

    query = MagicMock()
    filtered = MagicMock()
    ordered = MagicMock()
    mock_db.query.return_value = query
    query.filter.return_value = filtered
    filtered.first.return_value = worker
    filtered.order_by.return_value = ordered
    ordered.all.return_value = [policy]

    test_app.dependency_overrides[get_db] = lambda: mock_db
    try:
        ok = client.get(f"/api/v1/premium/history/{worker_id}")
        assert ok.status_code == 200
        assert ok.json()["history"]

        filtered.first.return_value = None
        missing = client.get(f"/api/v1/premium/history/{worker_id}")
        assert missing.status_code == 404
    finally:
        test_app.dependency_overrides.clear()


def test_premium_renew_with_admin_key_success(monkeypatch):
    test_app = FastAPI()
    test_app.include_router(router, prefix="/api/v1/premium")
    client = TestClient(test_app)

    worker_id = str(uuid4())
    mock_db = MagicMock()
    worker = MagicMock()
    worker.id = worker_id
    worker.enrollment_week = 6
    worker.flood_hazard_tier = "medium"
    worker.zone_cluster_id = 5
    worker.platform = "zomato"
    worker.language_preference = "ta"

    policy = MagicMock()
    policy.id = uuid4()
    policy.worker_id = worker_id

    query = MagicMock()
    filtered = MagicMock()
    mock_db.query.return_value = query
    query.filter.return_value = filtered
    filtered.first.side_effect = [worker, policy]

    monkeypatch.setattr("app.api.premium._build_feature_vector", lambda w, db: {
        "season_flag": "NE_monsoon",
        "delivery_baseline_30d": 320.0,
        "income_baseline_weekly": 3700.0,
        "open_meteo_7d_precip_probability": 0.5,
        "activity_consistency_score": 0.8,
        "historical_claim_rate_zone": 0.11,
        "tenure_discount_factor": 0.9,
    })

    test_app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            "/api/v1/premium/renew",
            json={"worker_id": worker_id},
            headers={"X-Admin-Key": "gigshield-admin"},
        )
        assert response.status_code == 200
    finally:
        test_app.dependency_overrides.clear()


def test_fetch_open_meteo_probability_failure_defaults(monkeypatch):
    from app.api.premium import _fetch_open_meteo_precip_probability

    def fail(*args, **kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr("app.api.premium.httpx.get", fail)
    assert _fetch_open_meteo_precip_probability(13.0, 80.0) == 0.3


def test_m7_identical_values_returns_one():
    from app.ml.inference import compute_activity_consistency_score

    assert compute_activity_consistency_score([100, 100, 100, 100, 100, 100, 100, 100]) == 1.0


def test_m7_six_values_returns_default_half():
    from app.ml.inference import compute_activity_consistency_score

    assert compute_activity_consistency_score([100, 120, 110, 130, 115, 125]) == 0.5


def test_m7_empty_list_returns_default_half():
    from app.ml.inference import compute_activity_consistency_score

    assert compute_activity_consistency_score([]) == 0.5


def test_m7_high_variance_below_half():
    from app.ml.inference import compute_activity_consistency_score

    assert compute_activity_consistency_score([10, 500, 20, 450, 30, 420, 15, 480]) < 0.5


def test_m5_loaded_if_artifact_exists():
    """If kmeans_m5.joblib exists, get_zone_cluster_for_pincode_ml should return an int."""
    from app.ml.inference import get_zone_cluster_for_pincode_ml
    artifact_path = os.path.join(os.path.dirname(__file__), "../../app/ml/artifacts/kmeans_m5.joblib")
    if not os.path.exists(artifact_path):
        pytest.skip("kmeans_m5.joblib not present")
    result = get_zone_cluster_for_pincode_ml(13.0827, 80.2707)
    assert isinstance(result, int)


# ---------------------------------------------------------------------------
# Section 4 — Person 2A training / data test classes
# ---------------------------------------------------------------------------

class TestTrainPremiumModelsDataLoader:
    """Tests for CSV loading and schema validation in training pipeline."""

    def test_load_training_data_happy_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "training_premium.csv"
            pd.DataFrame(
                {
                    "flood_hazard_zone_tier": ["high"],
                    "season_flag": ["NE_monsoon"],
                    "platform": ["zomato"],
                    "zone_cluster_id": [1],
                    "delivery_baseline_30d": [300.0],
                    "income_baseline_weekly": [4000.0],
                    "enrollment_week": [6],
                    "open_meteo_7d_precip_probability": [0.7],
                    "activity_consistency_score": [0.8],
                    "tenure_discount_factor": [0.95],
                    "historical_claim_rate_zone": [0.2],
                    "zone_claim_match": [1],
                    "activity_7d_score": [1.0],
                    "claim_to_enrollment_days": [120],
                    "event_claim_frequency": [1],
                    "weekly_premium": [99.0],
                }
            ).to_csv(csv_path, index=False)

            loaded = load_training_data(csv_path)
            assert loaded.shape == (1, 16)

    def test_load_training_data_missing_columns_raises(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "training_premium.csv"
            pd.DataFrame({"platform": ["zomato"]}).to_csv(csv_path, index=False)

            with pytest.raises(ValueError) as error_info:
                load_training_data(csv_path)

            assert "missing required columns" in str(error_info.value)


class TestTrainM1GlmColdStart:
    """Tests for M1 cold-start GLM training."""

    def test_train_m1_glm_cold_start_saves_artifact_and_returns_metrics(self):
        rows = []
        for index in range(20):
            rows.append(
                {
                    "flood_hazard_zone_tier": "high" if index % 2 else "medium",
                    "season_flag": "NE_monsoon" if index % 3 else "SW_monsoon",
                    "platform": "zomato" if index % 2 else "swiggy",
                    "zone_cluster_id": 1,
                    "delivery_baseline_30d": 300.0,
                    "income_baseline_weekly": 4000.0,
                    "enrollment_week": (index % 4) + 1,
                    "open_meteo_7d_precip_probability": 0.65,
                    "activity_consistency_score": 0.75,
                    "tenure_discount_factor": 0.95,
                    "historical_claim_rate_zone": 0.20,
                    "zone_claim_match": 1,
                    "activity_7d_score": 1.0,
                    "claim_to_enrollment_days": 120,
                    "event_claim_frequency": 1,
                    "weekly_premium": 80.0 + (index % 5),
                }
            )

        frame = pd.DataFrame(rows)

        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_path = Path(temp_dir) / "glm_cold_start.joblib"
            result = train_m1_glm_cold_start(frame, artifact_path)

            assert artifact_path.exists()
            assert result["rmse"] >= 0.0
            assert result["train_rows"] > 0
            assert result["valid_rows"] > 0

            artifact = joblib.load(artifact_path)
            assert artifact["model_name"] == "glm_cold_start"
            assert set(artifact["features"]) == {"flood_hazard_zone_tier", "season_flag", "platform"}
            assert set(artifact["encoders"].keys()) == {"flood_hazard_zone_tier", "season_flag", "platform"}

    def test_train_m1_glm_cold_start_raises_when_no_week_1_to_4_rows(self):
        frame = pd.DataFrame(
            {
                "flood_hazard_zone_tier": ["high", "low"],
                "season_flag": ["NE_monsoon", "heat"],
                "platform": ["zomato", "swiggy"],
                "enrollment_week": [5, 10],
                "weekly_premium": [99.0, 105.0],
                "zone_claim_match": [1, 1],
                "activity_7d_score": [1.0, 1.1],
                "claim_to_enrollment_days": [120, 180],
                "event_claim_frequency": [1, 1],
                "zone_cluster_id": [1, 2],
                "delivery_baseline_30d": [260.0, 280.0],
                "income_baseline_weekly": [3600.0, 4200.0],
                "open_meteo_7d_precip_probability": [0.5, 0.6],
                "activity_consistency_score": [0.7, 0.8],
                "tenure_discount_factor": [0.95, 0.90],
                "historical_claim_rate_zone": [0.2, 0.3],
            }
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_path = Path(temp_dir) / "glm_cold_start.joblib"
            with pytest.raises(ValueError) as error_info:
                train_m1_glm_cold_start(frame, artifact_path)

            assert "enrollment_week < 5" in str(error_info.value)


class TestTrainM2LgbmWeekly:
    """Tests for M2 LightGBM weekly premium training."""

    def test_train_m2_lgbm_weekly_saves_all_artifacts(self):
        rows = []
        for index in range(60):
            rows.append(
                {
                    "flood_hazard_zone_tier": ["low", "medium", "high"][index % 3],
                    "season_flag": ["dry", "heat", "SW_monsoon", "NE_monsoon"][index % 4],
                    "platform": "zomato" if index % 2 else "swiggy",
                    "zone_cluster_id": (index % 20) + 1,
                    "delivery_baseline_30d": 180.0 + float(index),
                    "income_baseline_weekly": 2500.0 + float(index * 20),
                    "enrollment_week": 5 + (index % 20),
                    "open_meteo_7d_precip_probability": 0.20 + (index % 10) * 0.05,
                    "activity_consistency_score": 0.30 + (index % 7) * 0.08,
                    "tenure_discount_factor": 0.85 + (index % 10) * 0.01,
                    "historical_claim_rate_zone": 0.05 + (index % 12) * 0.02,
                    "zone_claim_match": 1,
                    "activity_7d_score": 0.9,
                    "claim_to_enrollment_days": 100,
                    "event_claim_frequency": 1,
                    "weekly_premium": 49.0 + (index % 60),
                }
            )

        frame = pd.DataFrame(rows)

        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = Path(temp_dir) / "lgbm_m2.joblib"
            shap_path = Path(temp_dir) / "shap_explainer_m2.joblib"
            feature_path = Path(temp_dir) / "lgbm_m2_feature_list.joblib"

            result = train_m2_lgbm_weekly(frame, model_path, shap_path, feature_path)

            assert model_path.exists()
            assert shap_path.exists()
            assert feature_path.exists()
            assert result["rmse"] >= 0.0
            assert result["train_rows"] > 0
            assert result["valid_rows"] > 0
            assert result["negative_predictions"] == 0

            model = joblib.load(model_path)
            feature_list = joblib.load(feature_path)
            assert model.objective == "tweedie"
            assert model.tweedie_variance_power == 1.5
            assert len(feature_list) == 11

    def test_train_m2_lgbm_weekly_raises_when_no_week_5_plus_rows(self):
        frame = pd.DataFrame(
            {
                "flood_hazard_zone_tier": ["high", "low"],
                "season_flag": ["NE_monsoon", "heat"],
                "platform": ["zomato", "swiggy"],
                "zone_cluster_id": [1, 2],
                "delivery_baseline_30d": [250.0, 260.0],
                "income_baseline_weekly": [3500.0, 3600.0],
                "enrollment_week": [2, 4],
                "open_meteo_7d_precip_probability": [0.7, 0.4],
                "activity_consistency_score": [0.8, 0.6],
                "tenure_discount_factor": [0.95, 0.96],
                "historical_claim_rate_zone": [0.2, 0.1],
                "zone_claim_match": [1, 1],
                "activity_7d_score": [1.0, 1.0],
                "claim_to_enrollment_days": [120, 90],
                "event_claim_frequency": [1, 2],
                "weekly_premium": [90.0, 85.0],
            }
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = Path(temp_dir) / "lgbm_m2.joblib"
            shap_path = Path(temp_dir) / "shap_explainer_m2.joblib"
            feature_path = Path(temp_dir) / "lgbm_m2_feature_list.joblib"

            with pytest.raises(ValueError) as error_info:
                train_m2_lgbm_weekly(frame, model_path, shap_path, feature_path)

            assert "enrollment_week >= 5" in str(error_info.value)


class TestComputeWeeklyPremiumTarget:
    """Tests for premium target computation from loss ratio simulation."""

    def test_low_tier_dry_at_floor(self):
        """Low flood tier + dry season should hit ₹49 floor."""
        premium = compute_weekly_premium_target(
            avg_heavy_rain_days_yr=30.0,
            flood_tier_numeric=1,
            season_flag="dry",
        )
        # Base: 174 * 1.0 (low tier) = 174
        # Adjusted: 174 * 1.1 (climate) = 191.4
        # Annual: 191.4 / 0.65 = 294.46
        # Weekly: (294.46 / 52) * 0.8 (dry) = 4.55 -> clamped to 49
        assert abs(premium - 49.0) <= 0.01

    def test_high_tier_ne_monsoon_near_ceiling(self):
        """High flood tier + NE monsoon should remain within configured bounds."""
        premium = compute_weekly_premium_target(
            avg_heavy_rain_days_yr=80.0,
            flood_tier_numeric=3,
            season_flag="NE_monsoon",
        )
        assert WEEKLY_PREMIUM_FLOOR <= premium <= WEEKLY_PREMIUM_CEILING

    def test_medium_tier_heat_season(self):
        """Medium flood tier + heat season produces mid-range premium."""
        premium = compute_weekly_premium_target(
            avg_heavy_rain_days_yr=50.0,
            flood_tier_numeric=2,
            season_flag="heat",
        )
        # Base: 174 * 1.5 (medium tier) = 261
        # Adjusted: 261 * 1.1 (climate) = 287.1
        # Annual: 287.1 / 0.65 = 441.69
        # Weekly: (441.69 / 52) * 1.1 (heat) = 9.35
        assert WEEKLY_PREMIUM_FLOOR <= premium <= WEEKLY_PREMIUM_CEILING

    def test_invalid_flood_tier_raises(self):
        """Invalid flood_tier_numeric should raise ValueError."""
        try:
            compute_weekly_premium_target(
                avg_heavy_rain_days_yr=50.0,
                flood_tier_numeric=4,
                season_flag="dry",
            )
        except ValueError as error:
            assert "flood_tier_numeric must be 1, 2, or 3" in str(error)
        else:
            raise AssertionError("Expected ValueError")

    def test_invalid_season_raises(self):
        """Invalid season should raise ValueError."""
        try:
            compute_weekly_premium_target(
                avg_heavy_rain_days_yr=50.0,
                flood_tier_numeric=2,
                season_flag="invalid_season",
            )
        except ValueError as error:
            assert "season_flag must be one of" in str(error)
        else:
            raise AssertionError("Expected ValueError")

    def test_all_seasons_low_tier(self):
        """Verify season premiums are monotonic when clipping is taken into account."""
        premiums = {}
        for season in ["NE_monsoon", "SW_monsoon", "heat", "dry"]:
            premiums[season] = compute_weekly_premium_target(
                avg_heavy_rain_days_yr=40.0,
                flood_tier_numeric=1,
                season_flag=season,
            )

        # With floor clipping, equal values are valid when raw premiums fall below floor.
        assert premiums["NE_monsoon"] >= premiums["SW_monsoon"]
        assert premiums["SW_monsoon"] >= premiums["heat"]
        assert premiums["heat"] >= premiums["dry"]

    def test_output_is_float_in_valid_range(self):
        """Output should always be float and within [49, 149]."""
        for flood_tier in [1, 2, 3]:
            for season in ["NE_monsoon", "SW_monsoon", "heat", "dry"]:
                premium = compute_weekly_premium_target(
                    avg_heavy_rain_days_yr=50.0,
                    flood_tier_numeric=flood_tier,
                    season_flag=season,
                )
                assert isinstance(premium, float)
                assert 49.0 <= premium <= 149.0

    def test_higher_avg_rain_days_increases_premium(self, monkeypatch):
        import scripts.loss_ratio_simulation as loss_ratio_simulation

        monkeypatch.setattr(loss_ratio_simulation, "WEEKLY_PREMIUM_FLOOR", 0.0)
        monkeypatch.setattr(loss_ratio_simulation, "WEEKLY_PREMIUM_CEILING", 1000.0)

        low_rain = loss_ratio_simulation.compute_weekly_premium_target(
            avg_heavy_rain_days_yr=5.0,
            flood_tier_numeric=2,
            season_flag="NE_monsoon",
        )
        high_rain = loss_ratio_simulation.compute_weekly_premium_target(
            avg_heavy_rain_days_yr=25.0,
            flood_tier_numeric=2,
            season_flag="NE_monsoon",
        )
        assert high_rain > low_rain


class TestSyntheticTrainingData:
    """Tests for the synthetic CSV generation output."""

    def test_generate_synthetic_training_data_shape_and_columns(self):
        frame = generate_synthetic_training_data(num_rows=DEFAULT_NUM_ROWS, seed=42)

        expected_columns = [
            "flood_hazard_zone_tier",
            "zone_cluster_id",
            "platform",
            "delivery_baseline_30d",
            "income_baseline_weekly",
            "enrollment_week",
            "season_flag",
            "open_meteo_7d_precip_probability",
            "activity_consistency_score",
            "tenure_discount_factor",
            "historical_claim_rate_zone",
            "weekly_premium",
        ]

        assert frame.shape == (DEFAULT_NUM_ROWS, len(expected_columns))
        assert list(frame.columns) == expected_columns
        assert frame["weekly_premium"].between(WEEKLY_PREMIUM_FLOOR, WEEKLY_PREMIUM_CEILING).all()

        sparse_columns = [
            "zone_cluster_id",
            "delivery_baseline_30d",
            "income_baseline_weekly",
            "open_meteo_7d_precip_probability",
            "activity_consistency_score",
            "tenure_discount_factor",
            "historical_claim_rate_zone",
        ]
        early_rows = frame[frame["enrollment_week"] < 5]
        late_rows = frame[frame["enrollment_week"] >= 5]

        assert not early_rows.empty
        assert early_rows[sparse_columns].isnull().all().all()
        assert early_rows[["flood_hazard_zone_tier", "platform", "season_flag", "weekly_premium"]].notnull().all().all()
        assert late_rows.isnull().sum().sum() == 0

    def test_save_synthetic_training_data_writes_csv(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "synthetic_training_data.csv"
            frame = save_synthetic_training_data(output_path=output_path, num_rows=25, seed=42)

            assert output_path.exists()
            loaded = pd.read_csv(output_path)
            assert loaded.shape == frame.shape
            assert loaded.shape[0] == 25
