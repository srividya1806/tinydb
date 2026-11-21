# ADR-003: Scoped Information Handoffs and Context Filtering

## Status
Accepted

## Context
A critical vulnerability in multi-agent pipelines is context bloat and context contamination. When agents pass their full conversational history, raw tool outputs, or subjective internal reasoning to subsequent agents:
1. Context windows grow rapidly, increasing latency and cost.
2. Downstream agents inherit upstream hallucinated assumptions, cognitive biases, and rationalizations.
3. The Reviewer agent becomes susceptible to "sycophancy" (rubber-stamping code because it reads the author's confident explanation rather than critically inspecting the diff).

We must establish strict boundary contracts defining what information is transmitted between stages and what is deliberately redacted.

## Decision
We enforce a **Strict Scoped Handoff Protocol** based on formalized file artifacts:
1. **Requirements $\to$ Design**: Passes *only* `spec.md` (clean acceptance criteria) and the sanitized issue description. Raw issue comments and author discussions are excluded to prevent conversational noise.
2. **Design $\to$ Implementation**: Passes `design.md` (target files, functions, and planned modifications) and `spec.md`. The Design agent's internal exploration traces and rejected ideas are excluded.
3. **Implementation $\to$ Testing**: Passes `spec.md` and the git diff (`diff.patch`). The Testing agent receives the *what* and the *code*, but *not* the implementation agent's reasoning. This ensures the testing agent writes tests based purely on acceptance criteria rather than mirroring the implementer's assumptions.
4. **Testing $\to$ Implementation (Backtrack)**: Passes *only* the specific failed test assertion, stdout, and Python traceback. Full test suite logs of passing tests are pruned.
5. **Release $\to$ Reviewer**: The Reviewer receives **only**:
   - The original issue description.
   - The git diff (`git diff origin/main...HEAD`).
   - Read-only access to repository files at the PR commit.
   - **Deliberately Redacted**: The Reviewer never sees the Requirements, Design, Implementation, or Testing agents' conversation logs, thoughts, or internal deliberations.

## Consequences
### Positive
- Prevents confirmation bias and sycophantic approval in code review.
- Minimizes token consumption per call, keeping costs low.
- Standardized markdown and patch artifacts enable human traceability: maintainers can inspect exactly what each agent received and produced.

### Negative
- If a requirement nuance was discussed during issue grooming but omitted from `spec.md`, downstream agents cannot recover it without an explicit backtrack.
