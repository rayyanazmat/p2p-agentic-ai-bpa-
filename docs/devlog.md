# Development Log

This log records the main Phase 2 implementation and evaluation iterations. Run-level evidence is stored separately in `results/`; representative agent traces are in `logs/`.

## 2026-11-11 — Evaluation and reporting workflow

### Observation

The repository had a local simulator and baseline controllers, but did not yet provide a compact way to run the required experiment families, summarize benchmark composition, or save reusable result artifacts.

### Changes

- Added result-formatting and ablation-summary helpers.
- Added synthetic-manifest summaries and CLI reporting commands.
- Added separate E1–E6 entry points and an aggregate runner that records each run under `results/`.
- Added representative trajectory export and a machine-readable evidence summary for the research report.

### Effect

The project can run a fixed 100-case synthetic suite and a separate 100-case BPI-derived replay, report the eight E5 configurations, and retain representative traces. The BPI case fields and expected outcomes are reconstructed proxy labels, not invoice ground truth.

## 2026-11-12 — Remove expected-label access and refresh evidence

### Observation

Approval scoring and policy/compensation checks had access to the manifest's expected terminal status. That let evaluation labels influence the decision path and weakened the interpretation of the approval ablation.

### Changes

- Removed expected-status-dependent rules from approval and policy decisions; compensation suggestions now depend on observed case evidence.
- Stripped `expected_state` from the case view passed to agents by both the standard evaluator and the ablation runner. The evaluator reads the label after execution to score the outcome.
- Reran E1–E6 and updated the compact result summary, evidence JSON, and paper source.
- Updated the repository README and ignored the verbose, regenerable E5 case-level trace.

### Effect

The fixed-fixture exact-match, risk-alert, unsafe-mutation, and intervention rates remained unchanged. E5 still showed no aggregate effect from the approval toggle. Local timing measurements varied between runs and are reported as descriptive figures only. The base-paper method remains unreproduced because its Declare-translation task differs from P2P transaction execution.

## Current evidence limits

- The saved experiment runs use a deterministic offline planner, not a hosted LLM evaluation.
- Simulator-side state guards remain active in every ablation condition, so the results do not isolate the policy layer's causal effect on unsafe completed transactions.
- No human reviewers participated; intervention rate is an automated signal, not a workload or effectiveness measure.
- E4 uses BPI-derived proxy labels and cannot establish accuracy against real invoice outcomes.
- The existing compiled `submission/paper.pdf` predates the latest LaTeX source edits and needs to be rebuilt.
