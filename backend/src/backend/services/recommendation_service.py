def recommend_products(
    products,
    score: float
):

    recommendations = []

    for product in products:

        if score >= product.min_score_required:

            recommendations.append({

                "product_id":
                    product.product_id,

                "name":
                    product.name,

                "type":
                    product.type,

                "interest_rate":
                    product.interest_rate,

                "min_score_required":
                    product.min_score_required,

                "reason":
                    (
                        f"Your score of "
                        f"{score:.0f} meets the "
                        f"minimum score of "
                        f"{product.min_score_required:.0f}."
                    )
            })

    recommendations.sort(
        key=lambda x:
            x["min_score_required"]
    )

    return recommendations