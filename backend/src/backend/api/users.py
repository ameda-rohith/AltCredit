from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from db.database import get_db

from models.user import User

from schemas.user import UserCreate


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.post("/")
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db)
):

    existing = (
        db.query(User)
        .filter(
            User.user_id
            == payload.user_id
        )
        .first()
    )

    if existing:

        return {
            "user_id":
                existing.user_id,

            "role":
                existing.role
        }

    user = User(
        **payload.model_dump()
    )

    db.add(user)

    db.commit()

    db.refresh(user)

    return {
        "user_id":
            user.user_id,

        "role":
            user.role
    }


@router.get(
    "/{user_id}"
)
def get_user(
    user_id: str,
    db: Session = Depends(get_db)
):

    user = (
        db.query(User)
        .filter(
            User.user_id
            == user_id
        )
        .first()
    )

    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {
        "user_id":
            user.user_id,

        "role":
            user.role,

        "created_at":
            user.created_at
    }