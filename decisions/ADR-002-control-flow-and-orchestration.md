# ADR-002: State-Machine Orchestrator with Deterministic Backtracking Loops

## Status
Accepted (Supersedes ADR-002a)

## Context
ADR-002a proved that a linear single-shot pipeline yields poor end-to-end task completion (failing on 80% of real-world issues due to minor initial test failures). Real software development relies on feedback loops: tests fail, diagnostics are analyzed, code is adjusted, and reviewer feedback is incorporated.

We considered three control flow architectures:
1. **Unconstrained Autonomous Multi-Agent Planner**: An LLM agent acts as a planner, dynamically choosing which agent to call next based on free-form reasoning.
2. **Modular GitHub Actions Jobs Chained via Workflow Dispatch**: Separate GHA workflows triggering each other via repository dispatches or webhooks.
3. **Deterministic State-Machine Orchestrator with Bounded Feedback Loops**: A centralized Python orchestrator running within a single GitHub Actions job, enforcing deterministic transition tables, explicit verification gates, and hard backtrack budgets.

Option 1 suffers from non-deterministic looping, hallucinated routing, and runaway token costs. Option 2 introduces massive latency (each step takes 30-60s to spin up a new GHA runner and container) and state serialization fragility across separate runner environments.

## Decision
We choose the **Deterministic State-Machine Orchestrator with Bounded Feedback Loops**:
- The workflow execution is governed by a state machine with explicit stages: `REQUIREMENTS`, `DESIGN`, `IMPLEMENTATION`, `TESTING`, `RELEASE`, `REVIEW`, and `COMPLETED`.
- **Testing Feedback Loop**: If Stage 4 tests fail, the orchestrator routes the test failure trace back to Stage 3 (Implementation). The budget is capped at **3 retries**. If tests still fail after 3 retries, the orchestrator escalates to Stage 2 (Design) to re-evaluate architectural assumptions (capped at 1 design escalation).
- **Reviewer Feedback Loop**: If Stage 6 Reviewer outputs `REQUEST_CHANGES`, the orchestrator parses the structured verdict:
  - If `scope == "CODE"`, feedback is routed to Stage 3 (Implementation).
  - If `scope == "DESIGN"`, feedback is routed to Stage 2 (Design).
  - The review iteration is strictly capped at **2 rounds**.
- **Human Merge Gate**: Once Stage 6 approves or exhausts review rounds, the PR is left open for human decision. Agents never execute merge commands.

## Consequences
### Positive
- High resilience: agents autonomously recover from initial syntax, test, and stylistic issues.
- Strict predictability: hard iteration counters prevent runaway loops or infinite token spend.
- Fast execution: running within a single orchestrated runner avoids GHA container spin-up overhead.

### Negative
- Requires robust state tracking and error payload passing between stages.
- Retries consume additional LLM tokens, requiring strict per-stage token limits.
