"""
Tests for YAML configuration loaders.

Covers:
  - Loading each real YAML config file from configs/
  - Intentionally invalid YAML producing clear validation errors
  - The aggregate load_all_configs() function
  - Edge cases: empty files, non-mapping YAML, missing files
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config_loader import (
    load_advance_windows_config,
    load_airlines_config,
    load_airports_config,
    load_all_configs,
    load_index_config,
    load_routes_config,
    load_sources_config,
)
from app.schemas.domain import (
    AdvanceWindowConfig,
    AirlineConfig,
    AirportConfig,
    IndexConfig,
    ProjectConfig,
    RouteConfig,
    SourceConfig,
)


# ===================================================================
# Loading real config files
# ===================================================================


class TestLoadRealRoutes:
    def test_loads_successfully(self, configs_dir: Path):
        rc = load_routes_config(configs_dir / "routes.yml")
        assert isinstance(rc, RouteConfig)
        assert len(rc.routes) >= 1

    def test_routes_have_valid_codes(self, configs_dir: Path):
        rc = load_routes_config(configs_dir / "routes.yml")
        for r in rc.routes:
            assert len(r.origin) == 3
            assert len(r.destination) == 3
            assert r.origin != r.destination


class TestLoadRealSources:
    def test_loads_successfully(self, configs_dir: Path):
        sc = load_sources_config(configs_dir / "sources.yml")
        assert isinstance(sc, SourceConfig)
        assert len(sc.sources) >= 1

    def test_mock_source_enabled(self, configs_dir: Path):
        sc = load_sources_config(configs_dir / "sources.yml")
        mock = [s for s in sc.sources if s.code == "MOCK_AIRLINE"]
        assert len(mock) == 1
        assert mock[0].enabled is True


class TestLoadRealAdvanceWindows:
    def test_loads_successfully(self, configs_dir: Path):
        awc = load_advance_windows_config(configs_dir / "advance_windows.yml")
        assert isinstance(awc, AdvanceWindowConfig)
        assert awc.advance_purchase_days == [1, 7, 15, 30, 45]


class TestLoadRealIndex:
    def test_loads_successfully(self, configs_dir: Path):
        ic = load_index_config(configs_dir / "index.yml")
        assert isinstance(ic, IndexConfig)
        assert ic.currency == "INR"
        assert ic.representative_fare_statistic == "median"


class TestLoadRealAirports:
    def test_loads_successfully(self, configs_dir: Path):
        ac = load_airports_config(configs_dir / "airports.yml")
        assert isinstance(ac, AirportConfig)
        assert len(ac.airports) >= 6  # at least the route-basket airports

    def test_route_airports_present(self, configs_dir: Path):
        ac = load_airports_config(configs_dir / "airports.yml")
        codes = {a.iata_code for a in ac.airports}
        for required in ["DEL", "BOM", "BLR", "CCU", "HYD", "MAA"]:
            assert required in codes, f"Route airport {required} missing from airports.yml"


class TestLoadRealAirlines:
    def test_loads_successfully(self, configs_dir: Path):
        alc = load_airlines_config(configs_dir / "airlines.yml")
        assert isinstance(alc, AirlineConfig)
        assert len(alc.airlines) >= 1


# ===================================================================
# Aggregate loader
# ===================================================================


class TestLoadAllConfigs:
    def test_loads_all(self, configs_dir: Path):
        pc = load_all_configs(configs_dir)
        assert isinstance(pc, ProjectConfig)
        assert pc.routes is not None
        assert pc.sources is not None
        assert pc.advance_windows is not None
        assert pc.index is not None
        assert pc.airports is not None
        assert pc.airlines is not None


# ===================================================================
# Error cases — invalid YAML
# ===================================================================


class TestInvalidYaml:
    def test_missing_file(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            load_routes_config(tmp_path / "nonexistent.yml")

    def test_empty_file(self, tmp_yaml):
        p = tmp_yaml("")
        with pytest.raises(ValueError, match="empty"):
            load_routes_config(p)

    def test_non_mapping_yaml(self, tmp_yaml):
        p = tmp_yaml("- item1\n- item2\n")
        with pytest.raises(ValueError, match="mapping"):
            load_routes_config(p)

    def test_invalid_route_weight(self, tmp_yaml):
        content = """
version: test
routes:
  - code: DEL-BOM
    origin: DEL
    destination: BOM
    weight: 2.0
    effective_from: 2026-01-01
"""
        p = tmp_yaml(content)
        with pytest.raises(ValidationError):
            load_routes_config(p)

    def test_routes_weights_not_summing_to_one(self, tmp_yaml):
        content = """
version: test
routes:
  - code: DEL-BOM
    origin: DEL
    destination: BOM
    weight: 0.3
    effective_from: 2026-01-01
  - code: BLR-HYD
    origin: BLR
    destination: HYD
    weight: 0.3
    effective_from: 2026-01-01
"""
        p = tmp_yaml(content)
        with pytest.raises(ValidationError, match="sum to"):
            load_routes_config(p)

    def test_invalid_source_type(self, tmp_yaml):
        content = """
version: test
sources:
  - code: BAD
    type: INVALID_TYPE
"""
        p = tmp_yaml(content)
        with pytest.raises(ValidationError):
            load_sources_config(p)

    def test_advance_windows_zero(self, tmp_yaml):
        content = """
version: test
advance_purchase_days:
  - 0
  - 7
"""
        p = tmp_yaml(content)
        with pytest.raises(ValidationError, match="positive"):
            load_advance_windows_config(p)

    def test_index_bad_currency(self, tmp_yaml):
        content = """
version: test
currency: XX
frequencies:
  - daily
"""
        p = tmp_yaml(content)
        with pytest.raises(ValidationError, match="ISO 4217"):
            load_index_config(p)

    def test_airports_duplicate_codes(self, tmp_yaml):
        content = """
version: test
airports:
  - iata_code: DEL
    name: A
    city_code: DEL
    city_name: Delhi
  - iata_code: DEL
    name: B
    city_code: DEL
    city_name: Delhi
"""
        p = tmp_yaml(content)
        with pytest.raises(ValidationError, match="Duplicate IATA"):
            load_airports_config(p)

    def test_airlines_invalid_code(self, tmp_yaml):
        content = """
version: test
airlines:
  - code: X
    name: Bad Airline
"""
        p = tmp_yaml(content)
        with pytest.raises(ValidationError, match="2–3 uppercase"):
            load_airlines_config(p)
