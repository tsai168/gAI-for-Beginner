"""B0.5 smoke tests: the repo scaffold imports and the toolchain runs green.

Real coverage begins in WBS-B1 (TEST-DATA-01 onward, Work-3 §4).
"""

from __future__ import annotations

import importlib
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

LAYER_PACKAGES = [
    "ingestion",
    "knowledge",
    "models",
    "agents",
    "workflows",
    "reports",
    "governance",
    "api",
    "ui",
]


@pytest.mark.parametrize("pkg", LAYER_PACKAGES)
def test_layer_package_importable(pkg: str) -> None:
    assert importlib.import_module(pkg) is not None


def test_docs_present() -> None:
    docs = REPO_ROOT / "docs"
    for name in (
        "CHARTER_FREEZE_V1.md",
        "WORK1_TECH_SPEC_BASELINE_V1.md",
        "WORK2_CONTRACT_FREEZE_V1.md",
        "WORK3_IMPLEMENTATION_BLUEPRINT_V1.md",
    ):
        assert (docs / name).is_file(), name


def test_python_pinned_to_312() -> None:
    data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["requires-python"] == ">=3.12,<3.13"


def test_alembic_scaffold_present() -> None:
    assert (REPO_ROOT / "alembic.ini").is_file()
    assert (REPO_ROOT / "infra" / "db" / "migrations" / "env.py").is_file()
