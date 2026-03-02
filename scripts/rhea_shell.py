#!/usr/bin/env python3
"""
rhea_shell.py — Rhea multi-agent rich CLI.

Direct API shell for the Rhea tribunal system. Talks to tribunal_api.py
on localhost:8400 (or RHEA_API env). Rich colored output, multi-agent ops.

Usage:
  python3 scripts/rhea_shell.py                      # interactive REPL
  python3 scripts/rhea_shell.py -c "agents"          # one-shot command
  python3 scripts/rhea_shell.py --cloud              # connect to fly.dev
  RHEA_API=http://host:port python3 scripts/rhea_shell.py
"""
from __future__ import annotations

import argparse
import cmd
import json
import os
import shlex
import sys
import time

import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

console = Console()

DEFAULT_LOCAL = "http://localhost:8400"
DEFAULT_CLOUD = "https://rhea-tribunal.fly.dev"


class API:
    """Thin sync client for tribunal_api.py."""

    def __init__(self, base: str, token: str | None = None):
        self.base = base.rstrip("/")
        self.token = token
        self._client = httpx.Client(timeout=15)

    def _headers(self) -> dict:
        h: dict[str, str] = {}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        else:
            h["X-API-Key"] = "dev-bypass"
        return h

    def get(self, path: str) -> dict | list | None:
        try:
            r = self._client.get(f"{self.base}{path}", headers=self._headers())
            r.raise_for_status()
            return r.json()
        except Exception as e:
            console.print(f"[red]GET {path}: {e}[/]")
            return None

    def post(self, path: str, body: dict | None = None) -> dict | None:
        try:
            r = self._client.post(f"{self.base}{path}", headers=self._headers(), json=body or {})
            r.raise_for_status()
            return r.json()
        except Exception as e:
            console.print(f"[red]POST {path}: {e}[/]")
            return None


# ─── Command Handlers ────────────────────────────────────────────────


def cmd_agents(api: API, args: list[str]):
    """Show agent roster with status, tokens, cost."""
    data = api.get("/agents/status")
    if not data or "agents" not in data:
        console.print("[dim]No agent data[/]")
        return

    t = Table(title="AGENTS", box=box.SIMPLE_HEAVY, title_style="bold cyan")
    t.add_column("", width=2)
    t.add_column("NAME", style="bold white")
    t.add_column("MODE", width=10)
    t.add_column("T/day", justify="right")
    t.add_column("$/day", justify="right")
    t.add_column("PACE")
    t.add_column("MSGS", justify="right")
    t.add_column("TASKS", justify="right")

    agents = data["agents"]
    total_tok = 0
    total_cost = 0.0

    for name in sorted(agents):
        a = agents[name]
        alive = a.get("alive", False)
        dot = "[green]●[/]" if alive else "[red]○[/]"
        mode = a.get("mode", "?")
        mc = {"normal": "green", "cooldown": "yellow", "enforcement": "red"}.get(mode, "dim")
        tok = a.get("T_day", 0)
        cost = a.get("dollar_day", 0.0)
        pace = a.get("pace", "?")
        pc = {"green": "green", "yellow": "yellow"}.get(pace, "red")
        msgs = a.get("pending_msgs", 0)
        tasks = a.get("tasks_open", 0)
        total_tok += tok
        total_cost += cost

        t.add_row(
            dot, name,
            f"[{mc}]{mode}[/]",
            _fmt_tok(tok),
            f"[yellow]${cost:.2f}[/]",
            f"[{pc}]{pace}[/]",
            str(msgs) if msgs else "",
            str(tasks) if tasks else "",
        )

    console.print(t)
    console.print(f"  [dim]Total: {_fmt_tok(total_tok)} tokens, ${total_cost:.2f}[/]")


def cmd_wake(api: API, args: list[str]):
    """Wake an agent: wake <agent>"""
    if not args:
        console.print("[yellow]Usage: wake <agent>[/]")
        return
    name = args[0]
    r = api.post(f"/agents/wake/{name}")
    if r:
        console.print(f"[green]Woke {name}[/]")


