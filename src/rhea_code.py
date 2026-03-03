#!/usr/bin/env python3
"""
rhea-code — Multi-model AI coding assistant.

Unlike Claude Code (1 provider) or Cursor (Electron bloat):
  - 6 providers, 31 models, cost-aware tier routing
  - Persistent memory across sessions AND models
  - Tribunal consensus for critical decisions
  - Context engine via Aletheia

Usage:
    rhea code                        # Interactive REPL
    rhea code ask "question"         # One-shot query with workspace context
    rhea code edit file.py "instr"   # AI-assisted file edit
    rhea code search "query"         # Semantic search codebase
    rhea code context                # Show loaded context
    rhea code skills                 # List available skills
    rhea code rules                  # Show active rules
    rhea code memory                 # Show persistent memory
    rhea code status                 # Bridge status + models
"""

import json
import os
import re
import readline
import sys
import textwrap
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

# Resolve project root
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from rhea_bridge import RheaBridge, ModelResponse


# ═══════════════════════════════════════════════════════════════════════
# CONTEXT ENGINE — loads workspace rules, skills, memory
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class WorkspaceContext:
    """Aggregated workspace context for the coding assistant."""
    root: Path
    rules: List[Dict[str, str]] = field(default_factory=list)       # [{path, content, type}]
    skills: List[Dict[str, str]] = field(default_factory=list)      # [{name, description, path}]
    memory: Dict[str, str] = field(default_factory=dict)            # {key: value}
    file_tree: List[str] = field(default_factory=list)              # top-level file listing
    git_branch: str = ""
    git_status: str = ""

    def system_prompt(self) -> str:
        """Build system prompt from loaded context."""
        parts = [
            "You are rhea-code, a multi-model AI coding assistant.",
            "You have access to the full workspace and can read/edit files.",
            f"Workspace: {self.root}",
            f"Branch: {self.git_branch}" if self.git_branch else "",
        ]

        # Rules
        for rule in self.rules:
            parts.append(f"\n--- Rules from {rule['path']} ---\n{rule['content'][:2000]}")

        # Skills summary
        if self.skills:
            skill_list = "\n".join(f"  - {s['name']}: {s['description']}" for s in self.skills)
            parts.append(f"\nAvailable skills:\n{skill_list}")

        # Memory
        if self.memory:
            mem_text = "\n".join(f"  {k}: {v}" for k, v in list(self.memory.items())[:20])
            parts.append(f"\nPersistent memory:\n{mem_text}")

        return "\n".join(p for p in parts if p)


def load_context(workspace: Path) -> WorkspaceContext:
    """Load all workspace context: rules, skills, memory, git state."""
    ctx = WorkspaceContext(root=workspace)

    # --- Rules: CLAUDE.md, AGENTS.md, .augment/rules/, .claude/rules/ ---
    rule_files = [
        "CLAUDE.md", "AGENTS.md",
        ".augment/guidelines.md",
    ]
    for rf in rule_files:
        p = workspace / rf
        if p.is_file():
            ctx.rules.append({
                "path": rf,
                "content": p.read_text(errors="replace")[:4000],
                "type": "always_apply",
            })

    # Scan rule directories
    for rule_dir in [".augment/rules", ".claude/rules", ".agents/rules"]:
        rd = workspace / rule_dir
        if rd.is_dir():
            for md in sorted(rd.rglob("*.md")):
                content = md.read_text(errors="replace")[:4000]
                rule_type = "always_apply"
                # Parse frontmatter
                if content.startswith("---"):
                    end = content.find("---", 3)
                    if end > 0:
                        fm = content[3:end]
                        if "agent_requested" in fm:
                            rule_type = "agent_requested"
                        content = content[end + 3:].strip()
                ctx.rules.append({
                    "path": str(md.relative_to(workspace)),
                    "content": content,
                    "type": rule_type,
                })

    # --- Skills: .augment/skills/, .claude/skills/, .agents/skills/ ---
    for skill_dir in [".augment/skills", ".claude/skills", ".agents/skills"]:
        sd = workspace / skill_dir
        if sd.is_dir():
            for skill_md in sorted(sd.rglob("SKILL.md")):
                content = skill_md.read_text(errors="replace")
                name = skill_md.parent.name
                description = ""
                if content.startswith("---"):
                    end = content.find("---", 3)
                    if end > 0:
                        for line in content[3:end].splitlines():
                            if line.strip().startswith("description:"):
                                description = line.split(":", 1)[1].strip()
                ctx.skills.append({
                    "name": name,
                    "description": description,
                    "path": str(skill_md.relative_to(workspace)),
                })

    # --- Memory: .rhea/memory.json ---
    mem_file = workspace / ".rhea" / "memory.json"
    if mem_file.is_file():
        try:
            ctx.memory = json.loads(mem_file.read_text())
        except Exception:
            pass

    # --- Git state ---
    try:
        import subprocess
        r = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, cwd=str(workspace), timeout=5,
        )
        ctx.git_branch = r.stdout.strip()

        r = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True, text=True, cwd=str(workspace), timeout=5,
        )
        ctx.git_status = r.stdout.strip()[:1000]
    except Exception:
        pass

    # --- File tree (top 2 levels) ---
    try:
        import subprocess
        r = subprocess.run(
            ["find", ".", "-maxdepth", "2", "-not", "-path", "./.git/*",
             "-not", "-path", "./node_modules/*", "-not", "-path", "./.next/*"],
            capture_output=True, text=True, cwd=str(workspace), timeout=5,
        )
        ctx.file_tree = sorted(r.stdout.strip().splitlines()[:200])
    except Exception:
        pass

    return ctx


# ═══════════════════════════════════════════════════════════════════════
# MEMORY — persistent key-value across sessions
# ═══════════════════════════════════════════════════════════════════════

class Memory:
    """Simple persistent memory store."""

    def __init__(self, workspace: Path):
        self.path = workspace / ".rhea" / "memory.json"
        self.data: Dict[str, Any] = {}
        self._load()

    def _load(self):
        if self.path.is_file():
            try:
                self.data = json.loads(self.path.read_text())
            except Exception:
                self.data = {}

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2, ensure_ascii=False))

    def remember(self, key: str, value: str):
        self.data[key] = value
        self.save()

    def recall(self, key: str) -> Optional[str]:
        return self.data.get(key)

    def forget(self, key: str):
        self.data.pop(key, None)
        self.save()

    def all(self) -> Dict[str, Any]:
        return dict(self.data)


# ═══════════════════════════════════════════════════════════════════════
# FILE OPERATIONS — read, edit, search
# ═══════════════════════════════════════════════════════════════════════

def read_file(workspace: Path, filepath: str) -> str:
    """Read a file relative to workspace."""
    p = (workspace / filepath).resolve()
    if not str(p).startswith(str(workspace)):
        return f"ERROR: path outside workspace: {filepath}"
    if not p.is_file():
        return f"ERROR: file not found: {filepath}"
    try:
        return p.read_text(errors="replace")
    except Exception as e:
        return f"ERROR: {e}"


def edit_file(workspace: Path, filepath: str, old: str, new: str) -> str:
    """Replace old text with new text in a file."""
    p = (workspace / filepath).resolve()
    if not str(p).startswith(str(workspace)):
        return f"ERROR: path outside workspace: {filepath}"
    if not p.is_file():
        return f"ERROR: file not found: {filepath}"
    try:
        content = p.read_text(errors="replace")
        if old not in content:
            return f"ERROR: old_string not found in {filepath}"
        count = content.count(old)
        if count > 1:
            return f"ERROR: old_string appears {count} times — must be unique"
        content = content.replace(old, new, 1)
        p.write_text(content)
        return f"OK: edited {filepath}"
    except Exception as e:
        return f"ERROR: {e}"


def write_file(workspace: Path, filepath: str, content: str) -> str:
    """Write content to a file (creates dirs as needed)."""
    p = (workspace / filepath).resolve()
    if not str(p).startswith(str(workspace)):
        return f"ERROR: path outside workspace: {filepath}"
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return f"OK: wrote {filepath} ({len(content)} bytes)"
    except Exception as e:
        return f"ERROR: {e}"


def grep_workspace(workspace: Path, pattern: str, max_results: int = 20) -> str:
    """Search workspace files for a pattern."""
    import subprocess
    try:
        r = subprocess.run(
            ["grep", "-rn", "--include=*.py", "--include=*.ts", "--include=*.tsx",
             "--include=*.js", "--include=*.md", "--include=*.sh",
             "--include=*.swift", "--include=*.json",
             "-l", pattern, str(workspace)],
            capture_output=True, text=True, timeout=10,
        )
        files = r.stdout.strip().splitlines()[:max_results]
        return "\n".join(
            str(Path(f).relative_to(workspace)) for f in files
        ) if files else "No matches."
    except Exception as e:
        return f"ERROR: {e}"


# ═══════════════════════════════════════════════════════════════════════
# TOOL DISPATCH — parse and execute tool calls from model output
# ═══════════════════════════════════════════════════════════════════════

TOOL_SCHEMA = """
Available tools (use XML tags in your response):

<read_file path="relative/path"/>
<edit_file path="relative/path">
  <old>exact text to replace</old>
  <new>replacement text</new>
</edit_file>
<write_file path="relative/path">
file content here
</write_file>
<search pattern="regex or keyword"/>
<bash command="shell command"/>
<remember key="name" value="what to remember"/>
<recall key="name"/>
"""


def execute_tools(response: str, workspace: Path, memory: Memory) -> List[str]:
    """Parse and execute tool calls from model response."""
    results = []

    # read_file
    for m in re.finditer(r'<read_file\s+path="([^"]+)"\s*/>', response):
        r = read_file(workspace, m.group(1))
        results.append(f"[read {m.group(1)}]: {r[:2000]}")

    # edit_file
    for m in re.finditer(
        r'<edit_file\s+path="([^"]+)">\s*<old>(.*?)</old>\s*<new>(.*?)</new>\s*</edit_file>',
        response, re.DOTALL,
    ):
        r = edit_file(workspace, m.group(1), m.group(2), m.group(3))
        results.append(r)

    # write_file
    for m in re.finditer(
        r'<write_file\s+path="([^"]+)">\s*(.*?)\s*</write_file>',
        response, re.DOTALL,
    ):
        r = write_file(workspace, m.group(1), m.group(2))
        results.append(r)

    # search
    for m in re.finditer(r'<search\s+pattern="([^"]+)"\s*/>', response):
        r = grep_workspace(workspace, m.group(1))
        results.append(f"[search {m.group(1)}]:\n{r}")

    # bash
    for m in re.finditer(r'<bash\s+command="([^"]+)"\s*/>', response):
        import subprocess
        try:
            r = subprocess.run(
                m.group(1), shell=True, capture_output=True, text=True,
                cwd=str(workspace), timeout=30,
            )
            output = (r.stdout + r.stderr).strip()[:2000]
            results.append(f"[bash]: {output}")
        except Exception as e:
            results.append(f"[bash ERROR]: {e}")

    # remember
    for m in re.finditer(r'<remember\s+key="([^"]+)"\s+value="([^"]+)"\s*/>', response):
        memory.remember(m.group(1), m.group(2))
        results.append(f"[remembered]: {m.group(1)} = {m.group(2)}")

    # recall
    for m in re.finditer(r'<recall\s+key="([^"]+)"\s*/>', response):
        val = memory.recall(m.group(1))
        results.append(f"[recall {m.group(1)}]: {val or '(not found)'}")

    return results


# ═══════════════════════════════════════════════════════════════════════
# CONVERSATION ENGINE
# ═══════════════════════════════════════════════════════════════════════

class CodingAssistant:
    """Interactive coding assistant with multi-model backend."""

    def __init__(self, workspace: Path, tier: str = "cheap"):
        self.workspace = workspace
        self.tier = tier
        self.bridge = RheaBridge()
        self.context = load_context(workspace)
        self.memory = Memory(workspace)
        self.history: List[Dict[str, str]] = []
        self.max_history = 20

    def chat(self, user_input: str) -> str:
        """Process a user message and return assistant response."""
        # Build messages
        system = self.context.system_prompt() + "\n" + TOOL_SCHEMA
        self.history.append({"role": "user", "content": user_input})

        # Trim history
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

        # Build full prompt from history
        prompt = "\n".join(
            f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
            for m in self.history
        )
        prompt += "\nAssistant:"

        # Query bridge
        resp = self.bridge.ask_tier(self.tier, prompt, system=system, max_tokens=4096)

        if resp.error:
            return f"[ERROR: {resp.error}]"

        text = resp.text.strip()

        # Execute any tool calls
        tool_results = execute_tools(text, self.workspace, self.memory)
        if tool_results:
            text += "\n\n--- Tool Results ---\n" + "\n".join(tool_results)

        self.history.append({"role": "assistant", "content": text})

        # Status line
        model_tag = f"{resp.provider}/{resp.model}" if resp.provider else "unknown"
        latency = f"{resp.latency_s:.1f}s" if resp.latency_s else "?"
        status = f"  [{model_tag} | {latency} | tier:{self.tier}]"

        return text + "\n" + status

    def one_shot(self, query: str) -> str:
        """Single query with workspace context, no history."""
        system = self.context.system_prompt()
        resp = self.bridge.ask_tier(self.tier, query, system=system, max_tokens=4096)
        if resp.error:
            return f"[ERROR: {resp.error}]"
        return resp.text.strip()


# ═══════════════════════════════════════════════════════════════════════
# REPL — Interactive loop
# ═══════════════════════════════════════════════════════════════════════

BANNER = """
╔══════════════════════════════════════════════╗
║  rhea-code — multi-model coding assistant    ║
║  6 providers · 31 models · cost-aware tiers  ║
╠══════════════════════════════════════════════╣
║  /help  /tier  /context  /skills  /memory    ║
║  /read <file>  /edit  /search <pattern>      ║
║  /quit                                       ║
╚══════════════════════════════════════════════╝
"""


def repl(workspace: Path, tier: str = "cheap"):
    """Interactive REPL."""
    assistant = CodingAssistant(workspace, tier=tier)

    print(BANNER)
    print(f"  Workspace: {workspace}")
    print(f"  Branch: {assistant.context.git_branch}")
    print(f"  Rules: {len(assistant.context.rules)} loaded")
    print(f"  Skills: {len(assistant.context.skills)} found")
    print(f"  Tier: {tier}\n")

    # Readline history
    histfile = workspace / ".rhea" / "repl_history"
    histfile.parent.mkdir(parents=True, exist_ok=True)
    try:
        readline.read_history_file(str(histfile))
    except FileNotFoundError:
        pass

    try:
        while True:
            try:
                user_input = input("rhea> ").strip()
            except EOFError:
                break

            if not user_input:
                continue

            # Slash commands
            if user_input.startswith("/"):
                cmd_parts = user_input.split(maxsplit=1)
                cmd = cmd_parts[0].lower()
                arg = cmd_parts[1] if len(cmd_parts) > 1 else ""

                if cmd in ("/quit", "/q", "/exit"):
                    break
                elif cmd == "/help":
                    print(BANNER)
                elif cmd == "/tier":
                    if arg:
                        assistant.tier = arg.strip()
                    print(f"Current tier: {assistant.tier}")
                elif cmd == "/context":
                    print(f"Rules ({len(assistant.context.rules)}):")
                    for r in assistant.context.rules:
                        print(f"  [{r['type']}] {r['path']}")
                    print(f"\nSkills ({len(assistant.context.skills)}):")
                    for s in assistant.context.skills:
                        print(f"  {s['name']}: {s['description']}")
                    print(f"\nGit: {assistant.context.git_branch}")
                    print(f"Status:\n{assistant.context.git_status[:500]}")
                elif cmd == "/skills":
                    if not assistant.context.skills:
                        print("No skills found. Add SKILL.md files to .augment/skills/ or .claude/skills/")
                    for s in assistant.context.skills:
                        print(f"  {s['name']}: {s['description']}")
                elif cmd == "/rules":
                    for r in assistant.context.rules:
                        print(f"\n--- {r['path']} [{r['type']}] ---")
                        print(r['content'][:500])
                elif cmd == "/memory":
                    mem = assistant.memory.all()
                    if not mem:
                        print("No memories stored. Use /remember key value")
                    for k, v in mem.items():
                        print(f"  {k}: {v}")
                elif cmd == "/remember":
                    parts = arg.split(maxsplit=1)
                    if len(parts) == 2:
                        assistant.memory.remember(parts[0], parts[1])
                        print(f"Remembered: {parts[0]}")
                    else:
                        print("Usage: /remember key value")
                elif cmd == "/forget":
                    if arg:
                        assistant.memory.forget(arg.strip())
                        print(f"Forgot: {arg.strip()}")
                    else:
                        print("Usage: /forget key")
                elif cmd == "/read":
                    if arg:
                        content = read_file(workspace, arg.strip())
                        print(content[:3000])
                    else:
                        print("Usage: /read path/to/file")
                elif cmd == "/search":
                    if arg:
                        results = grep_workspace(workspace, arg.strip())
                        print(results)
                    else:
                        print("Usage: /search pattern")
                elif cmd == "/status":
                    import subprocess
                    r = subprocess.run(
                        [sys.executable, str(SCRIPT_DIR / "rhea_bridge.py"), "status"],
                        capture_output=True, text=True, timeout=15,
                    )
                    print(r.stdout[:2000])
                elif cmd == "/models":
                    import subprocess
                    r = subprocess.run(
                        [sys.executable, str(SCRIPT_DIR / "rhea_bridge.py"), "tiers"],
                        capture_output=True, text=True, timeout=15,
                    )
                    print(r.stdout[:2000])
                elif cmd == "/tribunal":
                    if arg:
                        resp = assistant.bridge.tribunal(arg.strip())
                        print(json.dumps(resp, indent=2, ensure_ascii=False)[:3000])
                    else:
                        print("Usage: /tribunal claim to verify")
                elif cmd == "/clear":
                    assistant.history.clear()
                    print("History cleared.")
                else:
                    print(f"Unknown command: {cmd}. Type /help for commands.")
                continue

            # Regular chat
            t0 = time.time()
            response = assistant.chat(user_input)
            print(f"\n{response}\n")

    except KeyboardInterrupt:
        print("\n")

    # Save history
    try:
        readline.write_history_file(str(histfile))
    except Exception:
        pass

    print("Session ended.")


