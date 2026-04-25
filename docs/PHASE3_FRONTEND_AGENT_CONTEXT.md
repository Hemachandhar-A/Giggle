# Giggle — Phase 3 Frontend Agent Context
### Guidewire DEVTrails 2026 | Team ShadowKernel | Live Demo Preparation
### Version 3.0 | Frontend Build + Backend Gap Fixes

---

## HOW TO USE THIS DOCUMENT

Upload this file to your agent at the start of every session.
This document extends the original AGENT_CONTEXT.md — it does not replace it.
Always read this alongside the original.

**Do not guess. Do not assume. Every API contract, field name, enum value, and business rule
is specified here. If something is not in this document or the original AGENT_CONTEXT.md, stop and ask.**

---

## SECTION A — WHAT ALREADY EXISTS (Do Not Rebuild)

The following is fully built, tested, and merged into `main`. Do NOT reimplment, modify structure,
or duplicate any of this unless explicitly instructed below.

### Backend — Fully Done
- FastAPI app at `backend/main.py` with all routers registered
- All SQLAlchemy ORM models in `backend/app/models/`
- Alembic migrations in `backend/migrations/`
- Premium API: `POST /api/v1/premium/calculate`, `GET /api/v1/premium/history/{worker_id}`, `POST /api/v1/premium/renew`
- Inference engine: `backend/app/ml/inference.py` with real GLM + LightGBM models loaded from `app/ml/artifacts/`
- Trigger engine in `backend/app/trigger/` — Open-Meteo 3-point sampler, AQI monitor, composite scorer
- Payout pipeline in `backend/app/payout/` — Razorpay client, payout calculator
- Celery tasks in `backend/app/tasks/` — trigger polling, weekly renewal, cascade recovery
- Fraud engine in `backend/app/fraud/` — IF + CBLOF ensemble scorer
- All 5 ML model artifacts in `backend/app/ml/artifacts/` via Git LFS
- Admin dashboard endpoints at `/api/v1/admin/`
- Health endpoint at `/api/v1/health`

### What Does NOT Exist Yet (Your Job)
- Frontend (React app) — does not exist at all
- `backend/scripts/seed_demo_data.py` — does not exist
- IMD mock classifier integrated as 3rd corroboration source — exists as file but NOT wired into composite scorer
- UPI autopay mandate UI + `upi_mandate_active` field on worker profile
- Hindi (hi) locale translations — Tamil exists in backend SHAP templates, Hindi does not
- `GET /api/v1/admin/enrollment-metrics` endpoint — check if Person 1 built this; if missing, add it
- 3rd party data source (IMD) as UI-visible corroboration step

---

## SECTION B — CRITICAL NAMING CONTRACTS

These are the EXACT field names, enum values, and strings used in the backend.
The frontend MUST use these exact values when calling APIs or displaying data.
Any mismatch will cause runtime errors.

### B1 — Season Flag Values
The backend `get_current_season()` in `app/api/premium.py` returns these EXACT strings.
The synthetic training data uses these EXACT strings.
Do NOT use 'dry_season' — the backend uses 'dry'.

```
'SW_monsoon'   — June through September
'NE_monsoon'   — October through December  
'heat'         — March through May
'dry'          — January through February
```

**Frontend display mapping:**
```javascript
const SEASON_DISPLAY = {
  'SW_monsoon': { en: 'SW Monsoon', ta: 'தென்மேற்கு பருவமழை', hi: 'दक्षिण-पश्चिम मानसून' },
  'NE_monsoon': { en: 'NE Monsoon', ta: 'வடகிழக்கு பருவமழை', hi: 'उत्तर-पूर्व मानसून' },
  'heat':       { en: 'Summer Heat', ta: 'கோடை வெப்பம்', hi: 'गर्मी का मौसम' },
  'dry':        { en: 'Dry Season', ta: 'வறண்ட காலம்', hi: 'शुष्क मौसम' }
}
```

### B2 — Flood Hazard Tier Values
Stored in `worker_profiles.flood_hazard_tier` as VARCHAR.
The backend and ML models use these EXACT lowercase strings:

```
'high'    — Tier 3 (highest risk)
'medium'  — Tier 2
'low'     — Tier 1 (lowest risk)
```

**Frontend display mapping:**
```javascript
const TIER_DISPLAY = {
  'high':   { en: 'High (Tier 3)', ta: 'அதிக ஆபத்து (நிலை 3)', hi: 'उच्च जोखिम (स्तर 3)', color: '#DC2626' },
  'medium': { en: 'Medium (Tier 2)', ta: 'மிதமான ஆபத்து (நிலை 2)', hi: 'मध्यम जोखिम (स्तर 2)', color: '#D97706' },
  'low':    { en: 'Low (Tier 1)', ta: 'குறைந்த ஆபத்து (நிலை 1)', hi: 'कम जोखिम (स्तर 1)', color: '#059669' }
}
```

### B3 — Platform Values
Stored in `worker_profiles.platform` as VARCHAR(10).
These are the ONLY valid values:

```
'zomato'
'swiggy'
```

**Frontend display:** 'Zomato' and 'Swiggy' (capitalized for display only)

### B4 — Policy Status Values
Stored in `policies.status` as VARCHAR(20).
These are the ONLY valid values:

```
'waiting'    — enrolled but within 28-day waiting period
'active'     — fully covered, eligible for payouts
'suspended'  — admin-suspended
'lapsed'     — premium not paid
```

**Frontend display + color:**
```javascript
const STATUS_DISPLAY = {
  'waiting':   { en: 'Waiting Period', ta: 'காத்திருப்பு காலம்', hi: 'प्रतीक्षा अवधि', color: '#6B7280' },
  'active':    { en: 'Active', ta: 'செயலில்', hi: 'सक्रिय', color: '#059669' },
  'suspended': { en: 'Suspended', ta: 'நிறுத்தப்பட்டது', hi: 'निलंबित', color: '#DC2626' },
  'lapsed':    { en: 'Lapsed', ta: 'காலாவதியானது', hi: 'समाप्त', color: '#9CA3AF' }
}
```

### B5 — Claim Status Values
Stored in `claims.status` as VARCHAR(20):

```
'pending'   — being processed
'approved'  — auto-approved, payout sent
'partial'   — 50% sent, rest under review
'held'      — fraud score > 0.7, manual review
'rejected'  — rejected after manual review
```

### B6 — Fraud Routing Values
Stored in `claims.fraud_routing` as VARCHAR(20):

```
'auto_approve'    — fraud score < 0.30
'partial_review'  — fraud score 0.30–0.70
'hold'            — fraud score > 0.70
```

### B7 — Trigger Type Values
Stored in `trigger_events.trigger_type` as VARCHAR(30):

