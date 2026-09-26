from backend.scoring.lifestyle import (
    calculate_lifestyle_score
)

from backend.scoring.spending_behavior import (
    calculate_spending_score
)

from backend.scoring.repayment_discipline import (
    calculate_repayment_score
)

from backend.scoring.bonus_penalty import (
    calculate_bonus,
    calculate_penalty
)


def calculate_score(features: dict) -> dict:

    lifestyle_factors = calculate_lifestyle_score(
        features
    )

    spending_factors = calculate_spending_score(
        features
    )

    repayment_factors = calculate_repayment_score(
        features
    )

    lifestyle_score = sum(
        lifestyle_factors.values()
    )

    spending_score = sum(
        spending_factors.values()
    )

    repayment_score = sum(
        repayment_factors.values()
    )

    bonus = calculate_bonus(
        features.get("qualifying_habits", 0)
    )

    penalty = calculate_penalty(
        features.get("risk_flags", 0)
    )

    raw_score = (
        lifestyle_score
        + spending_score
        + repayment_score
        + bonus
        - penalty
    )

    # The table's individual maxima total 1270,
    # while the specification defines the unified score
    # as 0–1000. Normalize the rule-table score.
    final_score = round(
        max(0, min(1000, raw_score * 1000 / 1270))
    )

    return {
        "lifestyle_score": lifestyle_score,
        "spending_score": spending_score,
        "repayment_score": repayment_score,
        "bonus_points": bonus,
        "penalty_points": penalty,
        "raw_score": raw_score,
        "final_score": final_score,
        "lifestyle_factors": lifestyle_factors,
        "spending_factors": spending_factors,
        "repayment_factors": repayment_factors
    }