import pytest
from httpx import AsyncClient
from app.main import app
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_recommendations(monkeypatch):
    async def mock_geocode(query):
        return {"lat": 9.0, "lon": 38.7}
    async def mock_matrix(lat, lon, destinations):
        return [{"distance": 5000, "time": 600} for _ in destinations]
    async def mock_generate_reason(*args, **kwargs):
        return "ይህ አፓርትመንት በቦሌ ከሥራዎ 5 ኪ.ሜ ርቀት ላይ ነው፣ ወርሃዊ ትራንስፖርት 50 ብር፣ በጀትዎ ውስጥ ነው።"
    async def mock_search_properties(*args, **kwargs):
        return [
            {"id": 1, "title": "Apartment in Bole", "location": "Bole", "price": 1500.0, "house_type": "apartment", "bedrooms": 2, "amenities": ["wifi", "parking"], "lat": 9.0, "lon": 38.7}
        ]
    monkeypatch.setattr("app.services.gebeta.geocode", mock_geocode)
    monkeypatch.setattr("app.services.gebeta.get_matrix", mock_matrix)
    monkeypatch.setattr("app.services.gemini.generate_reason", mock_generate_reason)
    monkeypatch.setattr("app.services.search.search_properties", mock_search_properties)
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/recommendations",
            json={
                "job_school_location": "Bole",
                "salary": 5000.0,
                "house_type": "apartment",
                "family_size": 2,
                "preferred_amenities": ["wifi", "parking"],
                "language": "am"
            },
            headers={"Authorization": "Bearer valid_token"}
        )
        assert response.status_code == 200
        assert len(response.json()["recommendations"]) <= 3
        assert response.json()["total_budget_suggestion"] == 1500.0
        assert "ቦሌ" in response.json()["recommendations"][0]["reason"]

@pytest.mark.asyncio
async def test_recommendations_unauthorized():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/recommendations", json={})
        assert response.status_code == 401

@pytest.mark.asyncio
async def test_recommendations_invalid_input():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/recommendations",
            json={"job_school_location": "", "salary": -100, "house_type": "", "family_size": 0},
            headers={"Authorization": "Bearer valid_token"}
        )
        assert response.status_code == 422

@pytest.mark.asyncio
async def test_recommendations_no_properties(monkeypatch):
    async def mock_search_properties(*args, **kwargs):
        return []
    monkeypatch.setattr("app.services.search.search_properties", mock_search_properties)
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/recommendations",
            json={
                "job_school_location": "Bole",
                "salary": 5000.0,
                "house_type": "apartment",
                "family_size": 2,
                "preferred_amenities": ["wifi"],
                "language": "en"
            },
            headers={"Authorization": "Bearer valid_token"}
        )
        assert response.status_code == 200
        assert response.json()["recommendations"] == []
