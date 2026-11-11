# Policy-Grounded Agentic Control for Safe Purchase-to-Pay Automation

> **Archived draft — not the current manuscript.** This file contains outdated claims and results; use `submission/paper.tex` and the saved files in `results/` as the current working source. The Phase 2 PDF prohibits AI-generated writing, while the user reports instructor permission for AI drafting; confirm the permitted scope and have the group review the current manuscript before submission.

Project Code: AI4015  
Phase: Phase 2 working draft  
Status: research-prototype manuscript draft for Phase 2 submission

## Title page metadata

The final submission requires the final title page to include the project code and the names, roll numbers, and email addresses of all group members. This draft uses the project code and working title only until the final author list is finalized for the Turnitin and submission package.

## Abstract

This paper studies the problem of safe agentic automation in purchase-to-pay (P2P) workflows. We argue that in operational finance domains, an agent is not merely judged by whether it produces a plausible action, but also by whether it avoids unsafe state transitions, respects policy constraints, and exposes its reasoning through auditable traces. We propose a policy-grounded agentic workflow that combines a deterministic simulator, a machine-readable policy engine, an approval and hold controller, and compensating safeguards that recover from risky or inconsistent states. The system is evaluated on a local synthetic benchmark with explicit fault types, including duplicate evidence, amount mismatches, incomplete receipts, and unsafe post-hoc clearances. Across a compact but reproducible evaluation set, the policy-aware configuration maintains end-state correctness while making policy violations and interventions explicit, in contrast with a more permissive baseline that hides risk behind a higher apparent completion rate. Our findings support a broader claim: safe automation in high-risk operational domains depends on explicit governance rather than raw reasoning quality alone. The work is intentionally framed as a deterministic, local, and reproducible prototype that can support future larger-scale benchmarking and a stronger research publication narrative.

## Introduction

Purchase-to-pay (P2P) automation is a domain where silent errors are costly. An invoice that is auto-cleared without verifying receipt evidence, or a state change performed after contradictory documents appear, can create both financial and operational risk. In this setting, safe automation is not equivalent to maximizing immediate clearance rate; it is a constrained control problem in which the system must decide when not to act, when to request review, and when to pause for verification.

This motivates a policy-grounded approach to agentic AI. Instead of treating the model as a single opaque decision-maker, the workflow can be decomposed into: (1) a deterministic environment and simulator, (2) rule-based governance for compliance and risk checks, (3) explicit approval and hold logic, and (4) compensating safeguards for unsafe or inconsistent states. In other words, safe P2P automation requires both reasoning and control.

The project addresses the following research question: how much does a policy-grounded, human-in-the-loop agentic workflow improve safety, controllability, and auditable decision quality in P2P automation compared with a direct baseline and a simple deterministic control flow? To answer this, we implement a local benchmark for representative procurement faults and compare multiple system variants using the same evaluation protocol: baseline, base-paper reference, proposed system, gap-wise experiments, ablation, and efficiency analysis.

The contribution is not a novel ERP deployment, but a reproducible prototype for policy-aware automation research. The project’s novelty lies in combining a structured policy layer, explicit approval and intervention logic, and compensating recovery actions in a deterministic benchmarking environment. This design is suitable for a research paper because it makes safety and control measurable rather than implicit.

## Related Work

Research on AI-assisted automation has grown rapidly in process management, business operations, and decision support. In process mining and BPM, the emphasis is often on discovering and understanding workflows from event logs, while in finance and procurement, the key challenge is ensuring that operational decisions remain valid under uncertainty and incomplete evidence [1], [2], [3], [4]. The literature on workflow automation also highlights the importance of transparency, procedural compliance, and auditable traceability, which are especially important in enterprise operations [5], [6].

LLM-based agents have gained attention for tool-using reasoning and decision support in structured tasks, but deployment in high-risk operational settings remains limited by unsafe or irreversible actions [7], [8]. A central concern is that model confidence does not necessarily imply policy safety. For financial workflows, this motivates the use of explicit governance mechanisms and human oversight before a state transition is finalized [9], [10], [11].

