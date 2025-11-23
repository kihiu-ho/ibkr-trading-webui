"""Tests for Workflow Symbols API multi-workflow associations."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.core.database import Base, get_db
from backend.main import app
from backend.models.workflow import Workflow

engine = create_engine("sqlite:///:memory:")
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


def setup_app_dependency():
    app.dependency_overrides[get_db] = override_get_db


setup_app_dependency()


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def workflow_factory(db_session):
    def _factory(name="Workflow"):
        wf = Workflow(name=name)
        db_session.add(wf)
        db_session.commit()
        db_session.refresh(wf)
        return wf

    return _factory


class TestWorkflowSymbolAPI:
    def test_create_symbol_with_multiple_workflows(self, client, workflow_factory):
        wf1 = workflow_factory("Primary")
        wf2 = workflow_factory("Secondary")
        payload = {
            "symbol": "TSLA",
            "name": "Tesla",
            "workflow_type": "trading_signal",
            "priority": 1,
            "workflow_ids": [wf1.id, wf2.id],
        }
        response = client.post("/api/workflow-symbols/", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["symbol"] == "TSLA"
        assert len(data["workflows"]) == 2
        assert {wf["id"] for wf in data["workflows"]} == {wf1.id, wf2.id}

    def test_create_symbol_requires_workflow_ids(self, client):
        payload = {
            "symbol": "AAPL",
            "workflow_ids": [],
        }
        response = client.post("/api/workflow-symbols/", json=payload)
        assert response.status_code == 422

    def test_update_symbol_replaces_workflows(self, client, workflow_factory):
        wf1 = workflow_factory("First")
        wf2 = workflow_factory("Second")
        create_payload = {
            "symbol": "NVDA",
            "workflow_ids": [wf1.id],
        }
        create_resp = client.post("/api/workflow-symbols/", json=create_payload)
        assert create_resp.status_code == 201

        update_resp = client.patch("/api/workflow-symbols/NVDA", json={"workflow_ids": [wf2.id]})
        assert update_resp.status_code == 200
        data = update_resp.json()
        assert len(data["workflows"]) == 1
        assert data["workflows"][0]["id"] == wf2.id

    def test_listing_includes_workflow_metadata(self, client, workflow_factory):
        wf = workflow_factory("Workflow Alpha")
        payload = {
            "symbol": "GOOG",
            "name": "Alphabet",
            "workflow_ids": [wf.id],
        }
        resp = client.post("/api/workflow-symbols/", json=payload)
        assert resp.status_code == 201

        list_resp = client.get("/api/workflow-symbols/")
        assert list_resp.status_code == 200
        symbol = next(item for item in list_resp.json() if item["symbol"] == "GOOG")
        assert symbol["workflows"]
        assert symbol["workflows"][0]["name"] == "Workflow Alpha"

    def test_update_symbol_requires_non_empty_workflows(self, client, workflow_factory):
        wf = workflow_factory()
        payload = {
            "symbol": "META",
            "workflow_ids": [wf.id],
        }
        create_resp = client.post("/api/workflow-symbols/", json=payload)
        assert create_resp.status_code == 201

        update_resp = client.patch("/api/workflow-symbols/META", json={"workflow_ids": []})
        assert update_resp.status_code == 400
        assert "at least one" in update_resp.json()["detail"].lower()
