import pytest
from fastapi import status
from jose import jwt

from app import schemas
from app.config import settings


def test_create_user_success(client):
    response = client.post(
        "/users/",
        json={"email": "correct_user@gmail.com", "password": "correct_password"},
    )

    new_user = schemas.UserOut(**response.json())
    assert new_user.email == "correct_user@gmail.com"
    assert response.status_code == 201


def test_user_login_success(test_user, client):
    response = client.post(
        "/login",
        data={"username": test_user["email"], "password": test_user["password"]},
    )
    login_res = schemas.Token(**response.json())
    payload = jwt.decode(
        login_res.access_token, settings.secret_key, algorithms=[settings.algorithm]
    )
    id = payload.get("user_id")
    assert id == test_user["id"]
    assert login_res.token_type == "bearer"
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize(
    # fmt: off
    "email, password, status_code",
    [
        ("correct_user@gmail.com", "wrong_password", 401),
        ("wrong_user@gmail.com", "correct_password", 401),
        (None, "correct_password", 422),
        ("correct_user@gmail.com", None, 422),
        (None, None, 422),
    ],
    # fmt: on
)
def test_incorrect_login(test_user, client, email, password, status_code):
    response = client.post("/login", data={"username": email, "password": password})

    assert response.status_code == status_code
