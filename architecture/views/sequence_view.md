# Sequence View: End-to-End Workflow Execution

This sequence diagram illustrates a representative execution trace of an issue run, including a testing feedback loop (Stage 4 $\to$ Stage 3 backtrack) and a reviewer feedback loop (Stage 6 $\to$ Stage 3 backtrack), culminating in maintainer sign-off.

```mermaid
sequenceDiagram
    autonumber
    actor Maintainer as Repository Maintainer
    participant GH as GitHub (Event / API)
    participant Orch as SDLC Orchestrator
    participant S1 as Stage 1: Requirements Agent
    participant S2 as Stage 2: Design Agent
    participant S3 as Stage 3: Implementation Agent
    participant S4 as Stage 4: Testing Agent
    participant S5 as Stage 5: Release Agent
    participant S6 as Stage 6: Independent Reviewer

    %% Trigger Phase
    Maintainer->>GH: Labels issue "autose" (or comments "/autose")
    GH->>Orch: Trigger workflow event (issues: labeled)
    Note over Orch: Verify actor permissions (write/admin)<br/>Acquire per-issue concurrency lock

    %% Stage 1: Requirements
    Orch->>S1: Prompt with sanitized Issue Title & Body
    S1->>Orch: spec.md (Acceptance Criteria)
    Note over Orch: Gate 1 Check: Acceptance criteria testable? (PASS)

    %% Stage 2: Design
    Orch->>S2: Prompt with spec.md + ARCHITECTURE.md
    S2->>Orch: design.md (Target files & functions)
    Note over Orch: Gate 2 Check: Target files and functions exist? (PASS)

    %% Stage 3 & 4: Initial Implementation & Test Cycle
    Orch->>S3: Prompt with design.md
    S3->>Orch: diff.patch (Code edits applied)
    Note over Orch: Gate 3 Check: Code builds/AST compiles? (PASS)

    Orch->>S4: Prompt with spec.md + diff.patch
    S4->>S4: Author tests/test_acceptance.py & run pytest
    S4-->>Orch: test_report.md (1 failure: edge case generator depleted)
    Note over Orch: Gate 4 Check: All tests pass? (FAIL)<br/>Backtrack 1/3 -> Route traceback to Stage 3

    %% Backtrack Iteration (Stage 3 fix)
    Orch->>S3: Prompt with failure trace from test_report.md
    S3->>Orch: diff.patch (Updated generator reset logic)
    Note over Orch: Gate 3 Check: Code builds? (PASS)

    Orch->>S4: Re-run test suite
    S4-->>Orch: test_report.md (228 baseline + 3 new tests PASS)
    Note over Orch: Gate 4 Check: 100% tests pass (PASS)

    %% Stage 5: Release
    Orch->>S5: Execute release (branch push + create PR)
    S5->>GH: git push autose/issue-42 && gh pr create
    GH-->>S5: PR #43 Created
    S5->>Orch: pr.md (PR #43 link & summary)
    Note over Orch: Gate 5 Check: PR open & CI green (PASS)

    %% Stage 6: Independent Review
    Note over Orch: Flush agent context memory<br/>Spawn reviewer with read-only sandbox
    Orch->>S6: Prompt with PR Diff + Original Issue only
    S6->>S6: Inspect diff & run local tests
    S6->>GH: Post PR Review Comment (REQUEST_CHANGES: Missing docstring / type annotation)
    S6-->>Orch: review.md (Status: REQUEST_CHANGES, Scope: CODE)
    
    %% Backtrack to Stage 3 for Review Feedback
    Note over Orch: Review Round 1/2 used -> Route feedback to Stage 3
    Orch->>S3: Apply requested docstring and type fix
    S3->>GH: git push autose/issue-42 (amend/update)
    Orch->>S4: Run pytest (All tests pass)
    Orch->>S6: Re-evaluate latest PR commit
    S6->>GH: Post PR Review Comment (APPROVE)
    S6-->>Orch: review.md (Status: APPROVED)

    %% Completion & Human Gate
    Orch->>GH: Upload all run artifacts (spec, design, diff, tests, pr, review)
    Orch->>Maintainer: Notify PR #43 ready for human merge decision
    Maintainer->>GH: Inspect PR & Review -> Click "Merge Pull Request"
```
