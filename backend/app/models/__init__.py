"""
ORM models package — re-exports all model classes and the shared Base.

Import from here for convenience:
    from app.models import Base, Airport, FareObservationModel, IndexValue
"""

from app.core.database import Base

from app.models.reference import (
    Airline,
    Airport,
    City,
    Route,
    Source,
    SourceConnector,
)
from app.models.methodology import RouteWeight
from app.models.evidence import FareRaw
from app.models.observations import FareObservationModel
from app.models.outputs import IndexComponent, IndexValue

__all__ = [
    "Base",
    # Reference
    "City",
    "Airport",
    "Airline",
    "Route",
    "Source",
    "SourceConnector",
    # Methodology
    "RouteWeight",
    # Evidence
    "FareRaw",
    # Observations
    "FareObservationModel",
    # Outputs
    "IndexValue",
    "IndexComponent",
]
