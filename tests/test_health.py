from importlib.metadata import version
from unittest.mock import patch

from fastapi.testclient import TestClient

from rag_audit.api.main import app


def test_health_without_database():
    with patch("rag_audit.db.psycopg.connect") as connect:
        with TestClient(app) as client:
            response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": version("rag-audit")}
    connect.assert_not_called()


def test_unknown_route():
    with TestClient(app) as client:
        assert client.get("/not-implemented").status_code == 404