def cmd_radio(api: API, args: list[str]):
    """Show radio feed or send a message: radio [send <text>]"""
    if args and args[0] == "send":
        text = " ".join(args[1:])
        if not text:
            console.print("[yellow]Usage: radio send <message>[/]")
            return
        api.post("/feed/push", {"sender": "human", "receiver": "all", "type": "radio", "text": text})
        console.print(f"[green]Sent: {text}[/]")
        return

    data = api.get("/feed")
    if not data or "items" not in data:
        console.print("[dim]No radio data[/]")
        return

    limit = 20
    if args and args[0].isdigit():
        limit = int(args[0])

    items = data["items"][-limit:]
    for item in items:
        ts = item.get("ts", "")
        ts_short = ts[11:19] if len(ts) >= 19 else ts
        sender = item.get("sender", "?").upper()
        sc = {"REX": "cyan", "ORION": "magenta", "GEMINI": "yellow", "HUMAN": "green",
              "RELAY": "rgb(255,165,0)", "SUPERVISOR": "rgb(200,100,255)"}.get(sender, "dim")
        recv = item.get("receiver", "")
        arrow = f"→{recv.upper()} " if recv and recv != "all" else ""
        text = item.get("text", "")
        if len(text) > 120:
            text = text[:120] + "..."
        console.print(f"[dim]{ts_short}[/] [{sc}]{sender:<6}[/] {arrow}{text}")


def cmd_tribunal(api: API, args: list[str]):
    """Submit a claim to the tribunal: tribunal <claim text>"""
    claim = " ".join(args)
    if not claim:
        console.print("[yellow]Usage: tribunal <claim>[/]")
        return

    console.print(f"[dim]Submitting to tribunal...[/]")
    r = api.post("/tribunal", {"prompt": claim, "mode": "tribunal"})
    if not r:
        return

    score = r.get("agreement_score", 0)
    conf = r.get("confidence", 0)
    models = r.get("models_used", [])
    resp = r.get("response", "")

    sc = "green" if score > 0.7 else "yellow" if score > 0.4 else "red"
    cc = "green" if conf > 0.7 else "yellow" if conf > 0.4 else "red"

    console.print(Panel(
        f"[{sc}]Agreement: {score*100:.0f}%[/]  [{cc}]Confidence: {conf*100:.0f}%[/]\n"
        f"[dim]Models: {', '.join(models)}[/]\n\n"
        f"{resp[:800]}",
        title="TRIBUNAL VERDICT",
        border_style="cyan",
    ))


def cmd_tasks(api: API, args: list[str]):
    """Show tasks or create one: tasks [add <title>]"""
    if args and args[0] == "add":
        title = " ".join(args[1:])
        if not title:
            console.print("[yellow]Usage: tasks add <title>[/]")
            return
        from urllib.parse import quote
        r = api.post(f"/tasks?title={quote(title)}&priority=P1&agent=rex")
        console.print(f"[green]Created task: {title}[/]")
        return

    data = api.get("/tasks")
    if not data or "tasks" not in data:
        # Try summary endpoint
        s = api.get("/tasks/summary")
        if s:
            console.print(f"[bold]Tasks:[/] total={s.get('total',0)}")
            for status, count in s.get("counts", {}).items():
                console.print(f"  {status}: {count}")
        return

    t = Table(title="TASKS", box=box.SIMPLE_HEAVY, title_style="bold cyan")
    t.add_column("STATUS", width=8)
    t.add_column("PRI", width=4)
    t.add_column("AGENT", width=8)
    t.add_column("TITLE")

    for task in data["tasks"][:30]:
        status = task.get("status", "?")
        sc = {"open": "yellow", "claimed": "cyan", "done": "green", "blocked": "red"}.get(status, "dim")
        t.add_row(
            f"[{sc}]{status}[/]",
            task.get("priority", ""),
            task.get("agent", ""),
            task.get("title", ""),
        )
    console.print(t)


