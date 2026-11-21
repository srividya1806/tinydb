# ADR-010: Trigger Mechanisms, Actor Authorization, and Concurrency Control

## Status
Accepted

## Context
A repository workflow that automatically creates branches, runs tests, and opens pull requests must not be triggered indiscriminately by unvetted users or run concurrently on the same issue.

Key challenges:
1. If any public user opening an issue immediately triggers the workflow, malicious actors could spam issues to exhaust the repository owner's API credits or runner quotas.
2. If two maintainers comment `/autose` at nearly the same time, or if an issue is edited or relabeled while a run is active, concurrent workflows will conflict over the same git branch (`autose/issue-<num>`), causing race conditions and git push failures.

## Decision
We implement **Strict Actor Authorization and Concurrency Controls**:
1. **Trigger Events**:
   - The workflow listens on `issues: [labeled]` and `issue_comment: [created]`.
   - **Label Trigger**: Triggers when the label `autose` is applied to an issue.
   - **Comment Trigger**: Triggers when an issue or PR comment starts with the slash command `/autose`.
2. **Actor Authorization Gate**:
   - The workflow inspects the event actor's repository association (`github.event.comment.author_association` or issue sender).
   - Only users with `OWNER`, `MEMBER`, or `COLLABORATOR` status (or possessing `write` / `admin` permissions) are permitted to trigger the workflow.
   - Unauthorized attempts immediately post an informative comment explaining that only repository maintainers can invoke the autonomous agent, and the job exits cleanly with zero agent calls.
3. **Concurrency Locking**:
   - Concurrency is managed via GitHub Actions `concurrency` groups:
     ```yaml
     concurrency:
       group: autose-issue-${{ github.event.issue.number }}
       cancel-in-progress: false
     ```
   - By setting `cancel-in-progress: false`, a duplicate trigger is queued or cleanly rejected rather than abruptly terminating a half-finished git commit or PR creation.

## Consequences
### Positive
- Total protection against resource exhaustion by random public users.
- Deterministic, conflict-free git branch management: only one workflow interacts with `autose/issue-<num>` at any time.
- Clean maintainer UX with clear slash command `/autose` and label triggers.

### Negative
- Maintainers must explicitly label or comment on an issue to start the pipeline (acceptable and desirable behavior).
