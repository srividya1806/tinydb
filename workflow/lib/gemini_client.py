"""Direct lightweight Gemini API client using standard library urllib."""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple


class GeminiClient:
    def __init__(self, api_key: Optional[str] = None, default_model: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.default_model = default_model or os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
        self.total_prompt_tokens = 0
        self.total_candidate_tokens = 0

    def set_api_key(self, api_key: str):
        self.api_key = api_key

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Call Gemini generateContent endpoint with candidate fallback and retry logic."""
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set. Please provide a valid Gemini API key.")

        preferred_model = model or self.default_model
        candidate_models = list(dict.fromkeys([preferred_model, "gemini-2.0-flash", "gemini-1.5-flash"]))

        last_error = None
        for candidate in candidate_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{candidate}:generateContent?key={self.api_key}"

            payload: Dict[str, Any] = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": prompt}],
                    }
                ],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                },
            }

            if system_instruction:
                payload["systemInstruction"] = {
                    "parts": [{"text": system_instruction}]
                }

            if tools:
                payload["tools"] = [{"functionDeclarations": tools}]

            data = json.dumps(payload).encode("utf-8")
            headers = {"Content-Type": "application/json"}

            max_retries = 3
            base_delay = 2.0

            for attempt in range(max_retries):
                try:
                    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
                    with urllib.request.urlopen(req, timeout=90) as response:
                        body = response.read().decode("utf-8")
                        result = json.loads(body)
                        
                        # Track token usage
                        usage = result.get("usageMetadata", {})
                        self.total_prompt_tokens += usage.get("promptTokenCount", 0)
                        self.total_candidate_tokens += usage.get("candidatesTokenCount", 0)
                        return result

                except urllib.error.HTTPError as e:
                    err_body = e.read().decode("utf-8", errors="replace")
                    if e.code == 404:
                        print(f"[GeminiClient] Model '{candidate}' returned 404. Trying fallback...", file=sys.stderr)
                        break  # Try next candidate model
                    if e.code in (429, 500, 503):
                        wait_time = base_delay * (2 ** attempt)
                        print(f"[GeminiClient] Model '{candidate}' HTTP {e.code} on attempt {attempt+1}/{max_retries}. Backing off {wait_time:.1f}s...", file=sys.stderr)
                        time.sleep(wait_time)
                        continue
                    last_error = RuntimeError(f"Gemini API HTTP {e.code}: {err_body}")
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        wait_time = base_delay * (2 ** attempt)
                        print(f"[GeminiClient] Error {e} on attempt {attempt+1}/{max_retries}. Backing off {wait_time:.1f}s...", file=sys.stderr)
                        time.sleep(wait_time)
                        continue
                    last_error = e
                    break

        if last_error:
            raise RuntimeError(f"Gemini API call failed across candidate models {candidate_models}: {last_error}")
        raise RuntimeError(f"Gemini API call failed across candidate models: {candidate_models}")

    def extract_text(self, response: Dict[str, Any]) -> str:
        """Extract text from the response."""
        candidates = response.get("candidates", [])
        if not candidates:
            return ""
        parts = candidates[0].get("content", {}).get("parts", [])
        text_parts = [p.get("text", "") for p in parts if "text" in p]
        return "\n".join(text_parts).strip()

    def get_token_summary(self) -> Dict[str, int]:
        return {
            "prompt_tokens": self.total_prompt_tokens,
            "candidate_tokens": self.total_candidate_tokens,
            "total_tokens": self.total_prompt_tokens + self.total_candidate_tokens,
        }
