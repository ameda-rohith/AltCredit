import pytest

from app.services.feature_service import (
    calculate_spend_income_ratio,
    calculate_expense_diversity,
    calculate_cashflow_volatility,
    calculate_savings_days,
    calculate_debt_to_income,
    calculate_credit_utilization
)


def test_spend_income_ratio():

    result = calculate_spend_income_ratio(
        monthly_spend=20000,
        monthly_income=50000
    )

    assert result == pytest.approx(0.40)


def test_spend_income_ratio_zero_income():

    result = calculate_spend_income_ratio(
        monthly_spend=20000,
        monthly_income=0
    )

    assert result == 1.0


def test_expense_diversity():

    result = calculate_expense_diversity(
        essential_spend=14000,
        total_spend=20000
    )

    assert result == pytest.approx(0.70)


def test_expense_diversity_zero_spending():

    result = calculate_expense_diversity(
        essential_spend=0,
        total_spend=0
    )

    assert result == 0.0


def test_cashflow_volatility():

    cashflows = [
        10000,
        12000,
        11000,
        9000,
        10000,
        11000
    ]

    result = calculate_cashflow_volatility(
        monthly_net_cashflows=cashflows,
        monthly_income=50000
    )

    assert result >= 0


def test_cashflow_volatility_empty_data():

    result = calculate_cashflow_volatility(
        monthly_net_cashflows=[],
        monthly_income=50000
    )

    assert result == 0.0


def test_savings_days():

    result = calculate_savings_days(
        liquid_savings=30000,
        monthly_income=60000
    )

    # Daily income = 60000 / 30 = 2000
    # Savings days = 30000 / 2000 = 15
    assert result == pytest.approx(15.0)


def test_savings_days_zero_income():

    result = calculate_savings_days(
        liquid_savings=30000,
        monthly_income=0
    )

    assert result == 0.0


def test_debt_to_income():

    result = calculate_debt_to_income(
        monthly_debt=10000,
        monthly_income=50000
    )

    assert result == pytest.approx(0.20)


def test_debt_to_income_zero_income():

    result = calculate_debt_to_income(
        monthly_debt=10000,
        monthly_income=0
    )

    assert result == 1.0


def test_credit_utilization():

    result = calculate_credit_utilization(
        outstanding=20000,
        credit_limit=100000
    )

    assert result == pytest.approx(0.20)


def test_credit_utilization_zero_limit():

    result = calculate_credit_utilization(
        outstanding=20000,
        credit_limit=0
    )

    assert result == 0.0