```
'heavy_rain'          — ≥64.5mm/24h
'very_heavy_rain'     — ≥115.6mm/24h
'extreme_heavy_rain'  — ≥204.4mm/24h
'severe_heatwave'     — >45°C for 4+ hours
'severe_aqi'          — AQI >300 for 4 consecutive hours
'platform_suspension' — mock platform API returns suspended
```

**Frontend display mapping:**
```javascript
const TRIGGER_DISPLAY = {
  'heavy_rain':          { en: 'Heavy Rain', ta: 'கனமழை', hi: 'भारी बारिश', icon: '🌧️' },
  'very_heavy_rain':     { en: 'Very Heavy Rain', ta: 'மிகவும் கனமழை', hi: 'अत्यधिक भारी बारिश', icon: '⛈️' },
  'extreme_heavy_rain':  { en: 'Extreme Rain', ta: 'அதிக கனமழை', hi: 'अत्यंत भारी बारिश', icon: '🌊' },
  'severe_heatwave':     { en: 'Severe Heatwave', ta: 'கடுமையான வெப்ப அலை', hi: 'गंभीर लू', icon: '🔥' },
  'severe_aqi':          { en: 'Severe Air Pollution', ta: 'கடுமையான காற்று மாசு', hi: 'गंभीर वायु प्रदूषण', icon: '😷' },
  'platform_suspension': { en: 'Platform Suspended', ta: 'தளம் நிறுத்தப்பட்டது', hi: 'प्लेटफ़ॉर्म निलंबित', icon: '📵' }
}
```

### B8 — Payout Event Status Values
Stored in `payout_events.status`:

```
'initiated'   — payout request sent to Razorpay
'processing'  — Razorpay processing
'paid'        — confirmed paid to UPI
'failed'      — payment failed
```

### B9 — Language Preference Values
Stored in `worker_profiles.language_preference` as VARCHAR(5):

```
'ta'  — Tamil (default)
'hi'  — Hindi
'en'  — English
```

### B10 — Trigger Status Values
Stored in `trigger_events.status`:

```
'active'     — disruption ongoing
'recovering' — disruption ending, cascade checks running
'closed'     — resolved
```

---

## SECTION C — COMPLETE API CONTRACTS

These are ALL the backend endpoints. Use EXACTLY these URLs, methods, and field names.
Base URL in development: `http://localhost:8000`
Base URL in production: `https://your-railway-url.railway.app`

Store base URL in `frontend/src/config/api.js`:
```javascript
export const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
```

### C1 — Health Check
```
GET /api/v1/health
Response: { "status": "healthy", "database": "connected", "redis": "connected", "celery": "connected" }
```

### C2 — Onboarding & Registration

**Step 1 — Aadhaar OTP (mock)**
```
POST /api/v1/onboarding/kyc/aadhaar
Body: { "aadhaar_number": "XXXXXXXXXXXX", "otp": "123456" }
Response 200: { "verified": true, "aadhaar_hash": "sha256_hash" }
Response 400: { "detail": "Invalid OTP" }
```
Frontend note: Accept any 6-digit OTP in demo mode.

**Step 2 — PAN Check (mock)**
```
POST /api/v1/onboarding/kyc/pan
Body: { "pan_number": "ABCDE1234F", "aadhaar_hash": "sha256_hash" }
Response 200: { "verified": true, "pan_hash": "sha256_hash" }
```

**Step 3 — Bank/UPI Validation (mock)**
```
POST /api/v1/onboarding/kyc/bank
Body: { "upi_vpa": "priya@upi", "account_holder_name": "Priya S" }
Response 200: { "verified": true, "upi_validated": true }
Response 400: { "detail": "Invalid UPI VPA format" }
```

**Step 4 — Platform Verification (mock)**
```
POST /api/v1/onboarding/platform/verify
Body: { "platform": "zomato", "partner_id": "ZMT123456" }
Response 200: { "verified": true, "platform": "zomato" }
```

**Final Registration**
```
POST /api/v1/onboarding/register
Body: {
  "name": "Priya S",
  "phone": "9876543210",
  "aadhaar_hash": "sha256_hash",
  "pan_hash": "sha256_hash",
  "platform": "zomato",
  "partner_id": "ZMT123456",
  "pincode": 600042,
  "upi_vpa": "priya@upi",
  "language_preference": "ta",
  "device_fingerprint": "device_hash_string"
}
Response 201: {
  "worker_id": "uuid",
  "zone_cluster_id": 7,
  "flood_hazard_tier": "high",
  "weekly_premium": 82.00,
  "model_used": "glm",
  "tamil_explanation": "உங்கள் பிரீமியம் கணக்கிடப்பட்டது",
  "waiting_period_ends": "2026-05-23T00:00:00Z",
  "enrollment_date": "2026-04-25T00:00:00Z"
}
Response 409: { "detail": "Worker already registered with this Aadhaar" }
```

**Registration Status**
```
GET /api/v1/onboarding/status/{worker_id}
Response 200: {
  "worker_id": "uuid",
  "is_active": true,
  "enrollment_date": "2026-04-25T00:00:00Z",
  "waiting_period_ends": "2026-05-23T00:00:00Z",
  "days_until_eligible": 28,
  "claim_eligible": false
}
```

### C3 — Policy

```
GET /api/v1/policy/{worker_id}
Response 200: {
  "id": "uuid",
  "worker_id": "uuid",
  "status": "active",
  "weekly_premium_amount": 82.00,
  "coverage_start_date": "2026-03-01T00:00:00Z",
  "coverage_week_number": 8,
  "clean_claim_weeks": 5,
  "last_premium_paid_at": "2026-04-20T00:00:00Z",
  "next_renewal_at": "2026-04-27T00:00:00Z",
  "model_used": "lgbm",
  "shap_explanation_json": {
    "top3": [
      "உங்கள் மண்டலத்தில் மழை முன்னறிவிப்பு (+₹12)",
      "வெள்ள அபாய மண்டலம் (+₹8)",
      "5 வார சுத்தமான பதிவு (-₹5)"
    ]
  }
}
```

```
GET /api/v1/policy/{worker_id}/coverage
Response 200: {
  "is_covered": true,
  "status": "active",
  "days_since_enrollment": 55,
  "claim_eligible": true,
  "days_until_eligible": 0
}
```

### C4 — Premium

```
POST /api/v1/premium/calculate
Body: { "worker_id": "uuid" }
Response 200: {
  "premium_amount": 82.00,
  "model_used": "lgbm",
  "recency_multiplier": 1.0,
  "shap_top3": [
    "உங்கள் மண்டலத்தில் மழை முன்னறிவிப்பு (+₹12)",
    "வெள்ள அபாய மண்டலம் (+₹8)",
    "5 வார சுத்தமான பதிவு (-₹5)"
  ],
  "affordability_capped": false,
  "tamil_explanation": "உங்கள் மண்டலத்தில் மழை முன்னறிவிப்பு (+₹12)"
}
```

