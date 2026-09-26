import pytest

from app.services.whatif_service import simulate_what_if


@pytest.fixture
def base_features():
    """
    Base user profile used for What-If tests.
    """

    return {
        "employment_months": 24,
        "housing_status": "rent",
        "residency_months": 18,

        "digital_payment_rate": 0.95,
        "education_level": "bachelor",

        "spend_income_ratio": 0.40,
        "essential_ratio": 0.65,
        "cashflow_volatility": 0.08,
        "savings_days": 60,

        "on_time_payment_rate": 0.95,
        "debt_to_income": 0.25,
        "credit_utilization": 0.20,
        "days_late": 0,

        "qualifying_habits": 1,
        "risk_flags": 0,

        "monthly_income": 40000,
        "daily_income": 40000 / 30,
    }


def test_whatif_returns_score(base_features):
    """
    Basic test:
    What-If simulation should return a calculated score.
    """

    result = simulate_what_if(
        current_features=base_features,
        changes={}
    )

    assert result is not None
    assert "final_score" in result
    assert "raw_score" in result

    assert 0 <= result["final_score"] <= 1000


def test_whatif_without_changes_keeps_score_same(base_features):
    """
    If the user makes no changes,
    the simulated score should remain the same.
    """

    current_result = simulate_what_if(
        current_features=base_features,
        changes={}
    )

    simulated_result = simulate_what_if(
        current_features=base_features,
        changes={
            "additional_savings": 0,
            "additional_monthly_spending": 0,
            "payment_rate_change": 0,
            "additional_debt": 0,
        }
    )

    assert (
        current_result["final_score"]
        == simulated_result["final_score"]
    )


def test_additional_savings_can_improve_score(base_features):
    """
    Increasing savings should not reduce the score.

    The test uses enough additional savings to
    cross a savings-score threshold.
    """

    current_result = simulate_what_if(
        current_features=base_features,
        changes={}
    )

    simulated_result = simulate_what_if(
        current_features=base_features,
        changes={
            "additional_savings": 30000
        }
    )

    assert (
        simulated_result["final_score"]
        >= current_result["final_score"]
    )


def test_higher_payment_rate_can_improve_score(base_features):
    """
    Improving on-time payment rate should not reduce
    the credit score.
    """

    current_result = simulate_what_if(
        current_features=base_features,
        changes={}
    )

    simulated_result = simulate_what_if(
        current_features=base_features,
        changes={
            "payment_rate_change": 0.03
        }
    )

    assert (
        simulated_result["final_score"]
        >= current_result["final_score"]
    )


def test_additional_debt_can_reduce_score(base_features):
    """
    Increasing debt-to-income ratio should not improve
    the score.
    """

    current_result = simulate_what_if(
        current_features=base_features,
        changes={}
    )

    simulated_result = simulate_what_if(
        current_features=base_features,
        changes={
            "additional_debt": 20000
        }
    )

    assert (
        simulated_result["final_score"]
        <= current_result["final_score"]
    )


def test_additional_spending_can_reduce_score(base_features):
    """
    Increasing monthly spending should not improve
    the score.
    """

    current_result = simulate_what_if(
        current_features=base_features,
        changes={}
    )

    simulated_result = simulate_what_if(
        current_features=base_features,
        changes={
            "additional_monthly_spending": 10000
        }
    )

    assert (
        simulated_result["final_score"]
        <= current_result["final_score"]
    )


def test_multiple_whatif_changes(base_features):
    """
    Test a realistic scenario where the user:
    - saves more
    - reduces spending
    - improves payment behaviour
    """

    current_result = simulate_what_if(
        current_features=base_features,
        changes={}
    )

    simulated_result = simulate_what_if(
        current_features=base_features,
        changes={
            "additional_savings": 15000,
            "additional_monthly_spending": -5000,
            "payment_rate_change": 0.03,
        }
    )

    assert simulated_result["final_score"] >= current_result["final_score"]


def test_original_features_are_not_modified(base_features):
    """
    The What-If simulation should work on a copy of the
    user's features and must not permanently modify
    the original profile.
    """

    original_savings_days = base_features["savings_days"]
    original_payment_rate = base_features["on_time_payment_rate"]
    original_dti = base_features["debt_to_income"]

    simulate_what_if(
        current_features=base_features,
        changes={
            "additional_savings": 10000,
            "payment_rate_change": 0.02,
            "additional_debt": 5000,
        }
    )

    assert (
        base_features["savings_days"]
        == original_savings_days
    )

    assert (
        base_features["on_time_payment_rate"]
        == original_payment_rate
    )

    assert (
        base_features["debt_to_income"]
        == original_dti
    )