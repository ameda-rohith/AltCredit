"""
Product Recommendation Engine

Uses the REAL users from:
    machine_learning/data/processed/merged_data.json

Uses products from:
    machine_learning/data/processed/product_catalog.json

Uses scoring logic from:
    machine_learning/engines/rule_engine.py

Output:
    machine_learning/data/processed/product_recommendations.csv

One row = one user.
"""

from typing import Dict, Any, List
from pathlib import Path
import json
import csv

from rule_engine import calculate_score


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "merged_data.json"
)

PRODUCT_PATH = (
    BASE_DIR
    / "data"
    / "processed"
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

def load_users(
    path: Path = DATA_PATH
) -> List[Dict[str, Any]]:

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as file:

        users = json.load(file)

    if not isinstance(users, list):

        raise ValueError(
            "merged_data.json must contain "
            "a list of users."
        )

    return users


# ============================================================
# LOAD PRODUCT CATALOG
# ============================================================

def load_product_catalog(
    path: Path = PRODUCT_PATH
) -> List[Dict[str, Any]]:

    with open(
        path,
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
        "a list or a 'products' field."
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

    value = (

        product.get("min_score")

        or product.get("minimum_score")

        or 0
    )

    return float(value)


# ============================================================
# RECOMMEND PRODUCTS FOR ONE USER
# ============================================================

def recommend_products(
    score: float,
    products: List[Dict[str, Any]]
) -> Dict[str, Any]:

    eligible = []
    unavailable = []

    for product in products:

        minimum_score = get_min_score(
            product
        )

        product_id = get_product_id(
            product
        )

        product_name = get_product_name(
            product
        )

        # ----------------------------------------------------
        # User is eligible
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
                    )
            })

        # ----------------------------------------------------
        # User is not eligible
        # ----------------------------------------------------

        else:

            unavailable.append({

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
                    )
            })

    # --------------------------------------------------------
    # Highest eligible product first
    # --------------------------------------------------------

    eligible.sort(

        key=lambda x:
            x["minimum_score"],

        reverse=True
    )

    # --------------------------------------------------------
    # Closest unavailable product first
    # --------------------------------------------------------

    unavailable.sort(

        key=lambda x:
            x["minimum_score"]
    )

    # --------------------------------------------------------
    # Highest product currently available
    # --------------------------------------------------------

    highest_eligible = (

        eligible[0]

        if eligible

        else None
    )

    # --------------------------------------------------------
    # Product requiring the fewest additional points
    # --------------------------------------------------------

    next_product = (

        unavailable[0]

        if unavailable

        else None
    )

    return {

        "current_score":
            score,

        "eligible_products":
            eligible,

        "ineligible_products":
            unavailable,

        "highest_eligible_product":
            highest_eligible,

        "next_product":
            next_product
    }


# ============================================================
# PROCESS ALL REAL USERS
# ============================================================

def generate_product_recommendations():

    # --------------------------------------------------------
    # Load data
    # --------------------------------------------------------

    users = load_users()

    products = load_product_catalog()

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
            # Calculate actual score
            # ------------------------------------------------

            score_result = calculate_score(
                user
            )

            score = score_result[
                "raw_score"
            ]

            # ------------------------------------------------
            # Product recommendation
            # ------------------------------------------------

            recommendation = recommend_products(
                score,
                products
            )

            eligible = recommendation[
                "eligible_products"
            ]

            highest = recommendation[
                "highest_eligible_product"
            ]

            next_product = recommendation[
                "next_product"
            ]

            # ------------------------------------------------
            # Convert product lists to CSV strings
            # ------------------------------------------------

            eligible_ids = [

                product["product_id"]

                for product in eligible
            ]

            eligible_names = [

                product["product_name"]

                for product in eligible
            ]

            # ------------------------------------------------
            # Create CSV row
            # ------------------------------------------------

            row = {

                "user_id":
                    user.get("user_id"),

                "applicant_id":
                    user.get("applicant_id"),

                "raw_score":
                    score,

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

        "raw_score",

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

    print("\n" + "=" * 60)
    print("PRODUCT RECOMMENDATION GENERATION COMPLETE")
    print("=" * 60)

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

    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    generate_product_recommendations()