```
GET /api/v1/premium/history/{worker_id}
Response 200: {
  "worker_id": "uuid",
  "history": [
    {
      "week_number": 8,
      "premium_amount": 82.00,
      "model_used": "lgbm",
      "shap_explanation_json": { "top3": [...] },
      "calculated_at": "2026-04-20T00:00:00Z"
    }
  ]
}
```

### C5 — Trigger Engine

```
GET /api/v1/trigger/zone/{zone_cluster_id}
Response 200: {
  "zone_cluster_id": 7,
  "status": "active",
  "trigger_type": "heavy_rain",
  "composite_score": 0.85,
  "rain_signal_value": 72.3,
  "aqi_signal_value": null,
  "temp_signal_value": null,
  "platform_suspended": true,
  "gis_flood_activated": true,
  "corroboration_sources": 3,
  "triggered_at": "2026-04-25T14:30:00Z"
}
Response 200 (no trigger): { "zone_cluster_id": 7, "status": "normal", "composite_score": 0.0 }
```

```
POST /api/v1/trigger/simulate
Body: {
  "zone_cluster_id": 7,
  "trigger_type": "heavy_rain",
  "intensity": "severe",
  "rain_mm": 72.3,
  "override_composite_score": 0.85
}
Response 200: {
  "trigger_event_id": "uuid",
  "zone_cluster_id": 7,
  "trigger_type": "heavy_rain",
  "composite_score": 0.85,
  "workers_affected": 12,
  "claims_created": 12,
  "claims_auto_approved": 9,
  "claims_partial_review": 2,
  "claims_held": 1,
  "total_payout_amount": 14280.00,
  "pipeline_duration_ms": 847
}
```

```
GET /api/v1/trigger/active
Response 200: {
  "active_triggers": [
    {
      "id": "uuid",
      "zone_cluster_id": 7,
      "trigger_type": "heavy_rain",
      "composite_score": 0.85,
      "triggered_at": "2026-04-25T14:30:00Z",
      "status": "active",
      "workers_affected": 12
    }
  ]
}
```

```
GET /api/v1/trigger/history
Response 200: {
  "triggers": [
    {
      "id": "uuid",
      "zone_cluster_id": 7,
      "trigger_type": "heavy_rain",
      "composite_score": 0.85,
      "triggered_at": "2026-04-25T14:30:00Z",
      "status": "closed",
      "corroboration_sources": 3
    }
  ]
}
```

### C6 — Claims

```
GET /api/v1/claims/{worker_id}
Response 200: {
  "claims": [
    {
      "id": "uuid",
      "trigger_event_id": "uuid",
      "policy_id": "uuid",
      "claim_date": "2026-04-25T14:30:00Z",
      "cascade_day": 1,
      "deliveries_completed": 10,
      "base_loss_amount": 180.00,
      "slab_delta_amount": 48.00,
      "monthly_proximity_amount": 0.00,
      "peak_multiplier_applied": false,
      "total_payout_amount": 228.00,
      "fraud_score": 0.22,
      "fraud_routing": "auto_approve",
      "zone_claim_match": true,
      "activity_7d_score": 0.85,
      "status": "approved"
    }
  ]
}
```

```
GET /api/v1/claims/detail/{claim_id}
Response 200: {
  "id": "uuid",
  "worker_id": "uuid",
  "trigger_event_id": "uuid",
  "fraud_score": 0.22,
  "fraud_routing": "auto_approve",
  "fraud_signals": {
    "zone_claim_match": true,
    "activity_7d_score": 0.85,
    "claim_to_enrollment_days": 55,
    "event_claim_frequency": 1,
    "cross_platform_flag": false,
    "enrollment_recency_score": 0.08,
    "rain_paradox_flag": false
  },
  "payout_breakdown": {
    "base_loss": 180.00,
    "slab_delta": 48.00,
    "monthly_proximity": 0.00,
    "peak_multiplier": 1.0,
    "cascade_taper": 1.0,
    "total": 228.00
  },
  "status": "approved"
}
```

### C7 — Payout

```
GET /api/v1/payout/{worker_id}/history
Response 200: {
  "payouts": [
    {
      "id": "uuid",
      "claim_id": "uuid",
      "razorpay_payout_id": "pay_PH5GsElk9jG3Rm",
      "amount": 228.00,
      "upi_vpa": "priya@upi",
      "status": "paid",
      "initiated_at": "2026-04-25T14:30:47Z",
      "completed_at": "2026-04-25T14:31:02Z"
    }
  ]
}
```

### C8 — Fraud

```
GET /api/v1/fraud/worker/{worker_id}/signals
Response 200: {
  "worker_id": "uuid",
  "current_fraud_score": 0.22,
  "signals": {
    "zone_claim_match": true,
    "activity_7d_score": 0.85,
    "claim_to_enrollment_days": 55,
    "event_claim_frequency": 1,
    "cross_platform_flag": false,
    "enrollment_recency_score": 0.08,
    "rain_paradox_flag": false
  },
  "routing_decision": "auto_approve"
}
```

```
GET /api/v1/fraud/queue
Response 200: {
  "queue": [
    {
      "claim_id": "uuid",
      "worker_id": "uuid",
      "fraud_score": 0.55,
      "fraud_routing": "partial_review",
      "created_at": "2026-04-25T14:30:00Z",
      "signals": { ... }
    }
  ]
}
```

### C9 — Admin Dashboard

```
GET /api/v1/admin/dashboard/summary
Response 200: {
  "active_policies": 4,
  "live_disruptions": 1,
  "claims_this_week": 8,
  "payouts_this_week_inr": 1840.00,
  "avg_fraud_score_this_week": 0.24,
  "total_workers": 22,
  "upi_mandate_coverage_pct": 78.5
}
```

```
GET /api/v1/admin/dashboard/loss-ratio
Response 200: {
  "loss_ratios": [
    {
      "zone_cluster_id": 7,
      "zone_name": "Velachery",
      "premiums_collected": 8200.00,
      "claims_paid": 5740.00,
      "loss_ratio_pct": 69.9,
      "status": "healthy"
    }
  ]
}
```

```
GET /api/v1/admin/dashboard/claims-forecast
Response 200: {
  "forecast_7d": [
    {
      "date": "2026-04-26",
      "predicted_claims": 3,
      "predicted_payout_inr": 684.00,
      "confidence": "medium"
    }
  ]
}
```

```
GET /api/v1/admin/model-health
Response 200: {
  "premium_model_rmse": 18.42,
  "fraud_model_precision": 0.924,
  "fraud_false_positive_rate": 0.032,
  "slab_config_last_verified_days_ago": 5,
  "slab_config_stale_alert": false,
  "premium_drift_pct": 4.2,
  "premium_drift_alert": false
}
```

