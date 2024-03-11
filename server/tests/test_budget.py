import pytest
from fastapi import status
from sqlalchemy import func

from app import models, schemas


@pytest.fixture()
def test_budget(session, test_user):
    new_budget = models.Budget(amount=100, user_id=test_user["id"])
    session.add(new_budget)
    session.commit()
    return new_budget


@pytest.fixture()
def test_deleted_at_budget(session, test_user):
    new_budget = models.Budget(
        amount=100,
        user_id=test_user["id"],
        deleted_at=func.now(),
        updated_at=func.now(),
    )
    session.add(new_budget)
    session.commit()
    return new_budget


# get_budget testing


def test_unauthorized_get_budget(client):
    response = client.get("/budgets/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_budget_success(authorized_client, test_budget):
    response = authorized_client.get("/budgets/")
    budget = schemas.BudgetOut(**response.json())
    assert budget.id == test_budget.id
    assert budget.user_id == test_budget.user_id
    assert budget.amount == test_budget.amount
    assert budget.created_at == test_budget.created_at


def test_no_budget(authorized_client):
    response = authorized_client.get("/budgets/")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json().get("detail") == "Budget not set"


def test_authorized_client(): ...


# create_budget testing
@pytest.mark.parametrize(
    "amount, status_code",
    [
        (100, status.HTTP_201_CREATED),
        ("100", status.HTTP_201_CREATED),
        (0, status.HTTP_201_CREATED),
    ],
)
def test_create_budget_success(authorized_client, amount, status_code):
    response = authorized_client.post("/budgets/", json={"amount": amount})
    created_budget = schemas.BudgetCreate(**response.json())
    assert created_budget.amount == int(amount)
    assert response.status_code == status_code


def test_unauthorized_create_budget(client):
    response = client.post("/budgets/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_budget_with_deleted_budget(
    authorized_client, test_deleted_at_budget, session
):

    # Ensure that there is an existing budget with deleted_at set
    assert test_deleted_at_budget.deleted_at is not None

    response = authorized_client.post("/budgets/", json={"amount": 100})
    updated_budget = (
        session.query(models.Budget).filter_by(id=test_deleted_at_budget.id).first()
    )

    assert updated_budget.deleted_at is None
    assert updated_budget.updated_at >= test_deleted_at_budget.updated_at
    assert updated_budget.amount == 100
    assert (
        updated_budget.user_id == test_deleted_at_budget.user_id
    )  # Ensure the same user
    assert response.status_code == status.HTTP_201_CREATED


def test_create_negative_budget(authorized_client):
    response = authorized_client.post("/budgets/", json={"amount": -100})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_existing_budget(authorized_client, test_budget):
    budget_data = {"amount": test_budget.amount, "user_id": test_budget.user_id}
    response = authorized_client.post("/budgets/", json=budget_data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST


# update_budget testing


def test_update_budget_success(authorized_client, test_budget):
    data = {
        "amount": 9999,
    }
    response = authorized_client.put("/budgets/", json=data)

    updated_budget = schemas.BudgetUpdate(**response.json())

    assert updated_budget.amount == data["amount"]
    assert response.status_code == status.HTTP_200_OK


def test_unauthorized_update_budget(client):
    response = client.put("/budgets/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_deleted_budget(authorized_client, test_deleted_at_budget):

    data = {
        "amount": 9999,
    }

    assert test_deleted_at_budget.deleted_at is not None
    response = authorized_client.put("/budgets/", json=data)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json().get("detail") == "Budget is deleted"


def test_update_nonexistant_budget(authorized_client):
    data = {
        "amount": 9999,
    }
    response = authorized_client.put("/budgets/", json=data)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json().get("detail") == "Budget not set"


def test_update_negative_budget(authorized_client, test_budget):
    response = authorized_client.put("/budgets/", json={"amount": -100})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# delete_budget testing


def test_delete_budget_success(authorized_client, test_budget):
    response = authorized_client.delete("/budgets/")
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_delete_deleted_budget(authorized_client, test_deleted_at_budget):
    response = authorized_client.delete("/budgets/")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_nonexistant_budget(authorized_client):
    response = authorized_client.delete("/budgets/")
    assert response.status_code == status.HTTP_404_NOT_FOUND
