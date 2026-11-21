# ADR-007: Deterministic Stage Verification Checks and Decision Gates

## Status
Accepted

## Context
A workflow must determine whether an artifact produced by a stage meets the threshold required to advance to subsequent stages. If verification checks are performed purely by the same LLM agent that produced the artifact (self-grading), confirmation bias occurs and invalid artifacts cascade through the pipeline. Conversely, relying exclusively on manual human checks halts automation.

We must define explicit, deterministic verification checks for every stage prior to stage hand-off.

Options considered:
1. **Pure LLM-as-a-Judge for all stages**: An LLM reviews each artifact and outputs PASS/FAIL.
2. **Hybrid Verification**: Deterministic static/runtime analysis for code and tests; structured schema validation for requirements and design.

Pure LLM grading is susceptible to prompt drift, hallucinations, and non-determinism. Code syntax and test pass rates should never be judged by an LLM when Python compilers and pytest exist.

## Decision
We enforce **Deterministic Hybrid Verification Gates**:
1. **Stage 1 (Requirements) Check**:
   - *Check*: The artifact `spec.md` must parse into markdown sections (`Problem Summary`, `Acceptance Criteria`).
   - *Validation*: Every acceptance criterion must match a structured testable format (Given-When-Then or clear assertive statement). If fewer than 2 verifiable criteria exist or vague placeholders are detected, gate fails.
2. **Stage 2 (Design) Check**:
   - *Check*: The artifact `design.md` must explicitly list `Target Files` and `Functions/Methods to Modify`.
   - *Validation*: The orchestrator runs a static check verifying that existing files listed in `design.md` actually exist in the repository tree.
3. **Stage 3 (Implementation) Check**:
   - *Check*: The patch in `diff.patch` must apply cleanly (`git apply --check`).
   - *Validation*: All modified Python files must parse through `ast.parse()` without syntax errors.
4. **Stage 4 (Testing) Check**:
   - *Check*: The orchestrator invokes `pytest` directly.
   - *Validation*: 100% of newly introduced tests pass, and 100% of existing baseline tests pass (0 regressions).
5. **Stage 5 (Release) Check**:
   - *Check*: Pull request is open on GitHub.
   - *Validation*: Verified via GitHub API (`gh pr view`) and repository branch protection checks.
6. **Stage 6 (Review) Check**:
   - *Check*: The reviewer issues a structured verdict (`APPROVE` or `REQUEST_CHANGES`).
   - *Validation*: If `APPROVE` or 2 review rounds are completed, gate passes to human maintainer. If `REQUEST_CHANGES`, routed back to Stage 3 or Stage 2.

## Consequences
### Positive
- Zero ambiguity: code that does not compile or fails existing tests cannot proceed to Release.
- High reliability: deterministic tools (`ast`, `pytest`, `git`) decide code correctness, not subjective LLM speculation.

### Negative
- Requirements criteria checks rely on regex/schema patterns which can occasionally flag an unusual but valid spec format.
