import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models, schemas
from core import security
from core.config import settings
from core.database import get_db
from services import user_service
from services.rate_limit import SlidingWindowLimiter

router = APIRouter(prefix="/auth", tags=["auth"])

# Failed attempts per (role, username, client ip); a success clears the counter.
login_failures = SlidingWindowLimiter(settings.login_max_failures, settings.login_window_seconds)


def _session(role: str, subject: str) -> dict:
    """What every successful auth call returns: who you are plus the bearer token to prove it."""
    return {
        "role": role,
        "subject": subject,
        "token": security.create_token(subject, role),
        "token_type": "bearer",
        "expires_in": settings.token_ttl_minutes * 60,
    }


@router.post("/login")
def login(body: schemas.LoginIn, request: Request, db: Session = Depends(get_db)):
    """Check the credentials and return a signed bearer token for the account."""
    client_ip = request.client.host if request.client else "-"
    key = f"{body.role}:{body.username.lower()}:{client_ip}"
    if login_failures.blocked(key):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "too many failed attempts, try again later",
            headers={"Retry-After": str(login_failures.retry_after(key))},
        )
    if body.role == "lender":
        account = db.scalar(select(models.Lender).where(models.Lender.username == body.username))
        subject = str(account.lender_id) if account else ""
    else:
        account = db.scalar(
            select(models.User).where(
                or_(
                    models.User.user_id == body.username,
                    models.User.email == body.username.lower(),
                )
            )
        )
        subject = account.user_id if account else ""
    # Unknown accounts are verified against a dummy hash so they take as long as a wrong
    # password does: the response gives no way to tell the two apart.
    stored = account.password_hash if account else security.dummy_hash()
    if not security.verify_password(body.password, stored) or account is None:
        login_failures.record(key)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid credentials")
    login_failures.reset(key)
    if security.needs_rehash(account.password_hash):  # transparently upgrade old hashes
        account.password_hash = security.hash_password(body.password)
        db.commit()
    return _session(body.role, subject)


def _next_user_id(db: Session) -> str:
    count = db.scalar(select(func.count()).select_from(models.User)) or 0
    user_id = f"USR_{count + 1:03d}"
    while db.get(models.User, user_id):
        count += 1
        user_id = f"USR_{count + 1:03d}"
    return user_id


def _create_user(db: Session, body: schemas.RegisterIn, email: str) -> models.User:
    """Insert the user, tolerating a concurrent signup taking the same id or email."""
    password_hash = security.hash_password(body.password)
    for _ in range(5):
        user = models.User(
            user_id=_next_user_id(db),
            applicant_id=str(uuid.uuid4()),
            full_name=body.full_name,
            email=email,
            password_hash=password_hash,
            age=body.age,
            city_tier=body.city_tier,
            employment_status=body.employment_status,
            education_level=body.education_level,
            share_with_lenders=body.share_with_lenders,
        )
        db.add(user)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            if db.scalar(select(models.User.user_id).where(models.User.email == email)):
                raise HTTPException(status.HTTP_409_CONFLICT, "email already registered") from None
            continue  # lost the race for the id: take the next one
        return user
    raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "could not create account, retry")


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: schemas.RegisterIn, db: Session = Depends(get_db)):
    """New-user portal: create a profile, then score the (thin) initial file."""
    email = body.email.lower()
    if db.scalar(select(models.User).where(models.User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "email already registered")
    user = _create_user(db, body, email)
    demographics = body.model_dump(
        exclude={"full_name", "email", "password", "share_with_lenders"}, exclude_none=True
    )
    result = user_service.record_scoring(db, user, demographics)
    return {
        **_session("user", user.user_id),
        "user_id": user.user_id,
        "credit_score": result["credit_score"],
        "risk_tier": result["risk_tier"],
        "missing_fields": result["missing_fields"],
    }


@router.post("/register-lender", status_code=status.HTTP_201_CREATED)
def register_lender(body: schemas.LenderRegisterIn, db: Session = Depends(get_db)):
    """Lender portal signup: create the institution with its lending policy."""
    if db.scalar(select(models.Lender).where(models.Lender.username == body.username)):
        raise HTTPException(status.HTTP_409_CONFLICT, "username already taken")
    if db.scalar(
        select(models.Lender).where(
            func.lower(models.Lender.company_name) == body.company_name.lower()
        )
    ):
        raise HTTPException(status.HTTP_409_CONFLICT, "company already registered")
    lender = models.Lender(
        company_name=body.company_name,
        username=body.username,
        password_hash=security.hash_password(body.password),
        min_credit_score_requirement=body.min_credit_score_requirement,
        max_pd_threshold=body.max_pd_threshold,
    )
    db.add(lender)
    try:
        db.commit()
    except IntegrityError:  # concurrent signup with the same username / company
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, "username or company already registered"
        ) from None
    return _session("lender", str(lender.lender_id))
