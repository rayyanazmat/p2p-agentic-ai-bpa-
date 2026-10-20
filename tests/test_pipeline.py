"""Tests for synthetic manifest generation and event-log parsing."""

import json

import pytest

from src.pipeline.loader import (
    build_seed_state,
    generate_manifest,
    load_event_log,
    load_manifest,
)


def test_manifest_has_100_unique_marked_synthetic_cases(tmp_path) -> None:
    """The fixed fixture is reproducible and never mislabeled as BPI data."""
    manifest_path = tmp_path / "manifest.json"
    cases = generate_manifest(manifest_path)
    document = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert len(cases) == document["case_count"] == 100
    assert len({case["case_id"] for case in cases}) == 100
    assert all(case["synthetic"] for case in load_manifest(manifest_path))
    assert document["dataset"] == "synthetic_fixture_not_BPI_2019"


def test_xes_loader_preserves_trace_and_event_attributes(tmp_path) -> None:
    """XES parser captures trace ID, activities, and event attribute maps."""
    xes = tmp_path / "tiny.xes"
    xes.write_text(
        '<log><trace><string key="concept:name" value="C1" />'
        '<string key="case:Purchasing Document" value="PO1" />'
        '<event><string key="concept:name" value="Invoice Receipt" />'
        '<string key="org:resource" value="u1" /></event></trace></log>',
        encoding="utf-8",
    )
    records = load_event_log(xes)
    assert records[0]["case_id"] == "C1"
    assert records[0]["activities"] == ["Invoice Receipt"]
    assert records[0]["events"][0]["org:resource"] == "u1"


def test_seed_state_requires_explicit_normalized_policy_fields() -> None:
    """Raw event data cannot silently become a synthetic decision oracle."""
    with pytest.raises(ValueError, match="missing required fields"):
        build_seed_state({"case_id": "BPI-1"})

