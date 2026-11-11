# Submission directory — draft artifacts only

The files in this directory are working artifacts, **not a final submission package**.

The Phase 2 assignment requires an 8–10 page IEEE/ACM two-column paper. Its PDF says AI-generated writing is not allowed. The user reports instructor permission for AI drafting, but that exception is not recorded here; confirm the permitted scope with the instructor. Group members must review the paper in full, verify every claim and citation, and follow the instructor's requirements before submission.

Current artifacts:

- `paper.tex`: 8-page working LaTeX manuscript with the rubric sections and current repository results.
- `paper.pdf`: last locally compiled 8-page draft; it predates the latest source edits and must be rebuilt before use.
- `DRAFT_STALE_4page_Phase2_AI4015_22P-0507_Paper.pdf`: legacy four-page export; not a submission artifact.
- `Phase2_AI4015_P220507_Paper.pdf`: target-named copy to create after rebuilding and group review.
- `Phase2_AI4015_P220507_Paper_source.zip`: refreshed source bundle (`paper.tex`, `references.bib`); regenerate after any further manuscript edits.
- `references.bib`: 30 cited entries with DOI or URL; DOI metadata and URL resolution have been checked, but group members should spot-check publication metadata against original sources.

For project code `AI4015` and group-head roll number `P220507`, the final PDF filename should be `Phase2_AI4015_P220507_Paper.pdf`. The required Turnitin files should be named `Phase2_AI4015_P220507_Similarity.pdf` and `Phase2_AI4015_P220507_AIReport.pdf`. Generate both from the same final group-authored paper version. The rubric also requires a paper-source ZIP, the GitHub repository URL, and the `phase2-final` release URL in the Google Classroom submission. The current environment lacks a LaTeX compiler and the IEEEtran class, so the refreshed `paper.tex` has not yet been compiled.

See `../docs/final_submission_checklist.md` and `../docs/rubric_compliance_check.md` for current blockers, including the base-paper comparison, proxy-label validity, instructor AI-use confirmation, Turnitin reports, group metadata, and release packaging. Expected-label leakage has been removed from controller inputs and the evaluation rerun; do not upload these draft artifacts as the final package before group review and required external steps.
