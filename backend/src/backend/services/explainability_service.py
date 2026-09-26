def generate_explanation(features: dict, scores: dict):

    factors = []

    if scores["lifestyle_score"] >= 250:
        factors.append({
            "factor": "Lifestyle Stability",
            "impact": "positive",
            "message": "Stable employment, housing or education contributed positively."
        })

    if scores["spending_score"] >= 250:
        factors.append({
            "factor": "Spending Behaviour",
            "impact": "positive",
            "message": "Healthy spending and savings behaviour improved the score."
        })

    if scores["repayment_score"] >= 400:
        factors.append({
            "factor": "Repayment Discipline",
            "impact": "positive",
            "message": "Strong payment consistency contributed positively."
        })

    if features.get("spend_income_ratio", 0) > 0.70:
        factors.append({
            "factor": "Spend-to-Income Ratio",
            "impact": "negative",
            "message": "High monthly spending relative to income reduced the score."
        })

    if features.get("cashflow_volatility", 0) > 0.20:
        factors.append({
            "factor": "Cash-flow Volatility",
            "impact": "negative",
            "message": "High cash-flow volatility reduced the score."
        })

    return factors