```
GET /api/v1/admin/enrollment-metrics
Response 200: {
  "total_enrolled": 22,
  "new_this_week": 3,
  "lapse_rate_pct": 4.5,
  "high_tier_enrollment_pct": 36.4,
  "adverse_selection_alert": false,
  "enrollment_by_week": [
    { "week": "2026-W15", "count": 3 },
    { "week": "2026-W16", "count": 5 }
  ]
}
```

---

## SECTION D — BACKEND CHANGES NEEDED BEFORE FRONTEND

These are specific backend changes required. Do these BEFORE building any frontend page that depends on them.

### D1 — Add `upi_mandate_active` to worker_profiles

This field is needed for the registration flow UPI autopay screen and the admin dashboard metric.

**Add to `worker_profiles` table via Alembic migration:**
```python
# In a new migration file
op.add_column('worker_profiles', sa.Column('upi_mandate_active', sa.Boolean(), nullable=False, server_default='false'))
```

**Add to SQLAlchemy model `app/models/worker.py`:**
```python
upi_mandate_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
```

**Add to registration response:** Include `"upi_mandate_active": false` in `POST /api/v1/onboarding/register` response.

**Add to summary endpoint:** `GET /api/v1/admin/dashboard/summary` must include `"upi_mandate_coverage_pct"` calculated as `(workers with upi_mandate_active=True / total workers) × 100`.

**Add PATCH endpoint for mandate:**
```
PATCH /api/v1/onboarding/{worker_id}/upi-mandate
Body: { "upi_mandate_active": true }
Response 200: { "worker_id": "uuid", "upi_mandate_active": true }
```

### D2 — Wire IMD Classifier as 3rd Corroboration Source

`backend/app/trigger/imd_classifier.py` exists but is NOT wired into `composite_scorer.py`.

**What to add in `composite_scorer.py`:**
The IMD warning now counts as part of the Environmental source category (together with Open-Meteo).
The corroboration gate already has Environmental + Geospatial + Operational = 3 sources.
IMD confirmation strengthens the Environmental source confidence — it does not add a 4th source category.

Add to the `TriggerEvent` response in `POST /api/v1/trigger/simulate`:
```python
"imd_warning_active": True,
"imd_warning_level": "orange",  # 'yellow', 'orange', 'red'
"imd_confidence": 0.85
```

Add `imd_warning_active` boolean and `imd_warning_level` VARCHAR(10) to `trigger_events` table via migration.

**Mock IMD response format** (return this from `imd_classifier.py` always in demo):
```python
def get_imd_warning(zone_cluster_id: int, trigger_type: str) -> dict:
    return {
        "warning_level": "orange",
        "district": "Chennai",
        "event_type": trigger_type,
        "confidence": 0.85,
        "issued_at": datetime.now(UTC).isoformat(),
        "valid_until": (datetime.now(UTC) + timedelta(hours=24)).isoformat()
    }
```

### D3 — Add Hindi SHAP Templates

`backend/app/ml/inference.py` has Tamil SHAP templates but NO Hindi equivalents.
When `worker.language_preference == 'hi'`, the `shap_top3` list must return Hindi strings.

**Add to `SHAP_HINDI_TEMPLATES` dict in `inference.py`:**
```python
SHAP_HINDI_TEMPLATES = {
    "flood_hazard_zone_tier": "बाढ़ जोखिम क्षेत्र आपके प्रीमियम को प्रभावित करता है",
    "season_flag": "वर्तमान मानसून मौसम उच्च जोखिम दर्शाता है",
    "open_meteo_7d_precip_probability": "अगले सप्ताह बारिश की संभावना है",
    "activity_consistency_score": "आपकी डिलीवरी गतिविधि में बदलाव देखा गया है",
    "historical_claim_rate_zone": "आपके क्षेत्र में दावों का इतिहास अधिक है",
    "zone_cluster_id": "आपके क्षेत्र का जोखिम स्तर प्रीमियम को प्रभावित करता है",
    "delivery_baseline_30d": "पिछले महीने की डिलीवरी गिनती को ध्यान में रखा गया है",
    "income_baseline_weekly": "आपकी साप्ताहिक आय को ध्यान में रखा गया है",
    "tenure_discount_factor": "लंबे समय के उपयोग पर छूट दी जा रही है",
    "platform": "आपका डिलीवरी प्लेटफ़ॉर्म ध्यान में रखा गया है",
    "enrollment_week": "नामांकन सप्ताह प्रीमियम को प्रभावित करता है"
}
```

**Also add English templates for `language == 'en'`:**
```python
SHAP_ENGLISH_TEMPLATES = {
    "flood_hazard_zone_tier": "High flood risk zone (+₹{amount})",
    "season_flag": "NE Monsoon season — elevated risk (+₹{amount})",
    "open_meteo_7d_precip_probability": "Rain forecast in your zone (+₹{amount})",
    "activity_consistency_score": "{weeks} weeks clean record (-₹{amount})",
    "historical_claim_rate_zone": "High claim history in your zone (+₹{amount})",
    "zone_cluster_id": "Zone risk profile affects premium",
    "delivery_baseline_30d": "Based on last month delivery count",
    "income_baseline_weekly": "Weekly income baseline calculated",
    "tenure_discount_factor": "Loyalty discount applied (-₹{amount})",
    "platform": "Platform coverage factor applied",
    "enrollment_week": "Enrollment week affects premium"
}
```

**Modify `calculate_premium()` in `inference.py`** to accept `language` parameter and select the right template dict. Currently it always uses Tamil. Fix:
```python
def _get_shap_template(language: str) -> dict:
    if language == 'hi':
        return SHAP_HINDI_TEMPLATES
    elif language == 'en':
        return SHAP_ENGLISH_TEMPLATES
    else:  # default 'ta'
        return SHAP_TAMIL_TEMPLATES
```

### D4 — Seed Demo Data Script

Create `backend/scripts/seed_demo_data.py`. This populates the database with realistic demo data for the live presentation.

**IMPORTANT:** Use `python backend/scripts/seed_demo_data.py` to run.
It must be idempotent — running it twice must not create duplicates (use `INSERT ... ON CONFLICT DO NOTHING` or check before inserting).

**Workers to seed (20 workers, these 3 MUST be first for demo login):**

Demo worker 1 (primary demo account):
```python
{
    "name": "Priya Sundaram",
    "phone": "9876543210",
    "platform": "zomato",
    "partner_id": "ZMT001",
    "pincode": 600042,  # Velachery
    "flood_hazard_tier": "high",
    "zone_cluster_id": 7,
    "upi_vpa": "priya.zomato@upi",
    "language_preference": "ta",
    "enrollment_week": 8,
    "is_active": True,
    # Policy: active, weekly_premium=82.00, model_used='lgbm', coverage_week=8, clean_claim_weeks=5
}
```

