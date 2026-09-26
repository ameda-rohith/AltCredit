"""Repayment-discipline scoring rules from the AltCredit use-case."""


def on_time_payment_score(
    rate: float
) -> int:

    if rate >= 0.98:
        return 200

    if rate >= 0.95:
        return 150

    if rate >= 0.90:
        return 100

    if rate >= 0.80:
        return 50

    return 0


def debt_to_income_score(
    ratio: float
) -> int:

    if ratio <= 0.20:
        return 120

    if ratio <= 0.35:
        return 80

    if ratio <= 0.50:
        return 40

    return 0


def credit_utilization_score(
    ratio: float,
    has_credit_line: bool = True
) -> int:

    if not has_credit_line:
        return 0

    if ratio <= 0.10:
        return 100

    if ratio <= 0.30:
        return 70

    if ratio <= 0.50:
        return 30

    return 0


def delinquency_score(
    delinq_30plus: int = 0,
    delinq_60plus: int = 0,
    delinq_90plus: int = 0
) -> int:

    d30 = max(
        0,
        int(delinq_30plus)
    )

    d60 = max(
        0,
        int(delinq_60plus)
    )

    d90 = max(
        0,
        int(delinq_90plus)
    )

    total_misses = (
        d30 + d60 + d90
    )

    # No missed payment
    if total_misses == 0:
        return 150

    # Multiple misses
    if total_misses > 1:
        return 0

    # 90+ day miss
    if d90 >= 1:
        return 0

    # 60-day miss
    if d60 >= 1:
        return 50

    # 30-day miss
    if d30 >= 1:
        return 100

    return 150


def calculate_repayment_score(
    features: dict
) -> dict:

    has_credit_line = bool(
        features["has_credit_line"]
        if "has_credit_line" in features
        else (
            "credit_utilization" in features
            or
            "credit_util" in features
        )
    )

    return {

        "On-time Payment Rate":
            on_time_payment_score(
                float(
                    features.get(
                        "on_time_payment_rate",
                        features.get(
                            "on_time_rate",
                            0.0
                        )
                    )
                )
            ),

        "Debt-to-Income Ratio":
            debt_to_income_score(
                float(
                    features.get(
                        "debt_to_income",
                        features.get(
                            "dti",
                            1.0
                        )
                    )
                )
            ),

        "Credit Utilization":
            credit_utilization_score(
                float(
                    features.get(
                        "credit_utilization",
                        features.get(
                            "credit_util",
                            0.0
                        )
                    )
                ),
                has_credit_line
            ),

        "Recent Delinquency Severity":
            delinquency_score(
                features.get(
                    "delinq_30plus",
                    0
                ),
                features.get(
                    "delinq_60plus",
                    0
                ),
                features.get(
                    "delinq_90plus",
                    0
                )
            )
    }