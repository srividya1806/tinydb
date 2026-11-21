"""Independent Reviewer Agent (Stage 6): Evaluates PR diff with zero upstream context."""

import json
import re
from typing import Any, Dict, Tuple
from workflow.lib.gemini_client import GeminiClient
from workflow.lib.tools import ToolHarness


REVIEWER_SYSTEM_PROMPT = """You are an Independent, Senior Code Reviewer in an autonomous SDLC.
Your mission is to perform rigorous, adversarial code review on the proposed Pull Request changes.

CRITICAL REVIEWER GUIDELINES:
1. INDEPENDENCE: You have no prior conversation context and no loyalty to the author. Do NOT give benefit of the doubt or rubber-stamp changes.
2. CORRECTNESS & REGRESSIONS: Scrutinize the diff line-by-line. Does it genuinely satisfy the original issue without introducing regressions, memory leaks, or unhandled edge cases?
3. ARCHITECTURAL INTEGRITY: Does the code adhere to the component boundaries and design principles of the project?
4. EDGE CASES: Look for zero/negative inputs, NoneType handling, empty iterators/generators, missing exception catches, and thread/process safety.

You must format your final review decision in the following exact JSON structure within a ```json codeblock:

```json
{
  "verdict": "APPROVE" or "REQUEST_CHANGES",
  "scope": "NONE" or "CODE" or "DESIGN",
  "summary": "1-2 sentence executive summary of review",
  "strengths": ["List of good practices observed"],
  "issues": [
    {
      "file": "path/to/file.py",
      "line_or_symbol": "line number or function name",
      "severity": "BLOCKING" or "SUGGESTION",
      "description": "Clear explanation of the defect"
    }
  ],
  "recommendation": "Concrete actionable guidance for author if changes requested"
}
```
If ANY blocking issues or unhandled edge cases exist, your verdict MUST be `REQUEST_CHANGES`. Only set verdict to `APPROVE` if the change is complete, correct, and robust.
"""


class ReviewerAgent:
    def __init__(self, client: GeminiClient, harness: ToolHarness, model: str = "gemini-3.8-flash"):
        self.client = client
        self.harness = harness
        self.model = model

    def run(self, issue_title: str, issue_body: str, diff_content: str) -> Tuple[str, Dict[str, Any]]:
        arch_overview = self.harness.read_file("ARCHITECTURE.md", max_lines=300)

        prompt = f"""Conduct an independent, adversarial code review of the proposed changes for the issue below.

<untrusted_user_input>
Issue Title: {issue_title}
Issue Description:
{issue_body}
</untrusted_user_input>

### Project Architecture Overview (ARCHITECTURE.md):
{arch_overview}

### Pull Request Diff to Review:
```diff
{diff_content}
```

Review this diff thoroughly. Test boundary conditions mentally. Output your decision and issues in the specified JSON format.
"""
        response = self.client.generate(
            prompt=prompt,
            system_instruction=REVIEWER_SYSTEM_PROMPT,
            model=self.model,
            temperature=0.0,
            max_tokens=4096,
        )
        response_text = self.client.extract_text(response)

        # Parse structured verdict
        parsed_decision = {
            "verdict": "REQUEST_CHANGES",
            "scope": "CODE",
            "summary": "Failed to parse reviewer structured JSON.",
            "issues": [],
            "recommendation": response_text,
        }

        json_match = re.search(r"```json\s*(.*?)\s*```", response_text, re.DOTALL)
        if json_match:
            try:
                parsed_decision = json.loads(json_match.group(1))
            except Exception as e:
                parsed_decision["summary"] = f"JSON parse error: {e}"
        elif "APPROVE" in response_text and "REQUEST_CHANGES" not in response_text:
            parsed_decision["verdict"] = "APPROVE"
            parsed_decision["scope"] = "NONE"
            parsed_decision["summary"] = "Approved upon heuristic evaluation."

        # Format review.md
        review_md = f"""# Independent Pull Request Review Report

## Review Verdict: **{parsed_decision.get('verdict', 'REQUEST_CHANGES')}**
- **Target Feedback Scope**: `{parsed_decision.get('scope', 'CODE')}`
- **Executive Summary**: {parsed_decision.get('summary', 'No summary provided.')}

### Strengths
"""
        for s in parsed_decision.get("strengths", []):
            review_md += f"- {s}\n"

        review_md += "\n### Identified Issues & Concerns\n"
        issues = parsed_decision.get("issues", [])
        if not issues:
            review_md += "No blocking issues identified.\n"
        else:
            for item in issues:
                review_md += f"- **[{item.get('severity', 'BLOCKING')}]** `{item.get('file', 'general')}` ({item.get('line_or_symbol', 'N/A')}): {item.get('description', '')}\n"

        review_md += f"\n### Recommendations\n{parsed_decision.get('recommendation', 'N/A')}\n"

        return review_md, parsed_decision

    @staticmethod
    def verify(review_decision: Dict[str, Any], current_round: int, max_rounds: int = 2) -> Tuple[bool, str]:
        """Gate 6 Check: The reviewer approves, or two review rounds are used up."""
        verdict = review_decision.get("verdict", "REQUEST_CHANGES")
        if verdict == "APPROVE":
            return True, "Gate 6 Passed: Reviewer approved the Pull Request."
        elif current_round >= max_rounds:
            return True, f"Gate 6 Passed: Maximum review rounds ({max_rounds}) reached; escalating to human maintainer."
        else:
            return False, f"Gate 6 Pending: Reviewer requested changes (Round {current_round}/{max_rounds})."
