from typing import NamedTuple

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app import models
from core import security
from core.database import get_db

bearer = HTTPBearer(auto_error=False)


class Principal(NamedTuple):
    role: str  # "user" | "lender"
    subject: str  # user_id, or str(lender_id)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status.HTTP_401_UNAUTHORIZED, detail, headers={"WWW-Authenticate": "Bearer"}
    )


def current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> Principal:
    if credentials is None:
        raise _unauthorized("authentication required")
    payload = security.decode_token(credentials.credentials)
    if payload is None:
        raise _unauthorized("invalid or expired token")
    return Principal(payload["role"], payload["sub"])


def existing_user(
    user_id: str,
    principal: Principal = Depends(current_principal),
    db: Session = Depends(get_db),
) -> models.User:
    # Ownership is checked before existence so ids cannot be probed for.
    if principal != Principal("user", user_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "not allowed to access this user")
    user = db.get(models.User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user not found")
    return user


def existing_lender(
    lender_id: int,
    principal: Principal = Depends(current_principal),
    db: Session = Depends(get_db),
) -> models.Lender:
    if principal != Principal("lender", str(lender_id)):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "not allowed to access this lender")
    lender = db.get(models.Lender, lender_id)
    if lender is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "lender not found")
    return lender