def cmd_governor(api: API, args: list[str]):
    """Show governor budget for all agents."""
    data = api.get("/governor")
    if not data:
        console.print("[dim]No governor data[/]")
        return

    t = Table(title="GOVERNOR", box=box.SIMPLE_HEAVY, title_style="bold cyan")
    t.add_column("AGENT", style="bold white")
    t.add_column("MODE")
    t.add_column("T/day", justify="right")
    t.add_column("$/day", justify="right")
    t.add_column("CAP", justify="right")
    t.add_column("PACE")
    t.add_column("BUDGET BAR", width=16)

    for name in sorted(data):
        g = data[name]
        mode = g.get("mode", "?")
        mc = {"normal": "green", "compact": "yellow", "enforcement": "red"}.get(mode, "dim")
        tok = g.get("T_day", 0)
        cost = g.get("dollar_day", 0.0)
        cap = g.get("budget_cap", 0.0)
        pace = g.get("pace", "?")
        pc = {"on_track": "green", "normal": "green", "over": "yellow", "critical": "red"}.get(pace, "dim")

        bar = ""
        if cap and cap > 0:
            pct = min(cost / cap, 1.0)
            filled = int(pct * 14)
            bc = "green" if pct < 0.7 else "yellow" if pct < 0.9 else "red"
            bar = f"[{bc}]{'█' * filled}[/][dim]{'░' * (14 - filled)}[/]"

        t.add_row(
            name,
            f"[{mc}]{mode}[/]",
            _fmt_tok(tok),
            f"[yellow]${cost:.3f}[/]",
            f"${cap:.1f}" if cap else "",
            f"[{pc}]{pace}[/]",
            bar,
        )
    console.print(t)


def cmd_sessions(api: API, args: list[str]):
    """Supervisor sessions: sessions [spawn <agent>] [kill <id>] [output <id>] [input <id> <text>]"""
    if args and args[0] == "spawn":
        agent = args[1] if len(args) > 1 else "rex"
        r = api.post("/supervisor/spawn", {"agent": agent, "label": f"{agent}-shell"})
        if r:
            console.print(f"[green]Spawned {agent}: {r.get('id', '?')}[/]")
        return

    if args and args[0] == "kill" and len(args) > 1:
        sid = args[1]
        api.post(f"/supervisor/kill/{sid}")
        console.print(f"[red]Killed session {sid}[/]")
        return

    if args and args[0] == "output" and len(args) > 1:
        sid = args[1]
        lines = int(args[2]) if len(args) > 2 else 30
        data = api.get(f"/supervisor/output/{sid}?lines={lines}")
        if data and "lines" in data:
            for line in data["lines"]:
                console.print(line.rstrip())
        return

    if args and args[0] == "input" and len(args) > 2:
        sid = args[1]
        text = " ".join(args[2:])
        api.post(f"/supervisor/input/{sid}", {"text": text})
        console.print(f"[green]Sent to {sid[:8]}[/]")
        return

    data = api.get("/supervisor/sessions")
    if not data or "sessions" not in data:
        console.print("[dim]No sessions[/]")
        return

    t = Table(title="SESSIONS", box=box.SIMPLE_HEAVY, title_style="bold magenta")
    t.add_column("", width=2)
    t.add_column("ID", width=10)
    t.add_column("AGENT")
    t.add_column("STATUS")
    t.add_column("STARTED")
    t.add_column("LINES", justify="right")

    for s in data["sessions"]:
        status = s.get("status", "?")
        sc = {"running": "green", "stopped": "dim", "crashed": "red"}.get(status, "dim")
        dot = "[green]●[/]" if status == "running" else "[red]○[/]"
        started = s.get("started_at", "")
        started_short = started[11:19] if len(started) >= 19 else started
        t.add_row(
            dot,
            s.get("id", "")[:8],
            s.get("agent", ""),
            f"[{sc}]{status}[/]",
            started_short,
            str(s.get("output_lines", 0)),
        )
    console.print(t)


def cmd_history(api: API, args: list[str]):
    """Show tribunal history from SQL."""
    limit = int(args[0]) if args and args[0].isdigit() else 20
    data = api.get(f"/cc/history?limit={limit}")
    if not data:
        console.print("[dim]No history[/]")
        return

    entries = data if isinstance(data, list) else data.get("entries", data.get("items", []))
    for e in entries:
        ts = e.get("created_at", "")
        ts_short = ts[11:16] if len(ts) >= 16 else ts
        typ = e.get("type", "?")
        score = e.get("agreement_score")
        prompt = e.get("prompt", "")[:80]
        sc_str = ""
        if score is not None:
            sc = "green" if score > 0.7 else "yellow" if score > 0.4 else "red"
            sc_str = f" [{sc}]{score*100:.0f}%[/]"
        console.print(f"[dim]{ts_short}[/] [cyan]{typ:>8}[/]{sc_str} {prompt}")