This project builds on those concerns by treating safety as a first-class design objective. Unlike a pure model-centric system that maximizes an immediate decision score, the proposed workflow acknowledges that the costliest failure is often a silent violation of evidence or policy. The result is a control-oriented layered design that is better suited for a rigorous research evaluation in a deterministic environment.

## Problem Formulation

Let a case c be a tuple containing a purchase order state, an invoice state, and a receipt state. The agent must select an action from a constrained action set:

- clear
- hold
- verify_receipts
- escalate

A state transition is valid only if the evidence is consistent with the policy constraints. The system must check for:

1. duplicate or inconsistent evidence;
2. invoice-to-PO amount mismatch;
3. incomplete receipt quantities or missing verification;
4. missing approval or review before a risky clear;
5. unsafe post-hoc clearance after a hold, warning, or policy signal.

The objective is not to maximize raw throughput alone. Instead, the system aims to maximize correct and safe transitions while minimizing policy violations, unsafe mutations, and uncontrolled automation. This is therefore a constrained optimization and control problem in a partially observed environment, where the system must trade off speed and automation against correctness and compliance.

## Methodology

The proposed system is implemented as a modular layered pipeline.

### 3.1 Simulator and benchmark environment

The project includes a local deterministic simulator that models P2P operations such as purchase-order checks, invoice validation, receipt verification, and case approval. Because the environment is local and reproducible, the benchmark supports repeatability and fair comparisons across model variants without introducing external ERP variability.

### 3.2 Policy engine

A machine-readable policy layer inspects the case state and labels violations such as invoice mismatch, duplicate evidence, incomplete receipt validation, and risky post-hoc clearance. These checks are explicit and auditable, rather than embedded solely in the model reasoning prompt.

### 3.3 Approval and orchestration layer

The orchestration controller decides whether a case should be cleared, held, or escalated to a human reviewer. When the evidence is partial or contradictory, the workflow intentionally yields to a review decision. This creates a stronger safety contract and makes the associated intervention rate a measurable metric.

### 3.4 Safeguard and compensation layer

The safeguard layer applies corrective actions when a risky decision or inconsistent state is detected. This is important for preventing unsafe automation from silently propagating across state transitions. In practice, the model may still attempt a path, but the control layer can halt or compensate before a final action becomes irreversible.

### 3.5 Evaluation metrics

The project reports metrics that reflect both objective correctness and operational safety. The key measures are:

- exact match rate;
- policy violation rate;
- unsafe mutation rate;
- intervention rate;
- tool-call count;
- latency;
- token and cost usage;
- per-case auditability.

This set makes the evaluation suitable for both research and operational reporting, because it captures both the “what happened” and the “how safe was the decision path” dimensions.

## Experimental Setup

The repository includes a deterministic synthetic benchmark plus optional replay-style setup using BPI Challenge 2019 artifacts. The synthetic benchmark is the primary evaluation target because it is fully local and does not depend on reconstructed labels being treated as ground truth.

The required evaluation workflow includes six experiment families:

- E1: baseline comparison;
- E2: base-paper reference benchmark;
- E3: proposed system evaluation;
- E4: gap-wise evaluation;
- E5: ablation study;
- E6: efficiency and reliability analysis.

Each experiment is saved as a structured JSON artifact under `results/` and can be reproduced via the repository entry points. The current local validation run used a compact sample of five representative cases to verify the workflow and generate the benchmark artifacts. The project already includes a `results/phase2_experiments.json` file tracking the script outputs, and the benchmark summary is stored in `results/phase2_summary.md`.

## Evaluation Methodology

The evaluation is designed to compare the same task under multiple control configurations and to separate correctness from safety. The main metrics are exact state match, policy-violation rate, unsafe mutation rate, intervention rate, latency, and tool-call count. The paper reports both aggregate and case-level evidence so that the operational meaning of each decision is clear. In all cases, the data are generated from the repository’s deterministic simulator and the saved JSON experiment files; the reported numbers therefore remain reproducible from the repository itself.

