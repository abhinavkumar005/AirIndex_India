"""
Shared pytest fixtures for AirIndex India tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture()
def configs_dir() -> Path:
    """Path to the real configs/ directory in the project root."""
    root = Path(__file__).resolve().parent.parent
    d = root / "configs"
    assert d.is_dir(), f"Expected configs directory at {d}"
    return d


@pytest.fixture()
def tmp_yaml(tmp_path: Path):
    """Factory fixture: write arbitrary YAML content to a temp file and return the path."""

    def _write(content: str, filename: str = "test.yml") -> Path:
        p = tmp_path / filename
        p.write_text(content, encoding="utf-8")
        return p

    return _write
