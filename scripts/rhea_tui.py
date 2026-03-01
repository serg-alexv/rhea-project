#!/usr/bin/env python3
"""
rhea_tui.py — Rhea Command Centre TUI (Textual)

Single-file terminal dashboard: agents, radio, tasks, tribunal.
Talks to tribunal_api.py on localhost:8400.

Usage:
    python3 scripts/rhea_tui.py
    # or with custom API:
    RHEA_API=http://192.168.1.5:8400 python3 scripts/rhea_tui.py
"""
import os, json, asyncio, httpx
from datetime import datetime
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Header, Footer, Static, Input, DataTable, Log, Label, Button
from textual.reactive import reactive
from textual.timer import Timer
from textual import work
from rich.text import Text
from rich.table import Table

API = os.environ.get("RHEA_API", "http://localhost:8400")
API_KEY = os.environ.get("RHEA_API_KEY", "dev-bypass")
HEADERS = {"X-API-Key": API_KEY}
POLL_INTERVAL = 5.0

PACE_COLORS = {"green": "green", "yellow": "yellow", "red": "red"}
MODE_COLORS = {"normal": "green", "cooldown": "yellow", "hard_fail": "red", "suspended": "red"}


class AgentPanel(Static):
    """Left sidebar: agent roster + governor stats."""

    agents: reactive[dict] = reactive({})

    def render(self) -> Text:
        if not self.agents:
            return Text("No agent data", style="dim")

        lines = []
        total_tok = 0
        total_cost = 0.0
        alive_count = 0

        for name in sorted(self.agents.keys()):
            a = self.agents[name]
            pace = a.get("pace", "red")
            dot = "●" if a.get("alive") else "○"
            dot_style = PACE_COLORS.get(pace, "red")
            mode = a.get("mode", "?")
            mode_style = MODE_COLORS.get(mode, "white")
            tok = a.get("T_day", 0)
            cost = a.get("dollar_day", 0.0)
            total_tok += tok
            total_cost += cost
            if a.get("alive"):
                alive_count += 1

            tok_str = f"{tok // 1000}K" if tok >= 1000 else str(tok)
            pending = a.get("pending_msgs", 0)
            pending_str = f" [{pending}msg]" if pending else ""

            line = Text()
            line.append(f" {dot} ", style=dot_style)
            line.append(f"{name:<8}", style="bold white")
            line.append(f" {mode:<10}", style=mode_style)
            line.append(f" {tok_str:>6}", style="cyan")
            line.append(f" ${cost:.2f}", style="yellow")
            line.append(pending_str, style="yellow")
            lines.append(line)

        header = Text()
        header.append("─── AGENTS ", style="bold cyan")
        header.append(f"{alive_count}/{len(self.agents)} alive", style="green" if alive_count == len(self.agents) else "yellow")
        header.append(" ───\n", style="bold cyan")

        footer = Text()
        tok_total = f"{total_tok // 1000}K" if total_tok >= 1000 else str(total_tok)
        footer.append(f"\n  Σ {tok_total} tokens  ${total_cost:.2f}", style="bold white")

        result = header
        for line in lines:
            result.append_text(line)
            result.append("\n")
        result.append_text(footer)
        return result


class TaskPanel(Static):
    """Task queue summary."""

    summary: reactive[dict] = reactive({})

    def render(self) -> Text:
        s = self.summary
        if not s:
            return Text("No task data", style="dim")

        counts = s.get("counts", {})
        priority = s.get("active_by_priority", {})

        result = Text()
        result.append("─── TASKS ───\n", style="bold cyan")
        result.append(f"  Total:   {s.get('total', 0)}\n", style="white")
        result.append(f"  Open:    {counts.get('open', 0)}\n", style="green")
        result.append(f"  Claimed: {counts.get('claimed', 0)}\n", style="cyan")
        result.append(f"  Done:    {counts.get('done', 0)}\n", style="dim")
        result.append(f"  Blocked: {counts.get('blocked', 0)}\n", style="red" if counts.get("blocked", 0) > 0 else "dim")

        if priority:
            result.append("  Priority: ", style="yellow")
            parts = [f"{k}={v}" for k, v in sorted(priority.items())]
            result.append(" ".join(parts) + "\n", style="yellow")

        stale = s.get("stale_count", 0)
        if stale > 0:
            result.append(f"  ⚠ {stale} stale\n", style="bold red")

        return result


class RadioLog(Log):
    """Radio feed log panel."""
    pass


class TribunalPanel(Vertical):
    """Tribunal claim submission."""

    def compose(self) -> ComposeResult:
        yield Label("─── TRIBUNAL ───", classes="header-label")
        yield Input(placeholder="Enter claim to evaluate...", id="tribunal-input")
        yield Static("Submit a claim for multi-model consensus.", id="tribunal-result")


