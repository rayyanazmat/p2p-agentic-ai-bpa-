# Policy-Grounded Agentic AI for Safe Purchase-to-Pay Automation

**Project code:** AI4015-P2P-01  
**Phase 1 repository:** Deliverable C — Technical Foundation and Working Baseline

## Abstract

This repository implements a deterministic mock procurement API and two initial purchase-to-pay (P2P) baselines: a structured-output ReAct loop and a fixed heuristic workflow. It includes a synthetic fixture, a streaming BPI Challenge 2019 XES profiler/replay-manifest builder, idempotent mutation contracts, audit records, and case-level evaluation metrics. The planned research direction extends Fionda *et al.*'s Declare semantic-validation work [1] with policy-aware simulated ERP actions. The checked-in `data/test_manifest_100.json` is synthetic; the locally generated BPI replay fixture is based on observed traces but reconstructs transaction values and proxy outcomes. Neither should be presented as a source-labeled transaction ground-truth benchmark.

The selected primary source is BPI Challenge 2019 from 4TU.ResearchData [2]. The IEEE-XES archive and expanded log are present locally under `data/raw/` and excluded from Git. The archive passed gzip integrity and its expanded file matched the publisher's MD5. The streamed profile under `data/processed/bpi_profile.json` reconciles 251,734 traces, 1,595,923 events, 42 activity labels, and 627 resources. Keep the source citation and CC BY 4.0 notice with any redistribution; do not add the large raw log to the repository without checking repository/course policy.

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

A local Ollama backend is available for memory-limited experiments. The verified one-case demonstration used `qwen3.5:0.8b`, 2,048-token context, two CPU threads, and Ollama's native JSON chat endpoint with thinking disabled. It returned a valid action but selected receipt verification for a two-way case; the simulator rejected that action and held the case. This proves the model-to-tool path and fail-closed behavior, not task accuracy. The 9B model is not recommended on memory-constrained machines.

```bash
export P2P_MODEL_PROVIDER=ollama
export OLLAMA_MODEL=qwen3.5:0.8b
export OLLAMA_NUM_CTX=2048
export OLLAMA_NUM_THREADS=2
export P2P_MODEL_CALL_BUDGET=10
python main.py --run-baseline --cases 1
```

Ollama must already be running. Local inference requires model weights and runtime memory on the machine; stop if the system becomes unstable. Local inference is reported at zero API charge, with token counts and latency recorded.

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

`src/pipeline/loader.py` parses XES traces and event CSV files; `src/pipeline/bpi.py` streams the BPI log and generates a separate PO-document-disjoint manifest with 25 cases per matching category. It restricts candidates to simple traces (at most one invoice receipt, goods receipt, and clear event) with events in 2018. The BPI log contains no invoice IDs, invoice-level amounts, unit quantities, or approval decisions. Those simulator fields are reconstructed and marked synthetic. `Clear Invoice` is an observed trace activity; when it is absent, `held` is assigned as a conservative replay target, not as ground-truth rejection. The separate `data/test_manifest_100.json` uses a fixed seed (`2019`) and has 80 ordinary synthetic cases plus 20 fault-injected synthetic cases.

Build/profile the trace-derived replay fixture:

```bash
python main.py --build-bpi-fixture
python main.py --run-bpi-baseline --cases 100
```

The BPI manifest has already been used for a baseline smoke run. Do not continue to call it an untouched holdout; reserve a new PO-document-disjoint subset for confirmatory testing and record its manifest hash before tuning.

The **synthetic** fixture tests code paths only. It is not drawn from BPI Challenge 2019 and does not support claims about real business frequencies or real-log generalization. For the BPI replay manifest, the checked-in `src/pipeline/bpi.py` parser was run against the locally acquired XES. The manifest is trace-derived but not transaction-level ground truth: reconstructed fields and conservative hold labels limit conclusions. Split by parent PO document to prevent item-level leakage.

### Initial functional run

On 20 October 2026, both baselines completed the synthetic 100-case fixture with 100% end-state exact match, 0% rejected-policy-action rate, 0% unsafe mutation rate, and 40% intervention rate. The ReAct run used `offline-scripted-react`; it did not call a language model. These outcomes verify fixture wiring and expected API behavior only. The synthetic cases and their oracle are generated from the same simple rules as the heuristic, so these results are not independent evidence of policy quality or research performance. The complete per-case results and tool histories are saved in `data/processed/baseline_run.json` after running the documented command.

On 21 October 2026, the offline baselines were also run on 100 BPI trace-derived replay cases. Both matched the generated replay targets on all cases with zero recorded policy violations and unsafe mutations; the intervention rate was 55% for each. This is a pipeline/simulator smoke test only: reconstructed transaction data and conservative `held` proxy labels make these figures unsuitable as claims about real invoice-level accuracy. A separate one-case Qwen 3.5 0.8B run selected a receipt-verification action on a two-way case; the simulator rejected it and safely held the case. Its log is `data/processed/ollama_08b_single_case_demo.json`.

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

- The proposed Declare retrieval, ASP/LTL validator, risk-based human-approval orchestration, and compensating-action workflow are not yet implemented; the current repository is the Deliverable C technical foundation with two baselines.
- The checked-in synthetic oracle is intentionally simple and must not be presented as a validated procurement policy or production behavior.
- Hosted model evaluation still requires provider credentials. The one-case local Qwen smoke test is not a comparative experiment and exposed a wrong action from a small model; the offline backend does not count as an LLM experiment.
- The simulator records approval decisions but the initial baselines do not implement the proposed risk-based approval policy, Declare retrieval, ASP/LTL validation, or compensating-action workflow. Those are the next system increments.
- The current store is in-memory; state resets when the service exits. SQLite persistence and concurrent stress evaluation remain future implementation tasks.

## References

[1] V. Fionda, A. Ielo, and F. Ricca, “Are Large Language Models Fluent in Declarative Process Mining?,” in *Proc. 34th Int. Joint Conf. Artificial Intelligence (IJCAI)*, 2025, pp. 4500–4508, doi: 10.24963/ijcai.2025/501.

[2] B. F. van Dongen, “BPI Challenge 2019,” 4TU.ResearchData, 2019, doi: 10.4121/uuid:d06aff4b-79f0-45e6-8ec8-e19730c248f1. [Online]. Available: https://doi.org/10.4121/uuid:d06aff4b-79f0-45e6-8ec8-e19730c248f1. License: CC BY 4.0.
