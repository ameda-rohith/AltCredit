"""Feature engineering formulas required by AltCredit."""


import numpy as np


def calculate_spend_income_ratio(
    monthly_spend: float,
    monthly_income: float
) -> float:

    if monthly_income <= 0:
        return 1.0

    return max(
        0.0,
        monthly_spend / monthly_income
    )


def calculate_expense_diversity(
    essential_spend: float,
    total_spend: float
) -> float:

    if total_spend <= 0:
        return 0.0

    return max(
        0.0,
        min(
            1.0,
            essential_spend / total_spend
        )
    )


def calculate_cashflow_volatility(
    monthly_net_cashflows: list[float],
    monthly_income: float
) -> float:

    if monthly_income <= 0:
        return 1.0

    if len(monthly_net_cashflows) != 6:
        raise ValueError(
            "Cash-flow volatility requires "
            "exactly 6 months of net cash-flow data."
        )

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

    return (
        liquid_savings * 30
        / monthly_income
    )


def calculate_debt_to_income(
    monthly_debt: float,
    monthly_income: float
) -> float:

    if monthly_income <= 0:
        return 1.0

    return (
        monthly_debt
        / monthly_income
    )


def calculate_credit_utilization(
    outstanding: float,
    credit_limit: float
) -> float:

    if credit_limit <= 0:
        return 0.0

    return (
        outstanding
        / credit_limit
    )


def build_features(
    raw: dict
) -> dict:

    features = dict(raw)

    income = float(
        raw.get(
            "monthly_income",
            0
        ) or 0
    )

    spend = float(
        raw.get(
            "monthly_spend",
            0
        ) or 0
    )

    # 2.1 Spend-to-Income
    if (
        income > 0
        and
        "monthly_spend" in raw
    ):

        features[
            "spend_income_ratio"
        ] = calculate_spend_income_ratio(
            spend,
            income
        )

    # 2.2 Expense Diversity
    if (
        "essential_spend" in raw
        and
        "monthly_spend" in raw
    ):

        features[
            "essential_ratio"
        ] = calculate_expense_diversity(
            float(
                raw.get(
                    "essential_spend",
                    0
                ) or 0
            ),
            spend
        )

    elif "essential_pct" in raw:

        features[
            "essential_ratio"
        ] = float(
            raw.get(
                "essential_pct",
                0
            ) or 0
        )

    # 2.3 Cash-flow volatility
    if "monthly_net_cashflows" in raw:

        features[
            "cashflow_volatility"
        ] = calculate_cashflow_volatility(
            [
                float(x)
                for x in
                raw["monthly_net_cashflows"]
            ],
            income
        )

    # 2.4 Savings
    if "liquid_savings" in raw:

        features[
            "savings_days"
        ] = calculate_savings_days(
            float(
                raw.get(
                    "liquid_savings",
                    0
                ) or 0
            ),
            income
        )

    # 3.2 DTI
    if (
        "monthly_debt" in raw
        and
        income > 0
    ):

        features[
            "debt_to_income"
        ] = calculate_debt_to_income(
            float(
                raw.get(
                    "monthly_debt",
                    0
                ) or 0
            ),
            income
        )

    # 3.3 Credit utilization
    if (
        "outstanding_balance" in raw
        and
        "credit_limit" in raw
    ):

        credit_limit = float(
            raw.get(
                "credit_limit",
                0
            ) or 0
        )

        features[
            "has_credit_line"
        ] = credit_limit > 0

        features[
            "credit_utilization"
        ] = calculate_credit_utilization(
            float(
                raw.get(
                    "outstanding_balance",
                    0
                ) or 0
            ),
            credit_limit
        )

    return features