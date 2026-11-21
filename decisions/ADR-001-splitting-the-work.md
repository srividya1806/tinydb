# ADR-001: Splitting Work Across Specialized Role-Based Agents

## Status
Accepted

## Context
In building an end-to-end autonomous Software Development Lifecycle (SDLC) pipeline triggered from GitHub issues to pull requests, we must decide how to divide labor across agents. Three architectural topologies were evaluated:
1. **Monolithic Single Agent**: A single LLM conversation loop handles requirements extraction, design planning, code editing, test authoring, test execution, pull request creation, and self-review.
2. **Strict Stage-Per-Agent (6 Agents)**: Exactly one unique agent per stage (Requirements, Design, Implementation, Testing, Release, Review).
3. **Decoupled 5-Role Topology with Independent Reviewer**: Specialized agents for Requirements, Design, Implementation, Testing, and Independent Review, with Release handled as a deterministic tool script.

The monolithic approach suffers from extreme context pollution, self-confirmation bias during review, lack of privilege separation, and compounding hallucination across long context horizons. Conversely, creating 6 completely autonomous free-form agents introduces excessive coordination overhead for deterministic administrative tasks (like git push and `gh pr create`).

## Decision
We choose the **Decoupled 5-Role Topology with an Independent Reviewer**:
- **Requirements Agent**: Specializes in parsing ambiguity, isolating problem statements, and outputting structured acceptance criteria in `spec.md`.
- **Design Agent**: Specializes in architectural mapping using `ARCHITECTURE.md` and identifying exact file/symbol touchpoints in `design.md`.
- **Implementation Agent**: Specializes in code editing and patch generation, focused strictly on adhering to `design.md`.
- **Testing Agent**: Specializes in test synthesis and test execution, running regression and acceptance suites in `test_report.md`.
- **Release Automation**: Deterministic script (not an LLM agent) that handles git commits, pushing, and GitHub PR API calls.
- **Independent Reviewer Agent**: A completely isolated agent with zero prior conversational history, evaluating the PR diff against the original issue.

## Consequences
### Positive
- **Context Hygiene**: Each agent receives only the scoped input relevant to its role, keeping context windows small, fast, and cost-efficient.
- **Adversarial Independence**: The reviewer has no attachment to previous implementation rationales, eliminating self-serving review bias.
- **Principle of Least Privilege**: Read-only stages (Requirements, Design, Review) do not have code modification or git push permissions.
- **Deterministic Release**: Releasing a PR does not risk LLM hallucination or command leakage.

### Negative
- Inter-stage serialization requires formal artifact contracts (`spec.md`, `design.md`, `diff.patch`, `test_report.md`).
- Backtracking loops require orchestrator mediation rather than informal conversational correction.
