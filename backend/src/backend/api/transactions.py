import json
import io

import pandas as pd

from fastapi import (
    APIRouter,
    HTTPException,
    UploadFile,
    File
)

from ..database.database import get_connection
from ..schemas.transaction import TransactionCreate
from ..services.data_processor import clean_transactions


router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"]
)


@router.post("/")
def create_transaction(
    transaction: TransactionCreate
):

    connection = get_connection()

    user = connection.execute(
        "SELECT user_id FROM users WHERE user_id = ?",
        (transaction.user_id,)
    ).fetchone()

    if not user:
        connection.close()

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    try:

        connection.execute("""
            INSERT INTO transactions (
                transaction_id,
                user_id,
                date,
                amount,
                category,
                type,
                payment_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            transaction.transaction_id,
            transaction.user_id,
            transaction.date,
            transaction.amount,
            transaction.category,
            transaction.type.lower(),
            transaction.payment_status
        ))

        connection.commit()

    except Exception as exc:

        connection.close()

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    connection.close()

    return {
        "message": "Transaction created",
        "transaction_id": transaction.transaction_id
    }


@router.get("/{user_id}")
def get_transactions(user_id: str):

    connection = get_connection()

    rows = connection.execute("""
        SELECT *
        FROM transactions
        WHERE user_id = ?
        ORDER BY date
    """, (user_id,)).fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


@router.post("/upload")
async def upload_transactions(
    file: UploadFile = File(...)
):

    content = await file.read()

    try:

        if file.filename.lower().endswith(".csv"):

            df = pd.read_csv(
                io.BytesIO(content)
            )

            transactions = df.to_dict(
                orient="records"
            )

        elif file.filename.lower().endswith(".json"):

            transactions = json.loads(
                content.decode("utf-8")
            )

            if isinstance(transactions, dict):
                transactions = [transactions]

        else:

            raise HTTPException(
                status_code=400,
                detail="Only CSV and JSON files are supported"
            )

        cleaned = clean_transactions(
            transactions
        )

        connection = get_connection()

        inserted = 0

        for tx in cleaned:

            try:

                connection.execute("""
                    INSERT INTO transactions (
                        transaction_id,
                        user_id,
                        date,
                        amount,
                        category,
                        type,
                        payment_status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    tx["transaction_id"],
                    tx["user_id"],
                    tx["date"],
                    tx["amount"],
                    tx["category"],
                    tx["type"],
                    tx.get("payment_status")
                ))

                inserted += 1

            except Exception:
                continue

        connection.commit()
        connection.close()

        return {
            "message": "Transactions processed",
            "inserted": inserted
        }

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )