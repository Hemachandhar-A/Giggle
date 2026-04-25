"""
scripts/seed_demo_data.py — Phase 3 Demo Data Seeder
=====================================================
Seeds exactly 3 required demo accounts with the partner IDs used in Login page
(ZMT001, SWG001, ZMT002) plus ~17 additional workers.

Usage:
    cd backend
    python scripts/seed_demo_data.py

Idempotent — running multiple times is safe (no duplicates).
"""

from __future__ import annotations

import hashlib
import os
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"), override=True)
except ImportError:
    pass

from app.core.database import SessionLocal, DeclarativeBase, engine  # noqa: E402
import app.models.audit  # noqa: F401, E402
import app.models.claims  # noqa: F401, E402
import app.models.delivery  # noqa: F401, E402
import app.models.payout  # noqa: F401, E402
import app.models.platform_partner  # noqa: F401, E402
import app.models.policy  # noqa: F401, E402
import app.models.trigger  # noqa: F401, E402
import app.models.worker  # noqa: F401, E402
import app.models.zone  # noqa: F401, E402

from app.models.audit import AuditEvent  # noqa: E402
from app.models.claims import Claim  # noqa: E402
from app.models.delivery import DeliveryHistory  # noqa: E402
from app.models.platform_partner import PlatformPartner  # noqa: E402
from app.models.policy import Policy  # noqa: E402
from app.models.payout import PayoutEvent  # noqa: E402
from app.models.trigger import TriggerEvent  # noqa: E402
from app.models.worker import WorkerProfile  # noqa: E402
from app.models.zone import ZoneCluster  # noqa: E402


def sha256(v: str) -> str:
    return hashlib.sha256(v.encode()).hexdigest()


# ─── Zone centroids ──────────────────────────────────────────────────────────
ZONE_CENTROIDS: dict[int, tuple[float, float]] = {
    1: (13.1180, 80.2785),   # North Chennai
    2: (13.1149, 80.2325),   # Perambur
    3: (13.0418, 80.2341),   # T. Nagar
    4: (13.0843, 80.2103),   # Anna Nagar
    5: (13.0012, 80.2565),   # Adyar
    6: (13.0524, 80.2220),   # Kodambakkam
    7: (12.9816, 80.2180),   # Velachery
    8: (13.0374, 80.2688),   # Mylapore
    9: (12.9308, 80.1473),   # Tambaram
    10: (13.0310, 80.1573),  # Porur
    11: (12.9521, 80.1378),  # Chromepet
    12: (13.1143, 80.1548),  # Ambattur
}

PINCODE_ZONES: dict[int, tuple[int, str]] = {
    600042: (7, "high"),    # Velachery
    600040: (4, "medium"),  # Anna Nagar
    600045: (9, "medium"),  # Tambaram
    600017: (3, "medium"),  # T. Nagar
    600020: (5, "low"),     # Adyar
    600044: (11, "medium"), # Chromepet
    600028: (6, "low"),     # Kodambakkam
    600024: (8, "high"),    # Mylapore
}

# ─── Required demo workers ────────────────────────────────────────────────────
DEMO_WORKERS = [
    {
        "name": "Priya Sundaram",
        "phone": "9876543210",
        "aadhaar": "999988887777",
        "pan": "ABCDE1234F",
        "partner_id": "ZMT001",
        "platform": "zomato",
        "pincode": 600042,
        "flood_tier": "high",
        "zone_cluster_id": 7,
        "upi_vpa": "priya.zomato@upi",
        "language": "ta",
        "enrollment_days_ago": 60,
        "enrollment_week": 8,
        "premium": Decimal("82.00"),
        "policy_status": "active",
        "model_used": "lgbm",
        "clean_claim_weeks": 5,
        "coverage_week": 8,
        "shap": [
            "உங்கள் மண்டலத்தில் மழை முன்னறிவிப்பு (+₹12)",
            "வெள்ள அபாய மண்டலம் (+₹8)",
            "5 வார சுத்தமான பதிவு (-₹5)",
        ],
    },
    {
        "name": "Ravi Kumar",
        "phone": "9876543211",
        "aadhaar": "888877776666",
        "pan": "BCDEF2345G",
        "partner_id": "SWG001",
        "platform": "swiggy",
        "pincode": 600040,
        "flood_tier": "medium",
        "zone_cluster_id": 4,
        "upi_vpa": "ravi.swiggy@upi",
        "language": "ta",
        "enrollment_days_ago": 40,
        "enrollment_week": 5,
        "premium": Decimal("67.00"),
        "policy_status": "active",
        "model_used": "lgbm",
        "clean_claim_weeks": 4,
        "coverage_week": 5,
        "shap": [],
    },
    {
        "name": "Mohammed Arif",
        "phone": "9876543212",
        "aadhaar": "777766665555",
        "pan": "CDEFG3456H",
        "partner_id": "ZMT002",
        "platform": "zomato",
        "pincode": 600045,
        "flood_tier": "medium",
        "zone_cluster_id": 9,
        "upi_vpa": "arif.zomato@upi",
        "language": "hi",
        "enrollment_days_ago": 21,   # only 21 days — still waiting
        "enrollment_week": 3,
        "premium": Decimal("75.00"),
        "policy_status": "waiting",
        "model_used": "glm",
        "clean_claim_weeks": 0,
        "coverage_week": 3,
        "shap": [],
    },
]

