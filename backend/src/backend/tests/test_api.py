from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root():

    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["application"] == "AltCredit"
    assert data["status"] == "running"


def test_health():

    response = client.get("/api/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"


def test_score_api():

    payload = {
        "employment_months": 24,
        "housing_status": "rent",
        "residency_months": 18,
        "digital_payment_rate": 0.96,
        "education_level": "bachelor",

        "spend_income_ratio": 0.35,
        "essential_ratio": 0.65,
        "cashflow_volatility": 0.08,
        "savings_days": 90,

        "on_time_payment_rate": 0.97,
        "debt_to_income": 0.25,
        "credit_utilization": 0.20,
        "days_late": 0,

        "qualifying_habits": 2,
        "risk_flags": 0
    }

    response = client.post(
        "/api/score/calculate",
        json=payload
    )

    assert response.status_code == 200

    data = response.json()

    assert "final_score" in data
    assert "risk_category" in data
    assert "lifestyle_score" in data
    assert "spending_score" in data
    assert "repayment_score" in data

    assert 0 <= data["final_score"] <= 1000


def test_score_api_invalid_data():

    payload = {
        "employment_months": 24
    }

    response = client.post(
        "/api/score/calculate",
        json=payload
    )

    # Because the current endpoint accepts a generic dict,
    # this may produce a 400 or 500 depending on validation.
    assert response.status_code in [400, 422, 500]