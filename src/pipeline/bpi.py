"""Streaming profiling and trace-derived fixture creation for BPI 2019."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from src.pipeline.loader import iter_xes


CATEGORY_MAP = {
    "2-way match": "two_way",
    "3-way match, invoice after gr": "three_way_after_gr",
    "3-way match, invoice before gr": "three_way_before_gr",
    "consignment": "consignment",
}
MATCHING_TYPE = {
    "two_way": "two_way",
    "three_way_after_gr": "three_way",
    "three_way_before_gr": "three_way",
    "consignment": "consignment",
}
ACTIVITY_KEYS = {
    "receipt": "Record Goods Receipt",
    "invoice": "Record Invoice Receipt",
    "clear": "Clear Invoice",
    "create_po": "Create Purchase Order Item",
}


def _trace_candidate(trace: dict[str, Any]) -> dict[str, Any] | None:
    """Reduce a raw trace to the observed fields needed for profiling/replay."""
    attributes = trace["attributes"]
    raw_category = attributes.get("Item Category", "").strip()
    category = CATEGORY_MAP.get(raw_category.casefold())
    document_id = attributes.get("Purchasing Document")
    if category is None or not document_id:
        return None

    activities = trace["activities"]
    event_counts = Counter(activities)
    amount_values: list[float] = []
    timestamps: list[str] = []
    for event in trace["events"]:
        raw_amount = event.get("Cumulative net worth (EUR)")
        if raw_amount:
            try:
                amount_values.append(float(raw_amount))
            except ValueError:
                pass
        timestamp = event.get("time:timestamp")
        if timestamp:
            timestamps.append(timestamp)

    create_name = ACTIVITY_KEYS["create_po"]
    create_index = next(
        (i for i, activity in enumerate(activities) if activity == create_name),
        None,
    )
    amount = amount_values[0] if amount_values else 1.0
    if create_index is not None:
        for event, activity in zip(trace["events"], activities):
            if activity == create_name:
                raw_amount = event.get("Cumulative net worth (EUR)")
                if raw_amount:
                    try:
                        amount = float(raw_amount)
                    except ValueError:
                        pass
                break

    return {
        "source_case_id": trace["case_id"],
        "purchasing_document": document_id,
        "item_category": attributes.get("Item Category", ""),
        "category": category,
        "item_type": attributes.get("Item Type", ""),
        "activities": activities,
        "event_count": len(activities),
        "receipt_count": event_counts[ACTIVITY_KEYS["receipt"]],
        "invoice_count": event_counts[ACTIVITY_KEYS["invoice"]],
        "clear_count": event_counts[ACTIVITY_KEYS["clear"]],
        "amount_eur": amount,
        "first_timestamp": min(timestamps) if timestamps else None,
        "last_timestamp": max(timestamps) if timestamps else None,
    }


def profile_and_build_manifest(
    xes_path: Path,
    manifest_path: Path,
    cases_per_category: int = 25,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Stream BPI XES, profile it, and create a labeled trace-derived fixture.

    Event names, category, case ID, PO document ID, event counts, and cumulative
    net worth are observed in the log. The simulator's invoice values,
    verification flag, and unit quantities are deliberately reconstructed and
    marked synthetic because the event log is not a transaction database.
    Non-cleared historical traces are routed to hold as a conservative replay
    target; this is not a recovered ground-truth disposition label.
    """
    category_counts: Counter[str] = Counter()
    raw_category_counts: Counter[str] = Counter()
    activity_counts: Counter[str] = Counter()
    candidates: dict[str, list[dict[str, Any]]] = defaultdict(list)
    resources: set[str] = set()
    trace_count = 0
    event_count = 0
    timestamp_min: str | None = None
    timestamp_max: str | None = None
    invoice_case_count = 0
    receipt_case_count = 0
    cleared_case_count = 0
    simple_case_counts: Counter[str] = Counter()
    excluded_simple_non_2018 = 0

    for trace in iter_xes(xes_path):
        trace_count += 1
        raw_category_counts[
            trace["attributes"].get("Item Category", "<MISSING>").strip()
        ] += 1
        for event in trace["events"]:
            activity = event.get("concept:name", "")
            activity_counts[activity] += 1
            timestamp = event.get("time:timestamp")
            if timestamp:
                timestamp_min = min(timestamp_min, timestamp) if timestamp_min else timestamp
                timestamp_max = max(timestamp_max, timestamp) if timestamp_max else timestamp
            resource = event.get("org:resource") or event.get("User")
            if resource and resource != "NONE":
                resources.add(resource)
        event_count += len(trace["events"])
        candidate = _trace_candidate(trace)
        if candidate is None:
            continue
        category_counts[candidate["category"]] += 1
        if candidate["invoice_count"]:
            invoice_case_count += 1
        if candidate["receipt_count"]:
            receipt_case_count += 1
        if candidate["clear_count"]:
            cleared_case_count += 1
        is_simple = (
            candidate["invoice_count"] <= 1
            and candidate["receipt_count"] <= 1
            and candidate["clear_count"] <= 1
        )
        timestamps_in_2018 = (
            candidate["first_timestamp"] is not None
            and candidate["last_timestamp"] is not None
            and candidate["first_timestamp"].startswith("2018-")
            and candidate["last_timestamp"].startswith("2018-")
        )
        if is_simple and timestamps_in_2018:
            simple_case_counts[candidate["category"]] += 1
            candidates[candidate["category"]].append(candidate)
        elif is_simple:
            excluded_simple_non_2018 += 1

    profile = {
        "dataset": "BPI Challenge 2019",
        "source": "4TU.ResearchData / ICPM 2019 public compressed XES mirror",
        "doi": "10.4121/uuid:d06aff4b-79f0-45e6-8ec8-e19730c248f1",
        "raw_filename": xes_path.name,
        "trace_count": trace_count,
        "event_count": event_count,
        "distinct_activity_count": len(activity_counts),
        "distinct_resource_count": len(resources),
        "first_timestamp": timestamp_min,
        "last_timestamp": timestamp_max,
        "matching_category_case_counts": dict(sorted(category_counts.items())),
        "raw_item_category_counts": dict(sorted(raw_category_counts.items())),
        "cases_with_invoice_receipt": invoice_case_count,
        "cases_with_goods_receipt": receipt_case_count,
        "cases_with_clear_invoice": cleared_case_count,
        "simple_replay_eligible_counts": dict(sorted(simple_case_counts.items())),
        "simple_cases_excluded_for_non_2018_timestamps": excluded_simple_non_2018,
        "activity_counts": dict(sorted(activity_counts.items())),
        "normalization_limitations": [
            "The log is an event history, not a PO/invoice/receipt transactional database.",
            "Individual invoice IDs and invoice amounts are not reconstructed.",
            "Unit quantities and invoice verification are synthetic simulator fields.",
            "A missing Clear Invoice event is not ground truth that the invoice was rejected.",
        ],
    }
    selected = _select_cases(candidates, cases_per_category)
    fixture_cases = [_to_simulator_case(row, index) for index, row in enumerate(selected, 1)]
    manifest = {
        "manifest_version": "1.0",
        "dataset": "BPI_2019_trace_derived_with_synthetic_transaction_fields",
        "source_doi": profile["doi"],
        "case_count": len(fixture_cases),
        "cases_per_category_requested": cases_per_category,
        "case_count_by_category": dict(
            sorted(Counter(case["category"] for case in fixture_cases).items())
        ),
        "oracle_note": (
            "Expected cleared is based on an observed Clear Invoice activity. "
            "Otherwise expected held is a conservative replay target, not an "
            "observed rejection or verified business-policy label."
        ),
        "cases": fixture_cases,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path = manifest_path.with_name("bpi_profile.json")
    profile_path.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return profile, manifest


def _select_cases(
    grouped: dict[str, list[dict[str, Any]]], cases_per_category: int
) -> list[dict[str, Any]]:
    """Select stable category quotas without splitting parent PO documents."""
    selected: list[dict[str, Any]] = []
    selected_documents: set[str] = set()
    categories = sorted(grouped, key=lambda key: (len(grouped[key]), key))
    for category in categories:
        candidates = sorted(
            grouped[category],
            key=lambda row: hashlib.sha256(
                row["source_case_id"].encode("utf-8")
            ).hexdigest(),
        )
        count = 0
        for row in candidates:
            document = row["purchasing_document"]
            if document in selected_documents:
                continue
            selected.append(row)
            selected_documents.add(document)
            count += 1
            if count == cases_per_category:
                break
    return selected


def _to_simulator_case(row: dict[str, Any], index: int) -> dict[str, Any]:
    """Build a simulator state while distinguishing observed and synthetic data."""
    amount = max(0.01, abs(float(row["amount_eur"])))
    cleared = row["clear_count"] > 0
    receipt_count = row["receipt_count"]
    requires_receipt = row["category"] in {
        "three_way_after_gr",
        "three_way_before_gr",
    }
    receipts = [
        {
            "event_id": f"BPI-GR-{index:03d}-{ordinal:02d}",
            "quantity": 1.0,
            "verified": False,
        }
        for ordinal in range(1, receipt_count + 1)
    ]
    if row["category"] == "consignment":
        invoice_verified = False
    else:
        invoice_verified = cleared
    if cleared and requires_receipt and not receipts:
        # The case-level ``Clear Invoice`` observation proves that the source
        # process reached clearing, but detailed receipt quantities are absent.
        # Add one explicitly synthetic receipt so the simplified tool can replay.
        receipts = [
            {
                "event_id": f"BPI-GR-SYN-{index:03d}",
                "quantity": 1.0,
                "verified": False,
            }
        ]
    po_quantity = float(max(1, len(receipts)))
    return {
        "case_id": f"BPI-{index:03d}",
        "po_item_id": f"BPI-PO-{index:03d}",
        "invoice_id": f"BPI-INV-{index:03d}",
        "po_quantity": po_quantity,
        "po_amount": round(amount, 2),
        "invoice_amount": round(amount, 2),
        "currency": "EUR",
        "matching_type": MATCHING_TYPE[row["category"]],
        "category": row["category"],
        "fault": None,
        "invoice_verified": invoice_verified,
        "invoice_status": "open",
        "po_status": "open",
        "receipt_events": receipts,
        "duplicate_invoice": False,
        "expected_state": {"invoice_status": "cleared" if cleared else "held"},
        "synthetic": True,
        "source_dataset": "BPI Challenge 2019",
        "source_case_id": row["source_case_id"],
        "source_purchasing_document": row["purchasing_document"],
        "source_item_category": row["item_category"],
        "source_activities": row["activities"],
        "source_event_counts": {
            "invoice_receipt": row["invoice_count"],
            "goods_receipt": row["receipt_count"],
            "clear_invoice": row["clear_count"],
        },
        "source_cumulative_net_worth_eur": row["amount_eur"],
        "normalization_note": (
            "Trace metadata/activity sequence observed; invoice ID, invoice amount, "
            "verification and unit quantity are reconstructed synthetic fields."
        ),
    }
