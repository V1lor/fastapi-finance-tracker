import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import get_db, Base


SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5434/test_db")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """
    Эта фикстура запускается перед каждым тестом.
    Она чистит базу данных, чтобы тесты не мешали друг другу.
    """
    Base.metadata.create_all(bind=engine)

    with engine.connect() as connection:
        connection.execute(text("TRUNCATE TABLE transactions, categories RESTART IDENTITY CASCADE;"))
        connection.commit()

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client(db_session):
    """
    Фикстура клиента API. Подменяет зависимость get_db на тестовую сессию.
    """

    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_create_category_valid(client):
    response = client.post("/categories/", json={"name": "еда"})
    assert response.status_code == 200
    assert response.json()["name"] == "Еда"
    assert "id" in response.json()


def test_create_category_invalid_digits(client):
    response = client.post("/categories/", json={"name": "Еда123"})
    assert response.status_code == 422
    assert "не должно содержать цифр" in response.text


def test_create_category_duplicate(client):
    client.post("/categories/", json={"name": "Дом"})
    response = client.post("/categories/", json={"name": "Дом"})
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_read_categories(client):
    client.post("/categories/", json={"name": "Первая"})
    client.post("/categories/", json={"name": "Вторая"})

    response = client.get("/categories/")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_create_transaction_success(client):
    cat = client.post("/categories/", json={"name": "Работа"}).json()
    cat_id = cat["id"]

    payload = {
        "amount": 50000.0,
        "description": "Зарплата",
        "category_id": cat_id
    }
    response = client.post("/transactions/", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["amount"] == 50000.0
    assert data["category_rel"]["name"] == "Работа"


def test_create_transaction_unknown_category(client):
    response = client.post(
        "/transactions/",
        json={"amount": 100, "category_id": 9999}
    )
    assert response.status_code == 400
    assert "Category not found" in response.json()["detail"]


def test_read_transactions_with_filter(client):
    cat1_id = client.post("/categories/", json={"name": "Еда"}).json()["id"]
    cat2_id = client.post("/categories/", json={"name": "Такси"}).json()["id"]

    client.post("/transactions/", json={"amount": 100, "category_id": cat1_id})
    client.post("/transactions/", json={"amount": 200, "category_id": cat1_id})
    client.post("/transactions/", json={"amount": 500, "category_id": cat2_id})

    response = client.get(f"/transactions/?category_id={cat1_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    for t in data:
        assert t["category_rel"]["name"] == "Еда"


def test_update_transaction(client):
    cat_id = client.post("/categories/", json={"name": "Тест"}).json()["id"]
    create_resp = client.post(
        "/transactions/",
        json={"amount": 100, "category_id": cat_id, "description": "Old"}
    )
    tx_id = create_resp.json()["id"]

    update_resp = client.put(
        f"/transactions/{tx_id}",
        json={"amount": 200, "category_id": cat_id, "description": "New"}
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["amount"] == 200
    assert update_resp.json()["description"] == "New"


def test_delete_transaction(client):
    cat_id = client.post("/categories/", json={"name": "Тест"}).json()["id"]
    tx_id = client.post(
        "/transactions/",
        json={"amount": 100, "category_id": cat_id}
    ).json()["id"]

    del_resp = client.delete(f"/transactions/{tx_id}")
    assert del_resp.status_code == 200

    get_resp = client.get(f"/transactions/{tx_id}")
    assert get_resp.status_code == 404


def test_summary(client):
    cat1_id = client.post("/categories/", json={"name": "Еда"}).json()["id"]
    cat2_id = client.post("/categories/", json={"name": "Такси"}).json()["id"]

    client.post("/transactions/", json={"amount": 100, "category_id": cat1_id})
    client.post("/transactions/", json={"amount": 50, "category_id": cat1_id})
    client.post("/transactions/", json={"amount": 200, "category_id": cat2_id})

    response = client.get("/transactions/summary/")
    assert response.status_code == 200
    data = response.json()

    food_summary = next(item for item in data if item["category"] == "Еда")
    taxi_summary = next(item for item in data if item["category"] == "Такси")

    assert food_summary["total"] == 150.0
    assert taxi_summary["total"] == 200.0