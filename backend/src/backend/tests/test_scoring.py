import pytest

from app.scoring.score_engine import calculate_score
from app.services.scoring_service import get_risk_category


def sample_features():
    return {
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


def test_score_calculation():

    features = sample_features()

    result = calculate_score(features)

    assert "lifestyle_score" in result
    assert "spending_score" in result
    assert "repayment_score" in result
    assert "bonus_points" in result
    assert "penalty_points" in result
    assert "raw_score" in result
    assert "final_score" in result


def test_score_is_within_valid_range():

    features = sample_features()

    result = calculate_score(features)

    assert 0 <= result["final_score"] <= 1000


def test_positive_user_gets_high_score():

    features = sample_features()

    result = calculate_score(features)

    assert result["final_score"] >= 700


def test_bonus_points():

    features = sample_features()

    result = calculate_score(features)

    assert result["bonus_points"] == 40


def test_penalty_points():

    features = sample_features()

    features["risk_flags"] = 2

    result = calculate_score(features)

    assert result["penalty_points"] == 40


def test_poor_payment_behaviour():

    features = sample_features()

    features["on_time_payment_rate"] = 0.50
    features["days_late"] = 90
    features["multiple_misses"] = True

    result = calculate_score(features)

    assert result["repayment_score"] < 450


def test_high_spending_reduces_score():

    good_features = sample_features()

    bad_features = sample_features()
    bad_features["spend_income_ratio"] = 0.80

    good_result = calculate_score(good_features)
    bad_result = calculate_score(bad_features)

    assert (
        bad_result["spending_score"]
        <
        good_result["spending_score"]
    )


def test_risk_category():

    assert get_risk_category(850) == "Excellent"
    assert get_risk_category(700) == "Good"
    assert get_risk_category(550) == "Fair"
    assert get_risk_category(400) == "Poor"
    assert get_risk_category(200) == "Very Poor"