"""Canonical AltCredit rule-based scoring engine."""


from scoring.lifestyle import (
    calculate_lifestyle_score
)

from scoring.spending_behavior import (
    calculate_spending_score
)

from scoring.Repayment_Discipline import (
    calculate_repayment_score
)

from scoring.bonus_and_penalty import (
    calculate_bonus,
    calculate_penalty
)


RAW_SCORE_MAX = 1270
FINAL_SCORE_MAX = 1000


def calculate_score(
    features: dict
) -> dict:

    lifestyle_factors = (
        calculate_lifestyle_score(
            features
        )
    )

    spending_factors = (
        calculate_spending_score(
            features
        )
    )

    repayment_factors = (
        calculate_repayment_score(
            features
        )
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
        features.get(
            "qualifying_habits",
            0
        )
    )

    penalty = calculate_penalty(
        features.get(
            "risk_flags",
            0
        )
    )

    raw_score = (
        lifestyle_score
        + spending_score
        + repayment_score
        + bonus
        - penalty
    )

    # The individual maxima in the PDF total 1270,
    # while the unified score is defined as 0-1000.
    final_score = round(
        max(
            0,
            min(
                FINAL_SCORE_MAX,
                raw_score
                * FINAL_SCORE_MAX
                / RAW_SCORE_MAX
            )
        )
    )

    return {

        "final_score":
            final_score,

        "raw_score":
            raw_score,

        "lifestyle_score":
            lifestyle_score,

        "spending_score":
            spending_score,

        "repayment_score":
            repayment_score,

        "bonus_points":
            bonus,

        "penalty_points":
            penalty,

        "lifestyle_factors":
            lifestyle_factors,

        "spending_factors":
            spending_factors,

        "repayment_factors":
            repayment_factors
    }