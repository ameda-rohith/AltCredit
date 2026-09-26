def calculate_bonus(
    qualifying_habits: int
) -> int:

    # PDF: +20 per qualifying habit,
    # maximum +50.
    return min(
        max(
            int(qualifying_habits or 0),
            0
        ) * 20,
        50
    )


def calculate_penalty(
    risk_flags: int
) -> int:

    # PDF: -20 per risk flag,
    # maximum -50.
    return min(
        max(
            int(risk_flags or 0),
            0
        ) * 20,
        50
    )