# Phase 2 Final Submission Checklist

This checklist is an honest status review against `phase2/AI4015_Agentic_AI_Semester_Project_Phase2.pdf`. The package is **not ready for final submission** yet.

## Repository and implementation

- [x] Project setup, dependency manifests, `.env.example`, CLI, API, and modular components are present.
- [x] Existing review recorded 24 passing tests on 2026-11-11. Tests were not rerun after the 2026-11-12 changes.
- [ ] Commit the current Phase 2 work. `phase1/.git` has no commits; project files are untracked.
- [ ] Create the `phase2-final` tag after the final code has been committed and reviewed. No such tag currently exists.
- [ ] Publish or confirm supervisor access to the GitHub repository and release.

## Experiments and evidence

- [x] Run and save E1–E6 on 100-case synthetic/BPI-derived fixtures, including an eight-variant factorial ablation.
- [ ] Implement a like-for-like E2 reproduction of the selected Declare-translation base paper. Current E2 is explicitly a heuristic domain comparator.
- [x] Save E3 full 100-case proposed-system results.
- [x] Save E4 100-case BPI-derived replay results; keep its expected statuses labeled as proxy outcomes, not invoice truth.
- [x] Save E5 policy/approval factorial ablation. Its approval toggle has no aggregate effect in the current deterministic fixture.
- [x] Save E6 local latency, token estimate, tool-call, and reliability metrics. The offline \$0 cost is not a hosted-model estimate.
- [x] Record seed 2019, manifests, offline backend, configurations, and result artifacts; the agent is not a hosted LLM evaluation.
- [x] Save two successful and two policy-risk trajectories. They are not two terminal failures: E3 recorded zero end-state mismatches.
- [x] Recalculate and label risk-category counts as synthetic fixture composition, not observed production failure prevalence.
- [x] Remove expected terminal labels from agent, policy, approval, and compensation decision inputs; rerun E1–E6 on 2026-11-12. The evaluator uses labels only after execution to score outcomes.

## Research paper

- [x] Expand the two-column IEEE manuscript to 8 pages and add the evaluation methodology, results, ablation/comparative analysis, failure analysis, limitations/threats, and gap-resolution table.
- [ ] Resolve the rubric's AI-writing prohibition against the user's report of instructor permission for AI drafting; obtain written confirmation and ensure all group members review and take responsibility for the final paper.
- [x] Align the manuscript's reported metrics with refreshed E1–E6 artifacts, including explicit proxy-label and offline-cost caveats.
- [x] Add 30 cited bibliography entries, each with a DOI or URL; [ ] manually verify every citation against its official publication/source.
- [ ] Confirm whether the title page must include other group members; currently it lists Rayyan Azmat (P220507) only.
- [x] Refresh the source ZIP from the current `paper.tex` and bibliography.
- [ ] Recompile the updated manuscript and refresh the target-named PDF. This environment has no `pdflatex`, `latexmk`, or IEEEtran class installed; the existing 8-page PDF predates the source edits.

## Turnitin and final upload

- [ ] After group review and confirmation of allowed AI assistance, submit the exact final paper version to Turnitin and obtain both required reports. The similarity report and AI-writing report are mandatory.
- [ ] Upload through Google Classroom as the group head.
- [ ] Attach the paper PDF, both Turnitin reports, and the LaTeX/Overleaf source ZIP.
- [ ] Include the GitHub repository URL and the `phase2-final` release URL in the submission.
- [ ] Use the rubric's filename pattern. With project code `AI4015` and group-head roll number `P220507`, the target names are:
  - `Phase2_AI4015_P220507_Paper.pdf`
  - `Phase2_AI4015_P220507_Similarity.pdf`
  - `Phase2_AI4015_P220507_AIReport.pdf`
  - The paper source ZIP (the rubric does not prescribe a filename; use a clear matching name).

The rubric lists the deadline as Sunday, 8 November 2026, 11:55 PM PKT. That date has passed; check the course late-submission policy or contact the instructor.