# ─── Extra workers ────────────────────────────────────────────────────────────
EXTRA_WORKERS_SPECS = [
    ("Anitha Rajan",    "666655554444", "DEFGH4567I", "ZMT003", "zomato",  600017, 3, "medium", "anitha@upi",   "ta",  35, 5),
    ("Suresh Babu",     "555544443333", "EFGHI5678J", "SWG002", "swiggy",  600020, 5, "low",    "suresh@upi",   "ta",  50, 7),
    ("Lakshmi Devi",    "444433332222", "FGHIJ6789K", "ZMT004", "zomato",  600044, 11,"medium", "lakshmi@upi",  "ta",  28, 4),
    ("Karthik R",       "333322221111", "GHIJK7890L", "SWG003", "swiggy",  600028, 6, "low",    "karthik@upi",  "en",  45, 6),
    ("Deepa S",         "222211110000", "HIJKL8901M", "ZMT005", "zomato",  600024, 8, "high",   "deepa@upi",    "ta",  32, 5),
    ("Vijay Anand",     "111100009999", "IJKLM9012N", "SWG004", "swiggy",  600042, 7, "high",   "vijay@upi",    "ta",  55, 8),
    ("Preethi M",       "000099998888", "JKLMN0123O", "ZMT006", "zomato",  600040, 4, "medium", "preethi@upi",  "ta",  20, 3),
    ("Ramesh Kumar",    "999988880000", "KLMNO1234P", "SWG005", "swiggy",  600017, 3, "medium", "ramesh@upi",   "hi",  42, 6),
    ("Saritha V",       "888877770000", "LMNOP2345Q", "ZMT007", "zomato",  600044, 11,"medium", "saritha@upi",  "ta",  37, 5),
    ("Bala K",          "777766660000", "MNOPQ3456R", "SWG006", "swiggy",  600045, 9, "medium", "bala@upi",     "ta",  25, 4),
    ("Nithya R",        "666655550000", "NOPQR4567S", "ZMT008", "zomato",  600020, 5, "low",    "nithya@upi",   "en",  60, 9),
    ("Selvam T",        "555544440000", "OPQRS5678T", "SWG007", "swiggy",  600024, 8, "high",   "selvam@upi",   "ta",  48, 7),
    ("Meena L",         "444433330000", "PQRST6789U", "ZMT009", "zomato",  600028, 6, "low",    "meena@upi",    "ta",  33, 5),
    ("Gopal S",         "333322220000", "QRSTU7890V", "SWG008", "swiggy",  600042, 7, "high",   "gopal@upi",    "hi",  56, 8),
    ("Padma A",         "222211110001", "RSTUV8901W", "ZMT010", "zomato",  600040, 4, "medium", "padma@upi",    "ta",  15, 2),
    ("Murugan D",       "111100000001", "STUVW9012X", "SWG009", "swiggy",  600017, 3, "medium", "murugan@upi",  "ta",  44, 6),
    ("Kavitha N",       "000099990001", "TUVWX0123Y", "ZMT011", "zomato",  600045, 9, "medium", "kavitha2@upi", "ta",  29, 4),
]


