import pytest
from httpx import AsyncClient
from app.main import app
from unittest.mock import AsyncMock

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="session")
async def client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def mock_auth_dependency(monkeypatch):
    async def mock_get_current_user():
        return {"id": 1, "email": "tenant1@example.com", "role": "Tenant"}
    monkeypatch.setattr("app.dependencies.auth.get_current_user", mock_get_current_user)

@pytest.fixture
def mock_owner_auth_dependency(monkeypatch):
    async def mock_get_current_user():
        return {"id": 2, "email": "owner1@example.com", "role": "Owner"}
    monkeypatch.setattr("app.dependencies.auth.get_current_user", mock_get_current_user)

@pytest.fixture
def mock_langgraph_agent(monkeypatch):
    async def mock_run_recommendation_agent(*args, **kwargs):
        return [
            {
                "property_id": 1,
                "title": "Apartment in Bole",
                "location": "Bole, Addis Ababa",
                "price": 1500.0,
                "transport_cost": 50.0,
                "affordability_score": 0.5,
                "reason": "ይህ አፓርትመንት በቦሌ ከሥራዎ 5 ኪ.ሜ ርቀት ላይ ነው፣ ወርሃዊ ትራንስፖርት 50 ብር፣ በጀትዎ ውስጥ ነው።",
                "map_url": "https://api.gebeta.app/tiles/9.0/38.7/15"
            }
        ]
    monkeypatch.setattr("app.services.langgraph_agent.run_recommendation_agent", mock_run_recommendation_agent)

@pytest.fixture
def mock_save_tenant_profile(monkeypatch):
    async def mock_save_profile(*args, **kwargs):
        return 1  # tenant_id
    monkeypatch.setattr("app.services.rag.save_tenant_profile", mock_save_profile)

@pytest.fixture
def mock_db_session(monkeypatch):
    class MockAsyncSession:
        def __init__(self):
            self.logs = []

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        async def execute(self, statement):
            class MockResult:
                def scalars(self):
                    class MockScalars:
                        def all(self):
                            return self.logs
                    return MockScalars()
            return MockResult()

        def add(self, log):
            self.logs.append(log)

        async def commit(self):
            pass

    monkeypatch.setattr("sqlalchemy.ext.asyncio.AsyncSession", MockAsyncSession)
    monkeypatch.setattr("sqlalchemy.ext.asyncio.create_async_engine", lambda *args, **kwargs: None)
