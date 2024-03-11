from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.utils import (
    check_deleted,
    check_existence,
    check_ownership,
    get_transaction_by_id,
    get_user_budget,
)

from .. import models, oauth2, schemas
from ..database import get_db

router = APIRouter(prefix="/transaction", tags=["Transactions"])


# testing purp  oses
@router.get("/all", response_model=List[schemas.TransactionOut])
def get_all_transactions(db: Session = Depends(get_db)):

    transactions = db.query(models.Transaction).all()
    return transactions


@router.get("/", response_model=List[schemas.TransactionOut])
def get_transactions(
    db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)
):
    transactions = (
        db.query(models.Transaction)
        .join(models.Category, models.Transaction.category_id == models.Category.id)
        .join(models.Budget, models.Category.budget_id == models.Budget.id)
        .join(models.User, models.Budget.user_id == models.User.id)
        .filter(
            models.User.id == current_user.id,
            models.Transaction.deleted_at.is_(None),
        )
        .all()
    )

    check_existence(transactions, "No set transactions")

    return transactions


@router.get("/{id}", response_model=schemas.TransactionOut)
def get_specific_transaction(
    id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    existing_transaction = get_transaction_by_id(db, id)

    check_existence(existing_transaction, f"Transaction id {id} not found")
    check_deleted(existing_transaction)
    check_ownership(existing_transaction, current_user.id)

    return existing_transaction


@router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=schemas.TransactionOut
)
def create_transaction(
    transaction_create: schemas.TransactionCreate,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    existing_budget = get_user_budget(db, current_user.id)
    existing_category = (
        db.query(models.Category)
        .filter(models.Category.id == transaction_create.category_id)
        .first()
    )

    check_existence(existing_category, "Category does not exist")
    check_existence(existing_budget, "Budget does not exist")
    check_deleted(existing_category)
    check_deleted(existing_budget)

    if transaction_create.amount < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Transaction amount cannot be negative",
        )

    transaction_data = {
        **transaction_create.model_dump(),
    }

    new_transaction = models.Transaction(**transaction_data)
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)

    return new_transaction


@router.put("/{id}", response_model=schemas.TransactionOut)
def update_transaction(
    id: int,
    transaction: schemas.TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    existing_transaction = get_transaction_by_id(db, id)

    check_existence(existing_transaction, f"Transaction id {id} not found")
    check_deleted(existing_transaction)
    check_ownership(existing_transaction, current_user.id)

    if transaction.amount < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Transaction amount cannot be negative",
        )

    existing_transaction.updated_at = func.now()
    existing_transaction.user_id = current_user.id

    db.query(models.Transaction).filter(models.Transaction.id == id).update(
        transaction.model_dump(), synchronize_session=False
    )
    db.commit()

    return existing_transaction


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    existing_transaction = get_transaction_by_id(db, id)

    check_existence(existing_transaction, f"Transaction id {id} not found")
    check_ownership(existing_transaction, current_user.id)
    check_deleted(existing_transaction)

    existing_transaction.deleted_at = func.now()
    db.commit()