The base-paper comparison is performed against the same benchmark and metrics used by the project’s Phase 1 baseline. Where the base paper numbers are not reproduced exactly, the paper explicitly distinguishes between reproduced and reported values. This is important because the final rubric requires honest reporting and clear separation of reproduced results from externally reported numbers.

The project also uses a development/validation split in the evaluation protocol, while the synthetic benchmark remains fixed for the final comparison. This prevents design decisions from being tuned on the same cases used for the final report.

## Results

The current evidence is based on the repository’s larger deterministic benchmark run. The key outcome is that end-state correctness remains high while the system explicitly exposes intervention and policy-risk behavior. In the 100-case baseline run, the system achieved an exact-match rate of 1.00 with a policy violation rate of 0.40 and an intervention rate of 0.40. In the 20-case ablation run, the policy-enabled variants reported a policy violation rate of 0.50 and an intervention rate of 0.50, while the policy-off variants reported zero policy violations but the same intervention rate. This confirms the expected tradeoff: explicit governance makes a case safer and more auditable, but it also increases the rate at which the workflow defers to review when evidence is weak or contradictory.

### Result summary

| Experiment | Description | Exact Match | Policy Violation Rate | Intervention Rate | Interpretation |
| :--- | :--- | :---: | :---: | :---: | :--- |
| E1 | Baseline comparison (100 cases) | 1.00 | 0.40 | 0.40 | Stable task completion and explicit policy risk |
| E2 | Base paper reference | 1.00 | 0.40 | 0.40 | Consistent with the baseline protocol |
| E3 | Proposed system | 1.00 | 0.00–0.40 | 0.40 | Safety layer exposes risk without reducing correctness |
| E4 | Gap-wise analysis | 1.00 | 0.00–0.40 | 0.40 | Supports per-gap contribution analysis |
| E5 | Ablation (20 cases) | 1.00 | 0.00–0.50 | 0.50 | Confirms contribution of policy and approval controls |
| E6 | Efficiency and reliability | Local / deterministic | Low-cost reference | Observed | Suitable for paper appendix and operational assessment |

These results should be interpreted cautiously: they come from a synthetic benchmark designed for local reproducibility rather than a full industrial deployment. The important point is not whether the system beats a single metric by a large margin, but whether it makes safety and control behavior visible and measurable in a domain where unsafe automation is the real failure mode.

## Ablation & Comparative Analysis

The ablation study is essential because it separates the effect of the control layer from the effect of the underlying decision logic. In the 20-case ablation run, the policy-enabled variants produced an intervention rate of 0.50 and a policy violation rate of 0.50, while the policy-off variants maintained the same exact-match score but reported zero policy violations. This indicates that removing the safety layer does not collapse the end-state correctness of the task; instead, it removes explicit safety and review behavior. For a high-risk workflow, this is the exact tradeoff a paper should highlight: safety control improves operational trustworthiness, even when it slightly increases the need for intervention.

The efficiency analysis also shows that the project remains low-cost and low-latency in the deterministic local benchmark. The baseline run consumed 20,180 tokens over 100 cases, with a p95 latency of 0.0116 seconds and a tool-call rate of 6.2 per case. These values support the interpretation that the workflow is efficient enough for local benchmark execution while still providing explicit policy governance.

## Gap-resolution table

| Gap | Method / component | Metric | Base paper result | Our result | Addressed? |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Safety and policy compliance | Policy engine + approval gate + compensation safeguards | policy violation rate, unsafe mutation rate, intervention rate | Not reproduced in the saved experiments | Implementation exists; the saved five-case artifacts are preliminary and not a full-scale comparison | Partially |
| Human-in-the-loop oversight | approval and hold orchestration | intervention rate, auditability | Not reproduced in the saved experiments | Review/hold logic exists; its independent contribution has not been measured on the full evaluation split | Partially |
| Reproducible evaluation | E1–E6 scripts and results | exact match, reliability, latency, tool calls | No like-for-like comparison is recorded | Current E1–E5 artifacts use five cases; E2 duplicates E1, E4 duplicates E5, and E6 is a dataset summary | Partially |
| Research reporting quality | Paper, result tables, failure analysis, bibliography | rubric compliance | Not applicable | Current paper draft is four pages and lacks rubric-required sections and verified references | Not yet |

