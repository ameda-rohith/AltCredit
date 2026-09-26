import numpy as np


def calculate_spend_income_ratio(
    monthly_spend: float,
    monthly_income: float
) -> float:

    if monthly_income <= 0:
        return 1.0

    return monthly_spend / monthly_income


def calculate_expense_diversity(
    essential_spend: float,
    total_spend: float
) -> float:

    if total_spend <= 0:
        return 0.0

    return essential_spend / total_spend


def calculate_cashflow_volatility(
    monthly_net_cashflows: list[float],
    monthly_income: float
) -> float:

    if not monthly_net_cashflows or monthly_income <= 0:
        return 0.0

    return float(
        np.std(monthly_net_cashflows)
        / monthly_income
    )


def calculate_savings_days(
    liquid_savings: float,
    monthly_income: float
) -> float:

    if monthly_income <= 0:
        return 0.0

    daily_income = monthly_income / 30

    return liquid_savings / daily_income


def calculate_debt_to_income(
    monthly_debt: float,
    monthly_income: float
) -> float:

    if monthly_income <= 0:
        return 1.0

    return monthly_debt / monthly_income


def calculate_credit_utilization(
    outstanding: float,
    credit_limit: float
) -> float:

    if credit_limit <= 0:
        return 0.0

    return outstanding / credit_limit