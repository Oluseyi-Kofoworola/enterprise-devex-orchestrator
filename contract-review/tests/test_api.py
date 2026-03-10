"""API endpoint tests.

Project: intent-legal-contract-review
"""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestRootEndpoint:
    """Tests for / root endpoint."""

    def test_root_returns_200(self, client: TestClient) -> None:
        """Root endpoint returns 200 OK."""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_response_structure(self, client: TestClient) -> None:
        """Root response contains required fields."""
        response = client.get("/")
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "status" in data

    def test_root_status_running(self, client: TestClient) -> None:
        """Root status is 'running'."""
        response = client.get("/")
        assert response.json()["status"] == "running"

    def test_root_has_docs_link(self, client: TestClient) -> None:
        """Root response includes docs URL."""
        response = client.get("/")
        assert response.json()["docs"] == "/docs"


class TestDocsEndpoint:
    """Tests for /docs OpenAPI endpoint."""

    def test_docs_returns_200(self, client: TestClient) -> None:
        """Docs endpoint is accessible."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_disabled(self, client: TestClient) -> None:
        """ReDoc is disabled as configured."""
        response = client.get("/redoc")
        assert response.status_code == 404


class TestNotFound:
    """Tests for undefined routes."""

    def test_undefined_route_returns_404(self, client: TestClient) -> None:
        """Undefined routes return 404."""
        response = client.get("/nonexistent")
        assert response.status_code == 404
