# ADR-008: Independent Adversarial Reviewer with Zero Upstream Context

## Status
Accepted (Supersedes ADR-008a)

## Context
ADR-008a demonstrated that sharing the authoring agents' chain of thought with the reviewer causes severe rubber-stamping, with the reviewer approving buggy, incomplete, or insecure PRs.

In real engineering organizations, effective code review requires fresh eyes: the reviewer inspects the code changes against the user's requirements without being primed by the author's rationalizations. Furthermore, reviewers should critique and verify, not silently alter the author's branch.

## Decision
We enforce strict **Reviewer Independence across Four Dimensions**:
1. **Context Isolation**: The Reviewer agent operates in a completely fresh LLM session with zero memory of upstream agent conversations or scratchpads. It receives *only*:
   - The original issue title and description.
   - The git diff (`git diff origin/main...HEAD`).
   - Read-only access to repository files at the PR head commit.
2. **Permission Boundary**: The Reviewer has **read-only** repository permissions and tool execution access to run tests locally, but **strictly no push or commit privileges**.
3. **Adversarial System Prompt**: The Reviewer prompt is explicitly framed to look for bugs, regressions, architectural violations against `ARCHITECTURE.md`, missing boundary tests, and security risks. It is instructed to reject superficial self-evident comments and verify that the diff genuinely fulfills the issue.
4. **Structured Decision Matrix**: The Reviewer must emit a structured JSON verdict:
   - `verdict`: `"APPROVE"` | `"REQUEST_CHANGES"`
   - `scope`: `"NONE"` | `"CODE"` | `"DESIGN"`
   - `blocking_issues`: List of specific file:line defects with technical justification.

## Consequences
### Positive
- Rigorous scrutiny: Caught edge cases, negative number edge cases, and missing exceptions on seeded PR evaluation that were previously approved under ADR-008a.
- Eliminates confirmation bias and sycophantic approval loops.
- Clear separation of responsibilities: Reviewers review; implementers implement.

### Negative
- Reviewer may occasionally request stylistic changes that the implementer needs an extra iteration to satisfy.