def cmd_proofs(api: API, args: list[str]):
    """Show Aletheia proofs."""
    data = api.get("/aletheia/proofs")
    if not data:
        console.print("[dim]No proofs[/]")
        return

    proofs = data if isinstance(data, list) else data.get("proofs", [])
    t = Table(title="PROOFS", box=box.SIMPLE_HEAVY, title_style="bold green")
    t.add_column("TIER", width=4)
    t.add_column("CLAIM")
    t.add_column("AGREE", justify="right")
    t.add_column("CONF", justify="right")

    for p in proofs:
        tier = p.get("tier", "?")
        tc = {"t0": "green", "t1": "cyan", "t2": "yellow", "t3": "red"}.get(tier.lower(), "dim")
        claim = (p.get("claim") or p.get("prompt") or "")[:60]
        score = p.get("agreement_score", 0)
        conf = p.get("confidence", 0)
        sc = "green" if score > 0.7 else "yellow" if score > 0.4 else "red"
        cc = "green" if conf > 0.7 else "yellow"
        t.add_row(
            f"[{tc}]{tier}[/]",
            claim,
            f"[{sc}]{score*100:.0f}%[/]",
            f"[{cc}]{conf*100:.0f}%[/]",
        )
    console.print(t)


def cmd_models(api: API, args: list[str]):
    """Show model roster and execution profile."""
    data = api.get("/models")
    if not data:
        console.print("[dim]No model data[/]")
        return

    raw = data.get("providers", {})
    # API returns dict {name: info} not list
    providers = raw.items() if isinstance(raw, dict) else [(p.get("name","?"), p) for p in raw]

    t = Table(title="PROVIDERS", box=box.SIMPLE_HEAVY, title_style="bold cyan")
    t.add_column("", width=2)
    t.add_column("NAME", style="bold white")
    t.add_column("MODELS", justify="right")
    t.add_column("STATUS")

    for name, p in sorted(providers):
        avail = p.get("available", False)
        dot = "[green]●[/]" if avail else "[red]○[/]"
        rs = p.get("routing_status", "")
        rc = "green" if avail else "red" if "dead" in rs else "yellow"
        t.add_row(dot, p.get("display_name", name), str(p.get("model_count", "")), f"[{rc}]{rs}[/]")

    console.print(t)

    profile = api.get("/governor/profile")
    if profile and isinstance(profile, dict):
        active = profile.get("active") or profile.get("profile", "?")
        console.print(f"  [dim]Profile:[/] [bold]{active}[/]")


def cmd_health(api: API, args: list[str]):
    """Quick health check."""
    data = api.get("/health")
    if not data:
        console.print("[red]API unreachable[/]")
        return

    status = data.get("status", "?")
    sc = "green" if status == "ok" else "red"
    console.print(f"[{sc}]{status}[/] | models={data.get('total_models',0)} | "
                  f"alive={data.get('alive_agents',0)}/{data.get('total_agents',0)} | "
                  f"proofs={data.get('proof_count',0)}")


def cmd_cowork(api: API, args: list[str]):
    """Toggle local/cloud: cowork local | cowork cloud"""
    return args  # handled by shell


def cmd_office(api: API, args: list[str]):
    """Show recent office messages: office [send <to> <text>]"""
    if args and args[0] == "send" and len(args) > 2:
        to = args[1]
        text = " ".join(args[2:])
        api.post("/office/send", {"sender": "human", "receiver": to, "text": text})
        console.print(f"[green]Sent to {to}[/]")
        return

    data = api.get("/office/history")
    if not data:
        console.print("[dim]No office messages[/]")
        return

    messages = data if isinstance(data, list) else data.get("messages", [])
    for m in messages[-20:]:
        ts = m.get("ts", "")
        ts_short = ts[11:16] if len(ts) >= 16 else ts
        sender = m.get("sender", "?")
        recv = m.get("receiver", "?")
        text = (m.get("text") or "")[:80]
        console.print(f"[dim]{ts_short}[/] [cyan]{sender}[/]→[magenta]{recv}[/] {text}")


# ─── Helpers ─────────────────────────────────────────────────────────


def _fmt_tok(n: int | float) -> str:
    n = int(n)
    if n >= 1_000_000:
        return f"{n // 1_000_000}M"
    if n >= 1_000:
        return f"{n // 1_000}K"
    return str(n)


COMMANDS = {
    "agents": cmd_agents,
    "wake": cmd_wake,
    "radio": cmd_radio,
    "tribunal": cmd_tribunal,
    "tasks": cmd_tasks,
    "governor": cmd_governor,
    "sessions": cmd_sessions,
    "history": cmd_history,
    "proofs": cmd_proofs,
    "models": cmd_models,
    "health": cmd_health,
    "office": cmd_office,
    "cowork": cmd_cowork,
}


