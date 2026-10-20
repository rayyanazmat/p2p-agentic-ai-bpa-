# Policy-Grounded Agentic AI for Safe Purchase-to-Pay Automation

**Project code:** AI4015-P2P-01  
**Phase 1 repository:** Deliverable C — Technical Foundation and Working Baseline

## Abstract

This repository implements a deterministic mock procurement API and two initial purchase-to-pay (P2P) baselines: a structured-output ReAct loop and a fixed heuristic workflow. It includes synthetic P2P scenarios, an event-log XES/CSV loader, idempotent mutation contracts, audit records, and case-level evaluation metrics. The planned research direction extends Fionda *et al.*'s Declare semantic-validation work [1] with policy-aware simulated ERP actions. The checked-in 100-case fixture is synthetic and reproducible; it is **not** the BPI Challenge 2019 log and must not be cited as empirical BPI data.

The selected primary source is BPI Challenge 2019 from 4TU.ResearchData [2]. Its raw log is not included because it must be acquired and licensed from its source. Once downloaded, record its version, checksum, acquisition date, and license metadata under `data/raw/` before deriving held-out cases.

## Repository structure

```text
p2p_agentic_ai/
├── README.md
├── requirements.txt
├── config.py
├── data/
│   ├── raw/                 # User-acquired BPI Challenge 2019 files; gitignored
│   ├── processed/           # Generated metrics and derived splits
│   └── test_manifest_100.json
├── src/
│   ├── simulator/           # FastAPI mock ERP and in-memory store
│   ├── pipeline/            # XES/CSV loader and synthetic fixture generator
│   ├── agents/              # ReAct and deterministic heuristic baselines
│   └── evaluation/          # Metric definitions and evaluation harness
├── tests/
└── main.py
```

## Quickstart

Use Python 3.10 or later. From this directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Generate the deterministic synthetic fixture (also created automatically if absent):

```bash
python main.py --generate-manifest
```

Run a local API service in one terminal:

```bash
uvicorn src.simulator.app:app --host 127.0.0.1 --port 8000
```

Or run the demo in another terminal; it starts and stops a local service automatically when one is not already listening:

```bash
python main.py --run-baseline
```

The default demo selects a small balanced sample across normal and fault-injected cases. Run the full synthetic 100-case fixture with:

```bash
python main.py --run-baseline --cases 100
```

Metrics and full tool/audit traces are written to `data/processed/baseline_run.json`. The CLI prints a compact per-system and per-case summary. To run the tests:

```bash
pytest -q
```

## Model/provider setup

The ReAct architecture has a custom bounded reasoning/action/observation loop and strict JSON decision parsing. With no credentials, it uses `OfflineBackend`, a deterministic scripted planner, so the mock workflow and end-to-end evaluation run without a network provider. This offline backend is **not an LLM result** and must be reported as a deterministic functional baseline.

To enable the optional OpenAI-compatible model backend, install the declared `openai` dependency and set environment variables in your shell (never commit secrets):

```bash
export OPENAI_API_KEY="your-key"
export OPENAI_MODEL="gpt-4o-mini"
# Optional for an OpenAI-compatible gateway:
export OPENAI_BASE_URL="https://provider.example/v1"
python main.py --run-baseline --cases 5
```

Hosted calls use JSON-object mode and the response is validated against the `Decision` Pydantic model. The simulator still enforces its own preconditions; model output never bypasses the tool service. Configure the provider's account-side spending quota before making hosted calls. Record the provider, exact model identifier, date, token usage, and applicable rates with experimental results. If using local inference instead, adapt `DecisionBackend` and record the model/runtime details.

For a computed API cost estimate, set `OPENAI_INPUT_USD_PER_MILLION` and `OPENAI_OUTPUT_USD_PER_MILLION` to the dated rates applicable to the selected model. Hosted cost is reported as `null` when rates are not provided; offline execution reports zero model charge.

## Data pipeline and test fixture

`src/pipeline/loader.py` parses basic XES traces and event CSV files, grouping activities under case IDs. It also generates `data/test_manifest_100.json` with a fixed seed (`2019`): 80 ordinary synthetic cases divided among two-way, three-way complete, three-way missing-receipt, and consignment categories, plus 20 fault-injected cases. Each manifest record includes mock PO/invoice/receipt state, fault metadata, and an expected terminal invoice status.

The fixture tests code paths only. It is not drawn from BPI Challenge 2019 and does not support claims about real business frequencies or real-log generalization. To process the source log, place the acquired XES/CSV in `data/raw/` and call `load_event_log(Path(...))` from a project script. Define and independently review scenario labels/oracle rules before producing any BPI-derived evaluation manifest. Split by parent PO document to prevent item-level leakage.

### Initial functional run

