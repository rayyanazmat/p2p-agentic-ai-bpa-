# Research Paper Blueprint: Policy-Grounded Agentic AI for Safe P2P Automation

## Executive summary
This project studies a control-oriented agentic workflow for purchase-to-pay (P2P) processing in a deterministic local simulator. The core claim is that safe automation is not achieved by a single monolithic policy or a raw decision model alone, but by combining a structured policy layer, explicit human-in-the-loop review, and compensating safeguards that intervene before unsafe actions can occur. The work is positioned as policy-grounded agentic workflow control rather than as a generic ERP automation demo.

## Research question
How much can a policy-grounded, human-in-the-loop agentic workflow improve safety, controllability, and operational transparency in purchase-to-pay automation compared with a direct decision baseline and a simple deterministic workflow policy?

## Novelty and contribution
The novelty is not a novel ERP or a new LLM prompt alone. The novelty is the integration of three explicit control layers:

1. a machine-readable policy engine that checks invoice, receipt, and duplicate evidence conditions;
2. an approval/orchestration layer that decides when a case must be reviewed or held instead of auto-cleared;
3. compensating safeguards that implement a structured recovery path when unsafe or inconsistent states are detected.

This creates an agentic workflow that is controllable, auditable, and testable in a deterministic sandbox. The key contribution is not simply higher accuracy on a narrow ledger task; it is the ability to expose high-risk decisions, enforce policy compliance, and preserve human oversight in a domain where silent automation would be unacceptable.

## Experimental protocol
We evaluate three families of solutions:

- Heuristic baseline: deterministic workflow logic without learned policy reasoning.
- ReAct baseline: tool-using agent with a fixed local reasoning loop.
- Policy-aware variants: same agentic control with policy checks and approval gating enabled or disabled.

Each experiment follows a fixed protocol:

- use the deterministic synthetic manifest as the primary benchmark;
- compare policy-on vs policy-off and approval-on vs approval-off variants;
- report exact end-state match, policy violations, inappropriate clears, intervention rate, latency, token cost, and tool-call count;
- ensure the simulator is reset before each batch to preserve reproducibility.

## Benchmark design
The benchmark should include:

- baseline synthetic cases spanning two-way, three-way, consignment, and fault-injected conditions;
- a clear expected terminal invoice state for every case;
- a fault taxonomy covering duplicate invoices, amount mismatches, incomplete receipts, missing verification, and unsafe post-hoc clearance;
- analysis by category and by failure mode to expose where the policy or agent fails;
- a larger synthetic benchmark of 500-1000 cases for the final paper version.

## Dataset transparency and constraints
This project explicitly avoids presenting reconstructed BPI labels as real source ground truth. Any BPI-derived replay material is treated as a proxy benchmark only. The paper must state that the simulator is local and synthetic, and that no live ERP integration or production payment logic is involved. This transparency is crucial for a credible experimental narrative.

## Expected paper claims
The paper can credibly claim the following:

- safety: policy-aware control reduces unsafe clearances and rule-breaking state transitions;
- controllability: the approval layer allows human review when evidence is partial or contradictory;
- transparency: audit trails and tool-call metrics make the decision path observable and explainable.

## Methodology narrative
The project’s central methodological framing is: safe agentic automation is a control problem, not merely a reasoning problem. In an operational procurement setting, the unsafe action is not always a wrong prediction—it is a decision that crosses a policy boundary or changes state without evidence. By forcing the decision loop to inspect and verify evidence before transition, the system trades some raw automation speed for a much clearer safety contract.

## Limitations
This work is a controlled simulation and should be presented as such. Limitations include:

- synthetic benchmark data rather than real ERP transactions;
- deterministic local simulator rather than production accounting semantics;
- no real procurement business process integration beyond the mock API;
- limited benchmark scale compared with a full industrial deployment.

The paper should include this honesty explicitly and frame the contribution as a reproducible and audit-friendly prototype for policy-grounded automation research.

## Publication-ready checklist
- [x] deterministic simulator and local API
- [x] policy engine and rule checks
- [x] approval and hold flow
- [x] compensation safeguard layer
- [x] ablation-minded evaluation harness
- [x] dataset summary and category tracking
- [x] benchmark table generation for paper reporting
- [ ] expand benchmark to a larger multi-seed synthetic study
- [ ] integrate more formal statistical reporting and confidence intervals
- [ ] write experimental section with figures and result tables
- [ ] draft introduction, method, results, limitations, and conclusion

## Suggested title
Policy-Grounded Agentic Control for Safe Purchase-to-Pay Automation: A Deterministic Benchmark for Safety, Review, and Auditability