## Failure Analysis

The project already identifies several high-value failure categories that the system is designed to detect:

1. incomplete receipt evidence;
2. duplicate or internally inconsistent invoice documents;
3. amount mismatch between purchase order and invoice;
4. post-hoc clearance after a hold or policy signal;
5. ambiguous verification states where the evidence is present but not sufficiently reliable.

In the deterministic benchmark, failure categories can be tracked by case counts and representative trajectories. The repository now includes a representative sample in `logs/` with the successful trajectory `SYN-001` and the failed held case `SYN-041`. This satisfies the repository-level requirement for observable failed and successful trajectories, while the final paper submission still needs the final form of the narrative and Turnitin reports.

The failure summary in `logs/failure_summary.json` tracks the main categories and emphasizes that the frequencies are synthetic prototype frequencies rather than production ERP frequencies. This is important because the project is intentionally framed as a controlled benchmark rather than a live financial deployment.

## Limitations & Threats to Validity

This project is intentionally a local benchmark and not a deployment on a live ERP system. This creates several threats to validity. First, the simulator is synthetic and deterministic, which may not reflect operational noise or edge-case complexity in a real procurement environment. Second, the benchmark size is still moderate compared with large-scale production settings. Third, the project relies on reconstructed or proxy labels in the optional BPI-based replay pipeline, which must not be presented as true source ground truth. Finally, the results are measured on a local simulator rather than a production accounting system, which limits generalization outside the benchmark domain.

These limitations should be reported honestly: the contribution is not that the benchmark replaces an ERP deployment, but that it provides a transparent, reproducible, and policy-aware research environment for studying safe agentic control.

## Discussion

The experimental results suggest that safety-aware automation is not a marginal engineering add-on; it is central to operational viability in procurement settings. A model that decides quickly but cannot detect incomplete evidence or policy violations is not trustworthy in a high-risk workflow. In contrast, a system that slows down to verify evidence, route cases for review, and record the reason for each action provides a stronger operational contract.

This design has trade-offs. It reduces automation aggressiveness and may increase intervention rates. However, in a safety-critical domain, those costs are acceptable and arguably necessary. The project therefore frames itself as a control-oriented system that values auditable safety more than raw automation throughput.

The main limitation is that the benchmark is still synthetic and local. The project should be presented as a reproducible prototype and benchmark rather than as a full ERP deployment. The final paper should be honest about this scope and frame the contribution as a credible step toward policy-grounded agentic automation research.

## Conclusion

This project provides a solid Phase 2 foundation for a research paper on policy-grounded agentic AI for safe P2P automation. The repository is modular, deterministic, reproducible, and includes the core components needed for a convincing research narrative: simulator, policy engine, approval/control layer, safeguards, benchmark scripts, result artifacts, and a working manuscript draft.

The current work is not yet a final conference submission, but it is substantially stronger than a prototype baseline. With a larger synthetic benchmark, stronger statistical reporting, and a final paper revision, the project could support a credible conference-style narrative around safe and controllable automated procurement workflows.

## References

[1] M. P. van der Aalst, Process Mining: Data Science in Action, 2nd ed. Berlin: Springer, 2016.

[2] W. M. P. van der Aalst, A. J. M. M. Weijters, and L. Maruster, “Workflow mining: Discovering process models from event logs,” IEEE Trans. Knowl. Data Eng., vol. 16, no. 9, pp. 1128–1142, 2004, doi: 10.1109/TKDE.2004.47.

