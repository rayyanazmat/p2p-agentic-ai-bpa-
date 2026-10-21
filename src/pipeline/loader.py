"""Synthetic seed generation and event-log parsing for P2P experiments."""

from __future__ import annotations

import csv
import json
import random
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterator


SEED = 2019


def make_case(index: int, category: str, fault: str | None = None) -> dict[str, Any]:
    """Construct one deterministic mock P2P case and its expected terminal state."""
    case_id = f"SYN-{index:03d}"
    matching_type = {
        "two_way": "two_way",
        "three_way_complete": "three_way",
        "three_way_missing_gr": "three_way",
        "consignment": "consignment",
    }.get(category, "three_way")
    amount = 100.0 + index
    quantity = 10.0
    receipts: list[dict[str, Any]] = []
    if category in {"three_way_complete", "consignment"}:
        receipts = [
            {"event_id": f"GR-{index:03d}-1", "quantity": quantity, "verified": False}
        ]
    if category == "three_way_missing_gr":
        receipts = [
            {"event_id": f"GR-{index:03d}-1", "quantity": 4.0, "verified": False}
        ]

    invoice_verified = True
    duplicate_invoice = False
    invoice_amount = amount
    if fault == "amount_mismatch":
        invoice_amount += 7.25
    elif fault == "incomplete_receipt":
        receipts = [
            {"event_id": f"GR-{index:03d}-F", "quantity": 2.0, "verified": False}
        ]
    elif fault == "unverified_invoice":
        invoice_verified = False
    elif fault == "duplicate_invoice":
        duplicate_invoice = True

    expected = "cleared"
    if fault or category == "three_way_missing_gr":
        expected = "held"
    return {
        "case_id": case_id,
        "po_item_id": f"PO-{index:03d}-10",
        "invoice_id": f"INV-{index:03d}",
        "po_quantity": quantity,
        "po_amount": round(amount, 2),
        "invoice_amount": round(invoice_amount, 2),
        "currency": "USD",
        "matching_type": matching_type,
        "category": category,
        "fault": fault,
        "invoice_verified": invoice_verified,
        "invoice_status": "open",
        "po_status": "open",
        "receipt_events": receipts,
        "duplicate_invoice": duplicate_invoice,
        "expected_state": {"invoice_status": expected},
        "synthetic": True,
    }


