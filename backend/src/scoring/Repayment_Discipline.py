def on_time_payment_score(rate: float) -> int:

    if rate >= 0.98:
        return 200

    if rate >= 0.95:
        return 150

    if rate >= 0.90:
        return 100

    if rate >= 0.80:
        return 50

    return 0


def debt_to_income_score(ratio: float) -> int:

    if ratio <= 0.20:
        return 120

    if ratio <= 0.35:
        return 80

    if ratio <= 0.50:
        return 40

    return 0


def credit_utilization_score(ratio: float) -> int:

    if ratio <= 0.10:
        return 100

    if ratio <= 0.30:
        return 70

    if ratio <= 0.50:
        return 30

    return 0


def delinquency_score(
    days_late: int = 0,
    multiple_misses: bool = False
) -> int:

    if multiple_misses or days_late >= 90:
        return 0

    if days_late >= 60:
        return 50

    if days_late >= 30:
        return 100

    return 150


def calculate_repayment_score(features: dict) -> dict:

    return {
        "On-time Payment Rate":
            on_time_payment_score(
                features.get(
                    "on_time_payment_rate", 0
                )
            ),

        "Debt-to-Income Ratio":
            debt_to_income_score(
                features.get(
                    "debt_to_income", 1
                )
            ),

        "Credit Utilization":
            credit_utilization_score(
                features.get(
                    "credit_utilization", 1
                )
            ),

        "Recent Delinquency Severity":
            delinquency_score(
                features.get("days_late", 0),
                features.get("multiple_misses", False)
            )
    }