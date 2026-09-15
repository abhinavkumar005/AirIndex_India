"""
Idempotent seed loader for AirIndex India reference data.

Loads cities, airports, airlines, sources, routes, and route weights
from `database/seed/*.json` and the YAML config basket into PostgreSQL.
Safe to re-run: existing rows are matched on their natural keys and
left untouched; only missing rows are inserted.

Usage (from project root, with DATABASE_URL set):
    python database/seed/seed_loader.py

Status: DEMO / PROTOTYPE / ASSUMPTION — curated lists, not exhaustive
DGCA registers.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from sqlalchemy.orm import Session

# Make the backend package importable when run as a script
_project_root = Path(__file__).resolve().parent.parent.parent
_backend_dir = _project_root / "backend"
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from app.core.database import get_engine, get_session_factory  # noqa: E402
from app.core.enums import ComplianceStatus, SourceType  # noqa: E402
from app.models import (  # noqa: E402
    Airline,
    Airport,
    City,
    Route,
    RouteWeight,
    Source,
)

SEED_DIR = Path(__file__).resolve().parent


def load_json(name: str) -> list[dict]:
    with open(SEED_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def seed_cities_and_airports(session: Session) -> tuple[int, int]:
    """Seed cities then airports (airports FK to cities). Returns (cities_added, airports_added)."""
    airports = load_json("airports.json")

    # Cities keyed by unique city_code
    city_codes = {a["city_code"] for a in airports}
    existing_cities = {c.code: c for c in session.query(City).all()}
    cities_added = 0
    for code in sorted(city_codes):
        if code not in existing_cities:
            # Name: prefer an airport entry that names the city
            name = next(
                (a["city_name"] for a in airports if a["city_code"] == code),
                code,
            )
            session.add(City(code=code, name=name))
            cities_added += 1

    session.flush()

    existing_airports = {a.iata_code: a for a in session.query(Airport).all()}
    airports_added = 0
    for a in airports:
        if a["iata_code"] not in existing_airports:
            city = session.query(City).filter_by(code=a["city_code"]).one()
            session.add(Airport(
                iata_code=a["iata_code"],
                name=a["name"],
                city_id=city.id,
            ))
            airports_added += 1

    return cities_added, airports_added


def seed_airlines(session: Session) -> int:
    airlines = load_json("airlines.json")
    existing = {a.code: a for a in session.query(Airline).all()}
    added = 0
    for a in airlines:
        if a["code"] not in existing:
            session.add(Airline(code=a["code"], name=a["name"]))
            added += 1
    return added


def seed_sources(session: Session) -> int:
    """Seed the MOCK source; real sources stay disabled pending authorization."""
    existing = {s.code for s in session.query(Source).all()}
    if "MOCK_AIRLINE" in existing:
        return 0
    session.add(Source(
        code="MOCK_AIRLINE",
        source_type=SourceType.MOCK.value,
        enabled=True,
        compliance_status=ComplianceStatus.APPROVED_FOR_SYNTHETIC_DEVELOPMENT.value,
        rate_limit_per_minute=None,
    ))
    return 1


def seed_routes_and_weights(session: Session) -> tuple[int, int]:
    """Seed routes and route weights from the YAML basket config."""
    from app.core.config_loader import load_all_configs

    config = load_all_configs(_project_root / "configs")
    existing_routes = {r.code: r for r in session.query(Route).all()}

    routes_added = 0
    for r in config.routes.routes:
        origin = session.query(Airport).filter_by(iata_code=r.origin).one()
        destination = session.query(Airport).filter_by(iata_code=r.destination).one()
        if r.code not in existing_routes:
            session.add(Route(
                code=r.code,
                origin_id=origin.id,
                destination_id=destination.id,
            ))
            routes_added += 1

    session.flush()

    # Route weights: idempotent per (route_code, config_version)
    existing_weights = session.query(RouteWeight).all()
    existing_keys = {(w.route.code, w.config_version) for w in existing_weights}
    weights_added = 0
    for r in config.routes.routes:
        key = (r.code, config.index.version)
        if key not in existing_keys:
            route = session.query(Route).filter_by(code=r.code).one()
            session.add(RouteWeight(
                route_id=route.id,
                weight=r.weight,
                effective_from=r.effective_from,
                effective_to=r.effective_to,
                config_version=config.index.version,
            ))
            weights_added += 1

    return routes_added, weights_added


def main() -> int:
    engine = get_engine()
    SessionFactory = get_session_factory(engine)

    with SessionFactory() as session:
        cities, airports = seed_cities_and_airports(session)
        airlines = seed_airlines(session)
        sources = seed_sources(session)
        routes, weights = seed_routes_and_weights(session)
        session.commit()

    print(f"Seed complete: {cities} cities, {airports} airports, "
          f"{airlines} airlines, {sources} sources, "
          f"{routes} routes, {weights} route weights added.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
