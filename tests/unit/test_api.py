"""
API endpoint tests for AirIndex India (Phase 6).

Tests all 11 planned API endpoints via the FastAPI test client.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


# ---------------------------------------------------------------------------
# Health & Root
# ---------------------------------------------------------------------------


class TestHealthAndRoot:
    """Tests for health check and root endpoints."""

    def test_health_check(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.1.0"
        assert "timestamp" in data

    def test_root(self, client: TestClient):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "AirIndex India API"
        assert data["api_base"] == "/api/v1"


# ---------------------------------------------------------------------------
# Index endpoints
# ---------------------------------------------------------------------------


class TestIndexEndpoints:
    """Tests for /api/v1/index/* endpoints."""

    def test_get_current_index(self, client: TestClient):
        response = client.get("/api/v1/index/current")
        assert response.status_code == 200
        envelope = response.json()
        assert "data" in envelope
        assert "meta" in envelope
        data = envelope["data"]
        assert "index_value" in data
        assert "coverage_pct" in data
        assert "route_count" in data
        assert data["frequency"] == "daily"

    def test_get_daily_index(self, client: TestClient):
        today = date.today()
        start = today - timedelta(days=2)
        response = client.get(
            "/api/v1/index/daily",
            params={"start_date": str(start), "end_date": str(today)},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)
        assert len(data) == 3  # 3 days inclusive

    def test_get_daily_index_defaults(self, client: TestClient):
        response = client.get("/api/v1/index/daily")
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)
        assert len(data) == 7  # Default 7 days

    def test_get_weekly_index(self, client: TestClient):
        today = date.today()
        start = today - timedelta(days=13)
        response = client.get(
            "/api/v1/index/weekly",
            params={"start_date": str(start), "end_date": str(today)},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_monthly_index(self, client: TestClient):
        today = date.today()
        start = today - timedelta(days=60)
        response = client.get(
            "/api/v1/index/monthly",
            params={"start_date": str(start), "end_date": str(today)},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_index_history_daily(self, client: TestClient):
        today = date.today()
        start = today - timedelta(days=2)
        response = client.get(
            "/api/v1/index/history",
            params={
                "frequency": "daily",
                "start_date": str(start),
                "end_date": str(today),
            },
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 3

    def test_get_index_history_default(self, client: TestClient):
        response = client.get("/api/v1/index/history")
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)

    def test_index_envelope_has_meta(self, client: TestClient):
        response = client.get("/api/v1/index/current")
        meta = response.json()["meta"]
        assert "generated_at" in meta
        assert meta["version"] == "v1"

    def test_index_current_is_idempotent(self, client: TestClient):
        """Regression: repeated identical requests must return the same
        index value (auditability / reproducibility requirement)."""
        r1 = client.get("/api/v1/index/current").json()["data"]
        r2 = client.get("/api/v1/index/current").json()["data"]
        assert r1["index_value"] == r2["index_value"]

    def test_daily_series_moves_off_base(self, client: TestClient):
        """With the first-observation base fallback, the anchor day is
        ~100 and at least one subsequent day must deviate from it
        (previously every day was trivially exactly 100)."""
        today = date.today()
        start = today - timedelta(days=6)
        response = client.get(
            "/api/v1/index/daily",
            params={"start_date": str(start), "end_date": str(today)},
        )
        assert response.status_code == 200
        series = response.json()["data"]
        assert len(series) == 7
        anchor = Decimal(series[0]["index_value"])
        assert abs(anchor - Decimal("100")) < Decimal("0.01")
        values = [Decimal(d["index_value"]) for d in series]
        assert any(abs(v - anchor) > Decimal("0.01") for v in values)
        # Every result must disclose its base period.
        assert all(d["base_period"] for d in series)


# ---------------------------------------------------------------------------
# Route endpoints
# ---------------------------------------------------------------------------


class TestRouteEndpoints:
    """Tests for /api/v1/routes endpoints."""

    def test_get_routes(self, client: TestClient):
        response = client.get("/api/v1/routes")
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)
        assert len(data) == 6  # 6 configured routes
        route = data[0]
        assert "code" in route
        assert "origin" in route
        assert "destination" in route
        assert "weight" in route

    def test_get_route_trend(self, client: TestClient):
        today = date.today()
        start = today - timedelta(days=2)
        response = client.get(
            "/api/v1/routes/DEL-BOM/trend",
            params={"start_date": str(start), "end_date": str(today)},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["route_code"] == "DEL-BOM"
        assert data["origin"] == "DEL"
        assert data["destination"] == "BOM"
        assert len(data["trend"]) == 3


# ---------------------------------------------------------------------------
# Fare endpoints
# ---------------------------------------------------------------------------


class TestFareEndpoints:
    """Tests for /api/v1/fares endpoint."""

    def test_get_fares_default(self, client: TestClient):
        response = client.get("/api/v1/fares")
        assert response.status_code == 200
        envelope = response.json()
        data = envelope["data"]
        assert isinstance(data, list)
        assert len(data) > 0
        # Check pagination
        meta = envelope["meta"]
        assert meta["pagination"] is not None
        assert meta["pagination"]["total"] > 0

    def test_get_fares_with_route_filter(self, client: TestClient):
        response = client.get(
            "/api/v1/fares",
            params={"route": "DEL-BOM"},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        for obs in data:
            assert obs["origin_airport"] == "DEL"
            assert obs["destination_airport"] == "BOM"

    def test_get_fares_with_airline_filter(self, client: TestClient):
        response = client.get(
            "/api/v1/fares",
            params={"airline": "6E"},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        for obs in data:
            assert obs["airline_code"] == "6E"

    def test_get_fares_pagination(self, client: TestClient):
        response = client.get(
            "/api/v1/fares",
            params={"per_page": 10, "page": 1},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) <= 10

    def test_fare_observation_fields(self, client: TestClient):
        response = client.get("/api/v1/fares", params={"per_page": 5})
        assert response.status_code == 200
        data = response.json()["data"]
        assert data, "expected at least one observation"
        for obs in data:
            assert "observation_id" in obs
            assert "observed_at" in obs
            assert "source_code" in obs
            assert "origin_airport" in obs
            assert "destination_airport" in obs
            assert "availability_status" in obs
            assert "quality_status" in obs
            # Regression: the pipeline must set quality_status (previously
            # every observation stayed PENDING forever).
            assert obs["quality_status"] in ("VALID", "FLAGGED")


# ---------------------------------------------------------------------------
# Source endpoints
# ---------------------------------------------------------------------------


class TestSourceEndpoints:
    """Tests for /api/v1/sources/status endpoint."""

    def test_get_sources_status(self, client: TestClient):
        response = client.get("/api/v1/sources/status")
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)
        assert len(data) >= 1  # At least the MOCK source

        # Find the MOCK source
        mock_source = next(
            (s for s in data if s["code"] == "MOCK_AIRLINE"), None
        )
        assert mock_source is not None
        assert mock_source["enabled"] is True
        assert mock_source["source_type"] == "MOCK"
        assert mock_source["health"] == "healthy"


# ---------------------------------------------------------------------------
# Quality endpoints
# ---------------------------------------------------------------------------


class TestQualityEndpoints:
    """Tests for /api/v1/data-quality endpoint."""

    def test_get_data_quality(self, client: TestClient):
        response = client.get("/api/v1/data-quality")
        assert response.status_code == 200
        data = response.json()["data"]
        assert "total_observations" in data
        assert "valid_count" in data
        assert "flagged_count" in data
        assert "outlier_count" in data
        assert data["total_observations"] > 0

    def test_quality_coverage_by_route(self, client: TestClient):
        response = client.get("/api/v1/data-quality")
        data = response.json()["data"]
        assert "coverage_by_route" in data
        assert isinstance(data["coverage_by_route"], dict)
        assert len(data["coverage_by_route"]) > 0


# ---------------------------------------------------------------------------
# Validation endpoints
# ---------------------------------------------------------------------------


class TestValidationEndpoints:
    """Tests for /api/v1/validation endpoint."""

    def test_get_validation_summary(self, client: TestClient):
        today = date.today()
        start = today - timedelta(days=2)
        response = client.get(
            "/api/v1/validation",
            params={"start_date": str(start), "end_date": str(today)},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["backtest_days"] == 3
        assert data["status"] == "prototype"
        assert data["average_index_value"] is not None
        assert data["total_observations"] > 0

    def test_validation_default_range(self, client: TestClient):
        response = client.get("/api/v1/validation")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["backtest_days"] == 7  # Default 7-day range


# ---------------------------------------------------------------------------
# OpenAPI / Swagger
# ---------------------------------------------------------------------------


class TestOpenAPI:
    """Tests for OpenAPI documentation availability."""

    def test_openapi_json(self, client: TestClient):
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "paths" in schema
        assert "/api/v1/index/current" in schema["paths"]
        assert "/api/v1/routes" in schema["paths"]
        assert "/api/v1/fares" in schema["paths"]

    def test_docs_page(self, client: TestClient):
        response = client.get("/docs")
        assert response.status_code == 200
