# ADR-008a: Shared-Context Pull Request Reviewer

## Status
Superseded by ADR-008

## Context
When designing the reviewer agent in Stage 6, the initial intuitive implementation passed the entire workflow execution context—including the Requirements agent's notes, the Design agent's architectural trade-offs, and the Implementation agent's internal rationale—to the Reviewer agent.

The assumption was that giving the reviewer complete context would allow it to understand the author's intent and provide more contextual feedback.

## Decision
Provide the Reviewer agent with full upstream conversation history, implementation rationale, and direct write permissions to quickly polish minor style issues.

## Consequences
### Positive
- The reviewer had full visibility into why the implementer chose specific patterns.

### Negative
- **Severe Confirmation Bias (Sycophancy)**: When evaluated across seeded buggy PRs, the reviewer agreed with the author's rationalizations and approved 5 out of 5 PRs, including PRs with deliberate security flaws, edge-case bugs, and architectural anti-patterns!
- **Lack of Independence**: Reading the author's confident explanations primed the reviewer to assume the code was correct rather than evaluating the diff from first principles.
- **Permission Creep**: Allowing the reviewer write permissions violated separation of duties and blurred the accountability boundary between author and reviewer.
