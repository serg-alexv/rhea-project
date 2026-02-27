#!/usr/bin/env python3
"""
dispatch.py — Rex dispatches tasks to Orion and Gemini via their APIs.

Same mechanism as tribunal (bridge calls multiple models),
but instead of a scientific question — a coding task with contract + context.

Rex reads code, builds the prompt, calls the API, gets back a diff, applies it.
No Codex CLI, no Jules, no special tooling. Just API calls.

Usage:
    from contracts.dispatch import Dispatcher
    d = Dispatcher()
    result = d.assign("orion", task=..., contract=..., code_context=...)
"""

import sys
import os
import json
from pathlib import Path
from dataclasses import dataclass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@dataclass
class TaskResult:
    agent: str
    success: bool
    diff: str               # unified diff to apply
    explanation: str         # what was done and why
    files_changed: list[str]
    acceptance_passed: bool | None  # None = not yet tested


AGENT_MODELS = {
    "orion": "openai/gpt-4o",       # GPT-5.3 when available; gpt-4o as current best
    "gemini": "google/gemini-2.0-flash",  # Gemini 3.1 when available
}

SYSTEM_PROMPT = """You are a senior engineer working within a strict contract boundary.

You receive:
1. A CONTRACT — the interface you must respect. Do not change types that cross the boundary.
2. CODE CONTEXT — the current implementation files.
3. AN OBJECTIVE — what to improve.

You return:
1. A unified diff (```diff ... ```) that achieves the objective.
2. A brief explanation of what you changed and why.
3. A list of files changed.

Rules:
- Stay within the contract boundary. Do not modify files outside your scope.
- Do not add dependencies.
- Do not refactor beyond the objective.
- If you cannot achieve the objective within the contract, say so and explain why.
"""


class Dispatcher:
    def __init__(self, bridge=None):
        if bridge is None:
            from rhea_bridge import RheaBridge
            bridge = RheaBridge()
        self.bridge = bridge

    def _build_prompt(self, objective: str, contract_path: str,
                      code_files: list[str]) -> str:
        """Build the full prompt with contract + code context + objective."""
        parts = [f"## Objective\n{objective}\n"]

        # Read contract
        contract = Path(contract_path)
        if contract.exists():
            parts.append(f"## Contract ({contract.name})\n```python\n{contract.read_text()}\n```\n")

        # Read code files
        for fpath in code_files:
            p = Path(fpath)
            if p.exists():
                parts.append(f"## File: {p.name}\n```python\n{p.read_text()}\n```\n")

        parts.append("## Instructions\nReturn a unified diff and explanation. Nothing else.")
        return "\n".join(parts)

    def assign(self, agent: str, objective: str, contract_path: str,
               code_files: list[str], max_tokens: int = 4096) -> TaskResult:
        """Dispatch a task to Orion or Gemini and get back a result."""
        if agent not in AGENT_MODELS:
            raise ValueError(f"Unknown agent: {agent}. Valid: {list(AGENT_MODELS.keys())}")

        model = AGENT_MODELS[agent]
        prompt = self._build_prompt(objective, contract_path, code_files)

        try:
            result = self.bridge.ask(
                model=model,
                prompt=prompt,
                system=SYSTEM_PROMPT,
                max_tokens=max_tokens,
            )
            text = result.get("text", "") if isinstance(result, dict) else str(result)
            diff, explanation, files = self._parse_response(text)

            return TaskResult(
                agent=agent,
                success=bool(diff),
                diff=diff,
                explanation=explanation,
                files_changed=files,
                acceptance_passed=None,
            )

        except Exception as e:
            return TaskResult(
                agent=agent,
                success=False,
                diff="",
                explanation=f"API call failed: {e}",
                files_changed=[],
                acceptance_passed=None,
            )

    def assign_parallel(self, tasks: list[dict]) -> list[TaskResult]:
        """Dispatch multiple tasks in parallel (one per pyramid)."""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        results = []
        with ThreadPoolExecutor(max_workers=len(tasks)) as pool:
            futures = {
                pool.submit(self.assign, **task): task["agent"]
                for task in tasks
            }
            for future in as_completed(futures):
                results.append(future.result())
        return results

    def _parse_response(self, text: str) -> tuple[str, str, list[str]]:
        """Extract diff, explanation, and file list from model response."""
        diff = ""
        explanation = ""
        files = []

        # Extract diff block
        import re
        diff_match = re.search(r'```diff\n(.*?)```', text, re.DOTALL)
        if diff_match:
            diff = diff_match.group(1).strip()
            # Extract filenames from diff headers
            files = re.findall(r'^[+-]{3} [ab]/(.+)$', diff, re.MULTILINE)
            files = list(set(files))

        # Everything outside the diff block is explanation
        explanation = re.sub(r'```diff\n.*?```', '', text, flags=re.DOTALL).strip()

        return diff, explanation, files


if __name__ == "__main__":
    print("Dispatcher ready.")
    print(f"Agents: {list(AGENT_MODELS.keys())}")
    print(f"Models: {json.dumps(AGENT_MODELS, indent=2)}")
    print("\nUsage:")
    print("  d = Dispatcher()")
    print('  result = d.assign("orion",')
    print('      objective="Fix stance detection word boundaries",')
    print('      contract_path="contracts/consensus_to_aletheia.py",')
    print('      code_files=["src/consensus_analyzer.py"])')
