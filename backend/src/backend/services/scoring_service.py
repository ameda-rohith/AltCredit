def get_risk_category(score: float) -> str:

    if score >= 800:
        return "Excellent"

    if score >= 650:
        return "Good"

    if score >= 500:
        return "Fair"

    if score >= 350:
        return "Poor"

    return "Very Poor"