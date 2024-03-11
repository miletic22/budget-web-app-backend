from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.utils import (
    check_deleted,
    check_existence,
    get_budget_query_by_id,
    reactivate_soft_deleted_budget,
)

from .. import models, oauth2, schemas
from ..database import get_db

router = APIRouter(prefix="/budgets", tags=["Budgets"])


# for easier testing purposes
@router.get("/all", response_model=List[schemas.BudgetOut])
def get_all_budgets(
    db: Session = Depends(get_db),
):
    # Filter budgets no matter if they were soft-deleted
    budgets = db.query(models.Budget).all()
    return budgets


@router.get("/", response_model=schemas.BudgetOut)
def get_budget(
    db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)
):
    # Retrieve the budget for the current user
    budget = (
        db.query(models.Budget).filter(models.Budget.user_id == current_user.id).first()
    )

    check_existence(budget, "Budget not set")
    check_deleted(budget)

    return budget


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.BudgetOut)
def create_budget(
    budget: schemas.BudgetCreate,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    # Check if a budget already exists for the user
    existing_budget = (
        db.query(models.Budget)
        .filter(
            models.Budget.user_id == current_user.id,
            models.Budget.deleted_at.is_(None),  # Exclude soft-deleted budgets
        )
        .first()
    )

    check_existence(
        existing_budget,
        custom_message=f"User with id: {current_user.id} already has a budget",
        expect_existence=True,
    )

    # # Check if the user exists
    # Not needed due to authentication
    # user = db.query(models.User).filter(models.User.id == budget.user_id).first()
    # if not user:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail=f"User with id: {budget.user_id} does not exist",
    #     )

    # Try to reactivate a soft-deleted budget
    soft_deleted_budget = reactivate_soft_deleted_budget(
        db, current_user.id, budget.model_dump()
    )
    if soft_deleted_budget:
        return soft_deleted_budget

    if budget.amount < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Budget amount cannot be negative",
        )
    # Create a new budget if all checks pass
    new_budget_data = {**budget.model_dump(), "user_id": current_user.id}
    new_budget = models.Budget(**new_budget_data)
    db.add(new_budget)
    db.commit()
    db.refresh(new_budget)

    return new_budget


@router.put("/", response_model=schemas.BudgetOut)
def update_budget(
    budget: schemas.BudgetUpdate,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    # Check if budget exists
    budget_query = db.query(models.Budget).filter(
        models.Budget.user_id == current_user.id
    )

    check_existence(budget_query.first(), custom_message="Budget not set")
    existing_budget = budget_query.first()

    check_deleted(existing_budget)

    if budget.amount < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Budget amount cannot be negative",
        )
    existing_budget.updated_at = func.now()
    budget_query.update(budget.model_dump(), synchronize_session=False)

    db.commit()

    return existing_budget


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    # Check if budget exists
    budget_query = get_budget_query_by_id(db, current_user.id)
    existing_budget = budget_query.first()

    check_existence(existing_budget, f"Budget for user {current_user.id} not found")

    # Check if budget has already been deleted
    check_deleted(existing_budget)

    # Soft delete the budget
    existing_budget.deleted_at = func.now()
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
