from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional
from .category import CategoryRead

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