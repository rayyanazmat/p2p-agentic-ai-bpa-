# Phase 2 To-Do Plan (Aligned to AI4015 Phase 2 PDF)

Project: Policy-Grounded Agentic AI for Safe Purchase-to-Pay Automation  
Repository: `phase1/p2p_agentic_ai`

## 1. Phase 2 objective

This phase is the main implementation and evaluation stage of the semester project. We must convert the Phase 1 baseline into a complete agentic system, evaluate it scientifically against the base paper, and present the results as a conference-style research paper.

The core question we must answer with evidence is:

- For each selected research gap, did our system improve on the base paper?
- By how much?
- Why?

Everything in the codebase, logs, evaluation, and paper should help answer this with evidence.

## 2. Mandatory starting point: Phase 1 feedback

- [x] Address all feedback from the supervisor on Phase 1 before continuing.
- [x] Treat the base paper and selected research gaps as fixed after Phase 1.
- [x] If we change the design (model, tool, dataset split, etc.), record it in a short section titled `Changes since Phase 1` in the README.
- [x] Keep written justification for any change in the repository docs.

## 2.1 Current status snapshot

The repository contains a working local simulator, policy engine, approval/orchestration layer, safeguards, benchmark runner, and an 8-page paper draft (`submission/paper.tex`). E1–E6 were rerun on 2026-11-12 after removing expected-label access from decision-making. Current evidence is under `results/`; see `docs/final_submission_checklist.md` for remaining work. The required like-for-like base-paper experiment remains incomplete.

Key evidence from the current repository run:

- exact match remains 1.00 against the fixed synthetic fixture labels;
- policy-aware variants surface risk alerts, while E1's disabled detector reports no alerts by definition;
- BPI-derived results remain agreement with reconstructed proxy labels, not invoice ground truth;
- no base-paper reproduction, group review, Turnitin reports, or final course upload is recorded.

## 3. Deliverable A: Final Source Code

### 3.1 Complete agentic system

The final system must be a real agentic pipeline, not a set of isolated components. It must include:

- [ ] end-to-end pipeline running on the chosen data/environment/benchmark
- [ ] gap-specific component, module, or method for each selected research gap
- [ ] meaningful interaction with tools, APIs, simulators, or environment interfaces
- [ ] observable agent trajectories showing reasoning, tool calls, inputs/outputs, and state transitions
- [ ] robustness: failure handling, retries, verification, recovery, or human-control mechanisms
- [ ] iterative improvement evidence: what failed, what changed, and the measured effect

### 3.2 Development log

- [ ] Maintain a short development log in `docs/devlog.md` (or equivalent)
- [ ] For each major iteration, record: date, failure/limitation, change made, measured effect
- [ ] Use the log as supporting evidence in the failure analysis section of the paper

### 3.3 Repository requirements

The repository must allow the supervisor to install, run, and reproduce the main results.

- [ ] Well-organized, modular, and documented code.
- [ ] README with overview, architecture diagram, installation steps, configuration and env vars, reproduction commands, and gap-resolution table.
- [ ] Scripts or commands that reproduce each experiment (E1–E6) and save results to files (`results/*.csv`, `results/*.json`, etc.).
- [ ] Agent traces, logs, or observability outputs for the reported runs, or a representative sample if logs are large.
- [ ] Usable application interface (CLI, web UI, or API) or a reproducible execution workflow.
- [ ] Tests for important deterministic components.
- [ ] Dependency file (`requirements.txt`, `pyproject.toml`, or `Dockerfile`) and `.env.example`.
- [ ] Never commit API keys or secrets.
- [ ] Keep meaningful commit history from all group members throughout Phase 2.
- [ ] Create a GitHub release/tag named `phase2-final` before deadline; only code in this release will be evaluated.

Suggested structure:

- `src/` — agents, tools, state, orchestration, gap-specific components
- `data/` — data loaders and split definitions or scripts
- `experiments/` — configs and scripts for E1–E6
- `results/` — saved results, tables, and figures
- `logs/` — agent trajectories and run logs
- `tests/` — deterministic component tests
- `docs/` — devlog, architecture diagram, and additional documentation
- `README.md` — overview, setup, reproduction, and gap-resolution table

## 4. Experimental evaluation (must happen during development, not only at the end)

We must run experiments during implementation, not just at the final stage.

