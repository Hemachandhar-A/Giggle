# Giggle — AI-Powered Parametric Income Insurance for India's Gig Economy

**Guidewire DEVTrails 2026 | Team ShadowKernel**

## Pitch Deck
[View the Pitch Deck Presentation](https://docs.google.com/presentation/d/1qn5IUIiTm2DbUQ9SqbRwwwnpnb5uIV69/edit?usp=sharing&ouid=117227792306688009709&rtpof=true&sd=true)

## What This Is

Giggle is a fully automated parametric income insurance backend for food delivery
workers on Zomato and Swiggy in Chennai. When a disruption (heavy rain, extreme
heat, severe AQI, zone curfew) is detected, the system automatically creates
claims, scores them through a 7-signal ML fraud engine, and deposits payouts to
worker UPI accounts in under 60 seconds. Workers do nothing.

## Tech Stack

- **Backend:** FastAPI + SQLAlchemy + Alembic
- **Frontend:** React + Vite + Tailwind CSS + i18next (Tamil/English/Hindi)
- **Database:** PostgreSQL (Supabase) with PostGIS
- **Task Queue:** Celery + Redis (Upstash)
- **ML Models:** LightGBM, statsmodels GLM, scikit-learn (Isolation Forest,
  CBLOF, k-Means), SHAP
- **Payments:** Razorpay sandbox (UPI payout simulation)
- **Weather:** Open-Meteo API (3-point spatial oversampling)
- **Deployment:** Railway.app / Render.com

## Prerequisites

- Python 3.11+
- Git with Git LFS enabled
- A Supabase account (free tier)
- An Upstash Redis account (free tier)
- A Razorpay test account (free)

## Local Setup Instructions

### 1. Clone the repo

```bash
git clone https://github.com/Hemachandhar-A/Giggle.git
cd Giggle/backend
```

### 2. Install Git LFS and pull model artifacts

```bash
git lfs install
git lfs pull
```

### 3. Create and activate virtual environment

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Set up environment variables

```bash
cp .env.example .env
```

Fill in `.env` with:
DATABASE_URL=your_supabase_postgres_url
REDIS_URL=your_upstash_redis_url
RAZORPAY_KEY_ID=rzp_test_xxxxx
RAZORPAY_KEY_SECRET=your_secret
OPEN_METEO_BASE_URL=https://api.open-meteo.com/v1
OPEN_METEO_ARCHIVE_URL=https://archive-api.open-meteo.com/v1
DATA_GOV_IN_API_KEY=your_key

### 6. Run database migrations

```bash
alembic upgrade head
```

### 7. Start the API server

```bash
uvicorn main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### 8. Start Celery worker (separate terminal)

```bash
celery -A app.tasks.celery_app worker --loglevel=info
```

### 9. Start Celery beat scheduler (separate terminal)

```bash
celery -A app.tasks.celery_app beat --loglevel=info
```

### 10. Set up and start Frontend (separate terminal)

```bash
cd ../frontend-new
npm install
cp .env.example .env  # Optional: defaults to http://localhost:8000
npm run dev
```

Frontend available at: http://localhost:5173

## Running Tests

```bash
# Run all Person 2 tests
python -m pytest tests/test_premium/ tests/test_ml/test_models.py -v

# Run with coverage
python -m pytest tests/test_premium/ tests/test_ml/test_models.py -v \
  --cov=app.ml --cov=app.api.premium --cov-report=term-missing
```

## Key API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | /api/v1/onboarding/register | Register a new worker |
| POST | /api/v1/premium/calculate | Calculate weekly premium |
| GET | /api/v1/premium/history/{worker_id} | Premium history |
| POST | /api/v1/trigger/simulate | Simulate a disruption (demo) |
| GET | /api/v1/trigger/active | Active disruptions |
| GET | /api/v1/claims/{worker_id} | Worker claim history |
| GET | /api/v1/admin/dashboard/summary | Admin overview |
| GET | /api/v1/admin/dashboard/loss-ratio | Loss ratio by zone |

## ML Model Artifacts

Stored in `app/ml/artifacts/` via Git LFS:
- `glm_m1.joblib` — GLM cold-start pricer (weeks 1–4)
- `lgbm_m2.joblib` — LightGBM weekly pricer (week 5+)
- `shap_explainer_m2.joblib` — SHAP explainer for Tamil explanations
- `lgbm_m2_feature_list.joblib` — Feature order for LightGBM
- `kmeans_m5.joblib` — Zone clustering model (k=20)

## Deployed Version

Live URL: https://giggle-q6pe.onrender.com/dashboard/
