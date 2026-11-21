"""Implementation Agent (Stage 3): Modifies code following design.md and outputs diff.patch."""

import ast
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from workflow.lib.gemini_client import GeminiClient
from workflow.lib.tools import ToolHarness


IMPLEMENTATION_SYSTEM_PROMPT = """You are the Implementation Agent in an autonomous Software Development Lifecycle (SDLC).
Your task is to implement the exact code changes specified in design.md.

RULES:
1. Only modify files identified in the design.
2. Produce clean, idiomatic, syntactically valid Python code.
3. Preserve all existing behaviors and backward compatibility.
4. Output your edits using explicit file blocks in the following exact format:

```file:path/to/file.py
[FULL REPLACEMENT CONTENT OF THE FILE]
```

You may provide multiple ```file:path...``` blocks if multiple files need changes. Do not output conversational filler outside or around these blocks.
"""


class ImplementationAgent:
    def __init__(self, client: GeminiClient, harness: ToolHarness, model: Optional[str] = None):
        self.client = client
        self.harness = harness
        self.model = model or client.default_model

    def run(self, design_content: str, spec_content: str, error_feedback: str = "") -> Tuple[str, List[str]]:
        # Identify target files from design with flexible regex
        raw_matches = re.findall(r"([a-zA-Z0-9_\-\./]+\.py)", design_content)
        file_matches = list(set([f.strip("`'\" ") for f in raw_matches if not f.endswith(".md")]))
        
        # Prioritize files that actually exist in tinydb/ or tests/
        valid_targets = []
        for f in file_matches:
            if (self.harness.workspace_root / f).exists():
                valid_targets.append(f)
            elif (self.harness.workspace_root / "tinydb" / Path(f).name).exists():
                valid_targets.append(f"tinydb/{Path(f).name}")
        valid_targets = list(set(valid_targets)) or ["tinydb/table.py"]

        target_file_contexts = []
        for f in valid_targets:
            content = self.harness.read_file(f, max_lines=600)
            if not content.startswith("Error"):
                target_file_contexts.append(f"### Current Content of `{f}`:\n```python\n{content}\n```")

        joined_contexts = "\n\n".join(target_file_contexts)
        prompt = f"""Implement the changes according to the design plan.

### Specification:
{spec_content}

### Design Plan:
{design_content}

### Target File Contexts:
{joined_contexts}
"""
        if error_feedback:
            prompt += f"\n### ERROR FEEDBACK FROM PREVIOUS RUN / TESTS:\n{error_feedback}\nFix the implementation to resolve this exact error.\n"

        response = self.client.generate(
            prompt=prompt,
            system_instruction=IMPLEMENTATION_SYSTEM_PROMPT,
            model=self.model,
            temperature=0.1,
            max_tokens=8192,
        )
        response_text = self.client.extract_text(response)

        # Parse file blocks and apply them
        modified_files = []
        file_blocks = re.findall(r"```(?:file:)?([a-zA-Z0-9_\-\./]+\.py)\n(.*?)```", response_text, re.DOTALL)
        if not file_blocks:
            # Fallback: if single python block and single target file
            py_blocks = re.findall(r"```python\n(.*?)```", response_text, re.DOTALL)
            if py_blocks and len(valid_targets) == 1:
                file_blocks = [(valid_targets[0], py_blocks[0])]

        for rel_path, new_content in file_blocks:
            rel_path = rel_path.strip()
            self.harness.write_file(rel_path, new_content)
            modified_files.append(rel_path)

        diff = self.harness.get_git_diff()
        return diff, modified_files

    def verify(self, modified_files: List[str]) -> Tuple[bool, str]:
        """Gate 3 Check: The code builds and parses cleanly with AST."""
        if not modified_files:
            return False, "Gate 3 Failed: No files were modified."

        for f in modified_files:
            if f.endswith(".py"):
                ok, msg = self.harness.check_syntax(f)
                if not ok:
                    return False, f"Gate 3 Failed: Syntax check failed on {f}: {msg}"

        return True, f"Gate 3 Passed: All modified files ({len(modified_files)}) compiled cleanly."
