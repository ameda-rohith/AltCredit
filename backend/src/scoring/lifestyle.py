"""Lifestyle scoring rules from the AltCredit use-case."""


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

    status = str(
        housing_status or ""
    ).strip().lower()

    if status in {
        "own",
        "owner",
        "own home",
        "owned"
    }:
        return 80

    if status == "rent":
        return (
            60
            if rent_payment_months >= 12
            else 30
        )

    return 0


def digital_footprint_score(
    payment_rate: float
) -> int:

    rate = max(
        0.0,
        min(float(payment_rate), 1.0)
    )

    if rate >= 0.95:
        return 70

    if rate >= 0.80:
        return 45

    if rate >= 0.60:
        return 20

    return 0


def education_score(
    education_level: str
) -> int:

    education = str(
        education_level or ""
    ).strip().lower()

    if education in {
        "master",
        "master's",
        "masters",
        "phd",
        "doctorate"
    }:
        return 50

    if education in {
        "bachelor",
        "bachelor's",
        "bachelors"
    }:
        return 40

    if education in {
        "professional certificate",
        "professional cert",
        "certification"
    }:
        return 30

    if education in {
        "high-school",
        "high school",
        "secondary"
    }:
        return 20

    return 0


def calculate_lifestyle_score(
    features: dict
) -> dict:

    return {
        "Employment Stability":
            employment_stability_score(
                int(
                    features.get(
                        "employment_months",
                        features.get(
                            "months_at_job",
                            0
                        )
                    ) or 0
                )
            ),

        "Housing Status":
            housing_score(
                features.get(
                    "housing_status",
                    features.get(
                        "housing",
                        "none"
                    )
                ),
                int(
                    features.get(
                        "rent_payment_months",
                        features.get(
                            "rent_on_time_months",
                            0
                        )
                    ) or 0
                )
            ),

        "Digital Footprint":
            digital_footprint_score(
                features.get(
                    "digital_payment_rate",
                    0.0
                ) or 0.0
            ),

        "Education / Skill Level":
            education_score(
                features.get(
                    "education_level",
                    features.get(
                        "education",
                        ""
                    )
                )
            )
    }