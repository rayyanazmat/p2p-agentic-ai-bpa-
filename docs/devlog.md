# Development Log

## 2026-11-12 — Remove expected-label access and refresh evidence

### Observation
The approval controller, policy checks, and compensation plan could read the manifest's expected terminal status. This exposed evaluation labels to the decision path. The saved named paper PDF was also a stale four-page export, and the checklist/status notes disagreed with the current experiment artifacts.

### Change made
- Removed expected-state-dependent approval and policy decisions; compensation checks now use observed invoice evidence.
- Stripped `expected_state` from the case passed to agents in both the standard evaluator and ablation runner. The evaluator still scores the final state against the label after the run.
- Reran E1–E6 and refreshed the evidence JSON, summary, and manuscript source with current measurements.
- Updated stale status and submission notes. Refreshed the source ZIP with the current LaTeX source and bibliography.

### Measured effect
- On the fixed 100-case manifests, exact-match, policy-alert, unsafe-mutation, and intervention rates remained unchanged; E5 still shows no aggregate effect from the approval toggle.
- Timing estimates changed between runs and are reported as local descriptive measurements only.
- The base-paper method remains unreproduced because it evaluates Declare-constraint translation, not P2P transaction execution.
- Tests were not rerun after these code edits. The existing PDF exports were not rebuilt because this environment has no LaTeX compiler or IEEEtran class installed.

## 2026-11-11 — Phase 2 work started

### Observation
The project already had a working local simulator, baseline agents, and policy safeguards. The gap was not functionality alone but reproducibility, benchmark reporting, and the formal evidence package required by the Phase 2 PDF.

### Change made
- Updated the to-do list to match the official Phase 2 assignment instructions.
- Added structured benchmark reporting utilities and a dataset summary command.
- Added a paper-ready outline and a reproducible experimental summary workflow.

### Measured effect
- The repository remains green under the project virtualenv.
- The project can now generate a dataset summary and a lightweight paper-style benchmark table.

## 2026-11-11 — Benchmark and reportability improvements

### Observation
The prototype had agent logic and safety checks, but it lacked a compact way to generate readable research output and reusable benchmark metadata.

### Change made
- Added `summarize_ablation_results` and `format_metric_table` to convert evaluation output into paper-ready tables.
- Added `summarize_case_manifest` for dataset counts and fault taxonomy summaries.
- Added a CLI summary hook for dataset and benchmark reporting.

### Measured effect
- Ablation results can now be read and copied into a research paper without manual post-processing.
- The dataset summary gives clear counts for categories and fault families.

## Upcoming iteration goals

- Add a formal experiment script that runs E1–E6 reproducibly and saves result files under `results/`.
- Expand the project narrative into the required conference-style paper sections.
- Convert the benchmark workflow into a concise, repeatable submission package.