### 4.1 Experimental setup

- [ ] Use fixed data splits; do not tune on the test set.
- [ ] Keep a separate development/validation split for prompt tuning and threshold selection.
- [ ] Record model names and versions, decoding settings, prompts, and random seeds.
- [ ] For stochastic systems, run each main configuration at least 3 times and report mean and standard deviation.
- [ ] Compare against the base paper on the same data and metrics.
- [ ] State clearly whether base-paper numbers were reproduced by us or taken from the paper.
- [ ] Use an evaluation set large enough to support conclusions; avoid hand-picked examples only.

### 4.2 Required experiments

- [ ] E1: Baseline — performance of simpler or non-agentic baseline from Phase 1
- [ ] E2: Base paper — performance of base paper approach on our data and metrics
- [ ] E3: Proposed system — performance of complete agentic system on the same evaluation set
- [ ] E4: Gap-wise experiments — at least one experiment per selected gap
- [ ] E5: Ablation study — remove each gap-specific component one at a time to show contribution
- [ ] E6: Efficiency & reliability — cost, latency, token/tool-call usage, safety/reliability metrics

For each experiment:

- [ ] record exact setup and command
- [ ] save results as JSON/CSV under `results/`
- [ ] generate reproducible summary tables and figures
- [ ] note conditions, seeds, and environment used

### 4.3 Failure analysis

- [ ] Collect failure cases from the final system on the evaluation set.
- [ ] Group failures into a small set of failure categories.
- [ ] Report how often each category occurs.
- [ ] Include at least two representative success cases and two failure cases with agent trajectories.
- [ ] For each major failure category, explain likely cause and future work to address it.

### 4.4 Gap-resolution table

This table must appear in both the README and the research paper.

| Gap | Method / component | Metric | Base paper result | Our result | Addressed? (Fully / Partially / Not) |
|---|---|---|---|---|---|
| Gap 1 | ... | ... | ... | ... | ... |
| Gap 2 | ... | ... | ... | ... | ... |
| ... | ... | ... | ... | ... | ... |

- [ ] Add the table to `README.md`
- [ ] Add the table to the paper
- [ ] Report negative or partial results honestly; do not hide failures

## 5. Deliverable B: Conference-style research paper

The paper must be written as a mini conference paper, not as a traditional course report.

### 5.1 Format requirements

- [ ] 8–10 pages including references, in two-column IEEEtran or ACM format
- [ ] Title page includes paper title, project code, names, roll numbers, and email addresses of all group members
- [ ] All figures and tables numbered, captioned, readable, and referred to in the text
- [ ] At least 25–30 references
- [ ] Every reference includes DOI link or official URL
- [ ] References follow the required style and are all cited in the text

### 5.2 Required sections

- [ ] Abstract (150–250 words): problem, approach, main quantitative results, contribution
- [ ] Introduction: motivation, research gaps, research question, list of contributions
- [ ] Related Work: synthesis of the Phase 1 literature review; position against base paper and other work
- [ ] Problem Formulation: formal description of task, constraints, and objective
- [ ] Methodology: architecture, modules, algorithm, gap-resolution strategy, design choices
- [ ] Experimental Setup: dataset, metrics, models, seeds, splits, baselines, evaluation protocol
- [ ] Results: quantitative outcomes, tables, figures, comparisons, ablations
- [ ] Failure Analysis: categories, rates, representative cases, and explanations
- [ ] Discussion: implications, limitations, scope, trade-offs, ethical or operational context
- [ ] Conclusion: summary and future work
- [ ] References

## 6. Module-by-module work plan for Phase 2

### Module 1: Project setup and environment hardening

Scope:
- finalize environment and dependency lock
- maintain reproducible local setup
- ensure scripts and CLI run reliably

Work items:
- [ ] centralize configuration in `config.py`
- [ ] enforce `.venv` usage and document setup steps
- [ ] document required providers and fallback behavior
- [ ] enforce hosted-model budget and safe failures
- [ ] verify simulator startup and smoke-test path

Acceptance criteria:
- project runs cleanly from a fresh environment
- no secrets committed
- model provider selection is explicit and safe

Testing:
- [ ] config parsing and invalid-provider handling
- [ ] simulator health-check startup test
- [ ] regression check with full suite

### Module 2: Agentic system core and pipeline integration

