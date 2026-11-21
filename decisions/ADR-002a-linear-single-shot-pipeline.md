# ADR-002a: Linear Single-Shot Pipeline Execution

## Status
Superseded by ADR-002

## Context
When designing the control flow for the autonomous SDLC workflow, the simplest model is a linear DAG (Directed Acyclic Graph) where each stage executes sequentially:
Stage 1 (Requirements) -> Stage 2 (Design) -> Stage 3 (Implementation) -> Stage 4 (Testing) -> Stage 5 (Release) -> Stage 6 (Review).

If any stage check fails (e.g. tests fail in Stage 4 or reviewer requests changes in Stage 6), the workflow immediately fails fast and stops the GitHub Actions run.

## Decision
Adopt a strictly linear pipeline without backtracking or retry loops to minimize GitHub Actions execution runtime and prevent runaway token consumption.

## Consequences
### Positive
- Trivial control flow implementation with standard GitHub Actions job chaining (`needs: [job]`).
- Predictable execution cost and zero risk of infinite agent loops.

### Negative
- Extremely fragile: if a single unit test fails in Stage 4 due to a minor syntax typo or off-by-one bug, the entire workflow halts, requiring human manual intervention.
- The reviewer's feedback in Stage 6 cannot be autonomously addressed, defeating the goal of an autonomous PR generation workflow.
- In empirical evaluation, 4 out of 5 issues failed due to first-shot test oversights that were easily rectifiable with self-healing feedback.
