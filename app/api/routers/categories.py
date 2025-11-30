from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.base import get_db
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryRead
from typing import List

router = APIRouter()


@router.get("/", response_model=List[CategoryRead])
async def read_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category))
    return result.scalars().all()


@router.post("/", response_model=CategoryRead)
async def create_category(category: CategoryCreate, db: AsyncSession = Depends(get_db)):
    query = select(Category).where(Category.name == category.name)
    result = await db.execute(query)
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")

    new_category = Category(name=category.name)
    db.add(new_category)
    await db.commit()
    await db.refresh(new_category)
    return new_category