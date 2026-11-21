"""Safe tools execution harness with role-based restrictions."""

import ast
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class ToolHarness:
    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = (workspace_root or Path.cwd()).resolve()
        # Protected directories that cannot be modified by agents
        self.protected_prefixes = [
            ".git",
            ".github/workflows",
            "decisions",
            "architecture",
            "experiment/hidden_tests",
        ]

    def _resolve_safe_path(self, relative_path: str) -> Path:
        resolved = (self.workspace_root / relative_path).resolve()
        if not str(resolved).startswith(str(self.workspace_root)):
            raise PermissionError(f"Access denied: path {relative_path} is outside workspace root.")
        return resolved

    def _check_write_permission(self, relative_path: str):
        norm = Path(relative_path).as_posix()
        for prefix in self.protected_prefixes:
            if norm == prefix or norm.startswith(prefix + "/"):
                raise PermissionError(f"Access denied: modifying '{relative_path}' is protected by security policy.")

    def read_file(self, path: str, max_lines: int = 500) -> str:
        """Read lines from a file."""
        safe_path = self._resolve_safe_path(path)
        if not safe_path.exists():
            return f"Error: File '{path}' does not exist."
        try:
            with open(safe_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
                if len(lines) > max_lines:
                    content = "".join(lines[:max_lines])
                    return f"{content}\n... [Truncated: {len(lines) - max_lines} more lines]"
                return "".join(lines)
        except Exception as e:
            return f"Error reading file '{path}': {e}"

    def write_file(self, path: str, content: str) -> str:
        """Write content to a file with directory creation and security checks."""
        self._check_write_permission(path)
        safe_path = self._resolve_safe_path(path)
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(safe_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Successfully wrote {len(content)} bytes to '{path}'."
        except Exception as e:
            return f"Error writing file '{path}': {e}"

    def replace_in_file(self, path: str, target: str, replacement: str) -> str:
        """Replace exact target string in file."""
        self._check_write_permission(path)
        safe_path = self._resolve_safe_path(path)
        if not safe_path.exists():
            return f"Error: File '{path}' does not exist."
        try:
            with open(safe_path, "r", encoding="utf-8") as f:
                content = f.read()
            if target not in content:
                return f"Error: Target text not found in '{path}'."
            new_content = content.replace(target, replacement, 1)
            with open(safe_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            return f"Successfully replaced target in '{path}'."
        except Exception as e:
            return f"Error updating file '{path}': {e}"

    def list_dir(self, path: str = ".") -> str:
        """List files and folders in directory."""
        safe_path = self._resolve_safe_path(path)
        if not safe_path.exists():
            return f"Error: Directory '{path}' does not exist."
        try:
            entries = []
            for item in sorted(os.listdir(safe_path)):
                if item in (".git", "__pycache__", ".pytest_cache", ".venv"):
                    continue
                p = safe_path / item
                suffix = "/" if p.is_dir() else ""
                entries.append(f"{item}{suffix}")
            return "\n".join(entries) if entries else "(empty directory)"
        except Exception as e:
            return f"Error listing directory '{path}': {e}"

    def search_code(self, query: str, search_path: str = ".") -> str:
        """Search for code matching query."""
        safe_path = self._resolve_safe_path(search_path)
        matches = []
        for root, dirs, files in os.walk(safe_path):
            dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", ".pytest_cache", ".venv", ".autose")]
            for f in files:
                if not (f.endswith(".py") or f.endswith(".md") or f.endswith(".toml") or f.endswith(".rst")):
                    continue
                file_path = Path(root) / f
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as fp:
                        for idx, line in enumerate(fp, start=1):
                            if query.lower() in line.lower():
                                rel = file_path.relative_to(self.workspace_root)
                                matches.append(f"{rel}:{idx}: {line.strip()}")
                                if len(matches) >= 50:
                                    return "\n".join(matches) + "\n... [Max 50 results reached]"
                except Exception:
                    continue
        return "\n".join(matches) if matches else f"No matches found for '{query}'."

    def check_syntax(self, path: str) -> Tuple[bool, str]:
        """Check whether a python file compiles cleanly with AST parse."""
        safe_path = self._resolve_safe_path(path)
        if not safe_path.exists():
            return False, f"File '{path}' does not exist."
        try:
            with open(safe_path, "r", encoding="utf-8") as f:
                code = f.read()
            ast.parse(code, filename=path)
            return True, f"Syntax check passed for '{path}'."
        except SyntaxError as e:
            return False, f"Syntax error in '{path}' at line {e.lineno}: {e.msg}\n  {e.text}"
        except Exception as e:
            return False, f"AST verification failed for '{path}': {e}"

    def run_tests(self, test_path: Optional[str] = None, timeout_sec: int = 45) -> Dict[str, Any]:
        """Execute pytest using uv or python3 with strict timeout."""
        cmd = ["pytest", "-v"]
        if test_path:
            cmd.append(test_path)

        # Prefer uv if available, otherwise fallback to python3 -m pytest
        uv_path = "/Users/eshwarg/.local/bin/uv"
        if os.path.exists(uv_path):
            exec_cmd = [uv_path, "run"] + cmd
        elif subprocess.run(["which", "uv"], capture_output=True).returncode == 0:
            exec_cmd = ["uv", "run"] + cmd
        else:
            exec_cmd = [sys.executable, "-m"] + cmd

        try:
            proc = subprocess.run(
                exec_cmd,
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                timeout=timeout_sec,
            )
            stdout = proc.stdout
            stderr = proc.stderr
            passed = proc.returncode == 0

            # Parse pytest summary
            summary_match = re.search(r"=+\s*(.*?)\s*=+$", stdout.strip())
            summary = summary_match.group(1) if summary_match else f"exited with code {proc.returncode}"

            return {
                "success": passed,
                "returncode": proc.returncode,
                "summary": summary,
                "stdout": stdout,
                "stderr": stderr,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "returncode": -1,
                "summary": f"Pytest timed out after {timeout_sec} seconds.",
                "stdout": "",
                "stderr": f"Timeout expired after {timeout_sec}s",
            }
        except Exception as e:
            return {
                "success": False,
                "returncode": -1,
                "summary": f"Failed to execute tests: {e}",
                "stdout": "",
                "stderr": str(e),
            }

    def get_git_diff(self, base_ref: str = "HEAD") -> str:
        """Get git diff from base ref."""
        try:
            proc = subprocess.run(
                ["git", "diff", base_ref],
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
            )
            return proc.stdout
        except Exception as e:
            return f"Error getting git diff: {e}"
