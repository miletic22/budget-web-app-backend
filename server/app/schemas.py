from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase, BaseModel):
    password: str


class UserOut(UserBase, BaseModel):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class BudgetBase(BaseModel):
    id: int


class BudgetCreate(BaseModel):
    amount: int


class BudgetOut(BudgetCreate, BaseModel):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]


class BudgetUpdate(BaseModel):
    amount: int


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: Optional[int] = None


class CategoryCreate(BaseModel):
    name: str
    amount: int


class CategoryOut(CategoryCreate, BaseModel):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]
    budget_id: int

    class Config:
        from_attributes = True


class CategoryUpdate(CategoryCreate, BaseModel): ...


class TransactionCreate(BaseModel):
    amount: int
    note: str
    category_id: int


class TransactionOut(TransactionCreate, BaseModel):
    id: int
    category_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]


class TransactionUpdate(BaseModel):
    amount: int
    note: str


class UserDataOut(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime
    updated_at: datetime

    BudgetOut
    CategoryOut
    TransactionOut

    class Config:
        from_attributes = True
