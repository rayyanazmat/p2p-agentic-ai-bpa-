"""Baseline 1: structured-output ReAct loop over the mock ERP API."""

from __future__ import annotations

import json
import time
from threading import Lock
import urllib.error
import urllib.request
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, ValidationError

from config import (
    AGENT_MAX_TURNS,
    API_BASE_URL,
    MODEL_CALL_BUDGET,
    MODEL_PROVIDER,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OLLAMA_NUM_CTX,
    OLLAMA_NUM_THREADS,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
    REQUEST_TIMEOUT_SECONDS,
)
from src.agents.state import AgentState
from src.orchestration.controller import ApprovalController
from src.policies.engine import PolicyEngine


class ToolError(Exception):
    """HTTP tool failure with status and detail preserved for the trace."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class Decision(BaseModel):
    """Strict action envelope returned by the planner backend."""

    model_config = ConfigDict(extra="forbid")

    action: str
    reason: str


class ToolClient:
    """Small standard-library HTTP client for simulator endpoints."""

    def __init__(self, base_url: str = API_BASE_URL) -> None:
        self.base_url = base_url.rstrip("/")

    def request(self, method: str, path: str, body: Any | None = None) -> Any:
        """Send JSON, retrying only reads and idempotency-keyed mutations."""
        payload = None if body is None else json.dumps(body).encode("utf-8")
        retryable = method == "GET" or bool(
            method == "POST"
            and isinstance(body, dict)
            and body.get("idempotency_key")
        )
        for attempt in range(3):
            request = urllib.request.Request(
                self.base_url + path,
                data=payload,
                method=method,
                headers={"Content-Type": "application/json"},
            )
            try:
                with urllib.request.urlopen(
                    request, timeout=REQUEST_TIMEOUT_SECONDS
                ) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                response_body = exc.read().decode("utf-8", errors="replace")
                if retryable and exc.code >= 500 and attempt < 2:
                    time.sleep(0.1 * (2**attempt))
                    continue
                try:
                    detail = json.loads(response_body).get("detail", response_body)
                except json.JSONDecodeError:
                    detail = response_body
                raise ToolError(exc.code, str(detail)) from exc
            except (urllib.error.URLError, TimeoutError) as exc:
                if retryable and attempt < 2:
                    time.sleep(0.1 * (2**attempt))
                    continue
                raise ToolError(503, str(exc)) from exc
        raise ToolError(503, "Request retry budget exhausted")

    def get_po(self, po_item_id: str) -> dict[str, Any]:
        """Read a PO item."""
        return self.request("GET", f"/purchase-orders/{po_item_id}")

    def get_invoice(self, invoice_id: str) -> dict[str, Any]:
        """Read an invoice."""
        return self.request("GET", f"/invoices/{invoice_id}")

    def get_receipts(self, po_item_id: str) -> dict[str, Any]:
        """Read receipt evidence."""
        return self.request("GET", f"/goods-receipts/{po_item_id}")

    def verify_receipts(self, po_item_id: str, key: str) -> dict[str, Any]:
        """Verify receipt evidence using an idempotency key."""
        return self.request(
            "POST",
            f"/goods-receipts/{po_item_id}/verify",
            {"idempotency_key": key},
        )

    def clear_invoice(self, invoice_id: str, key: str) -> dict[str, Any]:
        """Simulate invoice clearing using an idempotency key."""
        return self.request(
            "POST", f"/invoices/{invoice_id}/clear", {"idempotency_key": key}
        )

    def hold_case(self, case_id: str, reason: str) -> dict[str, Any]:
        """Place a case on hold for manual review."""
        return self.request(
            "POST",
            f"/cases/{case_id}/hold",
            {"idempotency_key": f"{case_id}-hold", "reason": reason},
        )

    def audit(self, case_id: str) -> dict[str, Any]:
        """Read the audit trail."""
        return self.request("GET", f"/cases/{case_id}/audit")

    def reset(self, cases: list[dict[str, Any]]) -> dict[str, Any]:
        """Seed or reset local simulator state."""
        return self.request("POST", "/admin/reset", cases)

    def case_state(self, case_id: str) -> dict[str, Any]:
        """Read simulator state for evaluation only."""
        return self.request("GET", f"/admin/cases/{case_id}")


class DecisionBackend(Protocol):
    """Interface for an action planner returning a constrained JSON object."""

    name: str

    def decide(self, context: dict[str, Any]) -> tuple[Decision, int, int]:
        """Return validated decision and input/output token estimates."""


class OfflineBackend:
    """Deterministic offline planner used when no provider key is configured."""

    name = "offline-scripted-react"

    def decide(self, context: dict[str, Any]) -> tuple[Decision, int, int]:
        """Choose the next action from simulator observations."""
        po = context["purchase_order"]
        invoice = context["invoice"]
        receipts = context["goods_receipts"]
        verified_qty = receipts["verified_quantity"]
        total_qty = sum(item["quantity"] for item in receipts["receipt_events"])
        if invoice["status"] == "cleared":
            action, reason = "done", "Invoice is already cleared"
        elif (
            not invoice["verified"]
            or invoice["duplicate_invoice"]
            or invoice["amount"] != po["amount"]
        ):
            action, reason = "hold", "Invoice evidence is incomplete or inconsistent"
        elif po["matching_type"] in {"three_way", "consignment"}:
            if total_qty < po["quantity"]:
                action, reason = "hold", "Required receipt quantity is incomplete"
            elif verified_qty < po["quantity"]:
                action, reason = (
                    "verify_receipts",
                    "Complete receipt needs verification",
                )
            else:
                action, reason = "clear", "Matching evidence is complete"
        else:
            action, reason = "clear", "Two-way invoice and PO amounts match"
        raw = json.dumps(context, sort_keys=True)
        return Decision(action=action, reason=reason), len(raw) // 4, 16


class OpenAICompatibleBackend:
    """OpenAI-compatible hosted or local model backend with structured output."""

    name = "openai-compatible"

    def __init__(self) -> None:
        from openai import OpenAI

        if MODEL_PROVIDER == "ollama":
            self.name = "ollama-local"
            self.model = OLLAMA_MODEL
            kwargs: dict[str, Any] = {
                "api_key": "ollama",
                "base_url": OLLAMA_BASE_URL,
            }
        else:
            if not OPENAI_API_KEY:
                raise RuntimeError(
                    "OPENAI_API_KEY is required for an OpenAI-compatible provider"
                )
            self.model = OPENAI_MODEL
            kwargs = {"api_key": OPENAI_API_KEY}
            if OPENAI_BASE_URL:
                kwargs["base_url"] = OPENAI_BASE_URL
        self.client = OpenAI(**kwargs)

    def decide(self, context: dict[str, Any]) -> tuple[Decision, int, int]:
        """Ask the configured model for one allowed action and parse JSON."""
        system = (
            "You are a tool-using P2P workflow baseline. Inspect the supplied state. "
            "Return only JSON with keys action and reason. action must be one of "
            "verify_receipts, clear, hold, done. Hold if invoice is unverified, "
            "duplicate, amount differs, or required receipt is incomplete. Verify "
            "complete unverified receipts before clearing. Do not claim a tool ran."
        )
        _reserve_model_call()
        if MODEL_PROVIDER == "ollama":
            # Use Ollama's native endpoint: its OpenAI-compatible endpoint can
            # return Qwen's reasoning channel separately from message.content.
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": json.dumps(context, sort_keys=True)},
                ],
                "format": "json",
                "stream": False,
                "think": False,
                "keep_alive": 0,
                "options": {
                    "num_ctx": OLLAMA_NUM_CTX,
                    "num_thread": OLLAMA_NUM_THREADS,
                    "num_predict": 128,
                    "temperature": 0,
                },
            }
            api_url = OLLAMA_BASE_URL.removesuffix("/v1") + "/api/chat"
            request = urllib.request.Request(
                api_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(
                request, timeout=REQUEST_TIMEOUT_SECONDS * 12
            ) as http_response:
                local_response = json.loads(http_response.read().decode("utf-8"))
            content = local_response.get("message", {}).get("content") or "{}"
            try:
                decision = Decision.model_validate_json(content)
            except (ValidationError, ValueError) as exc:
                raise ValueError(
                    f"Model returned invalid structured action: {content}"
                ) from exc
            return (
                decision,
                int(local_response.get("prompt_eval_count", 0) or 0),
                int(local_response.get("eval_count", 0) or 0),
            )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(context, sort_keys=True)},
            ],
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=128,
        )
        content = response.choices[0].message.content or "{}"
        try:
            decision = Decision.model_validate_json(content)
        except (ValidationError, ValueError) as exc:
            raise ValueError(
                f"Model returned invalid structured action: {content}"
            ) from exc
        usage = response.usage
        return (
            decision,
            int(getattr(usage, "prompt_tokens", 0) or 0),
            int(getattr(usage, "completion_tokens", 0) or 0),
        )


def configured_backend() -> DecisionBackend:
    """Select the explicitly configured model; default to the offline baseline."""
    if MODEL_PROVIDER == "ollama":
        return OpenAICompatibleBackend()
    if MODEL_PROVIDER in {"openai", "openai-compatible"} and OPENAI_API_KEY:
        return OpenAICompatibleBackend()
    return OfflineBackend()


_model_call_lock = Lock()
_model_calls_used = 0


def _reserve_model_call() -> None:
    """Enforce one process-wide model-call cap for the complete experiment."""
    global _model_calls_used
    with _model_call_lock:
        if _model_calls_used >= MODEL_CALL_BUDGET:
            raise RuntimeError(
                f"Model-call budget exhausted ({MODEL_CALL_BUDGET} calls)"
            )
        _model_calls_used += 1


class ReActAgent:
    """Bounded ReAct loop using structured actions and simulator observations."""

    def __init__(
        self,
        client: ToolClient,
        backend: DecisionBackend | None = None,
        max_turns: int = AGENT_MAX_TURNS,
        policy_enabled: bool = True,
        approval_enabled: bool = True,
    ) -> None:
        self.client = client
        self.backend = backend or configured_backend()
        self.max_turns = max_turns
        self.policy_enabled = policy_enabled
        self.approval_enabled = approval_enabled

    def run(self, case: dict[str, Any]) -> dict[str, Any]:
        """Run one procurement case and return a reproducible trace summary."""
        policy_report = PolicyEngine.evaluate(case) if self.policy_enabled else None
        approval = ApprovalController.decide(case) if self.approval_enabled else None
        state = AgentState(
            case_id=case["case_id"],
            po_item_id=case["po_item_id"],
            invoice_id=case["invoice_id"],
        )
        if policy_report is not None:
            state.policy_violations = [item.rule for item in policy_report.violations]
        if approval is not None and approval.decision != "approve":
            state.intervention_required = True
        state_dict: dict[str, Any] = {}
        initial_reads = (
            ("get_purchase_order", "purchase_order", case["po_item_id"]),
            ("get_invoice", "invoice", case["invoice_id"]),
            ("get_goods_receipts", "goods_receipts", case["po_item_id"]),
        )
        for tool_name, state_key, identifier in initial_reads:
            try:
                if tool_name == "get_purchase_order":
                    result = self.client.get_po(identifier)
                elif tool_name == "get_invoice":
                    result = self.client.get_invoice(identifier)
                else:
                    result = self.client.get_receipts(identifier)
                state_dict[state_key] = result
                state.observations.append({"tool": tool_name, "result": result})
            except ToolError as exc:
                state.policy_violations.append(f"{tool_name}: {exc.detail}")
                return self._finish(state, "failed", self.backend.name)
        state.phase = "evidence_retrieved"

        for turn in range(self.max_turns):
            try:
                decision, input_tokens, output_tokens = self.backend.decide(state_dict)
            except Exception as exc:  # Provider and parse failures fail closed.
                state.policy_violations.append(
                    f"Planner failed closed ({type(exc).__name__})"
                )
                self.client.hold_case(
                    case["case_id"], "Planner output unavailable or invalid"
                )
                state.phase = "held"
                state.intervention_required = True
                return self._finish(state, "held", self.backend.name)
            state.estimated_input_tokens += input_tokens
            state.estimated_output_tokens += output_tokens
            action = decision.action
            if action not in {"verify_receipts", "clear", "hold", "done"}:
                state.policy_violations.append(f"Invalid model action: {action}")
                action = "hold"
            state.actions.append(
                {"turn": turn + 1, "action": action, "reason": decision.reason}
            )
            try:
                if action == "verify_receipts":
                    self.client.verify_receipts(
                        case["po_item_id"], f"{case['case_id']}-verify"
                    )
                    state.phase = "receipt_verified"
                    state_dict["goods_receipts"] = self.client.get_receipts(
                        case["po_item_id"]
                    )
                    state_dict["invoice"] = self.client.get_invoice(case["invoice_id"])
                    continue
                if action == "clear":
                    self.client.clear_invoice(
                        case["invoice_id"], f"{case['case_id']}-clear"
                    )
                    state.phase = "cleared"
                    return self._finish(state, "cleared", self.backend.name)
                if action == "hold":
                    self.client.hold_case(case["case_id"], decision.reason)
                    state.phase = "held"
                    state.intervention_required = True
                    return self._finish(state, "held", self.backend.name)
                if action == "done":
                    if state_dict["invoice"]["status"] in {"cleared", "held"}:
                        return self._finish(
                            state, state_dict["invoice"]["status"], self.backend.name
                        )
                    state.policy_violations.append(
                        "Planner selected done while invoice remained open"
                    )
                    self.client.hold_case(
                        case["case_id"], "Invalid done action from planner"
                    )
                    state.phase = "held"
                    state.intervention_required = True
                    return self._finish(state, "held", self.backend.name)
            except ToolError as exc:
                state.policy_violations.append(f"{action}: {exc.detail}")
                state.observations.append(
                    {
                        "tool_error": action,
                        "status_code": exc.status_code,
                        "detail": exc.detail,
                    }
                )
                if action == "verify_receipts":
                    # A timed-out idempotent request may have succeeded server-side.
                    try:
                        state_dict["goods_receipts"] = self.client.get_receipts(
                            case["po_item_id"]
                        )
                        if (
                            state_dict["goods_receipts"]["verified_quantity"]
                            >= state_dict["purchase_order"]["quantity"]
                        ):
                            continue
                    except ToolError:
                        pass
                    self.client.hold_case(case["case_id"], exc.detail)
                    state.phase = "held"
                    state.intervention_required = True
                    return self._finish(state, "held", self.backend.name)
                if action == "clear":
                    # Reconcile after a lost response before issuing a hold.
                    try:
                        state_dict["invoice"] = self.client.get_invoice(
                            case["invoice_id"]
                        )
                        if state_dict["invoice"]["status"] == "cleared":
                            state.phase = "cleared"
                            return self._finish(state, "cleared", self.backend.name)
                    except ToolError:
                        pass
                # A rejected mutation is held rather than retried blindly.
                self.client.hold_case(case["case_id"], exc.detail)
                state.phase = "held"
                state.intervention_required = True
                return self._finish(state, "held", self.backend.name)
        self.client.hold_case(case["case_id"], "Maximum planner turns reached")
        state.phase = "held"
        state.intervention_required = True
        return self._finish(state, "held", self.backend.name)

    @staticmethod
    def _finish(
        state: AgentState, outcome: str, backend_name: str
    ) -> dict[str, Any]:
        """Serialize the final trace summary."""
        return {
            "case_id": state.case_id,
            "outcome": outcome,
            "backend": backend_name,
            "actions": state.actions,
            "policy_violations": state.policy_violations,
            "intervention_required": state.intervention_required,
            "input_tokens": state.estimated_input_tokens,
            "output_tokens": state.estimated_output_tokens,
            "agent_state": state.model_dump(mode="json"),
        }

