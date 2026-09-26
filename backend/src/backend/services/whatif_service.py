from copy import deepcopy

from app.scoring.score_engine import calculate_score


def simulate_what_if(
    current_features: dict,
    changes: dict
):

    simulated = deepcopy(current_features)

    # Additional savings
    simulated["savings_days"] += (
        changes.get("additional_savings", 0) /
        max(current_features["daily_income"], 1)
    )

    # Additional spending
    simulated["spend_income_ratio"] += (
        changes.get("additional_monthly_spending", 0) /
        max(current_features["monthly_income"], 1)
    )

    # Payment behaviour
    simulated["on_time_payment_rate"] += (
        changes.get("payment_rate_change", 0)
    )

    simulated["on_time_payment_rate"] = max(
        0,
        min(
            simulated["on_time_payment_rate"],
            1
        )
    )

    # Additional debt
    simulated["debt_to_income"] += (
        changes.get("additional_debt", 0) /
        max(current_features["monthly_income"], 1)
    )

    result = calculate_score(simulated)

    return result