import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


async def test_create_category_valid(client: AsyncClient):
    response = await client.post("/categories/", json={"name": "еда"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Еда"
    assert "id" in data


async def test_create_category_invalid_digits(client: AsyncClient):
    response = await client.post("/categories/", json={"name": "Еда123"})
    assert response.status_code == 422
    assert "не должно содержать цифр" in response.text


async def test_create_category_duplicate(client: AsyncClient):
    await client.post("/categories/", json={"name": "Дом"})
    response = await client.post("/categories/", json={"name": "Дом"})
    assert response.status_code == 400


async def test_read_categories(client: AsyncClient):
    await client.post("/categories/", json={"name": "Первая"})
    await client.post("/categories/", json={"name": "Вторая"})

    response = await client.get("/categories/")
    assert response.status_code == 200
    assert len(response.json()) == 2