class RheaTUI(App):
    """Rhea Command Centre — Terminal UI."""

    CSS = """
    Screen {
        layout: grid;
        grid-size: 3 2;
        grid-columns: 1fr 2fr 1fr;
        grid-rows: 3fr 1fr;
        grid-gutter: 1;
        background: $surface;
    }
    AgentPanel {
        row-span: 2;
        border: solid $primary;
        padding: 1;
        overflow-y: auto;
    }
    RadioLog {
        border: solid $primary;
        padding: 0 1;
    }
    TribunalPanel {
        border: solid $accent;
        padding: 1;
    }
    TaskPanel {
        border: solid $primary;
        padding: 1;
    }
    #tribunal-input {
        margin-top: 1;
    }
    #tribunal-result {
        margin-top: 1;
        height: auto;
    }
    .header-label {
        text-style: bold;
        color: $accent;
    }
    Horizontal {
        height: auto;
    }
    """

    TITLE = "Rhea Command Centre"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("w", "wake_all", "Wake All"),
        ("t", "focus_tribunal", "Tribunal"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield AgentPanel(id="agents")
        yield RadioLog(id="radio", highlight=True, markup=True)
        yield TaskPanel(id="tasks")
        yield TribunalPanel(id="tribunal")
        yield Static("", id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        self.poll_timer = self.set_interval(POLL_INTERVAL, self.poll_data)
        self.poll_data()
        self.fetch_radio()

    @work(exclusive=True, group="poll")
    async def poll_data(self) -> None:
        """Fetch agents + tasks from API."""
        async with httpx.AsyncClient(timeout=5) as client:
            # Agents
            try:
                resp = await client.get(f"{API}/agents/status", headers=HEADERS)
                data = resp.json()
                panel = self.query_one("#agents", AgentPanel)
                panel.agents = data.get("agents", {})
            except Exception as e:
                self.update_status(f"agents error: {e}")

            # Tasks
            try:
                resp = await client.get(f"{API}/tasks/summary", headers=HEADERS)
                data = resp.json()
                panel = self.query_one("#tasks", TaskPanel)
                panel.summary = data
            except Exception as e:
                self.update_status(f"tasks error: {e}")

    @work(exclusive=True, group="radio")
    async def fetch_radio(self) -> None:
        """Fetch radio feed."""
        radio = self.query_one("#radio", RadioLog)
        async with httpx.AsyncClient(timeout=5) as client:
            try:
                resp = await client.get(f"{API}/feed", headers=HEADERS)
                data = resp.json()
                items = data.get("items", [])
                for item in items[-50:]:
                    ts = item.get("ts", "")[:19]
                    sender = item.get("sender", "?").upper()[:6]
                    text = item.get("text", "").replace("\n", " ")[:120]
                    radio.write_line(f"[dim]{ts}[/] [bold]{sender:<6}[/] {text}")
            except Exception as e:
                radio.write_line(f"[red]radio error: {e}[/]")

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "tribunal-input":
            claim = event.value.strip()
            if not claim:
                return
            event.input.value = ""
            result_widget = self.query_one("#tribunal-result", Static)
            result_widget.update("[yellow]Evaluating...[/]")
            self.submit_tribunal(claim)

    @work(exclusive=True, group="tribunal")
    async def submit_tribunal(self, claim: str) -> None:
        result_widget = self.query_one("#tribunal-result", Static)
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.post(
                    f"{API}/tribunal",
                    headers={**HEADERS, "Content-Type": "application/json"},
                    json={"prompt": claim, "mode": "tribunal"},
                )
                data = resp.json()
                agreement = data.get("agreement_score", 0)
                confidence = data.get("confidence", 0)
                verdict = data.get("response", "")[:200]
                models = data.get("models_used", [])

                text = Text()
                text.append(f"Agreement: {agreement:.0%}\n", style="bold green" if agreement > 0.6 else "bold red")
                text.append(f"Confidence: {confidence:.0%}\n", style="cyan")
                text.append(f"Models: {', '.join(models)}\n", style="dim")
                text.append(f"\n{verdict}", style="white")
                result_widget.update(text)
            except Exception as e:
                result_widget.update(f"[red]Tribunal error: {e}[/]")

    def action_refresh(self) -> None:
        self.poll_data()
        self.fetch_radio()
        self.update_status("refreshed")

    @work(exclusive=True, group="wake")
    async def action_wake_all(self) -> None:
        """Wake all known agents."""
        async with httpx.AsyncClient(timeout=5) as client:
            for agent in ["REX", "ORION", "GEMINI", "HYPERION"]:
                try:
                    await client.post(f"{API}/agents/wake/{agent}", headers=HEADERS)
                except Exception:
                    pass
        self.update_status("wake sent to all agents")
        self.poll_data()

    def action_focus_tribunal(self) -> None:
        self.query_one("#tribunal-input", Input).focus()

    def update_status(self, msg: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        self.query_one("#status-bar", Static).update(f"[dim]{ts}[/] {msg}")


# TODO(human): implement the agent-permission multiplexer logic
# This function should handle auto-approving Claude Code permission prompts
# for managed agent sessions (bg/fg switching between N agents).
# See the user's requirement: "give this stupid agent permission"
def agent_permission_bridge():
    pass


if __name__ == "__main__":
    app = RheaTUI()
    app.run()
