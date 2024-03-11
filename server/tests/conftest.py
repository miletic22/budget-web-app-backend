import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models
from app.database import get_db
from app.main import app
from app.oauth2 import create_access_token

SQLALCHEMY_DATABASE_URL = (
    "postgresql://postgres:password@localhost:5432/budget-app_test"
)
# SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.database_username}:{settings.database_password}@{settings.database_hostname}:{settings.database_port}/{settings.database_name}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def session():
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client(session):
    def override_get_db():

        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)


@pytest.fixture
def test_user(client):
    user_data = {"email": "correct_user@gmail.com", "password": "correct_password"}
    response = client.post("/users/", json=user_data)

    assert response.status_code == 201

    new_user = response.json()
    new_user["password"] = user_data["password"]
    return new_user


# @pytest.fixture
# def multiple_test_users(client):
#     users = [
#         {"email": "test1@gmail.com", "password": "password1"},
#         {"email": "test2@gmail.com", "password": "password2"},
#         {"email": "test3@gmail.com", "password": "password3"},
#     ]

#     created_users = []

#     for user_data in users:
#         response = client.post("/users/", json=user_data)
#         assert response.status_code == 201
#         new_user = response.json()
#         new_user["password"] = user_data["password"]
#         created_users.append(new_user)

#     return created_users


@pytest.fixture
def token(test_user):
    return create_access_token({"user_id": test_user["id"]})


# @pytest.fixture
# def multiple_tokens(test_users):
#     return [create_access_token({"user_id": user["id"]}) for user in test_users]


@pytest.fixture
def authorized_client(client, token):
    client.headers = {**client.headers, "Authorization": f"Bearer {token}"}
    return client


# @pytest.fixture
# def multiple_authorized_clients(client, tokens):
#     clients = []

#     for token in tokens:
#         headers = {"Authorization": f"Bearer {token}"}
#         client_with_token = client.__class__(base_url=client.base_url, headers=headers)
#         clients.append(client_with_token)

#     return clients
