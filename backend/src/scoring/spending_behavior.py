def spend_income_score(ratio: float) -> int:

    if ratio <= 0.30:
        return 120

    if ratio <= 0.50:
        return 80

    if ratio <= 0.70:
        return 40

    return 0


def expense_diversity_score(ratio: float) -> int:

    if ratio >= 0.70:
        return 80

    if ratio >= 0.55:
        return 45

    if ratio >= 0.40:
        return 20

    return 0


def cashflow_volatility_score(volatility: float) -> int:

    if volatility <= 0.05:
        return 70

    if volatility <= 0.10:
        return 40

    if volatility <= 0.20:
        return 15

    return 0


def savings_score(days: float) -> int:

    if days >= 180:
        return 80

    if days >= 90:
        return 50

    if days >= 30:
        return 20

    return 0


def calculate_spending_score(features: dict) -> dict:

    return {
        "Spend-to-Income Ratio":
            spend_income_score(
                features.get("spend_income_ratio", 1)
            ),

        "Expense Diversity":
            expense_diversity_score(
                features.get("essential_ratio", 0)
            ),

        "Cash-flow Volatility":
            cashflow_volatility_score(
                features.get("cashflow_volatility", 1)
            ),

        "Savings / Emergency Fund":
            savings_score(
                features.get("savings_days", 0)
            )
    }