def ensure_zone(db, zone_id: int) -> None:
    """Ensure a zone_cluster row exists."""
    if db.query(ZoneCluster).filter_by(id=zone_id).first():
        return
    lat, lon = ZONE_CENTROIDS.get(zone_id, (13.0, 80.2))
    db.add(ZoneCluster(
        id=zone_id,
        centroid_lat=Decimal(str(lat)),
        centroid_lon=Decimal(str(lon)),
        flood_tier_numeric=3,
        avg_heavy_rain_days_yr=Decimal("10.00"),
        zone_rate_min=Decimal("15.00"),
        zone_rate_mid=Decimal("18.00"),
        zone_rate_max=Decimal("25.00"),
    ))
    db.commit()


def ensure_partner(db, platform: str, partner_id: str, name: str) -> None:
    if db.query(PlatformPartner).filter_by(partner_id=partner_id).first():
        return
    db.add(PlatformPartner(platform=platform, partner_id=partner_id, partner_name=name))
    db.commit()


def seed_worker_record(db, spec: dict) -> tuple[WorkerProfile, Policy]:
    """Create or return worker + policy. Idempotent."""
    ah = sha256(spec["aadhaar"])
    existing = db.query(WorkerProfile).filter_by(aadhaar_hash=ah).first()
    if existing:
        pol = db.query(Policy).filter_by(worker_id=existing.id).first()
        print(f"  [SKIP] {spec['name']} already exists ({existing.id})")
        return existing, pol

    ensure_zone(db, spec["zone_cluster_id"])
    ensure_partner(db, spec["platform"], spec["partner_id"], spec["name"])

    enrollment_date = datetime.now(timezone.utc) - timedelta(days=spec["enrollment_days_ago"])
    worker = WorkerProfile(
        aadhaar_hash=ah,
        pan_hash=sha256(spec["pan"]),
        platform=spec["platform"],
        partner_id=spec["partner_id"],
        pincode=spec["pincode"],
        flood_hazard_tier=spec["flood_tier"],
        zone_cluster_id=spec["zone_cluster_id"],
        upi_vpa=spec["upi_vpa"],
        device_fingerprint=f"demo-device-{spec['partner_id'].lower()}",
        registration_ip="127.0.0.1",
        enrollment_date=enrollment_date,
        enrollment_week=spec["enrollment_week"],
        is_active=True,
        language_preference=spec["language"],
    )
    db.add(worker)
    db.flush()

    policy = Policy(
        worker_id=worker.id,
        status=spec["policy_status"],
        weekly_premium_amount=spec["premium"],
        coverage_start_date=enrollment_date if spec["policy_status"] == "active" else None,
        coverage_week_number=spec["coverage_week"],
        clean_claim_weeks=spec["clean_claim_weeks"],
        next_renewal_at=datetime.now(timezone.utc) + timedelta(days=3),
        model_used=spec["model_used"],
        shap_explanation_json=spec.get("shap", []),
    )
    db.add(policy)
    db.commit()
    print(f"  [OK]   {spec['name']} -> {worker.id} (policy: {spec['policy_status']})")
    return worker, policy


def seed_delivery_history(db, worker: WorkerProfile) -> None:
    """30 days delivery history if enrollment >= 5 weeks old."""
    if db.query(DeliveryHistory).filter_by(worker_id=worker.id).count() > 0:
        return

    rng = random.Random(int(worker.enrollment_week) * 7)
    lat_base, lon_base = ZONE_CENTROIDS.get(int(worker.zone_cluster_id), (13.0, 80.2))
    now = datetime.now(timezone.utc)
    added = 0
    for day in range(30):
        dt = now - timedelta(days=day)
        if dt.weekday() == 6:
            continue
        for hour in [10, 19]:
            count = rng.randint(5, 9)
            lat = lat_base + rng.uniform(-0.04, 0.04)
            lon = lon_base + rng.uniform(-0.04, 0.04)
            pt = f"SRID=4326;POINT({lon:.6f} {lat:.6f})"
            db.add(DeliveryHistory(
                worker_id=worker.id,
                recorded_at=dt.replace(hour=hour, minute=0, second=0),
                deliveries_count=count,
                earnings_declared=Decimal(str(round(count * 18.5, 2))),
                gps_latitude=pt,
                gps_longitude=pt,
                platform=str(worker.platform),
                is_simulated=True,
            ))
            added += 1
    db.commit()