Demo worker 2:
```python
{
    "name": "Ravi Kumar",
    "phone": "9876543211",
    "platform": "swiggy",
    "partner_id": "SWG001",
    "pincode": 600040,  # Anna Nagar
    "flood_hazard_tier": "medium",
    "zone_cluster_id": 4,
    "upi_vpa": "ravi.swiggy@upi",
    "language_preference": "ta",
    "enrollment_week": 5,
    # Policy: active, weekly_premium=67.00, model_used='lgbm'
}
```

Demo worker 3:
```python
{
    "name": "Mohammed Arif",
    "phone": "9876543212",
    "platform": "zomato",
    "partner_id": "ZMT002",
    "pincode": 600045,  # Tambaram
    "flood_hazard_tier": "medium",
    "zone_cluster_id": 9,
    "upi_vpa": "arif.zomato@upi",
    "language_preference": "hi",
    "enrollment_week": 3,
    # Policy: waiting (only 21 days enrolled), weekly_premium=75.00, model_used='glm'
}
```

Then seed 17 more workers across these pincodes:
- 600017 (T. Nagar) — zone_cluster_id=3, flood_tier='medium'
- 600020 (Adyar) — zone_cluster_id=5, flood_tier='low'
- 600044 (Chromepet) — zone_cluster_id=11, flood_tier='medium'
- 600028 (Kodambakkam) — zone_cluster_id=6, flood_tier='low'
- 600024 (Mylapore) — zone_cluster_id=8, flood_tier='high'

Mix of Tamil and Hindi names. Mix of Zomato (12 total) and Swiggy (8 total).
Enrollment weeks: range from 1 to 26 across all workers.

**Delivery history:** For each active worker (enrollment_week ≥ 5), generate 30 days of delivery records:
- 12–16 deliveries per day with ±3 random variance
- earnings_declared: deliveries × ₹18 + random slab bonus
- GPS coordinates within ±0.05 degrees of their zone centroid
- is_simulated: True always

**Past claims (15 claims minimum):**
- 10 auto-approved (fraud_score 0.10–0.25, status='approved')
- 3 partial review (fraud_score 0.35–0.65, status='partial')
- 2 held (fraud_score 0.72–0.88, status='held')
- Spread across at least 4 different workers
- base_loss_amount: ₹150–₹250
- slab_delta_amount: ₹30–₹60
- total_payout_amount: ₹180–₹310

**Payout records (10 payouts minimum):**
- One per approved/partial claim
- razorpay_payout_id format: `pay_` + 16 alphanumeric chars (e.g., `pay_PH5GsElk9jG3Rm`)
- status: 'paid' for all past payouts
- completed_at: 45–75 seconds after initiated_at (realistic 60-second window)

**Trigger events (3 past events):**
```python
events = [
    { "zone_cluster_id": 7, "trigger_type": "heavy_rain", "composite_score": 0.85,
      "rain_signal_value": 72.3, "platform_suspended": True, "gis_flood_activated": True,
      "corroboration_sources": 3, "status": "closed",
      "triggered_at": "now() - interval '7 days'" },
    { "zone_cluster_id": 4, "trigger_type": "severe_heatwave", "composite_score": 0.62,
      "temp_signal_value": 46.2, "platform_suspended": False, "gis_flood_activated": False,
      "corroboration_sources": 2, "status": "closed",
      "triggered_at": "now() - interval '14 days'" },
    { "zone_cluster_id": 9, "trigger_type": "severe_aqi", "composite_score": 0.58,
      "aqi_signal_value": 342, "platform_suspended": False, "gis_flood_activated": False,
      "corroboration_sources": 2, "status": "closed",
      "triggered_at": "now() - interval '21 days'" }
]
```

**Zone name mapping** (for display in frontend — these are NOT in the DB schema, use this mapping in frontend config):
```javascript
export const ZONE_NAMES = {
  1: 'North Chennai',
  2: 'Perambur',
  3: 'T. Nagar',
  4: 'Anna Nagar',
  5: 'Adyar',
  6: 'Kodambakkam',
  7: 'Velachery',
  8: 'Mylapore',
  9: 'Tambaram',
  10: 'Porur',
  11: 'Chromepet',
  12: 'Ambattur',
  13: 'Avadi',
  14: 'Sholinganallur',
  15: 'Perungudi',
  16: 'Guindy',
  17: 'Nungambakkam',
  18: 'Egmore',
  19: 'Thiruvottiyur',
  20: 'Manali'
}
```

---

## SECTION E — FRONTEND ARCHITECTURE

### E1 — Project Setup

```bash
# From repo root
npm create vite@latest frontend -- --template react
cd frontend
npm install
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
npm install react-router-dom axios recharts react-i18next i18next
npm install @headlessui/react
```

**File structure:**
```
frontend/
├── src/
│   ├── config/
│   │   ├── api.js          ← Base URL + axios instance
│   │   └── constants.js    ← ZONE_NAMES, TIER_DISPLAY, TRIGGER_DISPLAY etc
│   ├── locales/
│   │   ├── en.json         ← English translations
│   │   ├── ta.json         ← Tamil translations  
│   │   └── hi.json         ← Hindi translations
│   ├── components/
│   │   ├── Layout.jsx      ← Shared header/nav
│   │   ├── StatusBadge.jsx ← Reusable status pills
│   │   ├── MetricCard.jsx  ← Reusable KPI cards
│   │   └── LoadingSpinner.jsx
│   ├── pages/
│   │   ├── Landing.jsx
│   │   ├── Register.jsx
│   │   ├── Login.jsx
│   │   ├── Dashboard.jsx   ← Worker portal
│   │   ├── Demo.jsx        ← Trigger simulation
│   │   ├── Fraud.jsx       ← Fraud engine view
│   │   └── Admin.jsx       ← Admin dashboard
│   ├── hooks/
│   │   ├── useWorker.js    ← Fetches worker + policy data
│   │   └── useAuth.js      ← Auth state management
│   ├── App.jsx
│   └── main.jsx
├── index.html
├── tailwind.config.js
└── vite.config.js
```

### E2 — Design System

**Colors (add to tailwind.config.js):**
```javascript
colors: {
  primary: {
    50:  '#f0fdf4',
    100: '#dcfce7',
    500: '#22c55e',
    700: '#15803d',
    900: '#0D2818',  // Deep forest green — primary dark
  },
  accent: {
    400: '#fbbf24',
    500: '#F5A623',  // Warm amber — CTA buttons
    600: '#d97706',
  },
  sage: {
    300: '#86efac',
    500: '#7DAE8A',  // Muted sage — secondary
  },
  surface: '#F8F6F1',  // Off-white — light page background
  dark: '#0D2818',
}
```

