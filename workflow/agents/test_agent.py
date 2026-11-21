"""Testing Agent (Stage 4): Writes tests for acceptance criteria and runs full suite."""

import re
from typing import Any, Dict, Tuple
from workflow.lib.gemini_client import GeminiClient
from workflow.lib.tools import ToolHarness


TESTING_SYSTEM_PROMPT = """You are the Testing Agent in an autonomous Software Development Lifecycle (SDLC).
Your task is to write high-quality, comprehensive pytest unit tests that thoroughly verify all acceptance criteria defined in spec.md.

RULES:
1. Write tests using pytest idioms and standard assertions.
2. Cover positive cases, negative cases, boundary conditions, and edge cases.
3. Import from tinydb as needed (e.g. `from tinydb import TinyDB, Query`, `from tinydb.operations import ...`, `from tinydb.storages import ...`).
4. Output your test file in the following exact format:

```file:tests/test_autose_acceptance.py
import pytest
from tinydb import TinyDB, Query, where
# other imports...

def test_acceptance_criterion_1(tmp_path):
    ...
```
Do not include commentary outside the code block.
"""


class TestAgent:
    __test__ = False

    def __init__(self, client: GeminiClient, harness: ToolHarness, model: str = "gemini-3.8-flash"):
        self.client = client
        self.harness = harness
        self.model = model

    def run(self, spec_content: str, diff_content: str) -> Tuple[str, Dict[str, Any]]:
        prompt = f"""Write complete pytest unit tests verifying every acceptance criterion in the specification.

### Specification (spec.md):
{spec_content}

### Code Changes Applied (diff.patch):
{diff_content}
"""
        response = self.client.generate(
            prompt=prompt,
            system_instruction=TESTING_SYSTEM_PROMPT,
            model=self.model,
            temperature=0.1,
            max_tokens=4096,
        )
        response_text = self.client.extract_text(response)

        # Extract and write test file
        test_file_path = "tests/test_autose_acceptance.py"
        file_blocks = re.findall(r"```(?:file:)?tests/test_autose_acceptance\.py\n(.*?)```", response_text, re.DOTALL)
        if not file_blocks:
            # Fallback to any python block if specific file tag was missed
            file_blocks = re.findall(r"```python\n(.*?)```", response_text, re.DOTALL)

        if file_blocks:
            self.harness.write_file(test_file_path, file_blocks[0].strip())

        # Execute the test suite
        test_result = self.harness.run_tests()

        # Build test_report.md
        status_str = "PASSED" if test_result["success"] else "FAILED"
        report_md = f"""# Test Execution Report

## Overall Status: {status_str}

### Test Summary
- **Exit Code**: {test_result["returncode"]}
- **Result Summary**: {test_result["summary"]}

### Pytest Console Output
```text
{test_result["stdout"][:4000]}
```

### Errors / Tracebacks (if any)
```text
{test_result["stderr"][:2000]}
```
"""
        return report_md, test_result

    @staticmethod
    def verify(test_result: Dict[str, Any]) -> Tuple[bool, str]:
        """Gate 4 Check: All new and existing tests pass."""
        if test_result.get("success"):
            return True, f"Gate 4 Passed: All tests passed ({test_result.get('summary')})."
        else:
            return False, f"Gate 4 Failed: Test suite failed with summary: {test_result.get('summary')}"
