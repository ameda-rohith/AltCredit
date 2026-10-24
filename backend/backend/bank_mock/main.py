import hmac
import uuid
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from core.config import settings

app = FastAPI(title="Partner Bank API (mock)", version="1.0")


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    if not x_api_key or not hmac.compare_digest(x_api_key, settings.bank_api_key):
        raise HTTPException(status_code=401, detail="invalid or missing API key")


class PreapprovalRequest(BaseModel):
    applicant_id: str  # synthetic id only - no names, no account numbers
    product_id: str
    product_type: Literal["Credit Card", "Loan"]
    credit_score: int = Field(ge=0, le=1000)
    min_score_required: int = Field(ge=0, le=1000)
    monthly_income: float = Field(ge=0)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/v1/preapproved-offers", dependencies=[Depends(require_api_key)])
def preapprove(req: PreapprovalRequest):
    # Mock limitation: the threshold comes from the caller. A real bank would apply its own
    # product rules and verify the score with ALTcredit instead of trusting these two fields.
    if req.credit_score < req.min_score_required:
        return {
            "status": "DECLINED",
            "reason": "score below product requirement",
            "reference": None,
        }
    multiple = 1 + (req.credit_score - req.min_score_required) / 250
    if req.product_type == "Credit Card":
        limit = round(req.monthly_income * 2 * multiple, -2)
        details = {"credit_limit": limit}
    else:
        limit = round(req.monthly_income * 6 * multiple, -2)
        details = {"approved_amount": limit, "tenure_months": 24}
    reference = f"BANK-{uuid.uuid4().hex[:10].upper()}"
    return {"status": "APPROVED", "reference": reference, "details": details}
