from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)


def generate_transparency_report(
    user_id: str,
    score_data: dict
) -> bytes:

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm
    )

    styles = getSampleStyleSheet()

    title_style = styles["Title"]
    heading_style = styles["Heading2"]
    body_style = styles["BodyText"]

    story = []

    story.append(
        Paragraph(
            "AltCredit - Transparency Report",
            title_style
        )
    )

    story.append(
        Spacer(1, 10)
    )

    story.append(
        Paragraph(
            f"User ID: {user_id}",
            body_style
        )
    )

    story.append(
        Spacer(1, 8)
    )

    final_score = score_data.get(
        "final_score",
        0
    )

    risk_category = score_data.get(
        "risk_category",
        "Unknown"
    )

    story.append(
        Paragraph(
            f"<b>Credit Score:</b> {final_score}/1000",
            body_style
        )
    )

    story.append(
        Paragraph(
            f"<b>Risk Category:</b> {risk_category}",
            body_style
        )
    )

    story.append(
        Spacer(1, 15)
    )

    story.append(
        Paragraph(
            "Score Breakdown",
            heading_style
        )
    )

    breakdown = [
        ["Component", "Points"],
        [
            "Lifestyle",
            str(
                score_data.get(
                    "lifestyle_score",
                    0
                )
            )
        ],
        [
            "Spending Behavior",
            str(
                score_data.get(
                    "spending_score",
                    0
                )
            )
        ],
        [
            "Repayment Discipline",
            str(
                score_data.get(
                    "repayment_score",
                    0
                )
            )
        ],
        [
            "Bonus",
            str(
                score_data.get(
                    "bonus_points",
                    0
                )
            )
        ],
        [
            "Penalty",
            str(
                score_data.get(
                    "penalty_points",
                    0
                )
            )
        ]
    ]

    table = Table(
        breakdown,
        colWidths=[
            100 * mm,
            40 * mm
        ]
    )

    table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                "#DDDDDD"
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                "#888888"
            ),
            (
                "ALIGN",
                (1, 0),
                (1, -1),
                "RIGHT"
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            )
        ])
    )

    story.append(table)

    story.append(
        Spacer(1, 15)
    )

    story.append(
        Paragraph(
            "Factor Analysis",
            heading_style
        )
    )

    factors = []

    for component in [
        "lifestyle_factors",
        "spending_factors",
        "repayment_factors"
    ]:

        component_factors = score_data.get(
            component,
            {}
        )

        for name, points in component_factors.items():

            impact = (
                "Positive"
                if points > 0
                else "Negative"
                if points < 0
                else "Neutral"
            )

            factors.append([
                name,
                str(points),
                impact
            ])

    factor_table_data = [
        [
            "Factor",
            "Points",
            "Impact"
        ]
    ]

    factor_table_data.extend(
        factors
    )

    if len(factor_table_data) > 1:

        factor_table = Table(
            factor_table_data,
            colWidths=[
                85 * mm,
                30 * mm,
                30 * mm
            ]
        )

        factor_table.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    "#DDDDDD"
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    "#888888"
                )
            ])
        )

        story.append(
            factor_table
        )

    story.append(
        Spacer(1, 15)
    )

    story.append(
        Paragraph(
            "Disclaimer",
            heading_style
        )
    )

    story.append(
        Paragraph(
            (
                "This report is generated by the AltCredit "
                "prototype using synthetic data. It is not "
                "a legally binding credit decision."
            ),
            body_style
        )
    )

    document.build(story)

    buffer.seek(0)

    return buffer.getvalue()