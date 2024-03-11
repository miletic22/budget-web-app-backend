from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.utils import (
    check_deleted,
    check_existence,
    check_ownership,
    get_category_by_id,
    get_user_budget,
    get_user_category,
)

from .. import models, oauth2, schemas
from ..database import get_db

router = APIRouter(prefix="/category", tags=["Categories"])


# testing purposes
@router.get("/all", response_model=List[schemas.CategoryOut])
def get_all_categories(db: Session = Depends(get_db)):

    categories = db.query(models.Category).all()
    return categories


@router.get("/", response_model=List[schemas.CategoryOut])
def get_categories(
    db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)
):
    existing_budget = get_user_budget(db, current_user.id)

    check_existence(
        existing_budget,
        custom_message=f"User with id {current_user.id} does not have a budget",
    )

    categories = (
        db.query(models.Category)
        .filter(
            models.Category.budget_id == existing_budget.id,
            models.Category.deleted_at.is_(None),
        )
        .all()
    )

    check_existence(categories, custom_message="No set categories")

    return categories


@router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=schemas.CategoryOut
)
def create_category(
    category_create: schemas.CategoryCreate,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    existing_budget = get_user_budget(db, current_user.id)

    check_existence(existing_budget, "Budget not found")
    check_deleted(existing_budget)

    if category_create.amount < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Category amount cannot be negative",
        )

    category_data = {
        **category_create.model_dump(),
        "budget_id": existing_budget.id,
    }

    new_category = models.Category(**category_data)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)

    return new_category


@router.put("/{id}", response_model=schemas.CategoryOut)
def update_category(
    id: int,
    category: schemas.CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    existing_category = get_user_category(db, current_user.id, id)

    check_ownership(existing_category, current_user.id)
    check_existence(existing_category, f"Category id {id} not found")
    check_deleted(existing_category)

    if category.amount < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Category amount cannot be negative",
        )

    existing_category.updated_at = func.now()
    existing_category.user_id = current_user.id
    existing_category.owner = current_user.budget.owner

    db.query(models.Category).filter(models.Category.id == id).update(
        category.model_dump(), synchronize_session=False
    )
    db.commit()

    return existing_category


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    existing_category = get_category_by_id(db, id)
    check_ownership(existing_category, current_user.id)
    check_deleted(existing_category)
    check_existence(existing_category, f"Category id {id} not found")

    existing_category.deleted_at = func.now()
    db.commit()
