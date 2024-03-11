from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app import oauth2, utils
from app.utils import check_deleted, check_existence

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):

    existing_user = (
        db.query(models.User).filter(models.User.email == user.email).first()
    )
    check_existence(
        existing_user,
        custom_message=f"User with {user.email} already exists",
        expect_existence=True,
        custom_status_code=status.HTTP_409_CONFLICT,
    )

    # hash password using bcrypt
    hashed_password = utils.hash(user.password)
    user.password = hashed_password

    new_user = models.User(**user.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.get("/", response_model=schemas.UserOut)
def get_user(
    db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)
):

    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    check_existence(user, custom_message=f"User with id: {id} does not exist")
    check_deleted(user)

    return user
