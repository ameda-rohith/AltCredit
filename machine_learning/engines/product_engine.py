"""
Automated Product Recommendation Engine

Uses:
    merged_data.json
    product_catalog.json
    AltCreditRuleEngine

Output:
    product_recommendations.csv

One row = one user.
"""

from pathlib import Path
from typing import Dict, Any, List
import json
import csv

from rule_engine import AltCreditRuleEngine


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_PATH = (
    BASE_DIR
    / "data"  
    / "merged_data.json"
)

PRODUCT_PATH = (
    BASE_DIR
    / "data"
    / "product_catalog.json"
)

OUTPUT_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "product_recommendations.csv"
)


# ============================================================
# LOAD USERS
# ============================================================

def load_users() -> List[Dict[str, Any]]:

    with open(
        DATA_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        users = json.load(file)

    if not isinstance(users, list):

        raise ValueError(
            "merged_data.json must contain a list."
        )

    return users


# ============================================================
# LOAD PRODUCTS
# ============================================================

def load_product_catalog() -> List[Dict[str, Any]]:

    with open(
        PRODUCT_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

    if isinstance(data, list):

        return data

    if isinstance(data, dict):

        if "products" in data:

            return data["products"]

    raise ValueError(
        "product_catalog.json must contain "
        "a list or 'products' field."
    )


# ============================================================
# PRODUCT HELPERS
# ============================================================

def get_product_id(
    product: Dict[str, Any]
) -> str:

    return str(

        product.get("product_id")

        or product.get("id")

        or product.get("code")

        or ""
    )


def get_product_name(
    product: Dict[str, Any]
) -> str:

    return str(

        product.get("product_name")

        or product.get("name")

        or product.get("title")

        or "Unknown Product"
    )


def get_min_score(
    product: Dict[str, Any]
) -> float:

    return float(

        product.get("min_score")

        or product.get("minimum_score")

        or 0
    )


# ============================================================
# RECOMMEND PRODUCTS FOR ONE USER
# ============================================================

def recommend_products(
    score: float,
    products: List[Dict[str, Any]]
) -> Dict[str, Any]:

    eligible = []
    ineligible = []

    for product in products:

        product_id = get_product_id(
            product
        )

        product_name = get_product_name(
            product
        )

        minimum_score = get_min_score(
            product
        )

        # ----------------------------------------------------
        # Eligible
        # ----------------------------------------------------

        if score >= minimum_score:

            eligible.append({

                "product_id":
                    product_id,

                "product_name":
                    product_name,

                "minimum_score":
                    minimum_score,

                "points_above_requirement":
                    round(
                        score - minimum_score,
                        2
                    ),

                "eligibility":
                    "eligible",

                "product_details":
                    product
            })

        # ----------------------------------------------------
        # Not eligible
        # ----------------------------------------------------

        else:

            ineligible.append({

                "product_id":
                    product_id,

                "product_name":
                    product_name,

                "minimum_score":
                    minimum_score,

                "points_needed":
                    round(
                        minimum_score - score,
                        2
                    ),

                "eligibility":
                    "not_eligible",

                "product_details":
                    product
            })

    # Highest score requirement first
    eligible.sort(

        key=lambda x:
            x["minimum_score"],

        reverse=True
    )

    # Closest product first
    ineligible.sort(

        key=lambda x:
            x["minimum_score"]
    )

    highest_eligible = (

        eligible[0]

        if eligible

        else None
    )

    next_product = (

        ineligible[0]

        if ineligible

        else None
    )

    return {

        "current_score":
            score,

        "eligible_products":
            eligible,

        "ineligible_products":
            ineligible,

        "highest_eligible_product":
            highest_eligible,

        "next_product":
            next_product
    }


# ============================================================
# GENERATE RECOMMENDATIONS FOR ALL USERS
# ============================================================

def generate_product_recommendations():

    users = load_users()

    products = load_product_catalog()

    engine = AltCreditRuleEngine()

    print(
        f"Loaded {len(users)} users."
    )

    print(
        f"Loaded {len(products)} products."
    )

    rows = []

    successful = 0
    failed = 0

    # --------------------------------------------------------
    # Process every real user
    # --------------------------------------------------------

    for user in users:

        try:

            # ------------------------------------------------
            # Calculate score using NEW rule engine
            # ------------------------------------------------

            evaluation = engine.evaluate_user(
                user
            )

            score = evaluation[
                "final_credit_score"
            ]

            risk_tier = evaluation[
                "risk_tier"
            ]

            # ------------------------------------------------
            # Product matching
            # ------------------------------------------------

            recommendation = recommend_products(
                score,
                products
            )

            eligible = recommendation[
                "eligible_products"
            ]

            next_product = recommendation[
                "next_product"
            ]

            highest = recommendation[
                "highest_eligible_product"
            ]

            # ------------------------------------------------
            # Product IDs
            # ------------------------------------------------

            eligible_ids = [

                item["product_id"]

                for item in eligible
            ]

            eligible_names = [

                item["product_name"]

                for item in eligible
            ]

            # ------------------------------------------------
            # Create CSV row
            # ------------------------------------------------

            row = {

                "user_id":
                    user.get("user_id"),

                "applicant_id":
                    user.get("applicant_id"),

                "final_credit_score":
                    score,

                "risk_tier":
                    risk_tier,

                "eligible_product_count":
                    len(eligible),

                "eligible_product_ids":
                    "|".join(
                        eligible_ids
                    ),

                "eligible_products":
                    "|".join(
                        eligible_names
                    ),

                "highest_eligible_product_id":
                    (
                        highest["product_id"]
                        if highest
                        else ""
                    ),

                "highest_eligible_product":
                    (
                        highest["product_name"]
                        if highest
                        else ""
                    ),

                "next_product_id":
                    (
                        next_product["product_id"]
                        if next_product
                        else ""
                    ),

                "next_product":
                    (
                        next_product["product_name"]
                        if next_product
                        else ""
                    ),

                "points_needed_for_next_product":
                    (
                        next_product["points_needed"]
                        if next_product
                        else 0
                    )
            }

            rows.append(row)

            successful += 1

        except Exception as error:

            failed += 1

            print(
                f"ERROR: "
                f"{user.get('user_id')} → "
                f"{error}"
            )

    # ========================================================
    # WRITE CSV
    # ========================================================

    fieldnames = [

        "user_id",
        "applicant_id",

        "final_credit_score",
        "risk_tier",

        "eligible_product_count",

        "eligible_product_ids",
        "eligible_products",

        "highest_eligible_product_id",
        "highest_eligible_product",

        "next_product_id",
        "next_product",

        "points_needed_for_next_product"
    ]

    with open(
        OUTPUT_PATH,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()

        writer.writerows(rows)

    # ========================================================
    # SUMMARY
    # ========================================================

    print("\n" + "=" * 65)
    print("PRODUCT RECOMMENDATION ENGINE COMPLETE")
    print("=" * 65)

    print(
        f"Total users:       {len(users)}"
    )

    print(
        f"Successfully done: {successful}"
    )

    print(
        f"Failed:            {failed}"
    )

    print(
        f"Output rows:       {len(rows)}"
    )

    print(
        f"Output:            {OUTPUT_PATH}"
    )

    print("=" * 65)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    generate_product_recommendations()