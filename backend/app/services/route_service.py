"""
Route service for AirIndex India.

Provides route basket retrieval for API endpoints.

Status: DEMO / PROTOTYPE / ASSUMPTION
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from app.core.config_loader import load_all_configs
from app.schemas.responses import RouteResponse


class RouteService:
    """Service for querying route basket configuration."""

    def _get_config(self):
        config_dir = Path(__file__).resolve().parent.parent.parent.parent / "configs"
        return load_all_configs(config_dir)

    def get_routes(self) -> list[RouteResponse]:
        """Get all configured routes in the basket."""
        config = self._get_config()
        return [
            RouteResponse(
                code=r.code,
                origin=r.origin,
                destination=r.destination,
                weight=r.weight,
                effective_from=r.effective_from,
                effective_to=r.effective_to,
            )
            for r in config.routes.routes
        ]

    def get_route_codes(self) -> list[str]:
        """Get list of route codes."""
        config = self._get_config()
        return [r.code for r in config.routes.routes]