def seed_trigger_events(db) -> list[TriggerEvent]:
    """Seed 3 historical trigger events if not already present."""
    if db.query(TriggerEvent).count() >= 3:
        return []

    events_data = [
        {"zone_cluster_id": 7, "trigger_type": "heavy_rain", "composite_score": Decimal("0.85"),
         "rain_signal_value": Decimal("72.3"), "aqi_signal_value": None, "temp_signal_value": None,
         "platform_suspended": True, "gis_flood_activated": True, "corroboration_sources": 3,
         "status": "closed", "days_ago": 7},
        {"zone_cluster_id": 4, "trigger_type": "severe_heatwave", "composite_score": Decimal("0.62"),
         "rain_signal_value": Decimal("0"), "aqi_signal_value": None, "temp_signal_value": Decimal("46.2"),
         "platform_suspended": False, "gis_flood_activated": False, "corroboration_sources": 2,
         "status": "closed", "days_ago": 14},
        {"zone_cluster_id": 9, "trigger_type": "severe_aqi", "composite_score": Decimal("0.58"),
         "rain_signal_value": Decimal("0"), "aqi_signal_value": 342, "temp_signal_value": None,
         "platform_suspended": False, "gis_flood_activated": False, "corroboration_sources": 2,
         "status": "closed", "days_ago": 21},
    ]

    created = []
    for ev in events_data:
        ensure_zone(db, ev["zone_cluster_id"])
        t = TriggerEvent(
            zone_cluster_id=ev["zone_cluster_id"],
            triggered_at=datetime.now(timezone.utc) - timedelta(days=ev["days_ago"]),
            trigger_type=ev["trigger_type"],
            composite_score=ev["composite_score"],
            rain_signal_value=ev["rain_signal_value"],
            aqi_signal_value=ev["aqi_signal_value"],
            temp_signal_value=ev["temp_signal_value"],
            platform_suspended=ev["platform_suspended"],
            gis_flood_activated=ev["gis_flood_activated"],
            corroboration_sources=ev["corroboration_sources"],
            fast_path_used=False,
            status=ev["status"],
        )
        db.add(t)
        created.append(t)
    db.commit()
    print(f"  [OK] Seeded {len(created)} historical trigger events")
    return created


def seed_past_claims(db, workers: list[WorkerProfile], triggers: list[TriggerEvent]) -> None:
    """Seed 15 past claims if not already present."""
    if db.query(Claim).count() >= 10:
        print(f"  [SKIP] Claims already seeded ({db.query(Claim).count()} existing)")
        return

    if not triggers:
        triggers = db.query(TriggerEvent).filter_by(status="closed").all()
    if not triggers:
        print("  [SKIP] No trigger events to attach claims to")
        return

    active_workers = [w for w in workers if db.query(Policy).filter_by(worker_id=w.id, status="active").first()]
    if not active_workers:
        print("  [SKIP] No active workers for claims")
        return

    rng = random.Random(2026)

    claim_specs = [
        # 10 auto-approved
        *[{"fraud_score": round(rng.uniform(0.10, 0.25), 3), "routing": "auto_approve", "status": "approved"} for _ in range(10)],
        # 3 partial review
        *[{"fraud_score": round(rng.uniform(0.35, 0.65), 3), "routing": "partial_review", "status": "partial"} for _ in range(3)],
        # 2 held
        *[{"fraud_score": round(rng.uniform(0.72, 0.88), 3), "routing": "hold", "status": "held"} for _ in range(2)],
    ]

    payouts_created = 0
    for i, spec in enumerate(claim_specs):
        worker = active_workers[i % len(active_workers)]
        policy = db.query(Policy).filter_by(worker_id=worker.id).first()
        if not policy:
            continue
        trigger = triggers[i % len(triggers)]

        base = Decimal(str(round(rng.uniform(150, 250), 2)))
        slab = Decimal(str(round(rng.uniform(30, 60), 2)))
        total = base + slab

        claim = Claim(
            worker_id=worker.id,
            trigger_event_id=trigger.id,
            policy_id=policy.id,
            claim_date=datetime.now(timezone.utc) - timedelta(days=rng.randint(1, 20)),
            cascade_day=1,
            deliveries_completed=rng.randint(8, 14),
            base_loss_amount=base,
            slab_delta_amount=slab,
            monthly_proximity_amount=Decimal("0.00"),
            peak_multiplier_applied=False,
            total_payout_amount=total,
            fraud_score=Decimal(str(spec["fraud_score"])),
            fraud_routing=spec["routing"],
            zone_claim_match=True,
            activity_7d_score=Decimal(str(round(rng.uniform(0.6, 0.95), 3))),
            status=spec["status"],
        )
        db.add(claim)
        db.flush()

        # Create payout for approved/partial claims
        if spec["status"] in ("approved", "partial"):
            payout_amount = total if spec["status"] == "approved" else total / 2
            chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
            rzp_id = "pay_" + "".join(rng.choices(chars, k=16))
            initiated = claim.claim_date + timedelta(seconds=rng.randint(10, 60))
            db.add(PayoutEvent(
                claim_id=claim.id,
                worker_id=worker.id,
                razorpay_payout_id=rzp_id,
                amount=payout_amount,
                upi_vpa=str(worker.upi_vpa),
                status="paid",
                initiated_at=initiated,
                completed_at=initiated + timedelta(seconds=rng.randint(45, 75)),
            ))
            payouts_created += 1

    db.commit()
    print(f"  [OK] Seeded {len(claim_specs)} claims and {payouts_created} payouts")


