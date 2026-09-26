from datetime import date


def clean_transactions(
    transactions: list[dict]
) -> list[dict]:

    cleaned = []

    required = {
        "transaction_id",
        "user_id",
        "date",
        "amount",
        "category",
        "type"
    }

    for row in transactions:

        if not required.issubset(
            row.keys()
        ):
            continue

        try:

            cleaned.append({

                "transaction_id":
                    str(
                        row[
                            "transaction_id"
                        ]
                    ),

                "user_id":
                    str(
                        row[
                            "user_id"
                        ]
                    ),

                "date":
                    date.fromisoformat(
                        str(
                            row["date"]
                        )[:10]
                    ),

                "amount":
                    float(
                        row["amount"]
                    ),

                "category":
                    str(
                        row["category"]
                    ),

                "type":
                    str(
                        row["type"]
                    ).lower(),

                "payment_status":
                    (
                        str(
                            row[
                                "payment_status"
                            ]
                        )
                        if row.get(
                            "payment_status"
                        ) is not None
                        else None
                    )
            })

        except (
            TypeError,
            ValueError
        ):
            continue

    return cleaned