**Typography (in index.css):**
```css
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&family=Inter:wght@400;500;600&display=swap');

body { font-family: 'Inter', sans-serif; }
h1, h2, h3, .heading { font-family: 'Sora', sans-serif; }
```

**Component patterns:**
- Primary buttons: `bg-accent-500 hover:bg-accent-600 text-white font-semibold px-6 py-3 rounded-xl`
- Secondary buttons: `border-2 border-primary-900 text-primary-900 hover:bg-primary-50 font-semibold px-6 py-3 rounded-xl`
- Cards: `bg-white border border-gray-200 rounded-2xl p-6` (NOT heavy shadows)
- Dark cards (admin only): `bg-primary-900 text-white rounded-2xl p-6`
- Status badge active: `bg-green-100 text-green-800 text-xs font-semibold px-2.5 py-1 rounded-full`
- Status badge waiting: `bg-gray-100 text-gray-600 text-xs font-semibold px-2.5 py-1 rounded-full`

### E3 — Auth State Management

Use localStorage for demo. In `useAuth.js`:
```javascript
// Auth state: { worker_id, name, platform, zone_cluster_id, language_preference, token }
// On login: store in localStorage('giggle_auth')
// On logout: clear localStorage
// On every protected page load: check localStorage, redirect to /login if missing
```

Demo login — do NOT call a real auth API (there is none in the backend spec).
Instead, call `GET /api/v1/onboarding/status/{worker_id}` to verify the worker exists,
then store worker_id in localStorage and use it for all subsequent API calls.

For the demo login page, hardcode these credentials:
```javascript
const DEMO_ACCOUNTS = [
  { label: 'Priya S. — Velachery (Tamil)', worker_id: '(fetched from DB by partner_id ZMT001)', platform: 'zomato' },
  { label: 'Ravi K. — Anna Nagar (Tamil)', worker_id: '(fetched from DB by partner_id SWG001)', platform: 'swiggy' },
  { label: 'Mohammed A. — Tambaram (Hindi)', worker_id: '(fetched from DB by partner_id ZMT002)', platform: 'zomato' }
]
```

Add a lookup endpoint to backend if needed:
```
GET /api/v1/onboarding/by-partner/{partner_id}
Response: { "worker_id": "uuid" }
```
This is a demo-only helper endpoint — add it to Person 1's onboarding router.

### E4 — i18next Setup

In `src/main.jsx`:
```javascript
import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import en from './locales/en.json'
import ta from './locales/ta.json'
import hi from './locales/hi.json'

i18n.use(initReactI18next).init({
  resources: { en: { translation: en }, ta: { translation: ta }, hi: { translation: hi } },
  lng: 'ta',  // default Tamil
  fallbackLng: 'en',
  interpolation: { escapeValue: false }
})
```

Language toggle component — when worker is logged in, changing language must:
1. Call `PATCH /api/v1/onboarding/{worker_id}/upi-mandate` — wait, this doesn't exist for language.
   Actually: add `PATCH /api/v1/workers/{worker_id}/language` to backend.
   Body: `{ "language_preference": "hi" }`, Response: `{ "language_preference": "hi" }`
2. Update i18n.changeLanguage()
3. Update localStorage

**Required locale keys (en.json):**
```json
{
  "nav": {
    "coverage": "Coverage",
    "workers": "Workers",
    "triggers": "Triggers & Payouts",
    "fraud": "Fraud Engine",
    "admin": "Admin",
    "logout": "Logout"
  },
  "dashboard": {
    "weekly_premium": "Weekly Premium",
    "coverage_week": "Coverage Week",
    "active_policies": "Active Policies",
    "live_disruptions": "Live Disruptions",
    "claims_this_week": "Claims This Week",
    "payouts_this_week": "Payouts This Week"
  },
  "policy": {
    "status_active": "Active",
    "status_waiting": "Waiting Period",
    "status_suspended": "Suspended",
    "status_lapsed": "Lapsed",
    "claim_eligible": "Eligible for Claims",
    "claim_not_eligible": "Waiting Period: {{days}} days remaining"
  },
  "fraud": {
    "auto_approve": "Auto-Approved",
    "partial_review": "Partial Review",
    "hold": "Under Review",
    "fraud_score": "Fraud Score"
  },
  "demo": {
    "trigger_event": "Trigger Event",
    "select_zone": "Select Zone",
    "select_type": "Select Disruption Type",
    "fire_trigger": "Fire Trigger →",
    "pipeline_running": "Pipeline Running...",
    "disruption_detected": "Disruption Detected",
    "claims_created": "Claims Created",
    "fraud_running": "Fraud Engine Running",
    "payout_sent": "UPI Payout Sent"
  },
  "common": {
    "loading": "Loading...",
    "error": "Something went wrong",
    "retry": "Retry",
    "back": "Back"
  }
}
```

**ta.json equivalents:**
```json
{
  "nav": {
    "coverage": "காப்பீடு",
    "workers": "தொழிலாளர்கள்",
    "triggers": "தூண்டுதல் & கொடுப்பனவு",
    "fraud": "மோசடி இயந்திரம்",
    "admin": "நிர்வாகம்",
    "logout": "வெளியேறு"
  },
  "dashboard": {
    "weekly_premium": "வாராந்திர பிரீமியம்",
    "coverage_week": "காப்பீட்டு வாரம்",
    "active_policies": "செயலில் உள்ள பாலிசிகள்",
    "live_disruptions": "நேரடி இடையூறுகள்",
    "claims_this_week": "இந்த வார கோரிக்கைகள்",
    "payouts_this_week": "இந்த வார கொடுப்பனவுகள்"
  },
  "policy": {
    "status_active": "செயலில்",
    "status_waiting": "காத்திருப்பு காலம்",
    "status_suspended": "நிறுத்தப்பட்டது",
    "status_lapsed": "காலாவதியானது",
    "claim_eligible": "கோரிக்கைக்கு தகுதியானது",
    "claim_not_eligible": "காத்திருப்பு காலம்: {{days}} நாட்கள் மீதமுள்ளன"
  },
  "fraud": {
    "auto_approve": "தானியங்கி அனுமதி",
    "partial_review": "பகுதி மதிப்பாய்வு",
    "hold": "மதிப்பாய்வில் உள்ளது",
    "fraud_score": "மோசடி மதிப்பெண்"
  },
  "demo": {
    "trigger_event": "நிகழ்வை தூண்டு",
    "select_zone": "மண்டலத்தை தேர்ந்தெடு",
    "select_type": "இடையூறு வகையை தேர்ந்தெடு",
    "fire_trigger": "தூண்டு →",
    "pipeline_running": "பைப்லைன் இயங்குகிறது...",
    "disruption_detected": "இடையூறு கண்டறியப்பட்டது",
    "claims_created": "கோரிக்கைகள் உருவாக்கப்பட்டன",
    "fraud_running": "மோசடி இயந்திரம் இயங்குகிறது",
    "payout_sent": "UPI கொடுப்பனவு அனுப்பப்பட்டது"
  },
  "common": {
    "loading": "ஏற்றுகிறது...",
    "error": "ஏதோ தவறு நடந்தது",
    "retry": "மீண்டும் முயற்சிக்கவும்",
    "back": "திரும்பு"
  }
}
```