# ─── Shell ───────────────────────────────────────────────────────────


class RheaShell(cmd.Cmd):
    intro = None
    prompt = ""

    def __init__(self, api: API, base_url: str):
        super().__init__()
        self.api = api
        self.base_url = base_url
        self._update_prompt()

    def _update_prompt(self):
        tag = "local" if "localhost" in self.base_url else "cloud"
        tc = "green" if tag == "local" else "cyan"
        # cmd.Cmd needs plain prompt; we print rich before input
        self.prompt = f"rhea({tag})> "

    def preloop(self):
        console.print(Panel(
            "[bold cyan]RHEA SHELL[/] — multi-agent command centre\n"
            f"[dim]Connected: {self.base_url}[/]\n"
            "[dim]Type [bold]help[/dim][dim] for commands, [bold]q[/dim][dim] to quit[/]",
            border_style="cyan", box=box.HEAVY,
        ))
        cmd_health(self.api, [])

    def default(self, line: str):
        parts = shlex.split(line)
        if not parts:
            return

        head = parts[0].lower()
        tail = parts[1:]

        if head in {"exit", "quit", "q"}:
            return True

        if head == "cowork":
            if tail and tail[0] == "cloud":
                self.base_url = DEFAULT_CLOUD
            else:
                self.base_url = DEFAULT_LOCAL
            self.api = API(self.base_url, self.api.token)
            self._update_prompt()
            console.print(f"[green]Switched to {self.base_url}[/]")
            cmd_health(self.api, [])
            return

        if head == "help":
            self._show_help()
            return

        handler = COMMANDS.get(head)
        if handler:
            handler(self.api, tail)
        else:
            console.print(f"[yellow]Unknown: {head}[/]. Type [bold]help[/].")

    def _show_help(self):
        t = Table(title="COMMANDS", box=box.SIMPLE, title_style="bold cyan", show_header=False)
        t.add_column("CMD", style="bold white", width=14)
        t.add_column("DESC")

        cmds = [
            ("agents", "Agent roster with status, tokens, cost"),
            ("wake <agent>", "Wake a dead agent"),
            ("radio [N]", "Show last N radio events (default 20)"),
            ("radio send <msg>", "Broadcast a radio message"),
            ("tribunal <claim>", "Submit claim to multi-model tribunal"),
            ("tasks", "Show task board"),
            ("tasks add <title>", "Create a new task"),
            ("governor", "Agent budget grid"),
            ("sessions", "List supervisor sessions"),
            ("sessions spawn <agent>", "Spawn agent session"),
            ("sessions kill <id>", "Kill a session"),
            ("sessions output <id>", "View session output"),
            ("sessions input <id> <text>", "Send input to session"),
            ("history [N]", "Tribunal history (SQL-backed)"),
            ("proofs", "Aletheia proof chain"),
            ("models", "Model roster + execution profile"),
            ("office", "Office message history"),
            ("office send <to> <msg>", "Send office message"),
            ("health", "Quick API health check"),
            ("cowork local|cloud", "Switch API endpoint"),
            ("q / exit", "Quit"),
        ]
        for c, d in cmds:
            t.add_row(c, d)
        console.print(t)

    def do_exit(self, _):
        return True

    def do_quit(self, _):
        return True

    def do_EOF(self, _):
        console.print()
        return True


# ─── Entry ───────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(description="Rhea multi-agent rich CLI")
    parser.add_argument("-c", "--command", default="", help="Run one command and exit")
    parser.add_argument("--cloud", action="store_true", help="Connect to fly.dev")
    parser.add_argument("--api", default="", help="Custom API base URL")
    parser.add_argument("--token", default="", help="JWT bearer token")
    args = parser.parse_args()

    base = args.api or os.environ.get("RHEA_API", "")
    if not base:
        base = DEFAULT_CLOUD if args.cloud else DEFAULT_LOCAL
    token = args.token or os.environ.get("RHEA_TOKEN", "")

    api = API(base, token or None)

    if args.command.strip():
        parts = shlex.split(args.command.strip())
        head = parts[0].lower()
        tail = parts[1:]
        handler = COMMANDS.get(head)
        if handler:
            handler(api, tail)
            return 0
        console.print(f"[red]Unknown command: {head}[/]")
        return 2

    shell = RheaShell(api, base)
    try:
        shell.cmdloop()
    except KeyboardInterrupt:
        console.print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
