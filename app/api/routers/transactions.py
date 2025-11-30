from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload

from app.db.base import get_db
from app.models.transaction import Transaction
from app.models.category import Category
from app.schemas.transaction import TransactionCreate, TransactionRead
from typing import List, Optional

router = APIRouter()


@router.post("/", response_model=TransactionRead)
async def create_transaction(transaction: TransactionCreate, db: AsyncSession = Depends(get_db)):
    category = await db.get(Category, transaction.category_id)
    if not category:
        raise HTTPException(status_code=400, detail="Category not found")

    new_transaction = Transaction(**transaction.model_dump())
    db.add(new_transaction)
    await db.commit()
    await db.refresh(new_transaction)
    new_transaction.category_rel = category
    return new_transaction


@router.get("/", response_model=List[TransactionRead])
async def read_transactions(
        category_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = Depends(get_db)
):
    query = select(Transaction).options(joinedload(Transaction.category_rel))

    if category_id:
        query = query.where(Transaction.category_id == category_id)

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)

    return result.scalars().all()


@router.get("/summary/")
async def get_summary(db: AsyncSession = Depends(get_db)):
    query = select(
        Category.name,
        func.sum(Transaction.amount).label("total_amount")
    ).join(Transaction).group_by(Category.name)

    result = await db.execute(query)
    summary = result.all()

    return [{"category": s[0], "total": s[1]} for s in summary]


@router.get("/{transaction_id}", response_model=TransactionRead)
async def read_transaction(transaction_id: int, db: AsyncSession = Depends(get_db)):
    query = select(Transaction) \
        .options(joinedload(Transaction.category_rel)) \
        .where(Transaction.id == transaction_id)

    result = await db.execute(query)
    transaction = result.scalar_one_or_none()

    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction


@router.put("/{transaction_id}", response_model=TransactionRead)
async def update_transaction(
        transaction_id: int,
        transaction_update: TransactionCreate,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Transaction).where(Transaction.id == transaction_id))
    db_transaction = result.scalar_one_or_none()

    if db_transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if transaction_update.category_id != db_transaction.category_id:
        category = await db.get(Category, transaction_update.category_id)
        if not category:
            raise HTTPException(status_code=400, detail="New category not found")

    for key, value in transaction_update.model_dump().items():
        setattr(db_transaction, key, value)

    await db.commit()

    query = select(Transaction) \
        .options(joinedload(Transaction.category_rel)) \
        .where(Transaction.id == transaction_id)

    result = await db.execute(query)
    updated_transaction = result.scalar_one()

    return updated_transaction


@router.delete("/{transaction_id}")
async def delete_transaction(transaction_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Transaction).where(Transaction.id == transaction_id))
    db_transaction = result.scalar_one_or_none()

    if db_transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")

    await db.delete(db_transaction)
    await db.commit()
    return {"detail": "Transaction deleted"}