def generate_manifest(path: Path, seed: int = SEED) -> list[dict[str, Any]]:
    """Write a reproducible 100-case synthetic manifest to ``path``."""
    rng = random.Random(seed)
    categories = [
        "two_way",
        "three_way_complete",
        "three_way_missing_gr",
        "consignment",
    ]
    cases = [
        make_case(i, categories[(i - 1) // 20]) for i in range(1, 81)
    ]
    faults = [
        "amount_mismatch",
        "incomplete_receipt",
        "unverified_invoice",
        "duplicate_invoice",
    ] * 5
    rng.shuffle(faults)
    cases.extend(
        make_case(i, "fault_injected", fault)
        for i, fault in zip(range(81, 101), faults)
    )
    document = {
        "manifest_version": "1.0",
        "dataset": "synthetic_fixture_not_BPI_2019",
        "seed": seed,
        "case_count": len(cases),
        "cases": cases,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    return cases


def load_manifest(path: Path) -> list[dict[str, Any]]:
    """Read and validate the basic shape of a generated manifest."""
    document = json.loads(path.read_text(encoding="utf-8"))
    cases = document.get("cases")
    if not isinstance(cases, list):
        raise ValueError("Manifest must contain a cases list")
    if document.get("case_count") != len(cases):
        raise ValueError("Manifest case_count does not match cases length")
    if len({case["case_id"] for case in cases}) != len(cases):
        raise ValueError("Manifest case_id values must be unique")
    return cases


def _xes_attributes(element: ET.Element) -> dict[str, str]:
    """Extract typed XES attribute elements as string values."""
    return {
        item.attrib.get("key", ""): item.attrib.get("value", "")
        for item in element
        if item.attrib.get("key")
    }


def iter_xes(path: Path) -> Iterator[dict[str, Any]]:
    """Yield XES traces incrementally to keep large logs within memory limits."""
    context = ET.iterparse(path, events=("start", "end"))
    _, root = next(context)
    for event, trace in context:
        if event != "end" or not trace.tag.endswith("trace"):
            continue
        attributes: dict[str, str] = {}
        activities: list[str] = []
        events: list[dict[str, str]] = []
        case_id = ""
        for child in trace:
            if child.tag.endswith("event"):
                event_values = _xes_attributes(child)
                activity = event_values.get("concept:name")
                if activity:
                    activities.append(activity)
                events.append(event_values)
            elif child.attrib.get("key"):
                key = child.attrib["key"]
                value = child.attrib.get("value", "")
                attributes[key] = value
                if key in {"concept:name", "case:concept:name"}:
                    case_id = value
        if case_id:
            yield {
                "case_id": case_id,
                "attributes": attributes,
                "activities": activities,
                "events": events,
            }
        trace.clear()
        root.clear()


def parse_xes(path: Path) -> list[dict[str, Any]]:
    """Parse XES traces into case IDs, attributes, and ordered activity names.

    This convenience function materializes the whole log. Use ``iter_xes``
    for large files such as BPI Challenge 2019.
    """
    return list(iter_xes(path))


def parse_csv(path: Path) -> list[dict[str, Any]]:
    """Group event CSV rows by case ID, preserving row order as event order."""
    grouped: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"attributes": {}, "activities": []}
    )
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise ValueError("CSV requires a header row")
        case_column = next(
            (
                name
                for name in ("case:concept:name", "case_id")
                if name in reader.fieldnames
            ),
            None,
        )
        activity_column = next(
            (
                name
                for name in ("concept:name", "activity", "activity_name")
                if name in reader.fieldnames
            ),
            None,
        )
        if case_column is None or activity_column is None:
            raise ValueError("CSV needs case ID and activity columns")
        for row in reader:
            case_id = row[case_column]
            grouped[case_id]["activities"].append(row[activity_column])
            grouped[case_id].setdefault("events", []).append(dict(row))
            grouped[case_id]["attributes"].update(
                {key: value for key, value in row.items() if key.startswith("case:")}
            )
    return [
        {"case_id": case_id, **values} for case_id, values in grouped.items()
    ]


def build_seed_state(normalized_case: dict[str, Any]) -> dict[str, Any]:
    """Convert an explicitly normalized trace into simulator seed state.

    The raw BPI schema contains event and case attributes whose semantic
    mapping must be reviewed before use. This adapter therefore requires a
    normalized record with the simulator's explicit field names instead of
    silently guessing monetary or receipt semantics from raw XES values.
    """
    required = {
        "case_id",
        "po_item_id",
        "invoice_id",
        "po_quantity",
        "po_amount",
        "invoice_amount",
        "currency",
        "matching_type",
        "invoice_verified",
        "receipt_events",
    }
    missing = required.difference(normalized_case)
    if missing:
        raise ValueError(
            "Normalized case is missing required fields: " + ", ".join(sorted(missing))
        )
    case = {
        "case_id": normalized_case["case_id"],
        "po_item_id": normalized_case["po_item_id"],
        "invoice_id": normalized_case["invoice_id"],
        "po_quantity": float(normalized_case["po_quantity"]),
        "po_amount": float(normalized_case["po_amount"]),
        "invoice_amount": float(normalized_case["invoice_amount"]),
        "currency": normalized_case["currency"],
        "matching_type": normalized_case["matching_type"],
        "category": normalized_case.get("category", "bpi_normalized"),
        "fault": normalized_case.get("fault"),
        "invoice_verified": bool(normalized_case["invoice_verified"]),
        "invoice_status": normalized_case.get("invoice_status", "open"),
        "po_status": normalized_case.get("po_status", "open"),
        "receipt_events": normalized_case["receipt_events"],
        "duplicate_invoice": bool(normalized_case.get("duplicate_invoice", False)),
        "expected_state": normalized_case.get(
            "expected_state", {"invoice_status": "held"}
        ),
        "synthetic": bool(normalized_case.get("synthetic", False)),
        "source_dataset": normalized_case.get("source_dataset"),
        "source_case_id": normalized_case.get("source_case_id"),
        "source_purchasing_document": normalized_case.get(
            "source_purchasing_document"
        ),
        "source_item_category": normalized_case.get("source_item_category"),
        "source_activities": normalized_case.get("source_activities", []),
        "source_event_counts": normalized_case.get("source_event_counts", {}),
        "source_cumulative_net_worth_eur": normalized_case.get(
            "source_cumulative_net_worth_eur"
        ),
        "normalization_note": normalized_case.get("normalization_note"),
    }
    if case["expected_state"].get("invoice_status") not in {"cleared", "held"}:
        raise ValueError("expected_state.invoice_status must be cleared or held")
    return case


def load_event_log(path: Path) -> list[dict[str, Any]]:
    """Load XES or CSV based on the file extension."""
    suffix = path.suffix.lower()
    if suffix == ".xes":
        return parse_xes(path)
    if suffix == ".csv":
        return parse_csv(path)
    raise ValueError(f"Unsupported event-log extension: {suffix}")

