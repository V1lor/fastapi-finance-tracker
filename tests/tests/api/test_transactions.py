import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_create_transaction_success(client: AsyncClient):
    cat_resp = await client.post("/categories/", json={"name": "Работа"})
    cat_id = cat_resp.json()["id"]

    payload = {
        "amount": 500.0,
        "description": "Зарплата",
        "category_id": cat_id
    }
    response = await client.post("/transactions/", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["amount"] == 500.0
    assert data["category_rel"]["name"] == "Работа"


async def test_create_transaction_unknown_category(client: AsyncClient):
    response = await client.post(
        "/transactions/",
        json={"amount": 100, "category_id": 9999}
    )
    assert response.status_code == 400


async def test_read_transactions_filter(client: AsyncClient):
    cat1 = (await client.post("/categories/", json={"name": "Еда"})).json()["id"]
    cat2 = (await client.post("/categories/", json={"name": "Такси"})).json()["id"]

    await client.post("/transactions/", json={"amount": 100, "category_id": cat1})
    await client.post("/transactions/", json={"amount": 200, "category_id": cat1})
    await client.post("/transactions/", json={"amount": 500, "category_id": cat2})

    response = await client.get(f"/transactions/?category_id={cat1}")
    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_summary(client: AsyncClient):
    cat1 = (await client.post("/categories/", json={"name": "Еда"})).json()["id"]

    await client.post("/transactions/", json={"amount": 100, "category_id": cat1})
    await client.post("/transactions/", json={"amount": 50, "category_id": cat1})

    response = await client.get("/transactions/summary/")
    assert response.status_code == 200

    data = response.json()
    assert data[0]["category"] == "Еда"
    assert data[0]["total"] == 150.0