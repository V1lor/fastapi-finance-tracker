from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime
from typing import Optional


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=30)

    @field_validator('name')
    def validate_name(cls, v: str):
        if any(char.isdigit() for char in v):
            raise ValueError('Название категории не должно содержать цифр')
        return v.strip().title()


class CategoryCreate(CategoryBase):
    pass


class CategoryRead(CategoryBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class TransactionBase(BaseModel):
    amount: float = Field(..., gt=0, description="Сумма должна быть больше 0")
    description: Optional[str] = Field(None, max_length=200)


class TransactionCreate(TransactionBase):
    category_id: int


class TransactionRead(TransactionBase):
    id: int
    transaction_date: datetime
    category_rel: CategoryRead

    model_config = ConfigDict(from_attributes=True)