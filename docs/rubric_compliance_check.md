# Phase 2 Rubric Compliance Check

Reviewed against `phase2/AI4015_Agentic_AI_Semester_Project_Phase2.pdf` on 2026-11-12. This is a repository readiness review, not evidence that the course has accepted the work. **Final submission is not ready.**

| Requirement | Status | Current evidence / gap |
|---|---|---|
| End-to-end system, modular components, interface, dependencies, and setup docs | Present | Simulator, agents, policy/orchestration/safeguard code, CLI/API, tests, and setup files exist. |
| Automated tests | Passing | `.venv/bin/pytest -q`: 24 passed; one dependency deprecation warning. |
| E1 baseline | Present | Saved 100-case ReAct run with policy and approval disabled; alert rate is zero because detection is disabled. |
| E2 base-paper approach | Partial | E2 is a 100-case heuristic domain comparator. It is not a reproduction of the selected Declare-translation paper. |
| E3 proposed system | Present | Saved 100-case ReAct run with policy and approval enabled. |
| E4 gap-wise / transfer experiment | Partial | Saved 100-case BPI-derived replay for ReAct and heuristic agents; expected invoice states are reconstructed proxies, not observed ground truth. |
| E5 ablation | Present with limitation | Eight 100-case variants independently toggle policy and approval for ReAct and heuristic controllers. Approval's aggregate effect is zero in this fixture. |
| E6 efficiency and reliability | Present with limitation | Local latency, calls, estimated tokens, and reliability metrics are saved; offline cost is not a hosted-model cost estimate. |
| Fixed split, seeds, model settings, reproducibility | Present with limitation | Frozen 100-case synthetic manifest (seed 2019), deterministic offline backend, and refreshed JSON artifacts are saved. Expected terminal labels are withheld from decision components and used only after execution for scoring. |
| Failure analysis | Present as risk analysis | Two success and two policy-risk traces are saved. E3 has no terminal mismatches; risk examples are correctly held, not terminal failures. Category frequencies describe the synthetic fixture only. |
| Gap-resolution table in paper | Present in draft | The manuscript includes a gap-resolution table, distinguishes proxy evidence, and states unresolved limitations. |
| IEEE/ACM two-column paper, 8–10 pages, required sections | Present in draft | Current LaTeX source compiles to 8 two-column pages with evaluation methodology, results, ablation/comparative analysis, failure analysis, limitations/threats, and the gap table. |
| Bibliography: 25–30 references with DOI or official URL, all cited | Structurally met; group review pending | 30 entries are cited; DOI metadata matches Crossref records and DOI/official URLs resolve. Some publisher sites restrict automated page access, so the group should spot-check bibliographic details against the publication pages. |
| Paper originality requirement | Requires permission confirmation and group review | The PDF says AI-generated writing is not allowed. The user reports instructor permission for AI drafting, but that exception is not recorded here. Obtain written confirmation, review the complete manuscript, and follow the instructor's permitted scope before submission. |
| Title-page metadata | Partial | Rayyan Azmat, P220507, and email are present; confirm whether there are additional group members and include all of them. |
| Turnitin similarity and AI-writing reports | Pending | Must be generated from the same final, group-authored paper version. |
| Final source commit and `phase2-final` release | Not met | `phase1/.git` has no commits; project files are untracked. No `phase2-final` tag exists. A reviewed commit and release still need to be created and published. |
| Google Classroom upload and links | Pending | Group head must upload the paper, both reports, and source ZIP, and include the repository and release links. |
| Deadline | Passed | The PDF lists 8 November 2026, 11:55 PM PKT; consult the late-submission policy. |

## Required upload set

For project code `AI4015` and group-head roll number `P220507`, the rubric's PDF filenames resolve to:

1. `Phase2_AI4015_P220507_Paper.pdf`
2. `Phase2_AI4015_P220507_Similarity.pdf`
3. `Phase2_AI4015_P220507_AIReport.pdf`
4. Paper source ZIP (LaTeX/Overleaf project; no exact ZIP filename is specified)
5. GitHub repository URL and `phase2-final` release URL, included with the Classroom submission

The existing 8-page PDF predates the latest manuscript-source edits; a separate legacy 4-page export was also found and must not be submitted. Recompile the current source first. Group members must review all text, references, data, and claims, and resolve the rubric/instructor permission discrepancy before uploading.
