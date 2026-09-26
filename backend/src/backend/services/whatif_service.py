from copy import deepcopy

from scoring.scoring_engine import calculate_score


def simulate_what_if(
    current_features: dict,
    changes: dict
) -> dict:

    simulated = deepcopy(
        current_features
    )

    income = float(
        simulated.get(
            "monthly_income",
            0
        ) or 0
    )

    if income <= 0:
        raise ValueError(
            "monthly_income must be "
            "greater than zero for "
            "What-If analysis"
        )

    # -----------------------------------------
    # 2.4 Savings / Emergency Fund
    # -----------------------------------------

    additional_savings = float(
        changes.get(
            "additional_savings",
            0
        ) or 0
    )

    current_savings_days = float(
        simulated.get(
            "savings_days",
            0
        ) or 0
    )

    simulated[
        "savings_days"
    ] = max(
        0.0,
        current_savings_days
        + (
            additional_savings
            * 30
            / income
        )
    )

    # -----------------------------------------
    # 2.1 Spend-to-Income Ratio
    # -----------------------------------------

    additional_spending = float(
        changes.get(
            "additional_monthly_spending",
            0
        ) or 0
    )

    simulated_spend = float(
        simulated.get(
            "monthly_spend",
            income
            * float(
                simulated.get(
                    "spend_income_ratio",
                    0
                )
            )
        )
    )

    simulated_spend += (
        additional_spending
    )

    simulated_spend = max(
        0.0,
        simulated_spend
    )

    simulated[
        "monthly_spend"
    ] = simulated_spend

    simulated[
        "spend_income_ratio"
    ] = (
        simulated_spend
        / income
    )

    # -----------------------------------------
    # 2.2 Expense Diversity
    # -----------------------------------------

    if "essential_spend" in simulated:

        essential_spend = max(
            0.0,
            float(
                simulated[
                    "essential_spend"
                ]
            )
        )

        simulated[
            "essential_ratio"
        ] = (
            essential_spend
            / simulated_spend
            if simulated_spend > 0
            else 0.0
        )

    # -----------------------------------------
    # 3.1 Payment Rate
    # -----------------------------------------

    simulated[
        "on_time_payment_rate"
    ] = max(
        0.0,
        min(
            1.0,
            float(
                simulated.get(
                    "on_time_payment_rate",
                    0.0
                )
            )
            +
            float(
                changes.get(
                    "payment_rate_change",
                    0
                ) or 0
            )
        )
    )

    # -----------------------------------------
    # 3.2 Debt-to-Income
    # -----------------------------------------

    additional_debt = float(
        changes.get(
            "additional_debt",
            0
        ) or 0
    )

    current_dti = float(
        simulated.get(
            "debt_to_income",
            0
        ) or 0
    )

    simulated[
        "debt_to_income"
    ] = max(
        0.0,
        current_dti
        + (
            additional_debt
            / income
        )
    )

    # -----------------------------------------
    # 2.3 Cash-flow Volatility
    # -----------------------------------------

    if "cashflow_volatility_change" in changes:

        simulated[
            "cashflow_volatility"
        ] = max(
            0.0,
            float(
                simulated.get(
                    "cashflow_volatility",
                    0
                )
            )
            +
            float(
                changes.get(
                    "cashflow_volatility_change",
                    0
                ) or 0
            )
        )

    # -----------------------------------------
    # 1.2 Rent payment history
    # -----------------------------------------

    simulated[
        "rent_payment_months"
    ] = max(
        0,
        int(
            simulated.get(
                "rent_payment_months",
                0
            )
        )
        +
        int(
            changes.get(
                "additional_rent_payment_months",
                0
            )
        )
    )

    # -----------------------------------------
    # 3.4 Delinquency
    # -----------------------------------------

    for key in (
        "delinq_30plus",
        "delinq_60plus",
        "delinq_90plus"
    ):

        simulated[key] = max(
            0,
            int(
                simulated.get(
                    key,
                    0
                )
            )
            +
            int(
                changes.get(
                    f"{key}_change",
                    0
                )
            )
        )

    return calculate_score(
        simulated
    )