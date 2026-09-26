def recommend_products(products, score: float):

    recommendations = []

    for product in products:

        if score >= product.min_score_required:

            recommendations.append({
                "product_id": product.product_id,
                "name": product.name,
                "type": product.type,
                "interest_rate": product.interest_rate,
                "reason": (
                    f"Your score of {score:.0f} "
                    f"meets the minimum score of "
                    f"{product.min_score_required:.0f}."
                )
            })

    recommendations.sort(
        key=lambda x: x["interest_rate"]
        if x["interest_rate"] is not None
        else 999
    )

    return recommendations