# ═══════════════════════════════════════════════════════════════════════
# CLI ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════

def main():
    args = sys.argv[1:]

    # Determine workspace
    workspace = Path.cwd()
    tier = os.environ.get("RHEA_TIER", "cheap")

    if not args or args[0] in ("repl", "interactive"):
        repl(workspace, tier=tier)
        return

    cmd = args[0]
    rest = " ".join(args[1:]) if len(args) > 1 else ""

    if cmd == "ask":
        if not rest:
            print("Usage: rhea code ask 'question'")
            sys.exit(1)
        assistant = CodingAssistant(workspace, tier=tier)
        print(assistant.one_shot(rest))

    elif cmd == "edit":
        if len(args) < 3:
            print("Usage: rhea code edit file.py 'instruction'")
            sys.exit(1)
        filepath = args[1]
        instruction = " ".join(args[2:])
        content = read_file(workspace, filepath)
        if content.startswith("ERROR:"):
            print(content)
            sys.exit(1)
        assistant = CodingAssistant(workspace, tier=tier)
        prompt = f"Edit this file according to the instruction.\n\nFile: {filepath}\n```\n{content[:8000]}\n```\n\nInstruction: {instruction}\n\nRespond with the complete edited file content only, no explanations."
        result = assistant.one_shot(prompt)
        print(result)

    elif cmd == "search":
        if not rest:
            print("Usage: rhea code search 'pattern'")
            sys.exit(1)
        print(grep_workspace(workspace, rest))

    elif cmd == "context":
        ctx = load_context(workspace)
        print(f"Workspace: {workspace}")
        print(f"Branch: {ctx.git_branch}")
        print(f"Rules: {len(ctx.rules)}")
        for r in ctx.rules:
            print(f"  [{r['type']}] {r['path']}")
        print(f"Skills: {len(ctx.skills)}")
        for s in ctx.skills:
            print(f"  {s['name']}: {s['description']}")

    elif cmd == "skills":
        ctx = load_context(workspace)
        if not ctx.skills:
            print("No skills found.")
            print("Add SKILL.md files to .augment/skills/ or .claude/skills/")
        for s in ctx.skills:
            print(f"  {s['name']}: {s['description']}")

    elif cmd == "rules":
        ctx = load_context(workspace)
        for r in ctx.rules:
            print(f"\n--- {r['path']} [{r['type']}] ---")
            print(r['content'][:500])

    elif cmd == "memory":
        mem = Memory(workspace)
        if rest == "clear":
            mem.data.clear()
            mem.save()
            print("Memory cleared.")
        elif rest.startswith("set "):
            parts = rest[4:].split(maxsplit=1)
            if len(parts) == 2:
                mem.remember(parts[0], parts[1])
                print(f"Remembered: {parts[0]}")
        elif rest.startswith("get "):
            val = mem.recall(rest[4:].strip())
            print(val or "(not found)")
        else:
            data = mem.all()
            if not data:
                print("No memories. Use: rhea code memory set key value")
            for k, v in data.items():
                print(f"  {k}: {v}")

    elif cmd == "status":
        import subprocess
        r = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "rhea_bridge.py"), "status"],
            capture_output=True, text=True, timeout=15,
        )
        print(r.stdout)

    elif cmd in ("help", "--help", "-h"):
        print(__doc__)

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
