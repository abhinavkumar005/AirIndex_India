"""
Fare service for AirIndex India.

Provides fare observation retrieval and filtering for API endpoints.

Status: DEMO / PROTOTYPE / ASSUMPTION
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from app.schemas.responses import FareObservationResponse, PaginationMeta
from app.services.mock_fare_generator import MockFareGenerator
from app.services.pipeline import FarePipeline


class FareService:
    """Service for querying fare observations.

    In this prototype, generates and processes mock fares on the fly.
    In production, this would query the database.
    """

    def __init__(self, seed: int = 42):
        self.generator = MockFareGenerator(seed=seed)
        self.pipeline = FarePipeline()

    def _get_config(self):
        """Load configuration from YAML files."""
        from pathlib import Path
        from app.core.config_loader import load_all_configs

        config_dir = Path(__file__).resolve().parent.parent.parent.parent / "configs"
        return load_all_configs(config_dir)

    def get_observations(
        self,
        observation_date: date | None = None,
        route_code: str | None = None,
        airline_code: str | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> tuple[list[FareObservationResponse], PaginationMeta]:
        """Get paginated fare observations with optional filters.

        Returns:
            Tuple of (observations, pagination_meta).
        """
        if observation_date is None:
            observation_date = date.today()

        config = self._get_config()

        routes = [
            {"code": r.code, "origin": r.origin, "destination": r.destination}
            for r in config.routes.routes
        ]
        airlines = [
            {"code": a.code, "name": a.name, "active": a.active}
            for a in config.airlines.airlines
        ]
        advance_days = config.advance_windows.advance_purchase_days

        # Generate and process
        raw_obs = self.generator.generate_day(
            observation_date=observation_date,
            routes=routes,
            airlines=airlines,
            advance_days=advance_days,
        )
        pipeline_result = self.pipeline.process(raw_obs)

        # Convert to response models
        all_responses: list[FareObservationResponse] = []
        for scored in pipeline_result.valid:
            obs = scored.observation
            resp = FareObservationResponse(
                observation_id=str(obs.observation_id),
                observed_at=obs.observed_at,
                source_code=obs.source_code,
                source_type=obs.source_type.value,
                origin_airport=obs.origin_airport,
                destination_airport=obs.destination_airport,
                departure_date=obs.departure_date,
                airline_code=obs.airline_code,
                airline_name=obs.airline_name,
                flight_number=obs.flight_number,
                fare_class=obs.fare_class.value if obs.fare_class else None,
                advance_purchase_days=obs.advance_purchase_days,
                base_fare=obs.components.base_fare,
                taxes=obs.components.taxes,
                airport_charges=obs.components.airport_charges,
                user_development_fee=obs.components.user_development_fee,
                convenience_fee=obs.components.convenience_fee,
                other_charges=obs.components.other_charges,
                total_payable_fare=obs.total_payable_fare,
                currency=obs.currency,
                availability_status=obs.availability_status.value,
                quality_status=obs.quality_status.value,
                quality_score=scored.quality_score,
            )
            all_responses.append(resp)

        # Apply filters
        if route_code:
            origin, dest = route_code.split("-") if "-" in route_code else ("", "")
            all_responses = [
                r for r in all_responses
                if r.origin_airport == origin and r.destination_airport == dest
            ]

        if airline_code:
            all_responses = [
                r for r in all_responses
                if r.airline_code == airline_code
            ]

        # Paginate
        total = len(all_responses)
        total_pages = max(1, (total + per_page - 1) // per_page)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_data = all_responses[start_idx:end_idx]

        pagination = PaginationMeta(
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
        )

        return page_data, pagination
