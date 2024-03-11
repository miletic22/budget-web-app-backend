from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app import database, models, schemas

from .config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes


def create_access_token(data: dict) -> str:
    """
    Creates an access token with the provided user data.

    Input:
        data (dict): User data to be encoded in the token.

    Output:
        str: The encoded JWT access token.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = expire.timestamp()
    to_encode.update({"expiration": expire})
    encoded_jwt = jwt.encode(claims=to_encode, key=SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_access_token(token: str, credentials_exception) -> dict:
    """
    Verifies the validity of an access token.

    Input:
        token (str): The JWT access token.
        credentials_exception: Exception to raise if credentials are not valid.

    Output:
        dict: Token data containing user ID.
    """
    try:
        payload = jwt.decode(token, key=SECRET_KEY, algorithms=[ALGORITHM])
        id: str = payload.get("user_id")
        if id is None:
            raise credentials_exception

        # Convert the expiration time from seconds to integer timestamp
        expiration_time = payload.get("expiration")

        # Compare with the current UTC time as integer timestamp
        current_time = int(datetime.utcnow().timestamp())

        if current_time > expiration_time:
            raise credentials_exception

        token_data = schemas.TokenData(id=id)

    except JWTError:
        raise credentials_exception

    return token_data


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)
) -> models.User:
    """
    Gets the current user based on the provided access token.

    Input:
        token (str): The JWT access token.

    Output:
        models.User: The user information retrieved from the database.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = verify_access_token(token, credentials_exception)
    user = db.query(models.User).filter(models.User.id == token.id).first()

    return user
