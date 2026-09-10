"""
Configuration loaders for AirIndex India.

Each loader reads a YAML file from disk and returns a validated Pydantic
domain model. Validation errors from Pydantic propagate with clear messages.

Usage:
    from app.core.config_loader import load_all_configs
    cfg = load_all_configs(Path("configs"))
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from app.schemas.domain import (
    AdvanceWindowConfig,
    Airline,
    AirlineConfig,
    Airport,
    AirportConfig,
    IndexConfig,
    ProjectConfig,
    Route,
    RouteConfig,
    Source,
    SourceConfig,
)

# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------


def _read_yaml(path: Path) -> dict[str, Any]:
    """Read a YAML file and return the top-level mapping.

    Raises:
        FileNotFoundError: If *path* does not exist.
        ValueError: If the file is empty or does not contain a YAML mapping.
    """
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    if data is None:
        raise ValueError(f"Configuration file is empty: {path}")
    if not isinstance(data, dict):
        raise ValueError(
            f"Expected a YAML mapping at top level in {path}, got {type(data).__name__}"
        )
    return data


# ---------------------------------------------------------------------------
# Individual config loaders
# ---------------------------------------------------------------------------


def load_routes_config(path: Path) -> RouteConfig:
    """Load and validate `routes.yml`.

    Args:
        path: Absolute or relative path to the YAML file.

    Returns:
        A validated ``RouteConfig`` instance.
    """
    data = _read_yaml(path)
    return RouteConfig(**data)


def load_sources_config(path: Path) -> SourceConfig:
    """Load and validate `sources.yml`.

    Args:
        path: Absolute or relative path to the YAML file.

    Returns:
        A validated ``SourceConfig`` instance.
    """
    data = _read_yaml(path)
    return SourceConfig(**data)


def load_advance_windows_config(path: Path) -> AdvanceWindowConfig:
    """Load and validate `advance_windows.yml`.

    Args:
        path: Absolute or relative path to the YAML file.

    Returns:
        A validated ``AdvanceWindowConfig`` instance.
    """
    data = _read_yaml(path)
    return AdvanceWindowConfig(**data)


def load_index_config(path: Path) -> IndexConfig:
    """Load and validate `index.yml`.

    Args:
        path: Absolute or relative path to the YAML file.

    Returns:
        A validated ``IndexConfig`` instance.
    """
    data = _read_yaml(path)
    return IndexConfig(**data)


def load_airports_config(path: Path) -> AirportConfig:
    """Load and validate `airports.yml`.

    Args:
        path: Absolute or relative path to the YAML file.

    Returns:
        A validated ``AirportConfig`` instance.
    """
    data = _read_yaml(path)
    return AirportConfig(**data)


def load_airlines_config(path: Path) -> AirlineConfig:
    """Load and validate `airlines.yml`.

    Args:
        path: Absolute or relative path to the YAML file.

    Returns:
        A validated ``AirlineConfig`` instance.
    """
    data = _read_yaml(path)
    return AirlineConfig(**data)


# ---------------------------------------------------------------------------
# Aggregate loader
# ---------------------------------------------------------------------------


def load_all_configs(config_dir: Path) -> ProjectConfig:
    """Load and validate every configuration file in *config_dir*.

    Expects the standard layout::

        config_dir/
            routes.yml
            sources.yml
            advance_windows.yml
            index.yml
            airports.yml
            airlines.yml

    Args:
        config_dir: Directory containing the YAML config files.

    Returns:
        A validated ``ProjectConfig`` aggregating all sub-configs.

    Raises:
        FileNotFoundError: If any expected file is missing.
        pydantic.ValidationError: If any file contains invalid data.
    """
    return ProjectConfig(
        routes=load_routes_config(config_dir / "routes.yml"),
        sources=load_sources_config(config_dir / "sources.yml"),
        advance_windows=load_advance_windows_config(config_dir / "advance_windows.yml"),
        index=load_index_config(config_dir / "index.yml"),
        airports=load_airports_config(config_dir / "airports.yml"),
        airlines=load_airlines_config(config_dir / "airlines.yml"),
    )
