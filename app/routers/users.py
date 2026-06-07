from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_me(
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if data.email and data.email != current_user.email:
        if db.query(User).filter(User.email == data.email, User.id != current_user.id).first():
            raise HTTPException(status_code=400, detail="Email already in use")
        current_user.email = data.email

    if data.name:
        current_user.name = data.name

    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/search", response_model=List[UserResponse])
def search_users(
    q: str = Query(..., min_length=2),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return (
        db.query(User)
        .filter(
            User.is_active == True,
            (User.name.ilike(f"%{q}%")) | (User.email.ilike(f"%{q}%")),
        )
        .limit(20)
        .all()
    )


@router.get("/", response_model=List[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return db.query(User).filter(User.is_active == True).offset(skip).limit(limit).all()


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: UUID, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