---

## SECTION F — PAGE-BY-PAGE IMPLEMENTATION NOTES

### F1 — Landing Page (`/`)
- No auth required
- Call `GET /api/v1/health` on load to show live "All systems operational" badge
- Stats bar values: hardcode for landing page (15M+, ₹49, 60 sec, 0 forms)
- "Get Protected" CTA → navigates to `/register`
- "Admin Login" small link in footer → navigates to `/login?role=admin`

### F2 — Registration (`/register`)
Multi-step flow using React state (no URL changes between steps).

Step 1: Phone + OTP mock
- Accept any 6-digit OTP
- On submit: just advance to step 2 (no real API call for phone OTP — add note in UI "Demo mode: any OTP works")

Step 2: Personal + Platform details
- Call `POST /api/v1/onboarding/kyc/aadhaar` with aadhaar_number + otp='123456'
- Call `POST /api/v1/onboarding/kyc/pan`
- Call `POST /api/v1/onboarding/platform/verify`
- Platform dropdown options: 'zomato' | 'swiggy' (lowercase values sent to API)

Step 3: Location + UPI
- Pincode input: show zone name and flood tier as worker types (use ZONE_NAMES mapping — lookup by closest pincode range)
- Call `POST /api/v1/onboarding/kyc/bank` with upi_vpa

Step 3b: UPI Autopay mandate screen
- Show: "Allow Giggle to auto-deduct ₹X every Sunday"
- "Approve Mandate" button → shows success animation → calls `PATCH /api/v1/onboarding/{worker_id}/upi-mandate` with `{ "upi_mandate_active": true }`
- "Skip for now" link → skips mandate but shows warning

Step 4: Call `POST /api/v1/onboarding/register`
- Show confirmation: worker_id, zone, flood tier, first premium, waiting period end date
- "Go to Dashboard" button → store worker_id in localStorage → navigate to `/dashboard`

### F3 — Login (`/login`)
- Worker ID field + Password field (password is not validated in backend — accept anything for demo)
- On submit: call `GET /api/v1/onboarding/status/{worker_id}` — if 200, store in localStorage and go to `/dashboard`
- If response has `waiting_period` info, show that on dashboard
- Admin login: separate form with hardcoded admin credentials (username: 'admin', password: 'admin') → goes to `/admin`
- Demo accounts section: 3 pre-filled buttons that fill the Worker ID field

**Worker ID to partner_id lookup:**
Add this to backend — `GET /api/v1/onboarding/by-partner/{partner_id}` returning `{ "worker_id": "uuid" }`.
Demo accounts use partner_ids: ZMT001, SWG001, ZMT002.

### F4 — Worker Dashboard (`/dashboard`)
Requires auth (worker_id in localStorage).

On load, call in parallel:
- `GET /api/v1/policy/{worker_id}`
- `GET /api/v1/premium/history/{worker_id}`
- `GET /api/v1/claims/{worker_id}`
- `GET /api/v1/payout/{worker_id}/history`
- `GET /api/v1/trigger/active` (to show disruption alert banner)
- `GET /api/v1/admin/dashboard/summary` (for header KPI bar)

**Alert banner logic:**
If `trigger/active` returns any triggers where `zone_cluster_id` matches the worker's zone → show amber alert banner.
Worker's zone_cluster_id stored in localStorage after registration/login.

**SHAP explanation display:**
`policy.shap_explanation_json.top3` is an array of strings already in the correct language from backend.
Display them exactly as returned — do NOT translate them on the frontend.
Each string is already Tamil, Hindi, or English based on `worker.language_preference`.

**Premium history chart:**
Use Recharts BarChart.
X-axis: week_number.
Y-axis: premium_amount.
Bar color: sage green.
Hover tooltip shows: model_used, shap_explanation_json.top3[0].

**Waiting period display (for Mohammed Arif demo account):**
If `policy.status == 'waiting'`, show progress bar from enrollment_date to waiting_period_ends.
Show: "X days remaining until claim eligible"
Calculate from: enrollment_date + 28 days.

### F5 — Demo Page (`/demo`)

**CRITICAL: This is the most important page for the live demo.**

Pipeline animation sequence after `POST /api/v1/trigger/simulate` returns:
```
Step 1 [0ms]     🌧️  Disruption Detected
                     Show: trigger_type display name, zone name, composite_score as %
                     Show: "3-Point Weather Check: 72.3mm/hr max reading"
                     Show: "IMD Warning: Orange Alert active"  ← new with D2 fix

Step 2 [1000ms]  📋  Claims Created
                     Show: "{{workers_affected}} eligible workers found in {{zone_name}}"
                     Show: "28-day waiting period enforced — 2 workers excluded"

Step 3 [2000ms]  🔍  Fraud Engine Running
                     Animated loading bar for 1.5 seconds
                     Then show: "{{claims_auto_approved}} auto-approved · {{claims_partial_review}} partial · {{claims_held}} held"

Step 4 [3500ms]  ✅  Routing Decision
                     Show 3 rows:
                     Green: "{{claims_auto_approved}} workers → Auto-Approve → UPI in 60 seconds"
                     Amber: "{{claims_partial_review}} workers → 50% released + 48hr review"
                     Red:   "{{claims_held}} workers → Manual review queue"

Step 5 [4500ms]  💰  UPI Payouts Sent
                     Show: "₹{{total_payout_amount}} disbursed"
                     Show: "Pipeline completed in {{pipeline_duration_ms}}ms"
                     Show mock Razorpay transaction IDs for first 3 workers
```

Console log at bottom: auto-scroll, monospace font, green text on dark background.
Shows 8–10 log lines like:
```
[14:30:00.123] Trigger event created: heavy_rain zone_7
[14:30:00.456] Open-Meteo: centroid 72.3mm, NNE 68.1mm, SSW 74.8mm → max 74.8mm
[14:30:00.789] IMD: Orange warning active for Chennai district
[14:30:01.012] 2-of-3 corroboration gate: PASSED (Environmental + Geospatial + Operational)
[14:30:01.234] 12 eligible workers in zone 7
[14:30:01.567] Fraud engine: IF+CBLOF ensemble scoring...
[14:30:02.890] Claim priya.zomato@upi: score=0.22 → auto_approve → ₹228.00
[14:30:03.112] Razorpay payout initiated: pay_PH5GsElk9jG3Rm → priya.zomato@upi
[14:30:03.987] Payout confirmed: ₹228.00 → priya.zomato@upi [55ms]
```

