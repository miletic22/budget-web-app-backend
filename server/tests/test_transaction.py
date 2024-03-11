import random
from datetime import datetime

import pytest
from fastapi import status
from sqlalchemy import func
from sqlalchemy.orm.session import Session

from app import models, schemas
from app.models import Category
from tests.test_budget import test_budget
from tests.test_category import test_categories


@pytest.fixture()
def test_transactions(session: Session, test_user, test_budget, test_categories):
    new_transaction1 = models.Transaction(
        amount=100, note="note 1", category_id=test_categories[0].id
    )
    new_transaction2 = models.Transaction(
        amount=200, note="note 2", category_id=test_categories[1].id
    )

    session.add_all([new_transaction1, new_transaction2])
    session.commit()
    return [new_transaction1, new_transaction2]


@pytest.fixture()
def test_deleted_at_transaction(test_user, session, test_budget, test_categories):
    deleted_transaction = models.Transaction(
        amount=100,
        note="note 1",
        category_id=test_categories[0].id,
        deleted_at=func.now(),
    )

    session.add(deleted_transaction)
    session.commit()
    return deleted_transaction


# test get_transactions


def test_unauthorized_get_transactions(client):
    response = client.get("/transaction/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_transactions_success(authorized_client, test_transactions):
    response = authorized_client.get("/transaction/")
    transactions = [
        schemas.TransactionOut(**transaction) for transaction in response.json()
    ]

    assert len(transactions) == len(test_transactions)
    for transaction, expected_transaction in zip(transactions, test_transactions):
        assert transaction.amount == expected_transaction.amount
        assert transaction.note == expected_transaction.note
        assert transaction.id == expected_transaction.id
        assert transaction.created_at == expected_transaction.created_at
        assert transaction.updated_at == expected_transaction.updated_at
        assert transaction.deleted_at == expected_transaction.deleted_at
        assert transaction.category_id == expected_transaction.category_id

    assert response.status_code == status.HTTP_200_OK


def test_no_transactions_get_transactions(authorized_client):
    response = authorized_client.get("/transaction/")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_no_categories_get_transactions(
    authorized_client, session, test_categories, test_transactions  # noqa: F811,
):
    # the transaction would be connected to test_categories[0]
    test_categories[0].deleted_at = func.now()

    # Save the changes to the database
    session.commit()
    session.refresh(
        test_categories[0]
    )  # Refresh the specific category object, not the entire list
    session.close()

    response = authorized_client.get("/transaction/")

    # User can still access their pre-existing transactions
    assert response.status_code == status.HTTP_200_OK


# test get_specific_transaction


def test_get_specific_transaction_success(authorized_client, test_transactions):
    response = authorized_client.get("/transaction/")
    transactions = [
        schemas.TransactionOut(**transaction) for transaction in response.json()
    ]

    assert len(transactions) == len(test_transactions)
    for transaction, expected_transaction in zip(transactions, test_transactions):
        assert transaction.note == expected_transaction.note
        assert transaction.amount == expected_transaction.amount
        assert transaction.id == expected_transaction.id
        assert transaction.created_at == expected_transaction.created_at
        assert transaction.updated_at == expected_transaction.updated_at
        assert transaction.deleted_at == expected_transaction.deleted_at
        assert transaction.category_id == expected_transaction.category_id


# def test_nonexistant_transaction_get_specific_transaction(authorized_client):
#     nonexistant_transaction_id = random.randint(1000, 100000)
#     update_url = f"/transaction/{nonexistant_transaction_id}"

#     response = authorized_client.get(update_url)

#     assert response.status_code == status.HTTP_404_NOT_FOUND


def test_deleted_transaction_get_specific_transaction(
    authorized_client, test_transactions, session
):
    # testing 1 transaction
    test_transactions[0].deleted_at = func.now()
    transaction_id = test_transactions[0].id

    # Save the changes to the database
    session.commit()
    session.refresh(
        test_transactions[0]
    )  # Refresh the specific category object, not the entire list
    session.close()
    update_url = f"/transaction/{transaction_id}"
    response = authorized_client.get(update_url)

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_unauthorized_get_specific_transaction(client, test_transactions):
    transaction_id = test_transactions[0].id
    update_url = f"/transaction/{transaction_id}"

    response = client.get(update_url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_invalid_transaction_id_format(authorized_client):
    invalid_transaction_id = "abc"
    update_url = f"/transaction/{invalid_transaction_id}"

    response = authorized_client.get(update_url)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# test create_category


def test_create_transaction_success(authorized_client, test_budget, test_categories):
    data = {"amount": 500, "note": "cccc", "category_id": test_categories[0].id}
    response = authorized_client.post("/transaction/", json=data)
    assert response.status_code == status.HTTP_201_CREATED
    created_transaction = response.json()

    assert created_transaction["amount"] == data["amount"]
    assert created_transaction["note"] == data["note"]
    assert created_transaction["category_id"] == data["category_id"]


def test_unauthorized_create_transaction(client, test_categories):  # noqa: F811
    data = {"amount": 500, "note": "cccc", "category_id": test_categories[0].id}
    response = client.post("/transaction/", json=data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_no_category_create_transaction(authorized_client):
    data = {"amount": 500, "note": "cccc", "category_id": 9999}
    response = authorized_client.post("/transaction/", json=data)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_deleted_category_create_transactiont(
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


def test_invalid_data_create_transaction(authorized_client):
    data = {"name": "aaa"}
    response = authorized_client.post("/transaction/", json=data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_negative_amount_create_transaction(authorized_client, test_categories):
    data = {"amount": -100, "note": "cccc", "category_id": test_categories[0].id}
    response = authorized_client.post("/transaction/", json=data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# update_transaction testing


def test_update_category_success(authorized_client, test_transactions, session):
    # Testing on 1 category
    transaction_to_update = test_transactions[0]

    data = {"amount": 532235, "note": "A new iPad for 'studying'"}

    update_url = f"/transaction/{transaction_to_update.id}"

    response = authorized_client.put(update_url, json=data)
    updated_transaction = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert updated_transaction["note"] == data["note"]
    assert updated_transaction["amount"] == data["amount"]
    assert updated_transaction["category_id"] == transaction_to_update.id


def test_unauthorized_update_transaction(client, test_transactions):
    update_url = f"/transaction/{test_transactions[0].id}"
    response = client.put(update_url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_deleted_category(authorized_client, test_deleted_at_transaction):

    data = {"amount": 100, "note": "test"}
    update_url = f"/transaction/{test_deleted_at_transaction.id}"

    assert test_deleted_at_transaction.deleted_at is not None

    response = authorized_client.put(update_url, json=data)

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_nonexistant_transaction_update_transaction(authorized_client):
    data = {"amount": 100, "note": "test"}
    nonexistant_transaction_id = random.randint(1000, 100000)
    update_url = f"/transaction/{nonexistant_transaction_id}"

    response = authorized_client.put(update_url, json=data)

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_negative_amount_update_transaction(authorized_client, test_transactions):
    data = {"amount": -100, "note": "test"}

    update_url = f"/transaction/{test_transactions[0].id}"

    response = authorized_client.put(update_url, json=data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# testing delete_transaction


def test_delete_transaction_success(authorized_client, test_transactions):
    # Testing on 1 category
    transaction_to_delete = test_transactions[0]
    delete_url = f"/transaction/{transaction_to_delete.id}"

    response = authorized_client.delete(delete_url)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_deleted_delete_transaction(authorized_client, test_deleted_at_transaction):
    delete_url = f"/transaction/{test_deleted_at_transaction.id}"

    response = authorized_client.delete(delete_url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_nonexistant_transaction_delete_transaction(authorized_client):
    nonexistant_transaction_id = random.randint(1000, 100000)
    delete_url = f"/transaction/{nonexistant_transaction_id}"
    response = authorized_client.delete(delete_url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_unauthorized_delete_transaction(client, test_transactions):
    delete_url = f"/transaction/{test_transactions[0].id}"
    response = client.delete(delete_url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED