#!/usr/bin/env python3
"""
rhea-cli — Unified CLI for the Rhea agent coordination OS.

Controls three planes from one command:
  1. GitHub org  (repos, licenses, profiles, topics)
  2. Fly.io      (deploy, secrets, logs, status)
  3. Tribunal API (agents, history, radio, office, tribunal)

Install:
    brew tap timelabs/tap && brew install rhea
    # or: pip install rhea-cli
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout
from rich.text import Text

from rhea_cli import __version__

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
ORG = "timelabs"
REPOS = ["rhea-project", "rhea-memory", "rhea-play", "rhea-ios", "rhea-keyboard", "rhea-atlas", "rhea-tutorials", ".github"]
FLY_APP = "rhea-tribunal"
API_LOCAL = os.environ.get("RHEA_API", "http://localhost:8400")
API_CLOUD = f"https://{FLY_APP}.fly.dev"

# When installed via pip/brew, REPO_ROOT points to wherever the user runs from.
# For repo-local operations (check, commit), we look for the repo root via git.
def _find_repo_root() -> Path:
    """Find the nearest git repo root, or fall back to cwd."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip())
    except Exception:
        pass
    return Path.cwd()

REPO_ROOT = _find_repo_root()
console = Console()

MIT_LICENSE = """MIT License

Copyright (c) 2026 timelabs npo

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


def _gh(*args, json_output=True):
    """Run gh CLI and return parsed JSON or raw text."""
    cmd = ["gh", "api"] + list(args)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return None
        if json_output:
            return json.loads(result.stdout) if result.stdout.strip() else None
        return result.stdout
    except (subprocess.TimeoutExpired, json.JSONDecodeError):
        return None


def _fly(*args):
    """Run fly CLI and return stdout."""
    cmd = ["fly"] + list(args) + ["-a", FLY_APP]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return "timeout"


def _api(endpoint, method="GET", base=None, data=None, timeout=15):
    """Call Rhea API endpoint."""
    base = base or API_LOCAL
    url = f"{base}{endpoint}"
    try:
        if method == "GET":
            r = requests.get(url, timeout=timeout)
        else:
            r = requests.post(url, json=data, timeout=timeout,
                              headers={"Content-Type": "application/json"})
        return r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text
    except Exception as e:
        return {"error": str(e)}


# ===========================================================================
# Main CLI
# ===========================================================================
@click.group()
@click.version_option(version=__version__, prog_name="rhea")
@click.option("--cloud", is_flag=True, help="Target cloud API instead of localhost")
@click.pass_context
def cli(ctx, cloud):
    """rhea -- control plane for the Rhea agent coordination OS."""
    ctx.ensure_object(dict)
    ctx.obj["api_base"] = API_CLOUD if cloud else API_LOCAL


# ===========================================================================
# ORG -- GitHub organization management
# ===========================================================================
@cli.group()
def org():
    """GitHub org: repos, licenses, profiles, topics."""
    pass


@org.command("status")
def org_status():
    """Show all repos with license, stars, topics, and visibility."""
    data = _gh(f"/orgs/{ORG}/repos", "--paginate", "-q", ".")
    if not data:
        console.print("[red]Failed to fetch repos[/red]")
        return
    table = Table(title=f"{ORG} repositories", show_lines=True)
    table.add_column("Repo", style="cyan", min_width=18)
    table.add_column("License", style="green")
    table.add_column("Stars", justify="right")
    table.add_column("Topics", style="dim")
    table.add_column("Vis", style="yellow")
    table.add_column("Updated", style="dim")
    for repo in sorted(data, key=lambda r: r.get("name", "")):
        lic = repo.get("license", {})
        lic_name = lic.get("spdx_id", "none") if lic else "none"
        topics = ", ".join(repo.get("topics", [])) or "-"
        updated = repo.get("updated_at", "")[:10]
        table.add_row(
            repo["name"],
            lic_name,
            str(repo.get("stargazers_count", 0)),
            topics,
            repo.get("visibility", "?"),
            updated,
        )
    console.print(table)


@org.command("license")
@click.option("--fix", is_flag=True, help="Fix missing/wrong licenses")
def org_license(fix):
    """Check (and optionally fix) MIT license across all repos."""
    import base64
    table = Table(title="License Audit")
    table.add_column("Repo", style="cyan")
    table.add_column("Has LICENSE", style="green")
    table.add_column("Copyright", style="yellow")
    table.add_column("Status")

    for repo_name in REPOS:
        lic_data = _gh(f"/repos/{ORG}/{repo_name}/contents/LICENSE")
        if not lic_data or "content" not in (lic_data if isinstance(lic_data, dict) else {}):
            table.add_row(repo_name, "NO", "-", "[red]MISSING[/red]")
            if fix:
                _create_license(repo_name)
                console.print(f"  [green]fixed: {repo_name}[/green]")
            continue
        content = base64.b64decode(lic_data["content"]).decode("utf-8", errors="replace")
        copyright_line = next((l for l in content.splitlines() if "Copyright" in l), "?")
        ok = "timelabs npo" in copyright_line.lower()
        status = "[green]OK[/green]" if ok else "[yellow]WRONG COPYRIGHT[/yellow]"
        table.add_row(repo_name, "YES", copyright_line.strip(), status)
        if fix and not ok:
            _update_license(repo_name, lic_data.get("sha", ""))
            console.print(f"  [green]fixed: {repo_name}[/green]")
    console.print(table)


def _create_license(repo_name):
    import base64
    b64 = base64.b64encode(MIT_LICENSE.encode()).decode()
    _gh(f"/repos/{ORG}/{repo_name}/contents/LICENSE",
        "-X", "PUT",
        "-f", "message=add MIT license (timelabs npo)",
        "-f", f"content={b64}",
        json_output=False)


def _update_license(repo_name, sha):
    import base64
    b64 = base64.b64encode(MIT_LICENSE.encode()).decode()
    _gh(f"/repos/{ORG}/{repo_name}/contents/LICENSE",
        "-X", "PUT",
        "-f", "message=fix copyright: timelabs npo",
        "-f", f"content={b64}",
        "-f", f"sha={sha}",
        json_output=False)


@org.command("profile")
def org_profile():
    """Show org profile metadata."""
    data = _gh(f"/orgs/{ORG}")
    if not data:
        console.print("[red]Failed to fetch org[/red]")
        return
    panel = Panel(
        f"[bold]{data.get('name', '?')}[/bold]\n"
        f"{data.get('description', '-')}\n\n"
        f"Location: {data.get('location', '-')}\n"
        f"Blog: {data.get('blog', '-')}\n"
        f"Public repos: {data.get('public_repos', 0)}\n"
        f"Members: {data.get('public_members_count', '?')}\n"
        f"Created: {data.get('created_at', '')[:10]}",
        title=f"github.com/{ORG}",
        border_style="cyan",
    )
    console.print(panel)


@org.command("create")
@click.argument("name")
@click.option("--desc", default="", help="Repository description")
@click.option("--private", "visibility", flag_value="private", default=True)
@click.option("--public", "visibility", flag_value="public")
def org_create(name, desc, visibility):
    """Create a new repo in the org."""
    result = subprocess.run(
        ["gh", "repo", "create", f"{ORG}/{name}",
         f"--{visibility}", "--clone=false",
         *(["--description", desc] if desc else [])],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        console.print(f"[green]Created: {ORG}/{name}[/green]")
        _create_license(name)
        console.print(f"[green]MIT license added[/green]")
    else:
        console.print(f"[red]{result.stderr.strip()}[/red]")


@org.command("topics")
@click.argument("repo")
@click.argument("topics", nargs=-1)
def org_topics(repo, topics):
    """Set topics on a repo. Pass topics as space-separated args."""
    if not topics:
        data = _gh(f"/repos/{ORG}/{repo}/topics")
        if data and "names" in data:
            console.print(f"[cyan]{repo}[/cyan]: {', '.join(data['names']) or 'none'}")
        return
    result = subprocess.run(
        ["gh", "api", f"/repos/{ORG}/{repo}/topics",
         "-X", "PUT", "--input", "-"],
        input=json.dumps({"names": list(topics)}),
        capture_output=True, text=True
    )
    if result.returncode == 0:
        console.print(f"[green]{repo} topics set: {', '.join(topics)}[/green]")
    else:
        console.print(f"[red]{result.stderr.strip()}[/red]")


# ===========================================================================
# FLY -- Fly.io deployment management
# ===========================================================================
@cli.group()
def fly():
    """Fly.io: deploy, secrets, logs, status."""
    pass


@fly.command("status")
def fly_status():
    """Show Fly.io app status and machines."""
    output = _fly("status")
    console.print(Panel(output.strip(), title=f"fly.io/{FLY_APP}", border_style="green"))


@fly.command("deploy")
@click.option("--ha/--no-ha", default=False, help="High availability (2 machines)")
def fly_deploy(ha):
    """Deploy current code to Fly.io."""
    console.print("[yellow]Deploying...[/yellow]")
    cmd = ["fly", "deploy", "-a", FLY_APP]
    if ha:
        cmd += ["--ha=true"]
    else:
        cmd += ["--ha=false"]
    result = subprocess.run(cmd, cwd=str(REPO_ROOT))
    if result.returncode == 0:
        console.print("[green]Deploy complete[/green]")
    else:
        console.print("[red]Deploy failed[/red]")


@fly.command("secrets")
@click.option("--set", "secret_pair", type=(str, str), multiple=True, help="KEY VALUE pairs")
@click.option("--unset", "unset_keys", multiple=True, help="Keys to remove")
def fly_secrets(secret_pair, unset_keys):
    """List, set, or unset Fly.io secrets."""
    if secret_pair:
        for key, val in secret_pair:
            output = _fly("secrets", "set", f"{key}={val}")
            console.print(f"[green]set {key}[/green]")
        return
    if unset_keys:
        for key in unset_keys:
            _fly("secrets", "unset", key)
            console.print(f"[yellow]unset {key}[/yellow]")
        return
    output = _fly("secrets", "list")
    console.print(Panel(output.strip(), title="Secrets", border_style="yellow"))


@fly.command("logs")
@click.option("-n", "lines", default=50, help="Number of lines")
def fly_logs(lines):
    """Tail Fly.io logs."""
    subprocess.run(["fly", "logs", "-a", FLY_APP, "-n", str(lines)])


@fly.command("ssh")
@click.argument("cmd", nargs=-1)
def fly_ssh(cmd):
    """Run command on Fly.io machine via SSH."""
    if cmd:
        subprocess.run(["fly", "ssh", "console", "-a", FLY_APP, "-C", " ".join(cmd)])
    else:
        subprocess.run(["fly", "ssh", "console", "-a", FLY_APP])


@fly.command("scale")
@click.argument("memory", type=int)
def fly_scale(memory):
    """Scale machine memory (MB). Example: rhea fly scale 1024"""
    output = _fly("scale", "memory", str(memory))
    console.print(output)


# ===========================================================================
# API -- Tribunal API operations
# ===========================================================================
@cli.group()
@click.pass_context
def api(ctx):
    """Tribunal API: health, tribunal, history, radio, agents, office."""
    pass


@api.command("health")
@click.pass_context
def api_health(ctx):
    """Health check on local and cloud API."""
    for label, base in [("local", API_LOCAL), ("cloud", API_CLOUD)]:
        try:
            r = requests.get(f"{base}/health", timeout=5)
            data = r.json()
            status = "[green]UP[/green]" if r.status_code == 200 else f"[red]{r.status_code}[/red]"
            console.print(f"  {label:6s} {status}  uptime={data.get('uptime_hours', '?')}h  models={data.get('models_available', '?')}")
        except Exception as e:
            console.print(f"  {label:6s} [red]DOWN[/red]  {e}")


@api.command("tribunal")
@click.argument("claim")
@click.option("--ice", is_flag=True, help="Use ICE (deep verification)")
@click.option("--models", default=None, help="Comma-separated model list")
@click.pass_context
def api_tribunal(ctx, claim, ice, models):
    """Submit a claim for tribunal verification."""
    base = ctx.obj.get("api_base", API_LOCAL)
    endpoint = "/tribunal/ice" if ice else "/tribunal"
    payload = {"prompt": claim}
    if models:
        payload["models"] = models.split(",")
    console.print(f"[yellow]Submitting to {endpoint}...[/yellow]")
    result = _api(endpoint, method="POST", base=base, data=payload, timeout=120)
    if isinstance(result, dict) and "error" not in result:
        agreement = result.get("agreement_score", result.get("agreement", "?"))
        confidence = result.get("confidence", "?")
        verdict = result.get("verdict", result.get("consensus_text", "?"))
        console.print(Panel(
            f"Agreement: {agreement}\n"
            f"Confidence: {confidence}\n"
            f"Verdict: {verdict}\n"
            f"Models: {result.get('models_used', result.get('models', '?'))}",
            title="Tribunal Result",
            border_style="green" if agreement and float(str(agreement).rstrip('%')) > 50 else "red",
        ))
    else:
        console.print(f"[red]{result}[/red]")


@api.command("history")
@click.option("-n", "limit", default=20, help="Number of entries")
@click.option("--type", "hist_type", default=None, help="Filter by type")
@click.pass_context
def api_history(ctx, limit, hist_type):
    """Query tribunal session history."""
    base = ctx.obj.get("api_base", API_LOCAL)
    params = f"?limit={limit}"
    if hist_type:
        params += f"&type={hist_type}"
    result = _api(f"/cc/history{params}", base=base)
    if isinstance(result, dict) and "history" in result:
        table = Table(title=f"History (last {limit})")
        table.add_column("Time", style="dim", min_width=16)
        table.add_column("Type", style="cyan")
        table.add_column("Prompt", max_width=50)
        table.add_column("Score", justify="right")
        for row in result["history"]:
            table.add_row(
                row.get("created_at", "")[:16],
                row.get("type", "?"),
                (row.get("prompt", "?") or "")[:50],
                str(row.get("agreement_score", "-")),
            )
        console.print(table)
    else:
        console.print(f"[dim]{result}[/dim]")


@api.command("radio")
@click.option("-n", "limit", default=30, help="Number of entries")
@click.pass_context
def api_radio(ctx, limit):
    """Query radio feed."""
    base = ctx.obj.get("api_base", API_LOCAL)
    result = _api(f"/cc/radio?limit={limit}", base=base)
    if isinstance(result, dict) and "radio" in result:
        for msg in result["radio"]:
            ts = msg.get("ts", "")[:16]
            sender = msg.get("sender", "?")
            text = (msg.get("text", "") or "")[:80]
            console.print(f"  [dim]{ts}[/dim] [cyan]{sender:>10s}[/cyan]  {text}")
    else:
        console.print(f"[dim]{result}[/dim]")


@api.command("agents")
@click.pass_context
def api_agents(ctx):
    """Show agent status and health."""
    base = ctx.obj.get("api_base", API_LOCAL)
    result = _api("/agents/status", base=base)
    if isinstance(result, dict) and "agents" in result:
        table = Table(title="Agent Roster")
        table.add_column("Agent", style="cyan")
        table.add_column("Status")
        table.add_column("Model", style="dim")
        table.add_column("Tokens", justify="right")
        table.add_column("Cost", justify="right")
        for agent in result["agents"]:
            status_color = "green" if agent.get("status") == "active" else "red"
            table.add_row(
                agent.get("name", "?"),
                f"[{status_color}]{agent.get('status', '?')}[/{status_color}]",
                agent.get("model", "-"),
                str(agent.get("total_tokens", 0)),
                f"${agent.get('total_cost', 0):.4f}",
            )
        console.print(table)
    else:
        console.print(f"[dim]{result}[/dim]")


@api.command("office")
@click.option("-n", "limit", default=20, help="Number of messages")
@click.pass_context
def api_office(ctx, limit):
    """Query office messages."""
    base = ctx.obj.get("api_base", API_LOCAL)
    result = _api(f"/cc/office?limit={limit}", base=base)
    if isinstance(result, dict) and "office" in result:
        table = Table(title=f"Office (last {limit})")
        table.add_column("Time", style="dim", min_width=16)
        table.add_column("From", style="cyan")
        table.add_column("To", style="yellow")
        table.add_column("Message", max_width=50)
        for msg in result["office"]:
            table.add_row(
                msg.get("ts", "")[:16],
                msg.get("sender", "?"),
                msg.get("receiver", "?"),
                (msg.get("text", "") or "")[:50],
            )
        console.print(table)
    else:
        console.print(f"[dim]{result}[/dim]")


@api.command("governor")
@click.pass_context
def api_governor(ctx):
    """Show governor token budgets and spending."""
    base = ctx.obj.get("api_base", API_LOCAL)
    result = _api("/governor", base=base)
    if isinstance(result, dict):
        table = Table(title="Governor")
        table.add_column("Agent", style="cyan")
        table.add_column("Tokens", justify="right")
        table.add_column("Cost", justify="right")
        table.add_column("Mode")
        agents = result.get("agents", result.get("governor", {}))
        if isinstance(agents, dict):
            for name, info in agents.items():
                if isinstance(info, dict):
                    table.add_row(
                        name,
                        str(info.get("total_tokens", 0)),
                        f"${info.get('total_cost', 0):.4f}",
                        info.get("mode", "-"),
                    )
        console.print(table)
    else:
        console.print(f"[dim]{result}[/dim]")


# ===========================================================================
# MONITOR -- Live terminal dashboard
# ===========================================================================
@cli.command()
@click.option("--interval", default=5, help="Refresh interval in seconds")
@click.pass_context
def monitor(ctx, interval):
    """Live terminal dashboard -- agents, tokens, history, radio."""
    base = ctx.obj.get("api_base", API_LOCAL)

    def _build_dashboard():
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3),
        )
        layout["body"].split_row(
            Layout(name="left"),
            Layout(name="right"),
        )
        layout["left"].split_column(
            Layout(name="agents"),
            Layout(name="governor"),
        )
        layout["right"].split_column(
            Layout(name="radio"),
            Layout(name="history"),
        )

        now = datetime.now().strftime("%H:%M:%S")
        layout["header"].update(Panel(
            f"[bold]rhea monitor[/bold]  |  {base}  |  {now}  |  refresh: {interval}s",
            style="cyan",
        ))

        agents_data = _api("/agents/status", base=base)
        if isinstance(agents_data, dict) and "agents" in agents_data:
            t = Table(show_header=True, expand=True)
            t.add_column("Agent")
            t.add_column("Status")
            t.add_column("Tokens", justify="right")
            agents_list = agents_data["agents"]
            if isinstance(agents_list, dict):
                iterator = agents_list.items()
            elif isinstance(agents_list, list):
                iterator = ((a.get("name", "?"), a) for a in agents_list if isinstance(a, dict))
            else:
                iterator = []
            for name, a in iterator:
                sc = "green" if a.get("status") == "active" else "red"
                t.add_row(name, f"[{sc}]{a.get('status', '?')}[/{sc}]", str(a.get("total_tokens", 0)))
            layout["agents"].update(Panel(t, title="Agents"))
        else:
            layout["agents"].update(Panel("[dim]no data[/dim]", title="Agents"))

        gov_data = _api("/governor", base=base)
        if isinstance(gov_data, dict):
            t = Table(show_header=True, expand=True)
            t.add_column("Agent")
            t.add_column("Cost", justify="right")
            agents = gov_data.get("agents", gov_data.get("governor", {}))
            if isinstance(agents, dict):
                for name, info in agents.items():
                    if isinstance(info, dict):
                        t.add_row(name, f"${info.get('total_cost', 0):.4f}")
            layout["governor"].update(Panel(t, title="Governor"))
        else:
            layout["governor"].update(Panel("[dim]no data[/dim]", title="Governor"))

        radio_data = _api("/cc/radio?limit=8", base=base)
        radio_text = Text()
        if isinstance(radio_data, dict) and "radio" in radio_data:
            for msg in radio_data["radio"]:
                ts = msg.get("ts", "")[-8:]
                sender = msg.get("sender", "?")
                text = (msg.get("text", "") or "")[:60]
                radio_text.append(f"{ts} ", style="dim")
                radio_text.append(f"{sender:>8s} ", style="cyan")
                radio_text.append(f"{text}\n")
        layout["radio"].update(Panel(radio_text or "[dim]no data[/dim]", title="Radio"))

        hist_data = _api("/cc/history?limit=5", base=base)
        hist_text = Text()
        if isinstance(hist_data, dict) and "history" in hist_data:
            for row in hist_data["history"]:
                ts = row.get("created_at", "")[-8:]
                prompt = (row.get("prompt", "?") or "")[:40]
                score = row.get("agreement_score", "-")
                hist_text.append(f"{ts} ", style="dim")
                hist_text.append(f"{prompt} ", style="white")
                hist_text.append(f"[{score}]\n", style="yellow")
        layout["history"].update(Panel(hist_text or "[dim]no data[/dim]", title="History"))

        layout["footer"].update(Panel(
            "[dim]q=quit  Ctrl+C=exit[/dim]",
            style="dim",
        ))
        return layout

    console.print("[yellow]Starting monitor... (Ctrl+C to exit)[/yellow]")
    try:
        with Live(_build_dashboard(), console=console, refresh_per_second=0.5) as live:
            while True:
                time.sleep(interval)
                live.update(_build_dashboard())
    except KeyboardInterrupt:
        console.print("[dim]Monitor stopped.[/dim]")


# ===========================================================================
# CHECK -- Run all invariant checks
# ===========================================================================
@cli.command()
def check():
    """Run all repo invariant checks."""
    console.print("[yellow]Running check.sh...[/yellow]")
    result = subprocess.run(
        ["bash", "scripts/rhea/check.sh"],
        cwd=str(REPO_ROOT),
        capture_output=True, text=True,
    )
    console.print(result.stdout)
    if result.returncode != 0:
        console.print(f"[red]{result.stderr}[/red]")


# ===========================================================================
# PUSH -- Git commit + push shortcut
# ===========================================================================
@cli.command()
@click.argument("message")
def commit(message):
    """Quick commit + push via rhea_commit.sh."""
    result = subprocess.run(
        ["bash", "scripts/rhea_commit.sh", message],
        cwd=str(REPO_ROOT),
        capture_output=True, text=True,
    )
    console.print(result.stdout)
    if result.returncode != 0:
        console.print(f"[red]{result.stderr}[/red]")
    subprocess.run(["git", "push"], cwd=str(REPO_ROOT))


# ===========================================================================
# NUKE -- Emergency operations
# ===========================================================================
@cli.group()
def emergency():
    """Emergency controls: stop agents, kill processes, rollback."""
    pass


@emergency.command("stop")
def emergency_stop():
    """Create STOP sentinel -- all daemons exit on next poll."""
    (REPO_ROOT / "STOP").touch()
    console.print("[red]STOP sentinel created. Daemons will exit.[/red]")


@emergency.command("resume")
def emergency_resume():
    """Remove all sentinels -- system operational."""
    for f in ["STOP", "PAUSE"]:
        (REPO_ROOT / f).unlink(missing_ok=True)
    console.print("[green]All sentinels removed. System operational.[/green]")


@emergency.command("pause")
def emergency_pause():
    """Create PAUSE sentinel -- loops will idle."""
    (REPO_ROOT / "PAUSE").touch()
    console.print("[yellow]PAUSE sentinel created. Loops will idle.[/yellow]")


@emergency.command("kill")
@click.argument("pattern")
def emergency_kill(pattern):
    """Kill processes matching pattern (shows before killing)."""
    result = subprocess.run(["pgrep", "-fl", pattern], capture_output=True, text=True)
    if not result.stdout.strip():
        console.print(f"[dim]No processes matching '{pattern}'[/dim]")
        return
    console.print(f"[yellow]Matching processes:[/yellow]\n{result.stdout}")
    subprocess.run(["pkill", "-f", pattern])
    console.print(f"[red]Killed processes matching '{pattern}'[/red]")


# ===========================================================================
# COWORK -- Agent coordination mode (reassembled co-work)
# ===========================================================================
@cli.group()
@click.pass_context
def cowork(ctx):
    """Co-work: interactive agent coordination from CLI."""
    pass


@cowork.command("session")
@click.option("--name", default=None, help="Session name")
@click.pass_context
def cowork_session(ctx, name):
    """Start a co-work session — multiplexed agent dashboard + command input."""
    import threading
    import uuid

    base = ctx.obj.get("api_base", API_LOCAL)
    session_id = name or f"cw-{uuid.uuid4().hex[:6]}"
    console.print(f"[cyan]Co-work session: {session_id}[/cyan]")
    console.print(f"[dim]API: {base}  |  Ctrl+C to exit[/dim]\n")

    stop_event = threading.Event()

    def _build_cowork_layout():
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="input", size=3),
        )
        layout["body"].split_row(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=2),
        )
        layout["left"].split_column(
            Layout(name="agents"),
            Layout(name="tasks"),
        )
        layout["right"].split_column(
            Layout(name="radio"),
            Layout(name="office"),
        )

        now = datetime.now().strftime("%H:%M:%S")
        layout["header"].update(Panel(
            f"[bold cyan]RHEA CO-WORK[/bold cyan]  |  {session_id}  |  {base}  |  {now}",
            style="cyan",
        ))

        # Agents pane
        agents_data = _api("/agents/status", base=base)
        if isinstance(agents_data, dict) and "agents" in agents_data:
            t = Table(show_header=True, expand=True, padding=(0, 1))
            t.add_column("Agent", style="cyan", min_width=6)
            t.add_column("●", min_width=1)
            t.add_column("T", justify="right", min_width=4)
            t.add_column("$", justify="right", min_width=5)
            agents_dict = agents_data["agents"]
            if isinstance(agents_dict, dict):
                for name_key, info in sorted(agents_dict.items()):
                    alive = info.get("alive", False)
                    dot = "[green]●[/green]" if alive else "[red]●[/red]"
                    tok = info.get("T_day", 0)
                    tok_s = f"{tok // 1000}K" if tok >= 1000 else str(tok)
                    cost = info.get("dollar_day", 0)
                    t.add_row(name_key[:6], dot, tok_s, f"{cost:.2f}")
            layout["agents"].update(Panel(t, title="[cyan]AGENTS[/cyan]", border_style="cyan"))
        else:
            layout["agents"].update(Panel("[dim]offline[/dim]", title="AGENTS"))

        # Tasks pane
        tasks_data = _api("/tasks", base=base)
        if isinstance(tasks_data, dict) and "tasks" in tasks_data:
            task_list = tasks_data["tasks"]
            summary = {}
            for task in task_list:
                s = task.get("status", "?")
                summary[s] = summary.get(s, 0) + 1
            parts = [f"[green]{summary.get('done', 0)} done[/green]",
                     f"[yellow]{summary.get('claimed', 0)} active[/yellow]",
                     f"[white]{summary.get('open', 0)} open[/white]",
                     f"[red]{summary.get('blocked', 0)} blocked[/red]"]
            task_text = Text()
            for task in task_list[:6]:
                status = task.get("status", "?")
                sc = {"done": "green", "claimed": "yellow", "open": "white", "blocked": "red"}.get(status, "dim")
                task_text.append(f"[{sc}]●[/{sc}] ", style=sc)
                title = (task.get("title", "?") or "")[:30]
                task_text.append(f"{title}\n")
            layout["tasks"].update(Panel(
                Text.from_markup("  ".join(parts)) if parts else task_text,
                title="[yellow]TASKS[/yellow]", border_style="yellow"))
        else:
            layout["tasks"].update(Panel("[dim]no data[/dim]", title="TASKS"))

        # Radio pane
        radio_data = _api("/feed?limit=12", base=base)
        radio_text = Text()
        if isinstance(radio_data, dict) and "items" in radio_data:
            for msg in radio_data["items"][:12]:
                ts = (msg.get("ts", "") or "")[-8:-3]
                sender = (msg.get("sender", "?") or "")[:6]
                text = ((msg.get("text", "") or "").replace("\n", " "))[:60]
                radio_text.append(f"{ts} ", style="dim")
                radio_text.append(f"{sender:>6s} ", style="cyan")
                radio_text.append(f"{text}\n")
        elif isinstance(radio_data, dict) and "radio" in radio_data:
            for msg in radio_data["radio"][:12]:
                ts = (msg.get("ts", "") or "")[-8:-3]
                sender = (msg.get("sender", "?") or "")[:6]
                text = ((msg.get("text", "") or "").replace("\n", " "))[:60]
                radio_text.append(f"{ts} ", style="dim")
                radio_text.append(f"{sender:>6s} ", style="cyan")
                radio_text.append(f"{text}\n")
        layout["radio"].update(Panel(radio_text or "[dim]waiting...[/dim]",
                                     title="[green]RADIO[/green]", border_style="green"))

        # Office pane
        office_data = _api("/cc/office?limit=6", base=base)
        office_text = Text()
        if isinstance(office_data, dict) and "office" in office_data:
            for msg in office_data["office"][:6]:
                sender = (msg.get("sender", "?") or "")[:4]
                receiver = (msg.get("receiver", "?") or "")[:4]
                text = ((msg.get("text", "") or "").replace("\n", " "))[:50]
                office_text.append(f"{sender}", style="cyan")
                office_text.append("→", style="dim")
                office_text.append(f"{receiver} ", style="yellow")
                office_text.append(f"{text}\n")
        layout["office"].update(Panel(office_text or "[dim]no messages[/dim]",
                                      title="[magenta]OFFICE[/magenta]", border_style="magenta"))

        layout["input"].update(Panel(
            "[dim]Commands: t <claim> = tribunal  |  task <title> = create task  |  "
            "wake <agent> = wake agent  |  q = quit[/dim]",
            style="dim",
        ))
        return layout

    try:
        with Live(_build_cowork_layout(), console=console, refresh_per_second=0.3) as live:
            while not stop_event.is_set():
                time.sleep(3)
                live.update(_build_cowork_layout())
    except KeyboardInterrupt:
        console.print(f"\n[dim]Session {session_id} ended.[/dim]")


@cowork.command("dispatch")
@click.argument("task_title")
@click.option("--agent", default="", help="Assign to specific agent")
@click.option("--priority", default="P1", help="Task priority (P0-P3)")
@click.pass_context
def cowork_dispatch(ctx, task_title, agent, priority):
    """Dispatch a task to the queue (like spawning an agent task)."""
    base = ctx.obj.get("api_base", API_LOCAL)
    import urllib.parse
    params = urllib.parse.urlencode({
        "title": task_title,
        "priority": priority,
        **({"agent": agent} if agent else {}),
    })
    try:
        r = requests.post(f"{base}/tasks?{params}", timeout=10)
        if r.status_code < 300:
            data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
            task_id = data.get("id", "?")
            console.print(f"[green]Task dispatched: {task_id}[/green]  {task_title}")
        else:
            console.print(f"[red]Failed: HTTP {r.status_code}[/red]")
    except Exception as e:
        console.print(f"[red]{e}[/red]")


@cowork.command("wake")
@click.argument("agent_name")
@click.pass_context
def cowork_wake(ctx, agent_name):
    """Wake an agent via radio broadcast."""
    base = ctx.obj.get("api_base", API_LOCAL)
    result = _api("/feed/broadcast", method="POST", base=base, data={
        "type": "wake",
        "sender": "human",
        "text": f"WAKE {agent_name.upper()} — requested via rhea cowork",
    })
    if isinstance(result, dict) and "error" not in result:
        console.print(f"[green]Wake signal sent to {agent_name}[/green]")
    else:
        console.print(f"[red]{result}[/red]")


@cowork.command("ask")
@click.argument("claim")
@click.option("--ice", is_flag=True, help="Use ICE (deep verification)")
@click.pass_context
def cowork_ask(ctx, claim, ice):
    """Quick tribunal query from co-work context."""
    base = ctx.obj.get("api_base", API_LOCAL)
    endpoint = "/tribunal/ice" if ice else "/tribunal"
    console.print(f"[yellow]→ {endpoint}[/yellow]")
    result = _api(endpoint, method="POST", base=base,
                  data={"prompt": claim, "k": 3, "tier": "cheap"}, timeout=120)
    if isinstance(result, dict) and "error" not in result:
        agreement = result.get("agreement_score", "?")
        consensus = result.get("consensus", result.get("consensus_text", "?"))
        color = "green" if isinstance(agreement, (int, float)) and agreement >= 0.6 else "red"
        console.print(Panel(
            f"[{color}]Agreement: {agreement}[/{color}]\n\n{consensus}",
            title="Tribunal", border_style=color,
        ))
    else:
        console.print(f"[red]{result}[/red]")


# ===========================================================================
# SWITCH -- Cloud/Localhost toggle
# ===========================================================================
@cli.command("local")
@click.pass_context
def switch_local(ctx):
    """Switch API target to localhost:8400."""
    os.environ["RHEA_API"] = "http://localhost:8400"
    console.print("[green]● LOCAL[/green]  http://localhost:8400")
    # Test connection
    try:
        r = requests.get("http://localhost:8400/health", timeout=3)
        if r.status_code == 200:
            console.print("[green]  connected[/green]")
        else:
            console.print(f"[yellow]  HTTP {r.status_code}[/yellow]")
    except Exception:
        console.print("[red]  unreachable[/red]")


@cli.command("cloud")
@click.pass_context
def switch_cloud(ctx):
    """Switch API target to rhea-tribunal.fly.dev."""
    os.environ["RHEA_API"] = API_CLOUD
    console.print(f"[cyan]● CLOUD[/cyan]  {API_CLOUD}")
    try:
        r = requests.get(f"{API_CLOUD}/health", timeout=5)
        if r.status_code == 200:
            console.print("[green]  connected[/green]")
        else:
            console.print(f"[yellow]  HTTP {r.status_code}[/yellow]")
    except Exception:
        console.print("[red]  unreachable[/red]")


# ===========================================================================
# Entry
# ===========================================================================
if __name__ == "__main__":
    cli(obj={})
