from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional

from . import models, schemas, database


app = FastAPI(
    title="Personal Finance Tracker",
    description="API для управления личными финансами. Позволяет отслеживать доходы и расходы по категориям.",
    version="1.0.0"
)


@app.get("/categories/", response_model=List[schemas.CategoryRead], tags=["Categories"])
def read_categories(db: Session = Depends(database.get_db)):
    """
    Получить список всех категорий.

    Возвращает список объектов с полями:
    - **id**: Уникальный идентификатор категории.
    - **name**: Название категории.
    """
    return db.query(models.Category).all()


@app.post("/categories/", response_model=schemas.CategoryRead, tags=["Categories"])
def create_category(category: schemas.CategoryCreate, db: Session = Depends(database.get_db)):
    """
    Создать новую категорию расходов.

    - **name**: Название категории. Должно быть уникальным.

    Если категория с таким именем уже существует, вернет ошибку 400.
    """
    existing = db.query(models.Category).filter(models.Category.name == category.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")

    db_category = models.Category(name=category.name)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


@app.post("/transactions/", response_model=schemas.TransactionRead, tags=["Transactions"])
def create_transaction(transaction: schemas.TransactionCreate, db: Session = Depends(database.get_db)):
    """
    Добавить новую транзакцию (расход или доход).

    Требует:
    - **amount**: Сумма (должна быть > 0).
    - **category_id**: ID существующей категории.
    - **description**: Описание (опционально).

    Возвращает созданный объект транзакции с датой создания.
    """
    category = db.query(models.Category).filter(models.Category.id == transaction.category_id).first()
    if not category:
        raise HTTPException(status_code=400, detail="Category not found. Check /categories/ for valid IDs.")

    db_transaction = models.Transaction(**transaction.model_dump())
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


@app.get("/transactions/", response_model=List[schemas.TransactionRead], tags=["Transactions"])
def read_transactions(
        category_id: Optional[int] = Query(None, description="Фильтр по ID категории"),
        skip: int = Query(0, description="Сколько записей пропустить (пагинация)"),
        limit: int = Query(100, description="Сколько записей вернуть (макс. 100)"),
        db: Session = Depends(database.get_db)
):
    """
    Получить список транзакций.

    Поддерживает фильтрацию и пагинацию:
    - Если указан **category_id**, вернет транзакции только этой категории.
    - **skip** и **limit** используются для постраничного вывода.
    """
    query = db.query(models.Transaction).options(joinedload(models.Transaction.category_rel))

    if category_id:
        query = query.filter(models.Transaction.category_id == category_id)

    return query.offset(skip).limit(limit).all()


@app.get("/transactions/{transaction_id}", response_model=schemas.TransactionRead, tags=["Transactions"])
def read_transaction(transaction_id: int, db: Session = Depends(database.get_db)):
    """
    Получить одну конкретную транзакцию по её ID.
    """
    transaction = db.query(models.Transaction) \
        .options(joinedload(models.Transaction.category_rel)) \
        .filter(models.Transaction.id == transaction_id) \
        .first()

    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction


@app.put("/transactions/{transaction_id}", response_model=schemas.TransactionRead, tags=["Transactions"])
def update_transaction(
        transaction_id: int,
        transaction_update: schemas.TransactionCreate,
        db: Session = Depends(database.get_db)
):
    """
    Обновить данные транзакции.

    Полностью заменяет данные транзакции (сумма, категория, описание).
    Если указан новый **category_id**, проверяется его существование.
    """
    db_transaction = db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
    if db_transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if transaction_update.category_id != db_transaction.category_id:
        category = db.query(models.Category).filter(models.Category.id == transaction_update.category_id).first()
        if not category:
            raise HTTPException(status_code=400, detail="New category not found")

    for key, value in transaction_update.model_dump().items():
        setattr(db_transaction, key, value)

    db.commit()
    db.refresh(db_transaction)
    return db_transaction


@app.delete("/transactions/{transaction_id}", tags=["Transactions"])
def delete_transaction(transaction_id: int, db: Session = Depends(database.get_db)):
    """
    Удалить транзакцию по ID.

    Действие необратимо.
    """
    db_transaction = db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
    if db_transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")

    db.delete(db_transaction)
    db.commit()
    return {"detail": "Transaction deleted"}


@app.get("/transactions/summary/", tags=["Analytics"])
def get_summary(db: Session = Depends(database.get_db)):
    """
    Получить сводку расходов.

    Возвращает список категорий с общей суммой расходов по каждой из них.
    Формат: `[{"category": "Еда", "total": 1500.0}, ...]`
    """
    summary = db.query(
        models.Category.name,
        func.sum(models.Transaction.amount).label("total_amount")
    ).join(models.Transaction).group_by(models.Category.name).all()

    return [{"category": s[0], "total": s[1]} for s in summary]