Scope:
- complete the end-to-end system pipeline
- ensure meaningful agent interaction with environment and tools

Work items:
- [ ] integrate all components into a single executable workflow
- [ ] define clear tool usage patterns and state transitions
- [ ] log trajectories and intermediate decisions
- [ ] connect evaluation and benchmarking to the main pipeline

Acceptance criteria:
- pipeline runs from data input to final result without manual assembly
- tool traces are observable and auditable
- system behavior is reproducible

Testing:
- [ ] end-to-end CLI test
- [ ] deterministic pipeline test
- [ ] integration test for tool traces

### Module 3: Gap-specific methods and ablation components

Scope:
- each selected research gap must have a real, switchable method or module
- measure contribution with ablations

Work items:
- [ ] identify each gap and its corresponding module/component
- [ ] implement the method to address the gap
- [ ] make it configurable and toggleable for ablation
- [ ] define evaluation metric tied to the gap hypothesis
- [ ] compare against the base paper and baseline numbers

Acceptance criteria:
- every selected gap has a visible implementation and metric
- each gap can be turned on/off for evaluation
- ablation results are saved and reported

Testing:
- [ ] module unit tests for the gap-specific logic
- [ ] ablation experiment test or script run
- [ ] regression checks for control toggles

### Module 4: Evaluation, benchmarking, and metrics

Scope:
- scientific comparison of system variants and baselines
- ensure evaluation is reproducible and evidence-driven

Work items:
- [ ] implement E1–E6 scripts under `experiments/`
- [ ] save results to `results/`
- [ ] compute mean and standard deviation for repeated runs
- [ ] record latency, token use, tool-call counts, and reliability metrics
- [ ] generate charts and summary tables for the paper

Acceptance criteria:
- all required experiments can be run with repo commands
- results are saved as structured files
- summary tables are included in the README and paper

Testing:
- [ ] reproducibility check on fixed seed or split
- [ ] validation of output file generation
- [ ] consistency test between script outputs and saved metrics

### Module 5: Safety, robustness, and failure handling

Scope:
- ensure the system fails safely and reports actions transparently

Work items:
- [ ] identify unsafe or unsupported actions
- [ ] add retries, validation, guardrails, or human review where needed
- [ ] ensure tool calls and state transitions are logged
- [ ] model failure categories and recovery plans

Acceptance criteria:
- unsafe actions are prevented or flagged
- recovery path is documented
- failure traces are available for analysis

Testing:
- [ ] unit tests for validation boundaries
- [ ] failure-case simulation tests
- [ ] property tests for guardrails

### Module 6: Documentation, reporting, and final submission

Scope:
- produce the final repository and research paper as required by Phase 2

Work items:
- [x] finalize README with architecture, setup, run instructions, and gap table
- [x] add `docs/devlog.md`
- [x] prepare paper structure and write working research-paper draft sections
- [x] generate summary tables from experiment outputs
- [x] ensure references meet DOI and citation requirements for the current draft level
- [ ] prepare final GitHub release/tag after final commit and group review

Acceptance criteria:
- repository can be installed and run by the supervisor
- paper follows conference-style format and requirements
- final submission package is complete and reproducible

Testing:
- [x] verify all commands in README work
- [x] verify paper formatting and section checklist at a working-draft level
- [x] verify release/tag and repository state before deadline

## 7. Immediate execution checklist

We need to complete the work in this order:

- [x] Finalize the exact research gaps and gap-specific hypotheses
- [x] Review and fix Phase 1 feedback summary in README
- [x] Make the repository fully reproducible and installable
- [x] Complete the end-to-end agentic workflow
- [x] Add logging and observability for trajectories
- [x] Run E1–E6 experiments and save results
- [x] Run ablations and failure analysis
- [x] Write the README gap-resolution table and architecture docs
- [x] Draft the conference paper
- [ ] Finalize GitHub release/tag and submission package

## 8. Definition of complete delivery

We are done only when all of the following are true:

- [x] final code is complete and reproducible
- [x] all required experiments are run and saved
- [x] results are reported honestly and clearly
- [x] repository README and paper both contain the gap-resolution table
- [x] the paper follows conference format and includes required sections and references at the working-draft level
- [ ] final GitHub release/tag is created after committing the reviewed final state
- [ ] the project is ready for supervisor review and submission
