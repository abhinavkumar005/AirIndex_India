# Changelog

## Phase 1 — Domain Models and Validated Configuration Loaders (2026-09-10)

### Added

- `pyproject.toml` — project metadata, dependencies (Pydantic v2, PyYAML), dev tools (pytest, pytest-cov).
- `backend/app/core/enums.py` — 11 domain enums: `SourceType`, `ComplianceStatus`, `AvailabilityStatus`, `CancellationStatus`, `QualityStatus`, `FareClass`, `IndexFrequency`, `OutlierPolicy`, `MissingCellPolicy`, `WeightRedistributionPolicy`, `ConfigStatus`.
- `backend/app/schemas/domain.py` — Pydantic v2 models: `Airport`, `Airline`, `Route`, `Source`, `RouteConfig`, `SourceConfig`, `AdvanceWindowConfig`, `IndexConfig`, `AirportConfig`, `AirlineConfig`, `ProjectConfig`, `FareComponent`, `FareObservation`.
- `backend/app/core/config_loader.py` — Validated YAML loaders for routes, sources, advance windows, index, airports, airlines, plus `load_all_configs()`.
- `configs/airports.yml` — 12 prototype Indian airports.
- `configs/airlines.yml` — 8 prototype Indian domestic airlines.
- `backend/app/__init__.py`, `backend/app/core/__init__.py`, `backend/app/schemas/__init__.py` — package init files with re-exports.
- `tests/conftest.py` — shared fixtures (`configs_dir`, `tmp_yaml` factory).
- `tests/unit/test_enums.py` — enum membership, string-value, and re-export tests.
- `tests/unit/test_domain_models.py` — model construction, field validation, and cross-field invariant tests.
- `tests/unit/test_config_loader.py` — real-config loading, aggregate loading, and error-case tests.
- **88 unit tests passing.**

## Phase 0 — Repository Initialization (2026-09-07)

### Added

- Initial modular monorepo directory structure.
- Project-control documents: `AGENTS.md`, `PROJECT_STATUS.md`, `ROADMAP.md`, `ARCHITECTURE.md`, `DATABASE.md`, `API_SPEC.md`, `DATA_DICTIONARY.md`, `STATISTICAL_METHODOLOGY.md`, `KNOWN_ISSUES.md`, `DECISIONS.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `DEPLOYMENT.md`, `DEVELOPMENT_PLAN.md`, `SCRAPING_POLICY.md`, `SECURITY.md`, `TESTING.md`, `ENVIRONMENT.md`, `DATA_PIPELINE.md`.
- Skeleton YAML configs: `routes.yml`, `sources.yml`, `advance_windows.yml`, `index.yml`.
- `.env.example`, `.editorconfig`, `.gitignore`, `.gitattributes`.
- `docker-compose.yml` placeholder.