On 20 October 2026, both baselines completed the synthetic 100-case fixture with 100% end-state exact match, 0% rejected-policy-action rate, 0% unsafe mutation rate, and 40% intervention rate. The ReAct run used `offline-scripted-react`; it did not call a language model. These outcomes verify fixture wiring and expected API behavior only. The synthetic cases and their oracle are generated from the same simple rules as the heuristic, so these results are not independent evidence of policy quality or research performance. The complete per-case results and tool histories are saved in `data/processed/baseline_run.json` after running the documented command.

## Architecture and tool contracts

The simulator is a deterministic FastAPI application with Pydantic input/output models and an in-memory, thread-safe store. It models no live ERP and sends no payment. The admin reset and state-read endpoints exist solely to seed and score local experiments. By default, the CLI binds its service to `127.0.0.1`.

| Method and route | Contract behavior |
| :--- | :--- |
| `GET /purchase-orders/{po_item_id}` | Read PO quantity, amount, currency, matching type, and status. |
| `GET /invoices/{invoice_id}` | Read invoice amount, verification, duplicate marker, and clearing status. |
| `GET /goods-receipts/{po_item_id}` | Read receipt events and verified quantity. |
| `POST /goods-receipts/{po_item_id}/verify` | Verify complete receipt evidence; requires `idempotency_key`. |
| `POST /invoices/{invoice_id}/clear` | Simulate clearing after server-side invoice, amount, duplicate, and receipt checks; requires `idempotency_key`. |
| `POST /cases/{case_id}/approval` | Record approve/reject decision, rationale, and evidence reference. |
| `GET /cases/{case_id}/audit` | Return tool-call and state-transition history. |
| `POST /cases/{case_id}/hold` | Additional local action to safely route unresolved cases for review; requires an idempotency key and reason. |
| `POST /admin/reset`, `GET /admin/cases/{case_id}` | Local test harness endpoints; seed and read case state/oracle. Do not expose beyond localhost. |

The two baselines use the same HTTP tools and seeded state. Baseline 1 uses a ReAct loop with a hosted structured-output backend when configured, otherwise the explicitly labeled offline planner. Baseline 2 uses fixed branches with no LLM planning. Both produce server audit traces. The evaluator reports end-state exact match, policy-violation rate, unsafe-mutation rate, intervention rate, token use/cost field, p95 latency, mean latency, and calls per case. The current in-memory implementation blocks policy-invalid mutations; unsafe mutation rate should therefore remain zero unless a defect is found. Policy-violation rate includes rejected attempts and agent-recorded policy failures.

## GitHub and supervisor access

This workspace does not create a remote repository or change GitHub permissions. To share the implementation with the course supervisor:

1. Create a private GitHub repository under the group owner account and push this directory using the course-approved account.
2. Add the supervisor as a collaborator with repository read access (or use the public repository option if the group approves public release).
3. Confirm access while signed out or with a supervisor-provided account, then submit the repository URL with the Phase 1 submission.
4. Keep API credentials, downloaded data subject to license restrictions, `.env` files, and generated sensitive outputs out of commits. Commit the synthetic fixture and code; document any excluded data and acquisition instructions.

Suggested initial commands after repository creation:

```bash
git init
git add README.md requirements.txt config.py src tests main.py data/test_manifest_100.json
git commit -m "Add P2P simulator and baseline evaluation"
git branch -M main
git remote add origin <group-repository-url>
git push -u origin main
```

Make meaningful commits under each contributor's own account; a single generated commit does not demonstrate the course's requested contribution history.

## Limitations and next implementation steps

- BPI Challenge 2019 has not been downloaded or parsed in this repository yet.
- The checked-in synthetic oracle is intentionally simple and must not be presented as a validated procurement policy or production behavior.
- Hosted model integration is optional and cannot run without provider credentials; the default offline backend does not count as an LLM experiment.
- The simulator records approval decisions but the initial baselines do not implement the proposed risk-based approval policy, Declare retrieval, ASP/LTL validation, or compensating-action workflow. Those are the next system increments.
- The current store is in-memory; state resets when the service exits. SQLite persistence and concurrent stress evaluation remain future implementation tasks.

## References

[1] V. Fionda, A. Ielo, and F. Ricca, “Are Large Language Models Fluent in Declarative Process Mining?,” in *Proc. 34th Int. Joint Conf. Artificial Intelligence (IJCAI)*, 2025, pp. 4500–4508, doi: 10.24963/ijcai.2025/501.

[2] B. F. van Dongen, “BPI Challenge 2019,” 4TU.ResearchData, 2019, doi: 10.4121/uuid:d06aff4b-79f0-45e6-8ec8-e19730c248f1. [Online]. Available: https://doi.org/10.4121/uuid:d06aff4b-79f0-45e6-8ec8-e19730c248f1. License: CC BY 4.0.
