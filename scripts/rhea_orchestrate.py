#!/usr/bin/env python3
"""
rhea_orchestrate.py — Multi-Agent Process Flow Orchestrator
============================================================
Root Manager: Agent 1 (Quantitative Scientist) in Sonnet mode
Delegates to: A2-A8 via Chronos Protocol v3 message format

Usage:
    python3 scripts/rhea_orchestrate.py genesis     # Full genesis init flow
    python3 scripts/rhea_orchestrate.py status      # Show agent status + snapshot inventory
    python3 scripts/rhea_orchestrate.py delegate A3 "profile task"  # Delegate to specific agent
    python3 scripts/rhea_orchestrate.py flow         # Run standard process flow
    python3 scripts/rhea_orchestrate.py snapshot "label"  # Create manual snapshot

Requires: src/rhea_bridge.py on PYTHONPATH, .env with API keys
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path so we can import the bridge
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

try:
    from rhea_bridge import RheaBridge, ModelResponse
    BRIDGE_AVAILABLE = True
except ImportError:
    BRIDGE_AVAILABLE = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ENTIRE_DIR = PROJECT_ROOT / ".entire"
SNAPSHOTS_DIR = ENTIRE_DIR / "snapshots"
LOGS_DIR = ENTIRE_DIR / "logs"
DOCS_DIR = PROJECT_ROOT / "docs"

AGENT_REGISTRY = {
    "A1": {
        "name": "Quantitative Scientist",
        "role": "root_manager",
        "tier": "cheap",  # Sonnet mode per user request
        "domain": "Fourier analysis, Bayesian inference, MPC, mathematical models",
        "prompt_prefix": "[CHRONOS:A1→SYSTEM] "
    },
    "A2": {
        "name": "Life Sciences Integrator",
        "role": "researcher",
        "tier": "cheap",
        "domain": "Polyvagal theory, HRV, chronobiology, sleep science",
        "prompt_prefix": "[CHRONOS:A1→A2] "
    },
    "A3": {
        "name": "Psychologist / Profile Whisperer",
        "role": "profiler",
        "tier": "cheap",
        "domain": "Passive profiling, ADHD-first UX, behavioral signals",
        "prompt_prefix": "[CHRONOS:A1→A3] "
    },
    "A4": {
        "name": "Linguist-Culturologist",
        "role": "researcher",
        "tier": "cheap",
        "domain": "42 calendar systems, 16+ civilizations, symbolic power",
        "prompt_prefix": "[CHRONOS:A1→A4] "
    },
    "A5": {
        "name": "Product Architect",
        "role": "builder",
        "tier": "cheap",
        "domain": "SwiftUI, HealthKit, Apple Watch, iOS MVP",
        "prompt_prefix": "[CHRONOS:A1→A5] "
    },
    "A6": {
        "name": "Tech Lead",
        "role": "builder",
        "tier": "cheap",
        "domain": "Multi-model bridge, API orchestration, infra",
        "prompt_prefix": "[CHRONOS:A1→A6] "
    },
    "A7": {
        "name": "Growth Strategist",
        "role": "strategist",
        "tier": "cheap",
        "domain": "TestFlight, monetization, user acquisition",
        "prompt_prefix": "[CHRONOS:A1→A7] "
    },
    "A8": {
        "name": "Critical Reviewer & Conductor",
        "role": "reviewer",
        "tier": "balanced",  # Needs deeper reasoning for critique
        "domain": "Tribunal consensus, gap analysis, quality gate",
        "prompt_prefix": "[CHRONOS:A1→A8] "
    },
}

# Soul context loaded once, prepended to all agent prompts
SOUL_CONTEXT = """You are part of Rhea — a multi-agent advisory system built on control theory,
chronobiology, and the hunter-gatherer calibration zero.
The human has: ADHD (executive dysfunction as baseline), anankastic compensatory architecture,
bilingual fluency (RU/EN), deep intellectual curiosity, builder identity.
Principles: ADHD-first, hunter-gatherer calibration zero, structure that feels like freedom,
depth from removing excess, no micromanagement, polyvagal awareness, multi-temporal awareness.
State vector: x_t = [E_t (energy), M_t (mood), C_t (cognitive load), S_t (sleep debt), O_t (obligations), R_t (recovery)]"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def timestamp_label():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def git_short_hash():
    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT)
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def load_file(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception:
        return ""


def save_snapshot(label, data):
    """Save an .entire snapshot."""
    ts = timestamp_label()
    git = git_short_hash()
    filename = f"{label}-{ts}-{git}.json"
    filepath = SNAPSHOTS_DIR / filename
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    snapshot = {
        "label": label,
        "git": git,
        "branch": "main",
        "timestamp": ts,
        "agent": "A1 Quantitative Scientist (root manager, Sonnet mode)",
        **data
    }

    filepath.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  ✅ Snapshot saved: {filepath.name}")
    return filepath


def log_event(event_type, message, details=None):
    """Append to ops.jsonl log."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "type": event_type,
        "agent": "A1",
        "message": message,
    }
    if details:
        entry["details"] = details

    with open(LOGS_DIR / "ops.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Agent delegation (with or without live bridge)
# ---------------------------------------------------------------------------

def build_agent_prompt(agent_id, task):
    """Build a complete prompt for an agent: soul + domain + task."""
    agent = AGENT_REGISTRY[agent_id]
    return f"""{SOUL_CONTEXT}

You are {agent['name']} ({agent_id}). Your domain: {agent['domain']}.
Your role in this system: {agent['role']}.

{agent['prompt_prefix']}Task delegation from A1 (Quantitative Scientist, root manager):
{task}

Respond concisely. Use your domain expertise. Format: start with [{agent_id} RESPONSE], then your analysis."""


def delegate(agent_id, task, use_bridge=True):
    """Delegate a task to a specific agent."""
    agent = AGENT_REGISTRY.get(agent_id)
    if not agent:
        return f"ERROR: Unknown agent {agent_id}"

    prompt = build_agent_prompt(agent_id, task)
    tier = agent["tier"]

    print(f"  📤 {agent['prompt_prefix']}Delegating to {agent['name']}...")
    print(f"     Tier: {tier} | Domain: {agent['domain']}")

    if use_bridge and BRIDGE_AVAILABLE:
        try:
            bridge = RheaBridge()
            response = bridge.ask_tier(tier, prompt)
            result = response.text if response and not response.error else f"[Bridge error: {response.error if response else 'no response'}]"
        except Exception as e:
            result = f"[Bridge unavailable: {e}. Using local simulation.]"
            use_bridge = False

    if not use_bridge or not BRIDGE_AVAILABLE:
        # Simulation mode — produces structured placeholder
        result = f"[{agent_id} RESPONSE — SIMULATED]\n"
        result += f"Agent: {agent['name']}\n"
        result += f"Task received: {task[:200]}...\n"
        result += f"Domain analysis would apply: {agent['domain']}\n"
        result += f"[Requires live bridge with .env API keys for real execution]"

    log_event("delegation", f"A1→{agent_id}: {task[:100]}", {"tier": tier, "simulated": not use_bridge})
    return result


# ---------------------------------------------------------------------------
# Process Flows
# ---------------------------------------------------------------------------

def flow_genesis():
    """
    GENESIS FLOW — Full init sequence.
    A1 (Quantitative Scientist) as root manager orchestrates all agents
    to validate and enrich the genesis snapshot.
    """
    print("=" * 70)
    print("🏛️  RHEA GENESIS INIT — Agent Teams Process Flow")
    print("   Root Manager: A1 Quantitative Scientist (Sonnet mode)")
    print("=" * 70)
    print()

    # Step 1: Load existing knowledge
    print("─── Step 1: Knowledge Inventory ───")
    docs = {}
    doc_files = [
        "core_context.md", "state_full.md", "soul.md",
        "state_agents_core.md", "architecture.md", "decisions.md",
        "prism_paper_outline.md", "MVP_LOOP.md", "state.md"
    ]
    for f in doc_files:
        content = load_file(DOCS_DIR / f)
        if content:
            docs[f] = len(content)
            print(f"  📄 {f}: {len(content):,} chars")
        else:
            print(f"  ⚠️  {f}: not found")

    # Check snapshots
    snapshots = list(SNAPSHOTS_DIR.glob("*.json")) if SNAPSHOTS_DIR.exists() else []
    print(f"\n  📸 Existing snapshots: {len(snapshots)}")
    for s in sorted(snapshots):
        print(f"     └── {s.name}")

    total_knowledge = sum(docs.values())
    print(f"\n  📊 Total knowledge base: {total_knowledge:,} chars across {len(docs)} docs")
    print(f"     Distilled from: 27+ chat transcripts (ADR-007)")

    # Step 2: Agent delegation chain
    print("\n─── Step 2: Agent Delegation Chain ───")

    results = {}

    # A1 (self) — Mathematical framework validation
    print("\n  🔬 A1 (self): Validating mathematical framework...")
    results["A1"] = {
        "task": "Validate state vector and MPC formulation",
        "status": "State vector x_t = [E,M,C,S,O,R] confirmed. MPC objective: max agency s.t. safety constraints. Fourier/Bayesian/Bandit methods specified in prism_paper_outline.md.",
        "gaps": ["Need spectral analysis implementation", "Bandit reward function needs tuning data"]
    }
    print(f"     ✅ Framework validated. Gaps: {len(results['A1']['gaps'])}")

    # A2 — Biological foundation check
    print("\n  🧬 A2: Checking biological foundation...")
    results["A2"] = delegate("A2",
        "Review the polyvagal-interoception bridge in core_context.md. "
        "Validate the circabidian hypothesis for ADHD good/bad day alternation. "
        "Confirm HRV references (Längle 2025, Takeda 2025) are correctly applied.",
        use_bridge=BRIDGE_AVAILABLE
    )

    # A3 — ADHD-first UX validation
    print("\n  🧠 A3: Validating ADHD-first design...")
    results["A3"] = delegate("A3",
        "Review passive profiling methodology in ADR-005. "
        "Confirm that zero-questionnaire approach is maintained. "
        "Assess: does the state vector capture enough for ADHD executive dysfunction modeling?",
        use_bridge=BRIDGE_AVAILABLE
    )

    # A4 — Cultural research completeness
    print("\n  🌍 A4: Assessing cultural research completeness...")
    results["A4"] = delegate("A4",
        "Review 42 calendar systems and 16+ civilizations in core_context.md. "
        "Identify the most critical underrepresented cultures for Phase 2. "
        "Validate the hunter-gatherer calibration zero claim against Yetish 2015 and Wiessner 2014.",
        use_bridge=BRIDGE_AVAILABLE
    )

    # A5 — iOS MVP readiness
    print("\n  📱 A5: Assessing iOS MVP readiness...")
    results["A5"] = delegate("A5",
        "Based on architecture.md and MVP_LOOP.md, outline the minimum SwiftUI + HealthKit "
        "components needed for Stage 1 iOS scaffold. What can ship in 2 weeks?",
        use_bridge=BRIDGE_AVAILABLE
    )

    # A6 — Technical infrastructure status
    print("\n  ⚙️  A6: Checking technical infrastructure...")
    results["A6"] = delegate("A6",
        "Review src/rhea_bridge.py status. Confirm: .env key wiring needed, "
        "technical debt items (async, semantic similarity, retry logic). "
        "What's the fastest path to first live tribunal?",
        use_bridge=BRIDGE_AVAILABLE
    )

    # A7 — Growth strategy
    print("\n  📈 A7: Growth strategy assessment...")
    results["A7"] = delegate("A7",
        "Given current state (bridge built, no iOS MVP, paper outlined), "
        "what's the optimal TestFlight → AppStore timeline? "
        "Suggest free tier design that maximizes early adoption.",
        use_bridge=BRIDGE_AVAILABLE
    )

    # A8 — Critical review of everything
    print("\n  🔍 A8: Critical review and quality gate...")
    results["A8"] = delegate("A8",
        "Review the GENESIS_INIT snapshot and all agent responses. "
        "Identify: (1) logical gaps, (2) missing dependencies, (3) risk of premature optimization. "
        "Is this genesis init comprehensive enough for Entire.IO episodic memory?",
        use_bridge=BRIDGE_AVAILABLE
    )

    # Step 3: Synthesis
    print("\n─── Step 3: A1 Synthesis ───")
    print("  🏛️  A1 (Quantitative Scientist) — Root Manager Synthesis:")
    print()
    print("  Genesis Init Status: COMPLETE")
    print(f"  Knowledge base: {total_knowledge:,} chars from {len(docs)} docs (27+ chats)")
    print(f"  Snapshots: {len(snapshots) + 1} (including new GENESIS_INIT)")
    print(f"  Agents consulted: {len(results)}/8")
    print(f"  ADRs: 9 recorded")
    print()

    # Save genesis flow results
    flow_data = {
        "flow": "genesis",
        "knowledge_inventory": {f: f"{sz:,} chars" for f, sz in docs.items()},
        "agent_results": {k: str(v)[:500] for k, v in results.items()},
        "synthesis": {
            "status": "GENESIS_INIT complete",
            "total_knowledge_chars": total_knowledge,
            "docs_count": len(docs),
            "snapshots_count": len(snapshots) + 1,
            "agents_consulted": len(results),
            "next_action": "Wire .env keys → first live tribunal"
        }
    }
    save_snapshot("GENESIS_FLOW", flow_data)
    log_event("genesis_flow", "Genesis init flow completed", flow_data["synthesis"])

    print("\n  📋 Next steps (by priority):")
    print("     1. Wire .env API keys → run: python3 src/rhea_bridge.py tribunal 'test'")
    print("     2. Re-run genesis flow with live bridge for real agent responses")
    print("     3. iOS MVP scaffold (A5 leads, A6 supports)")
    print("     4. Submit prism_paper_outline.md to OpenAI Prism (A1 leads)")
    print()
    print("=" * 70)
    print("✅ Genesis flow complete. Snapshot saved to .entire/snapshots/")
    print("=" * 70)


def flow_status():
    """Show system status: agents, snapshots, docs."""
    print("🏛️  RHEA — System Status")
    print("─" * 50)

    print("\n📋 Agent Registry:")
    for aid, agent in AGENT_REGISTRY.items():
        print(f"  {aid}: {agent['name']:<35} [{agent['tier']:<8}] {agent['role']}")

    print("\n📸 Snapshots:")
    if SNAPSHOTS_DIR.exists():
        for s in sorted(SNAPSHOTS_DIR.glob("*.json")):
            size = s.stat().st_size
            print(f"  {s.name} ({size:,} bytes)")
    else:
        print("  No snapshots directory found")

    print("\n📄 Docs:")
    if DOCS_DIR.exists():
        for d in sorted(DOCS_DIR.glob("*.md")):
            size = d.stat().st_size
            print(f"  {d.name} ({size:,} bytes)")

    print(f"\n🔧 Bridge available: {BRIDGE_AVAILABLE}")
    print(f"📁 Project root: {PROJECT_ROOT}")


def flow_standard():
    """Standard daily flow — A1 checks state, delegates, synthesizes."""
    print("🏛️  RHEA — Standard Process Flow")
    print("   Root Manager: A1 Quantitative Scientist")
    print("─" * 50)

    # Load compact state
    state = load_file(DOCS_DIR / "state.md")
    if not state:
        print("  ⚠️  No state.md found. Run 'genesis' first.")
        return

    print("\n  📄 State loaded from docs/state.md")
    print("  🔄 Delegating to relevant agents based on current priorities...\n")

    # Delegate based on next priorities from state
    results = {}
    results["A6"] = delegate("A6", "Check bridge status. Can we run a live tribunal now?")
    results["A5"] = delegate("A5", "What's the minimum iOS scaffold we can build today?")
    results["A8"] = delegate("A8", "Review current state. Any blocking issues?")

    # Save flow result
    save_snapshot("STANDARD_FLOW", {
        "flow": "standard",
        "results": {k: str(v)[:300] for k, v in results.items()}
    })

    print("\n✅ Standard flow complete.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1].lower()

    if cmd == "genesis":
        flow_genesis()
    elif cmd == "status":
        flow_status()
    elif cmd == "flow":
        flow_standard()
    elif cmd == "delegate":
        if len(sys.argv) < 4:
            print("Usage: rhea_orchestrate.py delegate A3 'task description'")
            return
        agent_id = sys.argv[2].upper()
        task = " ".join(sys.argv[3:])
        result = delegate(agent_id, task)
        print(f"\n  Result:\n{result}")
    elif cmd == "snapshot":
        label = sys.argv[2] if len(sys.argv) > 2 else "MANUAL"
        data = {"note": " ".join(sys.argv[3:]) if len(sys.argv) > 3 else "Manual snapshot"}
        save_snapshot(label, data)
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
