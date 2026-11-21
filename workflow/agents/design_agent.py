"""Design Agent (Stage 2): Formulates design.md based on spec.md and ARCHITECTURE.md."""

import re
from pathlib import Path
from typing import Tuple
from workflow.lib.gemini_client import GeminiClient
from workflow.lib.tools import ToolHarness


DESIGN_SYSTEM_PROMPT = """You are the Design Agent in an autonomous Software Development Lifecycle (SDLC).
Your task is to plan the exact code changes needed to satisfy the specification (spec.md) while adhering to the project's architecture document (ARCHITECTURE.md).

Your output must be a Markdown document with the following exact structure:

# Design Plan

## 1. Architectural Alignment
Explain how this change fits into the existing component architecture defined in ARCHITECTURE.md.

## 2. Target Files and Functions to Change
List every file and function/class to be modified or created. Format as:
- `path/to/file.py`: `function_or_class_name()` - [Nature of modification]

## 3. Step-by-Step Implementation Strategy
1. Step 1: ...
2. Step 2: ...
3. Step 3: ...

## 4. Edge Cases and Defensive Considerations
- Edge case handling
- Boundary conditions (empty inputs, None, type safety)
"""


class DesignAgent:
    def __init__(self, client: GeminiClient, harness: ToolHarness, model: str = "gemini-3.8-flash"):
        self.client = client
        self.harness = harness
        self.model = model

    def run(self, spec_content: str, feedback: str = "") -> str:
        arch_content = self.harness.read_file("ARCHITECTURE.md", max_lines=400)
        repo_files = self.harness.list_dir("tinydb")

        prompt = f"""Generate the design document (design.md) for the following specification.

### Project Architecture Overview (ARCHITECTURE.md):
{arch_content}

### Available Source Files in tinydb/:
{repo_files}

### Specification (spec.md):
{spec_content}
"""
        if feedback:
            prompt += f"\n### Feedback from previous failed attempt / review:\n{feedback}\nPlease address this feedback directly in your updated design.\n"

        response = self.client.generate(
            prompt=prompt,
            system_instruction=DESIGN_SYSTEM_PROMPT,
            model=self.model,
            temperature=0.1,
        )
        design_content = self.client.extract_text(response)
        return design_content

    @staticmethod
    def verify(design_content: str, workspace_root: Path) -> Tuple[bool, str]:
        """Gate 2 Check: The plan names the files and functions to change."""
        if not design_content or len(design_content.strip()) < 100:
            return False, "Gate 2 Failed: design.md is empty or trivially short."

        if "Target Files" not in design_content:
            return False, "Gate 2 Failed: Missing 'Target Files and Functions' section."

        # Find file references like `tinydb/...`
        file_matches = re.findall(r"`([a-zA-Z0-9_\-\./]+\.py)`", design_content)
        if not file_matches:
            return False, "Gate 2 Failed: No explicit Python file paths (`*.py`) named in design."

        # Verify that at least one named file exists in the codebase or has valid target location
        existing_targets = [f for f in file_matches if (workspace_root / f).exists()]
        if not existing_targets:
            return False, f"Gate 2 Failed: None of the named target files exist in repository: {file_matches}"

        return True, f"Gate 2 Passed: Verified target files exist: {existing_targets}"
