def employment_stability_score(months: int) -> int:
    if months >= 24:
        return 150
    if months >= 12:
        return 100
    if months >= 6:
        return 50
    return 0


def housing_score(
    housing_status: str,
    rent_payment_months: int = 0
) -> int:

    housing_status = housing_status.lower()

    if housing_status in {"own", "owner"}:
        return 80

    if housing_status == "rent":
        if rent_payment_months >= 12:
            return 60

        if rent_payment_months > 0:
            return 30

    return 0


def digital_footprint_score(
    payment_rate: float
) -> int:

    if payment_rate >= 0.95:
        return 70

    if payment_rate >= 0.80:
        return 45

    if payment_rate >= 0.60:
        return 20

    return 0


def education_score(
    education_level: str
) -> int:

    education = education_level.lower()

    if education in {"master", "master's", "phd", "doctorate"}:
        return 50

    if education in {"bachelor", "bachelor's"}:
        return 40

    if education in {
        "professional certificate",
        "professional cert",
        "certification"
    }:
        return 30

    if education in {"high-school", "high school", "secondary"}:
        return 20

    return 0


def calculate_lifestyle_score(features: dict) -> dict:

    employment = employment_stability_score(
        features.get("employment_months", 0)
    )

    housing = housing_score(
        features.get("housing_status", "none"),
        features.get("rent_on_time_months", 0)
    )

    digital = digital_footprint_score(
        features.get("digital_payment_rate", 0)
    )

    education = education_score(
        features.get("education_level", "")
    )

    return {
        "Employment Stability": employment,
        "Housing Status": housing,
        "Digital Footprint": digital,
        "Education / Skill Level": education
    }