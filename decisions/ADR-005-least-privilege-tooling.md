# ADR-005: Least-Privilege Tooling and Capability Sandboxing

## Status
Accepted

## Context
Autonomous agents require tools to read code, edit files, execute tests, and interact with GitHub. However, granting broad tool access (e.g. arbitrary bash shell execution or unrestricted write permissions to all agents) introduces catastrophic failure modes:
1. An agent may accidentally force-push to `main` or modify workflow YAML files.
2. An agent may execute destructive shell commands (`rm -rf`, curl external domains).
3. A reviewer agent granted write tools might attempt to fix code directly rather than independently critiquing it.

We must decide how tools are implemented, scoped, and provisioned to each agent role.

Options considered:
1. **GitHub MCP Server / Generic MCP Tool Server**: Running external Model Context Protocol server processes.
2. **Unrestricted Bash Execution**: Providing a single generic `bash` execution tool to all agents.
3. **Role-Scoped Python Harness with Typed Tool Schemas**: Defining tightly typed, role-specific Python functions with strict filesystem and command constraints.

Option 1 introduces external process management complexity and protocol latency in GHA runners. Option 2 violates least privilege, allowing untrusted code or prompt injection to compromise the runner.

## Decision
We choose **Role-Scoped Python Harness with Typed Tool Schemas**:
Tools are defined as standard JSON schemas passed to the Gemini API tool-calling mechanism, with dispatch handled by our Python runner:
- **Read-Only Inspection Tools** (`read_file`, `list_directory`, `search_symbol`, `view_architecture`): Available to Requirements, Design, Implementation, Testing, and Reviewer.
- **Code Modification Tools** (`write_file`, `replace_in_file`): Available **strictly** to Implementation and Testing agents. Restricted from touching `.github/workflows/`, `decisions/`, or hidden test paths.
- **Execution Tools** (`run_pytest`, `check_syntax`): Available to Testing and Reviewer agents. Execution is locked down to invoking `pytest` via `uv` or `python3 -m pytest` with hard execution timeouts (30s).
- **GitHub API Tools** (`create_pull_request`, `post_review_comment`): Executed deterministically by the orchestrator using `gh` CLI or GitHub REST API with repository token. No LLM agent is granted direct token access or push credentials.

## Consequences
### Positive
- Strict security: Impossible for an LLM agent to push malicious commits to protected branches or exfiltrate environment secrets.
- Deterministic boundary: The reviewer can run tests to verify diffs but cannot alter the diff.
- Self-contained: No external MCP daemon required on the GHA runner.

### Negative
- Custom tool definitions must be maintained in the harness repository.
