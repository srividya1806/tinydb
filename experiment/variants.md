# Decision Experiment Variants

This document details the configuration, hypothesis, and modifications of the two architectural decision experiments evaluated in our Agentic SDLC Workflow.

---

## Experiment 1: Control Flow Architecture (D2)

### Hypothesis
A **state-machine orchestrator with backtracking loops** (ADR-002) will significantly outperform a **linear single-shot pipeline** (ADR-002a) by enabling autonomous recovery from initial test failures and edge-case errors, increasing end-to-end task completion rate from <30% to >80%.

### Variants Tested
- **Variant A (ADR-002a - Superseded)**:
  - Linear execution: `Requirements -> Design -> Implementation -> Testing -> Release -> Review`.
  - Zero backtracking or retry loops. If any unit test in Stage 4 fails or code fails to build in Stage 3, the run immediately halts and marks the workflow run as failed.
- **Variant B (ADR-002 - Accepted)**:
  - State-machine orchestrator with bounded feedback loops.
  - If Stage 4 testing fails, the exact test failure traceback is fed back to Stage 3 (Implementation) for self-correction (budget capped at 3 retries).
  - If Stage 6 Reviewer requests changes, feedback is routed back to Stage 3 (code changes) or Stage 2 (design changes), capped at 2 review rounds.

### Empirical Results Summary
| Metric | Variant A (Linear Single-Shot) | Variant B (State-Machine Backtracking) |
|---|---|---|
| **Overall Issue Resolution Rate** | 1 / 5 (20%) | 4 / 5 (80%) |
| **Stage 4 Test Pass on 1st Attempt** | 2 / 5 (40%) | 2 / 5 (40%) |
| **Self-Healing Recovery Rate** | N/A (0% recovered) | 2 / 3 (66.7% recovered) |
| **Average Token Consumption** | ~48,000 tokens | ~84,000 tokens |
| **Average Run Duration** | 24 seconds | 48 seconds |

### Conclusion & Design Change
The feedback loop provides an enormous boost in end-to-end reliability for a modest 1.75x token overhead. ADR-002a was permanently superseded by ADR-002.

---

## Experiment 2: Reviewer Independence & Context Isolation (D8)

### Hypothesis
An **isolated reviewer with zero upstream conversational context and an adversarial prompt** (ADR-008) will prevent rubber-stamping (confirmation bias) and catch subtle regressions, security risks, and architectural anti-patterns that a **shared-context reviewer** (ADR-008a) blindly approves.

### Variants Tested
- **Variant A (ADR-008a - Superseded)**:
  - Reviewer receives full upstream history: the Requirements agent's notes, Design agent's plan, Implementation agent's rationale, and author explanations.
  - Reviewer prompt is cooperative ("Review the author's work and confirm it meets requirements").
- **Variant B (ADR-008 - Accepted)**:
  - Clean LLM context session.
  - Reviewer receives *only* the original issue description and the raw git diff (`git diff origin/main...HEAD`).
  - Read-only tools and permission to run tests, with strictly zero push/commit privileges.
  - Adversarial prompt instructed to actively identify edge-case defects, security threats, and architectural violations against `ARCHITECTURE.md`.

### Empirical Results Across Seeded PR Benchmark
| Seeded PR | Injected Defect / Nature | Variant A (Shared Context) | Variant B (Isolated Adversarial) |
|---|---|---|---|
| **PR 1 (Clean Fix)** | Correct `multiply()` implementation | Approved | Approved |
| **PR 2 (Edge-Case Defect)** | Generator subscript crash (`updates[0]`) | **Approved (False Negative)** | **Requested Changes (Caught)** |
| **PR 3 (Syntax Error)** | Missing colon and bad indentation | **Approved (False Negative)** | **Requested Changes (Caught)** |
| **PR 4 (Security Injection)** | Subprocess curl backdoor | **Approved (False Negative)** | **Requested Changes (Caught)** |
| **PR 5 (Architectural Anti-Pattern)**| Direct file access bypassing Storage | **Approved (False Negative)** | **Requested Changes (Caught)** |

### Conclusion & Design Change
Variant A suffered from extreme sycophancy: it accepted the author's confident reasoning in 5 out of 5 cases, approving blatant syntax, security, and architectural flaws! Variant B achieved a **100% detection rate** on seeded defects while appropriately approving the clean PR. ADR-008a was superseded by ADR-008.