### F6 — Fraud Engine Page (`/fraud`)
Call on load:
- `GET /api/v1/admin/model-health` for precision/RMSE metrics
- `GET /api/v1/fraud/queue` for live claims table
- `GET /api/v1/fraud/worker/{worker_id}/signals` for the logged-in worker's signals

**7 signal visualization:**
Horizontal progress bars, color-coded:
- Zone GPS Match: green if true, red if false
- Activity Score: color based on value (>0.7 green, 0.4–0.7 amber, <0.4 red)
- Enrollment Days: green if >28, red if <28
- Claim Frequency: green if ≤2, amber if 3–5, red if >5
- Cross-Platform: green if false, red if true
- Recency Score: display as inverse (lower score = safer)
- Rain Paradox: green if false, red if true

**Routing threshold visual:**
A horizontal gradient bar from green (0.0) through amber (0.30, 0.70) to red (1.0).
Show a vertical marker at the worker's current fraud score.

### F7 — Admin Dashboard (`/admin`) — dark theme
Call on load:
- `GET /api/v1/admin/dashboard/summary`
- `GET /api/v1/admin/dashboard/loss-ratio`
- `GET /api/v1/admin/dashboard/claims-forecast`
- `GET /api/v1/admin/model-health`
- `GET /api/v1/admin/enrollment-metrics`

**Loss ratio table + chart:**
Use Recharts BarChart for loss ratios by zone.
Color each bar: <65% = green, 65–85% = amber, >85% = red.
If any zone >85%, show a red alert banner: "⚠️ Zone {{name}} loss ratio critical — premium recalibration recommended"

**Adverse selection alert:**
If `enrollment_metrics.high_tier_enrollment_pct > 40`, show amber banner:
"⚠️ Adverse selection risk: {{pct}}% of new enrollments are High flood tier"

**Model drift indicator:**
If `model_health.premium_drift_pct > 20`, show red alert:
"🔴 Premium model drift detected — consider retraining"

**Slab config panel:**
Show Zomato slab table: 7→₹50, 12→₹120, 15→₹150, 21→₹200
Show "Last verified X days ago" — if >30 days, show amber warning
Show "Mark as Verified" button → calls `PUT /api/v1/admin/slab-config/verify`

---

## SECTION G — THINGS THAT WILL BREAK WITHOUT THESE FIXES

These are the specific runtime errors that WILL happen if you skip the backend changes.

| What breaks | Why | Fix in section |
|---|---|---|
| Dashboard shows no SHAP in Hindi | inference.py only has Tamil templates | D3 |
| Registration step 3b crashes | upi_mandate_active field doesn't exist in DB | D1 |
| Admin summary missing UPI mandate % | field not in DB, endpoint doesn't return it | D1 |
| Demo console shows "2 sources" not "3 sources" | IMD not wired into composite scorer | D2 |
| Demo accounts can't log in | no by-partner lookup endpoint | F3, add to onboarding router |
| Language toggle does nothing on backend | no language update endpoint | E4, add PATCH /workers/{id}/language |
| Workers table empty | no seed data | D4 |
| Loss ratio page shows zeros | no seed data | D4 |
| SHAP strings missing on English language | no English templates | D3 |

---

## SECTION H — ENVIRONMENT VARIABLES FOR FRONTEND

Create `frontend/.env.development`:
```
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=Giggle
VITE_APP_ENV=development
```

Create `frontend/.env.production`:
```
VITE_API_BASE_URL=https://your-railway-url.railway.app
VITE_APP_NAME=Giggle
VITE_APP_ENV=production
```

---

## SECTION I — BUILD AND RUN COMMANDS

**Development:**
```bash
cd frontend
npm install
npm run dev          # starts at http://localhost:5173
```

**Backend must also be running:**
```bash
cd backend
uvicorn main:app --reload --port 8000
```

**Seed the database (run once):**
```bash
cd backend
python scripts/seed_demo_data.py
```

**Production build:**
```bash
cd frontend
npm run build        # outputs to frontend/dist/
```

**Deploy frontend to Vercel (free):**
```bash
npm install -g vercel
cd frontend
vercel --prod
# Set environment variable VITE_API_BASE_URL to your Railway URL
```

Or deploy to Railway as a static site:
- Add to `frontend/package.json`: `"preview": "vite preview --host 0.0.0.0 --port $PORT"`
- Railway start command: `npm run build && npm run preview`

---

## SECTION J — DEMO SCRIPT CHECKLIST

Use this to verify everything works before the live demo:

```
□ Landing page loads at http://localhost:5173
□ "All systems operational" badge shows green
□ Click "Get Protected" → registration form opens
□ Complete registration with Priya's details (pincode 600042)
□ UPI mandate screen appears and works
□ Confirmation shows zone=Velachery, tier=High, premium=₹82
□ Login with demo account ZMT001 (Priya)
□ Dashboard shows policy ACTIVE, premium ₹82, Tamil SHAP strings
□ Switch language to தமிழ் → all labels change
□ Switch to Hindi → labels change to Hindi
□ Claims tab shows past claims with fraud scores
□ Payouts tab shows Razorpay transaction IDs
□ Navigate to Demo page → fire Heavy Rain at Velachery
□ Pipeline animates all 5 steps with 3 corroboration sources shown
□ Console log scrolls with realistic log lines
□ Fraud Engine page shows 92.4% precision, 7 signals for Priya
□ Admin page shows loss ratio table with chart
□ Admin shows adverse selection and model drift indicators
□ All pages work in Tamil, Hindi, and English
```

---

## SECTION K — DO NOT DO THESE THINGS

1. **Do NOT call `/api/v1/fraud/score` directly from frontend** — this is an internal endpoint called by the payout pipeline only
2. **Do NOT build a separate auth service** — use localStorage + worker_id as described in E3
3. **Do NOT use dark mode everywhere** — landing page and worker dashboard are light/warm, only admin is dark
4. **Do NOT use the season value 'dry_season'** — the backend uses 'dry' (see B1)
5. **Do NOT hardcode Tamil strings in React components** — all text must go through i18next
6. **Do NOT modify any file in `backend/app/models/`** — use Alembic migrations for schema changes
7. **Do NOT call premium/calculate on every page load** — it's a write operation that updates the DB; call it only during the renewal flow
8. **Do NOT invent new API endpoints** — use only the ones defined in this document and the original AGENT_CONTEXT.md. If you need one that doesn't exist, stop and ask.
9. **Do NOT use navy blue as the primary color** — every competing team used navy. Use the forest green palette defined in E2.
10. **Do NOT copy any UI pattern from the competitor screenshots** — the color palette, layout, and component patterns are all different by design.

---

*End of Phase 3 Frontend Agent Context*
*Version 3.0 — Team ShadowKernel — Guidewire DEVTrails 2026*
