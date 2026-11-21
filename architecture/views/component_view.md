# Component View: Agentic SDLC Architecture

## 1. System Overview

The Agentic SDLC Workflow is designed as an automated, multi-agent pipeline executing within GitHub Actions. It ingests an issue (triggered by maintainer label `autose` or comment `/autose`) and orchestrates specialized agent roles to generate a fully tested, validated, and independently reviewed pull request.

The architecture emphasizes **separation of concerns**, **least privilege**, and **adversarial independence** between authoring agents and the reviewing agent.

```mermaid
flowchart TD
    subgraph Trigger ["GitHub Event Trigger & Safety Gate"]
        GH_EVENT["Issue Event (labeled / comment)"] --> AUTH_CHECK{"Maintainer Auth & Concurrency Check"}
        AUTH_CHECK -->|Authorized & Unique| ORCH["Workflow State Orchestrator"]
        AUTH_CHECK -->|Unauthorized or Duplicate| DROP["Abort & Comment"]
    end

    subgraph Pipeline ["Agentic SDLC Core Stages"]
        ORCH -->|Stage 1: Spec| REQ_A["Requirements Agent"]
        REQ_A -->|spec.md| GATE1{"Gate 1: Acceptance Criteria Testable"}
        
        GATE1 -->|Pass| DES_A["Design Agent"]
        DES_A -->|design.md| GATE2{"Gate 2: Target Files/Functions Named"}
        
        GATE2 -->|Pass| IMP_A["Implementation Agent"]
        IMP_A -->|diff.patch| GATE3{"Gate 3: Code Builds & Syntactically Valid"}
        
        GATE3 -->|Pass| TST_A["Testing Agent"]
        TST_A -->|test_report.md| GATE4{"Gate 4: 100% Tests Pass (Old + New)"}
        
        GATE4 -->|Fail (retry <= 3)| IMP_A
        GATE4 -->|Fail (budget exhausted)| DES_A
        GATE4 -->|Pass| REL_A["Release Agent"]
        
        REL_A -->|pr.md + PR URL| GATE5{"Gate 5: PR Open & CI Green"}
    end

    subgraph ReviewGate ["Independent Review & Human Merge Gate"]
        GATE5 -->|Pass| REV_A["Independent Reviewer Agent"]
        REV_A -->|review.md| GATE6{"Gate 6: Review Decision"}
        
        GATE6 -->|Changes: Code Bug (round <= 2)| IMP_A
        GATE6 -->|Changes: Flawed Design (round <= 2)| DES_A
        GATE6 -->|Approved or Max Rounds Used| HUMAN["Maintainer / Human-in-the-Loop"]
        HUMAN -->|Merge or Close| DONE["Final SDLC Resolution"]
    end

    subgraph ToolingLayer ["Agent Tools & Capabilities"]
        direction LR
        T_RO["Read-only Tools:\n- read_file\n- grep_code\n- list_dir"]
        T_RW["Read/Write Tools:\n- edit_file\n- write_file"]
        T_SH["Execution Tools:\n- run_pytest\n- check_syntax"]
        T_GH["GitHub API Tools:\n- gh_create_pr\n- gh_post_comment"]
    end

    REQ_A -.-> T_RO
    DES_A -.-> T_RO
    IMP_A -.-> T_RO & T_RW & T_SH
    TST_A -.-> T_RO & T_RW & T_SH
    REL_A -.-> T_GH
    REV_A -.-> T_RO & T_SH
```

## 2. Component Descriptions

### 2.1 Workflow Orchestrator
- **Responsibility**: State transition management, artifact persistence, loop budget enforcement (max 3 implementation retries, max 2 review rounds), and feedback routing.
- **Runtime**: GitHub Actions runner process executing a lightweight Python harness (`workflow/runner.py`).

### 2.2 Requirements Agent (Stage 1)
- **Role**: Ingests issue title, body, and sanitizes untrusted input. Translates business intent into a crisp specification.
- **Output Artifact**: `spec.md`.
- **Tools**: Read-only codebase exploration.
- **Verification Gate**: Ensures all acceptance criteria are formally structured and deterministically verifiable.

### 2.3 Design Agent (Stage 2)
- **Role**: Examines `spec.md`, `ARCHITECTURE.md`, and relevant module dependencies. Formulates step-by-step modification plan.
- **Output Artifact**: `design.md`.
- **Tools**: Read-only codebase exploration.
- **Verification Gate**: Explicitly validates that target files, classes, and methods exist and match architectural patterns.

### 2.4 Implementation Agent (Stage 3)
- **Role**: Operates in an isolated git branch (`autose/issue-<num>`). Applies precise code modifications following `design.md`.
- **Output Artifact**: `diff.patch`.
- **Tools**: File read, file edit, AST syntax verification.
- **Verification Gate**: Python AST parse check and compilation passes without errors.

### 2.5 Testing Agent (Stage 4)
- **Role**: Authors dedicated unit tests for every acceptance criterion in `spec.md`, and executes the full test suite (`pytest`) to guarantee zero regressions.
- **Output Artifact**: `test_report.md`.
- **Tools**: Test authoring, pytest execution harness.
- **Verification Gate**: 100% of new unit tests pass and all existing baseline regression tests pass. If failures occur, supplies stdout/traceback to Implementation Agent for iterative refinement.

### 2.6 Release Agent (Stage 5)
- **Role**: Pushes the branch to the remote repository, generates PR body containing summary of changes and links to artifacts, and opens the Pull Request.
- **Output Artifact**: `pr.md` + PR URL.
- **Tools**: `gh pr create`, `git push`.
- **Verification Gate**: PR is verified open via GitHub REST API and branch CI passes.

### 2.7 Independent Reviewer Agent (Stage 6)
- **Role**: Provides objective, adversarial code review.
- **Context Isolation**: Fresh LLM context. Receives **only** the original issue text, the git diff (`diff.patch`), and read-only access to repository files. It has **no access** to prior agent chain-of-thought, implementation rationales, or agent chat logs.
- **Permissions**: Read-only repository access + test execution. **Strictly no push rights**.
- **Output Artifact**: `review.md` and GitHub PR review comment.
- **Verification Gate**: Evaluates code correctness, security, architectural adherence, and edge cases. Emits `APPROVE` or `REQUEST_CHANGES` (specifying whether it is an implementation bug or design flaw).
