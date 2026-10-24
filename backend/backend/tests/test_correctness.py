import io
from datetime import UTC, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app import models
from core.config import settings
from core.database import SessionLocal, engine
from services import data_parser, user_service

API = settings.api_prefix
CLEAN_CSV = (
    b"date,amount,category,type,status\n"
    b"2025-01-01,5000,Salary,CREDIT,Completed\n2025-01-05,900,Rent,DEBIT,Completed\n"
    b"2025-02-01,5000,Salary,CREDIT,Completed\n2025-02-05,900,Rent,DEBIT,Completed\n"
)
LATE_CSV = CLEAN_CSV.replace(
    b"2025-02-05,900,Rent,DEBIT,Completed", b"2025-02-05,900,Rent,DEBIT,Late"
)


def _upload(client, uid, content):
    return client.post(
        f"{API}/scoring/{uid}/transactions",
        files={"file": ("s.csv", io.BytesIO(content), "text/csv")},
    )


def _delinquency(client, uid):
    return client.get(f"{API}/scoring/{uid}").json()["subfactor_breakdown"][
        "3.4_delinquency_severity"
    ]["val"]


def test_clean_statement_cannot_erase_a_recorded_delinquency(client, login_as):
    login_as("USR_008")
    client.put(f"{API}/scoring/USR_008/profile", json={"delinq_30plus": 1})
    assert _delinquency(client, "USR_008") == "30-59 Days Late"
    up = _upload(client, "USR_008", CLEAN_CSV)
    assert up.status_code == 200 and up.json()["derived_features"]["delinq_30plus"] == 1
    assert _delinquency(client, "USR_008") == "30-59 Days Late"


def test_a_late_payment_in_a_statement_still_raises_the_flag(client, login_as):
    login_as("USR_009")
    client.put(f"{API}/scoring/USR_009/profile", json={"delinq_30plus": 0})
    assert _upload(client, "USR_009", CLEAN_CSV).json()["derived_features"]["delinq_30plus"] == 0
    assert _upload(client, "USR_009", LATE_CSV).json()["derived_features"]["delinq_30plus"] == 1
    assert _delinquency(client, "USR_009") == "30-59 Days Late"


def test_keep_recorded_delinquencies_unit():
    keep = data_parser.keep_recorded_delinquencies
    assert (
        keep({"delinq_30plus": 1}, {"delinq_30plus": 0, "monthly_income": 5})["delinq_30plus"] == 1
    )
    assert keep({"delinq_30plus": 0.4}, {"delinq_30plus": 0})["delinq_30plus"] == 1
    assert keep({}, {"delinq_30plus": 1})["delinq_30plus"] == 1
    assert keep({"delinq_30plus": 1}, {"on_time_rate": 1}) == {"on_time_rate": 1}  # untouched


def test_zero_risk_flags_are_not_reported_as_a_weakness(client, login_as):
    login_as("USR_002")  # seed profile has no risk flags
    body = client.get(f"{API}/scoring/USR_002").json()
    flags = next(
        f for f in body["explanation"]["all_factors"] if f["factor_key"] == "4.2_risk_flags"
    )
    assert flags["score"] == 0 and flags["contribution_type"] == "strong"
    assert flags["explanation"].startswith("No penalty applied")
    weak = {f["factor_key"] for f in body["explanation"]["weak_factors"]}
    suggested = {s["factor"] for s in body["explanation"]["improvement_suggestions"]}
    assert "4.2_risk_flags" not in weak and "Risk Flags" not in suggested
    assert all(s["potential_points"] > 0 for s in body["explanation"]["improvement_suggestions"])


def test_actual_risk_flags_are_still_a_negative_factor():
    row = dict(data_parser.load_merged_users()[1])
    out = user_service.score({**row, "risk_flags": 2})
    flags = next(
        f for f in out["explanation"]["all_factors"] if f["factor_key"] == "4.2_risk_flags"
    )
    assert flags["score"] == -40 and flags["contribution_type"] == "negative"
    assert flags in out["explanation"]["negative_factors"]


def test_sqlite_enforces_foreign_keys():
    with engine.connect() as conn:
        assert conn.execute(text("PRAGMA foreign_keys")).scalar() == 1
    with SessionLocal() as db, pytest.raises(IntegrityError):
        db.add(
            models.LoanApplication(
                user_id="NO_SUCH_USER", monthly_income=1, debt_to_income=0, profile={}
            )
        )
        db.commit()


def test_timestamps_are_timezone_aware_in_python_and_in_json(client, login_as):
    login_as("USR_002")
    stamp = client.get(f"{API}/scoring/USR_002/history").json()[0]["evaluated_at"]
    assert stamp.endswith("+00:00") or stamp.endswith("Z")
    with SessionLocal() as db:
        user = db.get(models.User, "USR_002")
        assert user.created_at.tzinfo is not None
        naive_utc = datetime(2026, 1, 2, 3, 4, 5)
        db.add(
            models.BankApplication(
                user_id="USR_002", product_id="T", status="X", created_at=naive_utc
            )
        )
        db.flush()
        row = db.query(models.BankApplication).filter_by(product_id="T").one()
        db.refresh(row)  # read it back from SQLite rather than the in-memory object
        assert row.created_at == datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)
        db.rollback()
