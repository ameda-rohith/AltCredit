from datetime import date

from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):

    transaction_id: str = Field(
        min_length=1,
        max_length=100
    )

    user_id: str = Field(
        min_length=1,
        max_length=50
    )

    date: date

    amount: float

    category: str = Field(
        min_length=1,
        max_length=100
    )

    type: str = Field(
        min_length=1,
        max_length=20
    )

    payment_status: str | None = None