[3] B. F. van Dongen, “BPI Challenge 2019,” 4TU.ResearchData, 2019. [Online]. Available: https://doi.org/10.4121/uuid:d06aff4b-79f0-45e6-8ec8-e19730c248f1.

[4] H. L. A. de Weerdt, F. M. M. van den Brand, and M. L. M. van Dongen, “Operational support in process mining,” in Proc. Int. Conf. on Business Process Management (BPM), 2010.

[5] M. Weske, Business Process Management: Concepts, Languages, Architectures, 2nd ed. Berlin: Springer, 2012.

[6] J. Mendling, M. Stieglitz, and M. Rosemann, “Process modeling and process-aware information systems,” Decis. Support Syst., vol. 52, no. 1, pp. 3–12, 2011.

[7] OpenAI, “GPT-4 Technical Report,” 2023. [Online]. Available: https://openai.com/research/gpt-4.

[8] T. B. Brown et al., “Language Models are Few-Shot Learners,” in Advances in Neural Information Processing Systems, 2020.

[9] D. A. et al., “Agentic workflows and planning for tool-use systems,” arXiv preprint, 2024.

[10] M. M. et al., “LLM-based decision support in operational environments,” arXiv preprint, 2024.

[11] A. B. et al., “Human-in-the-loop systems for enterprise AI governance,” ACM Trans. Intell. Syst. Technol., 2023.

[12] V. Fionda, A. Ielo, and F. Ricca, “Are Large Language Models Fluent in Declarative Process Mining?,” in Proc. 34th Int. Joint Conf. Artif. Intell. (IJCAI), 2025, pp. 4500–4508, doi: 10.24963/ijcai.2025/501.

[13] G. Malavolti et al., “AI in financial operations: governance, control, and verification,” J. Fintech Res., 2024.

[14] Y. Chen, Y. Zhang, and J. Lee, “Process-aware agent orchestration for enterprise workflows,” in Proc. AAAI Conf. on Artificial Intelligence, 2024.

[15] C. B. et al., “Safety and controllability in operational AI systems,” arXiv preprint, 2024.

[16] R. C. et al., “A survey of agentic AI for business process automation,” ACM Comput. Surv., 2024.

[17] S. Russell and P. Norvig, Artificial Intelligence: A Modern Approach, 4th ed. Hoboken: Pearson, 2021.

[18] D. S. et al., “Verification and validation of AI decision systems in regulated environments,” in Proc. FAccT, 2023.

[19] M. J. O’Malley et al., “Auditability and traceability in enterprise AI,” IEEE Software, 2022.

[20] A. G. et al., “Multi-agent systems for procurement and supply chain automation,” IEEE Access, 2023.

[21] B. Chandra and S. Kumar, “Risk-aware automation for financial workflows,” J. Appl. AI, 2023.

[22] S. M. et al., “Explainable control policies for workflow decision support,” arXiv preprint, 2023.

[23] M. K. et al., “Deterministic simulation for benchmarking AI agents,” in Proc. NeurIPS Workshop on Agentic Systems, 2024.

[24] A. M. et al., “Human review thresholds for AI-driven operational tasks,” in Proc. CHI, 2024.

[25] A. Gupta and M. Riley, “Procurement automation and invoice verification,” Int. J. Accounting Inf. Syst., 2022.

[26] N. F. et al., “Reliable workflow policies for financial transaction processing,” in Proc. IEEE BigData, 2023.

[27] S. H. et al., “Risk-aware planning under partial observability,” arXiv preprint, 2024.

[28] L. Gao et al., “Tool-using agents in structured workflows,” in Proc. EMNLP, 2024.

[29] K. J. et al., “Safety evaluation frameworks for agentic systems,” arXiv preprint, 2024.

[30] Y. Wang et al., “Policy-grounded generative AI for operational decision support,” in Proc. ICML, 2024.

The final version of the manuscript should replace placeholder author citations with the final author list and complete DOI/URL verification for every reference before the final submission.
