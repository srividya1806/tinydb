# ADR-004: State Persistence, Inter-Stage Storage, and Run Recovery

## Status
Accepted

## Context
An autonomous SDLC workflow executes across multiple asynchronous stages and may experience transient network blips, API rate limits, or runner cancellations. We must decide where and how stage outputs, operational logs, and execution state are persisted between stages and across potential run restarts.

Options considered:
1. **GitHub PR Comments / Issue Comments as State**: Storing intermediate state by posting JSON blobs or markdown updates as comments on the issue or PR.
2. **GitHub Actions Cache / Step Outputs**: Storing state purely in memory / environment variables and GHA caching mechanisms.
3. **Artifact-First Filesystem on Dedicated Git Branch + GHA Workflow Artifacts**: Maintaining a local structured `.autose/` directory on the issue branch containing all stage artifacts (`spec.md`, `design.md`, `diff.patch`, `test_report.md`, `review.md`, and `state.json`), committed and uploaded as GitHub Actions artifacts.

Option 1 creates extreme notification spam for maintainers and exposes operational state to tampering. Option 2 does not survive cross-run debugging or maintainer inspection if a run fails mid-flight.

## Decision
We choose **Artifact-First Filesystem on Dedicated Git Branch + GHA Workflow Artifacts**:
- All stage results are stored as discrete files under `.autose/` within the runner workspace:
  - `.autose/spec.md`
  - `.autose/design.md`
  - `.autose/diff.patch`
  - `.autose/test_report.md`
  - `.autose/pr.md`
  - `.autose/review.md`
  - `.autose/state.json` (records current stage, retry counters, token tallies, commit hashes)
- At the conclusion of every stage, the state is persisted to disk and bundled into the GitHub Actions artifact upload (`actions/upload-artifact@v4`).
- **Restart Semantics**: If a run is re-triggered on the same issue branch (`autose/issue-<num>`), the orchestrator inspects `.autose/state.json`. If prior stages successfully passed their verification gates, the orchestrator can fast-forward past completed stages or resume from the last failed verification gate rather than re-executing from scratch.

## Consequences
### Positive
- Total visibility: maintainers and auditors can inspect any historical run simply by downloading the GHA workflow artifacts or inspecting the PR description.
- High resilience: state survives transient GHA runner failures.
- No spam: zero extraneous comment creation during intermediate computation.

### Negative
- Branch workspace must be carefully managed so that `.autose/` metadata files are ignored by git during patch generation or stored in an isolated git notes / artifact directory.
