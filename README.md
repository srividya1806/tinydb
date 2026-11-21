# AutoSE: Architecting an Agentic SDLC Workflow

**Student Roll Number:** 2025204020  
**Target Repository Fork:** [https://github.com/srividya1806/tinydb](https://github.com/srividya1806/tinydb)  
**Pinned Upstream Commit:** `edff96a` (`msiemens/tinydb@edff96a`)  
**Demo Video:** [demo.mp4](./demo.mp4) (4m 42s walkthrough of Issue #3, Run #44879709730, PR #6, and 2-round review backtrack)

---

## 1. Overview

This repository implements an autonomous GitHub Actions workflow that converts a user-reported GitHub issue into a tested, verified, and independently reviewed pull request.

The system is designed according to rigorous software architecture principles:
- **Role Separation**: 5 distinct agent specializations (Requirements, Design, Implementation, Testing, Review).
- **Adversarial Reviewer Independence**: The Reviewer runs in an isolated context with zero prior upstream thoughts, read-only tools, and no push permissions.
- **Bounded Backtracking Loops**: Self-healing test failure loops (max 3 retries) and reviewer change feedback loops (max 2 rounds).
- **Deterministic Verification Gates**: Code correctness, syntax, and test suites are checked using deterministic tools (`ast`, `pytest`, `git`), never subjective self-grading.
- **Human-in-the-Loop**: The maintainer always retains final merge and close authority.

---

## 2. Models & Cost Profile

- **Primary Models**:
  - `gemini-3.8-flash`: Requirements, Design, Implementation, Testing, and Reviewer agents. Highly cost-effective, near-instant sub-second response times, and state-of-the-art code generation.
- **Total Benchmark Cost**: Less than $0.35 total across all 5 benchmark runs and 5 seeded PR evaluations.

---

## 3. How to Trigger the Workflow

Maintainers can trigger the autonomous SDLC workflow in two ways:

### Option A: Issue Label Trigger
Add the label `autose` to any open GitHub issue.

### Option B: Issue Comment Trigger
Post a comment on any open issue starting with:
```text
/autose
```

### Authorization Check
Only repository users with `OWNER`, `MEMBER`, or `COLLABORATOR` permissions (or write access) can trigger workflow runs. Attempts by unauthorized users are automatically rejected with an explanatory message.

---

## 4. Repository Structure

```text
├── README.md                  # Fork URL, commit, models, trigger instructions, AI disclosure
├── report.pdf                 # Comprehensive architectural report
├── architecture/
│   ├── ARCHITECTURE.md        # TinyDB codebase architecture reference
│   └── views/
│       ├── component_view.md  # Component diagram & agent interaction topology
│       ├── sequence_view.md   # End-to-end execution sequence diagram
│       └── stage_map.md       # Stage, Agent, Artifact, and Check matrix
├── decisions/                 # Formal Nygard-format Architecture Decision Records
│   ├── ADR-001-splitting-the-work.md
│   ├── ADR-002-control-flow-and-orchestration.md
│   ├── ADR-002a-linear-single-shot-pipeline.md (Superseded)
│   ├── ADR-003-information-handoffs.md
│   ├── ADR-004-state-persistence.md
│   ├── ADR-005-least-privilege-tooling.md
│   ├── ADR-006-model-selection-strategy.md
│   ├── ADR-007-stage-verification-checks.md
│   ├── ADR-008-reviewer-independence.md
│   ├── ADR-008a-shared-context-reviewer.md (Superseded)
│   ├── ADR-009-safety-timeouts-prompt-injection.md
│   └── ADR-010-trigger-and-concurrency-control.md
├── workflow/
│   ├── .github/workflows/autose.yml
│   ├── runner.py              # State-machine orchestrator
│   ├── agents/                # Role agents (Requirements, Design, Impl, Test, Review)
│   └── lib/                   # Lightweight Gemini API client and tool harness
├── experiment/
│   ├── issues/                # 5 benchmark issues (2 bugs, 2 features, 1 vague)
│   ├── hidden_tests/          # Hidden acceptance test suites
│   ├── seeded_prs/            # 5 seeded PR diffs for reviewer rigor evaluation
│   └── variants.md            # In-depth analysis of tested ADR variants
└── results/
    ├── results.csv            # Detailed benchmark quantitative metrics
    └── runs.md                # Direct links to Actions runs, PRs, and review comments
```

---

## 5. AI Assistance Disclosure

In accordance with course policies:
Coding agents (Google Gemini / Claude) assisted in scaffold generation, test scaffolding, and initial drafting. All architectural designs, ADR decisions, verification gate formulations, reviewer independence boundaries, and report analyses were reviewed, validated, and refined by the author.
