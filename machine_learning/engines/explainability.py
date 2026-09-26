"""
Explainability Engine

Uses the real users from:
    machine_learning/data/processed/merged_data.json

Uses scoring logic from:
    machine_learning/engines/rule_engine.py

Output:
    machine_learning/data/processed/score_explanations.csv

One row = one user + one scoring factor.
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

OUTPUT_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "score_explanations.csv"
)


# ============================================================
# LOAD REAL USERS
# ============================================================

def load_users(
    data_path: Path = DATA_PATH
) -> List[Dict[str, Any]]:

    with open(
        data_path,
        "r",
        encoding="utf-8"
    ) as file:

        users = json.load(file)

    if not isinstance(users, list):
        raise ValueError(
            "merged_data.json must contain a list of users."
        )

    return users


# ============================================================
# FACTOR BREAKDOWN
# ============================================================

def get_factor_breakdown(
    score_result: Dict[str, Any]
) -> List[Dict[str, Any]]:

    breakdown = []

    for component in score_result.get(
        "components",
        []
    ):

        score = component.get(
            "score",
            0
        )

        max_score = component.get(
            "max_score",
            0
        )

        if score > 0:
            contribution = "positive"

        elif score == 0:
            contribution = "weak"

        else:
            contribution = "negative"

        breakdown.append({

            "factor":
                component.get("factor"),

            "score":
                score,

            "max_score":
                max_score,

            "contribution":
                contribution,

            "status":
                component.get("status"),

            "reason":
                component.get("reason")
        })

    return breakdown


# ============================================================
# POSITIVE FACTORS
# ============================================================

def get_positive_factors(
    score_result: Dict[str, Any]
) -> List[Dict[str, Any]]:

    return [

        {
            "factor":
                item["factor"],

            "score":
                item["score"],

            "reason":
                item["reason"]
        }

        for item in score_result.get(
            "components",
            []
        )

        if item.get(
            "score",
            0
        ) > 0
    ]


# ============================================================
# WEAK FACTORS
# ============================================================

def get_weak_factors(
    score_result: Dict[str, Any]
) -> List[Dict[str, Any]]:

    return [

        {
            "factor":
                item["factor"],

            "score":
                item["score"],

            "max_score":
                item["max_score"],

            "reason":
                item["reason"]
        }

        for item in score_result.get(
            "components",
            []
        )

        if item.get(
            "score",
            0
        ) == 0
    ]


# ============================================================
# TOP CONTRIBUTORS
# ============================================================

def get_top_factors(
    score_result: Dict[str, Any],
    limit: int = 5
) -> List[Dict[str, Any]]:

    components = [

        item

        for item in score_result.get(
            "components",
            []
        )

        if item.get(
            "score",
            0
        ) > 0
    ]

    components.sort(

        key=lambda x:
            x.get("score", 0),

        reverse=True
    )

    return components[:limit]


# ============================================================
# BUILD EXPLANATION FOR ONE USER
# ============================================================

def build_explanation(
    score_result: Dict[str, Any]
) -> Dict[str, Any]:

    breakdown = get_factor_breakdown(
        score_result
    )

    positive = get_positive_factors(
        score_result
    )

    weak = get_weak_factors(
        score_result
    )

    top_factors = get_top_factors(
        score_result
    )

    return {

        "summary": {

            "user_id":
                score_result.get(
                    "user_id"
                ),

            "raw_score":
                score_result.get(
                    "raw_score"
                ),

            "positive_factor_count":
                len(positive),

            "weak_factor_count":
                len(weak)
        },

        "breakdown":
            breakdown,

        "positive_factors":
            positive,

        "weak_factors":
            weak,

        "top_contributors": [

            {
                "factor":
                    item["factor"],

                "score":
                    item["score"],

                "reason":
                    item["reason"]
            }

            for item in top_factors
        ]
    }


# ============================================================
# GENERATE CSV FOR ALL USERS
# ============================================================

def generate_explanation_csv():

    # --------------------------------------------------------
    # Load real users
    # --------------------------------------------------------

    users = load_users()

    print(
        f"Loaded {len(users)} users."
    )

    rows = []

    successful = 0
    failed = 0

    # --------------------------------------------------------
    # Process every user
    # --------------------------------------------------------

    for user in users:

        try:

            # Run REAL rule engine
            score_result = calculate_score(
                user
            )

            # Build explanation
            explanation = build_explanation(
                score_result
            )

            # One row per factor
            for factor in explanation[
                "breakdown"
            ]:

                rows.append({

                    "user_id":
                        user.get("user_id"),

                    "applicant_id":
                        user.get("applicant_id"),

                    "raw_score":
                        score_result.get(
                            "raw_score"
                        ),

                    "factor":
                        factor["factor"],

                    "score":
                        factor["score"],

                    "max_score":
                        factor["max_score"],

                    "contribution":
                        factor["contribution"],

                    "status":
                        factor["status"],

                    "reason":
                        factor["reason"]
                })

            successful += 1

        except Exception as error:

            failed += 1

            print(
                f"ERROR: "
                f"{user.get('user_id')} → "
                f"{error}"
            )

    # --------------------------------------------------------
    # CSV columns
    # --------------------------------------------------------

    fieldnames = [

        "user_id",
        "applicant_id",
        "raw_score",

        "factor",

        "score",
        "max_score",

        "contribution",

        "status",

        "reason"
    ]

    # --------------------------------------------------------
    # Write CSV
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("EXPLAINABILITY GENERATION COMPLETE")
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
        f"Explanation rows:  {len(rows)}"
    )

    print(
        f"Output:            {OUTPUT_PATH}"
    )

    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    generate_explanation_csv()