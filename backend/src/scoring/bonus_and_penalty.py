def calculate_bonus(
    qualifying_habits: int
) -> int:

    qualifying_habits = max(
        0,
        min(qualifying_habits, 3)
    )

    return qualifying_habits * 20


def calculate_penalty(
    risk_flags: int
) -> int:

    risk_flags = max(0, risk_flags)

    return min(risk_flags * 20, 50)