def main() -> None:
    print("\n" + "=" * 65)
    print("  GIGGLE PHASE 3 — DEMO DATA SEEDER")
    print("=" * 65)

    DeclarativeBase.metadata.create_all(bind=engine)
    print("[OK] Schema ready")

    db = SessionLocal()
    try:
        # ── 1. Required demo workers (ZMT001, SWG001, ZMT002) ──────────────
        print("\n[1/4] Seeding 3 required demo workers...")
        demo_worker_objs = []
        for spec in DEMO_WORKERS:
            w, p = seed_worker_record(db, spec)
            demo_worker_objs.append(w)
            # Seed delivery history for workers with enough enrollment time
            if spec["enrollment_days_ago"] >= 35:
                seed_delivery_history(db, w)

        # ── 2. Extra workers ──────────────────────────────────────────────
        print("\n[2/4] Seeding 17 extra workers...")
        all_workers = list(demo_worker_objs)
        for name, aadhaar, pan, partner_id, platform, pincode, zone_id, tier, upi, lang, days_ago, week in EXTRA_WORKERS_SPECS:
            spec = {
                "name": name, "aadhaar": aadhaar, "pan": pan,
                "partner_id": partner_id, "platform": platform,
                "pincode": pincode, "zone_cluster_id": zone_id,
                "flood_tier": tier, "upi_vpa": upi, "language": lang,
                "enrollment_days_ago": days_ago, "enrollment_week": week,
                "premium": Decimal(str(round(49 + week * 4.5, 2))),
                "policy_status": "active" if days_ago >= 28 else "waiting",
                "model_used": "lgbm" if week >= 5 else "glm",
                "clean_claim_weeks": max(0, week - 1),
                "coverage_week": week,
                "shap": [],
            }
            w, p = seed_worker_record(db, spec)
            all_workers.append(w)
            if days_ago >= 35:
                seed_delivery_history(db, w)

        # ── 3. Historical trigger events ───────────────────────────────────
        print("\n[3/4] Seeding 3 historical trigger events...")
        trigger_objs = seed_trigger_events(db)

        # ── 4. Past claims + payouts ───────────────────────────────────────
        print("\n[4/4] Seeding past claims and payouts...")
        seed_past_claims(db, all_workers, trigger_objs)

    finally:
        db.close()

    print("\n" + "=" * 65)
    print("  SEEDING COMPLETE")
    print("=" * 65)
    print("  Demo login accounts:")
    print("    Priya Sundaram   -> partner_id=ZMT001  (Tamil, Velachery)")
    print("    Ravi Kumar       -> partner_id=SWG001  (Tamil, Anna Nagar)")
    print("    Mohammed Arif    -> partner_id=ZMT002  (Hindi, Tambaram)")
    print()
    print("  Run backend: cd backend && uvicorn main:app --reload --port 8000")
    print("  Run frontend: cd frontend && npm run dev")
    print()


if __name__ == "__main__":
    main()
