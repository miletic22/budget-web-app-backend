import random
from datetime import datetime

import pytest
from fastapi import status
from sqlalchemy import func
from sqlalchemy.orm.session import Session

from app import models, schemas
from app.models import Category
from tests.test_budget import test_budget


@pytest.fixture()
def test_categories(session: Session, test_user, test_budget):
    new_category1 = models.Category(
        name="Category 1", amount=100, budget_id=test_user["id"]
    )
    new_category2 = models.Category(
        name="Category 2", amount=200, budget_id=test_user["id"]
    )

    session.add_all([new_category1, new_category2])
    session.commit()
    return [new_category1, new_category2]


@pytest.fixture()
def test_deleted_at_category(test_user, session, test_budget):
    deleted_category = models.Category(
        name="Category 1", amount=100, budget_id=test_user["id"], deleted_at=func.now()
    )

    session.add(deleted_category)
    session.commit()
    return deleted_category


# test get_categories


def test_unauthorized_get_categories(client):
    response = client.get("/category/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_categories_success(authorized_client, test_categories):
    response = authorized_client.get("/category/")
    categories = [schemas.CategoryOut(**category) for category in response.json()]

    assert len(categories) == len(test_categories)
    for category, expected_category in zip(categories, test_categories):
        assert category.name == expected_category.name
        assert category.amount == expected_category.amount
        assert category.id == expected_category.id
        assert category.created_at == expected_category.created_at
        assert category.updated_at == expected_category.updated_at
        assert category.deleted_at == expected_category.deleted_at
        assert category.budget_id == expected_category.budget_id


def test_no_categories_get_categories(authorized_client):
    response = authorized_client.get("/category/")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_no_budget_get_categories(
    authorized_client,
    test_budget,
    session,
    test_categories,  # noqa: F811
):
    test_budget.deleted_at = func.now()

    # Save the changes to the database
    session.add(test_budget)
    session.commit()
    session.refresh(test_budget)
    session.close()

    response = authorized_client.get("/category/")

    # User can still access their pre-existing categories
    assert response.status_code == status.HTTP_200_OK


# test create_category


def test_create_category_success(authorized_client, test_budget):  # noqa: F811
    data = {"name": "aaa", "amount": 100}
    response = authorized_client.post("/category/", json=data)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["name"] == data["name"]
    assert response.json()["amount"] == data["amount"]


def test_unauthorized_create_category(client, test_budget):  # noqa: F811
    data = {"name": "aaa", "amount": 100}
    response = client.post("/category/", json=data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_category_no_budget(authorized_client):
    data = {"name": "aaa", "amount": 100}
    response = authorized_client.post("/category/", json=data)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_create_category_deleted_budget(
    authorized_client, test_budget, session
):  # noqa: F811
    test_budget.deleted_at = func.now()

    # Save the changes to the database
    session.add(test_budget)
    session.commit()
    session.refresh(test_budget)
    session.close()

    data = {"name": "aaa", "amount": 100}
    response = authorized_client.post("/category/", json=data)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_invalid_data_create_category(authorized_client):
    data = {"name": "aaa"}
    response = authorized_client.post("/category/", json=data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_negative_amount_create_category(authorized_client):
    data = {"name": "aaa", "amount": -100}
    response = authorized_client.post("/budgets/", json=data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# update_category testing


def test_update_category_success(authorized_client, test_categories, session):
    # Testing on 1 category
    category_to_update = test_categories[0]

    updated_data = {"name": "category", "amount": 50}

    update_url = f"/category/{category_to_update.id}"

    response = authorized_client.put(update_url, json=updated_data)
    updated_category = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert updated_category["name"] == updated_data["name"]
    assert updated_category["amount"] == updated_data["amount"]
    assert updated_category["id"] == category_to_update.id


def test_unauthorized_update_category(client, test_categories):
    update_url = f"/category/{test_categories[0].id}"
    response = client.put(update_url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_deleted_category(authorized_client, test_deleted_at_category):

    updated_data = {"name": "category", "amount": 50}
    update_url = f"/category/{test_deleted_at_category.id}"

    assert test_deleted_at_category.deleted_at is not None

    response = authorized_client.put(update_url, json=updated_data)

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_nonexistant_category(authorized_client):
    updated_data = {"name": "category", "amount": 50}
    nonexistent_category_id = random.randint(1000, 100000)
    update_url = f"/category/{nonexistent_category_id}"

    response = authorized_client.put(update_url, json=updated_data)

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_negative_amount_category(authorized_client, test_categories):
    updated_data = {"name": "category", "amount": -100}
    response = authorized_client.put("/budgets/", json=updated_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# delete_category testing


def test_delete_category_success(authorized_client, test_categories):
    # Testing on 1 category
    category_to_delete = test_categories[0]
    delete_url = f"/category/{category_to_delete.id}"

    response = authorized_client.delete(delete_url)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_deleted_category_delete_category(authorized_client, test_deleted_at_category):
    delete_url = f"/category/{test_deleted_at_category.id}"

    response = authorized_client.delete(delete_url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_nonexistant_category_delete_category(authorized_client):
    nonexistent_category_id = random.randint(1000, 100000)
    delete_url = f"/category/{nonexistent_category_id}"
    response = authorized_client.delete(delete_url)
    assert response.status_code == status.HTTP_404_NOT_FOUND
