"""Unit tests for simulator invariants, idempotency, and API validation."""

from fastapi.testclient import TestClient

from src.pipeline.loader import make_case
from src.simulator.app import app
from src.simulator.database import store


def setup_function() -> None:
    """Give each test an isolated deterministic state."""
    store.reset([make_case(1, "three_way_complete")])


def test_receipt_verification_is_idempotent() -> None:
    """A repeated verify request with one key makes only one transition."""
    client = TestClient(app)
    body = {"idempotency_key": "verify-once"}
    first = client.post("/goods-receipts/PO-001-10/verify", json=body)
    second = client.post("/goods-receipts/PO-001-10/verify", json=body)
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()
    audit = client.get("/cases/SYN-001/audit").json()
    transitions = [
        item for item in audit["transitions"] if item["entity"] == "goods_receipts"
    ]
    assert len(transitions) == 1


def test_clear_rejects_unmet_receipt_precondition() -> None:
    """The API rejects clearing a three-way invoice before GR verification."""
    client = TestClient(app)
    response = client.post(
        "/invoices/INV-001/clear", json={"idempotency_key": "clear-too-early"}
    )
    assert response.status_code == 409
    assert "receipt" in response.json()["detail"].lower()
    assert client.get("/invoices/INV-001").json()["status"] == "open"


def test_request_contract_rejects_missing_idempotency_key() -> None:
    """Mutation schemas require an explicit idempotency key."""
    client = TestClient(app)
    response = client.post("/invoices/INV-001/clear", json={})
    assert response.status_code == 422


def test_duplicate_invoice_is_never_cleared() -> None:
    """Duplicate invoice evidence is a server-side clearance blocker."""
    case = make_case(2, "fault_injected", "duplicate_invoice")
    store.reset([case])
    client = TestClient(app)
    response = client.post(
        "/invoices/INV-002/clear", json={"idempotency_key": "duplicate"}
    )
    assert response.status_code == 409


def test_hold_request_is_idempotent_and_audited() -> None:
    """Repeated hold requests with one key do not duplicate transitions."""
    client = TestClient(app)
    body = {"idempotency_key": "hold-once", "reason": "Needs review"}
    assert client.post("/cases/SYN-001/hold", json=body).status_code == 200
    assert client.post("/cases/SYN-001/hold", json=body).status_code == 200
    audit = client.get("/cases/SYN-001/audit").json()
    holds = [item for item in audit["transitions"] if item["after"] == "held"]
    assert len(holds) == 1

