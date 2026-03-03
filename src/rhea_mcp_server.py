#!/usr/bin/env python3
"""
rhea_mcp_server.py — MCP server exposing Rhea Tribunal tools.

Connects to Xcode 26.3, Claude Code, Codex, or any MCP-compatible client.

Usage (stdio):
    python3 src/rhea_mcp_server.py

Register with Claude Code:
    claude mcp add --transport stdio rhea -- python3 src/rhea_mcp_server.py

Register with Xcode (ClaudeAgentConfig):
    Add to ~/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/settings.json
"""
from __future__ import annotations

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Project root + bridge import
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "src"))

_bridge = None

def _get_bridge():
    global _bridge
    if _bridge is None:
        from rhea_bridge import RheaBridge
        _bridge = RheaBridge()
    return _bridge

# ---------------------------------------------------------------------------
# Tribunal API base URL (local or remote)
# ---------------------------------------------------------------------------
TRIBUNAL_URL = os.environ.get("RHEA_TRIBUNAL_URL", "http://localhost:8400")

def _api_call(method: str, path: str, body: dict | None = None) -> dict:
    """Call tribunal API endpoint. Falls back to direct bridge if API unreachable."""
    import requests
    url = f"{TRIBUNAL_URL}{path}"
    api_key = os.environ.get("RHEA_API_KEY", "dev")
    headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
    try:
        if method == "GET":
            r = requests.get(url, headers=headers, timeout=30)
        else:
            r = requests.post(url, headers=headers, json=body or {}, timeout=60)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------
mcp = FastMCP(
    "Rhea Tribunal",
    instructions=(
        "Rhea is a multi-model consensus system. Use tribunal tools to get "
        "agreement analysis across multiple AI models. Disagreement between "
        "models is a red flag — high agreement = high confidence."
    ),
)


@mcp.tool(
    name="tribunal_consensus",
    description=(
        "Query the Rhea Tribunal for multi-model consensus. "
        "Sends a prompt to k different AI models and returns structured "
        "agreement analysis. Use this for code review, fact-checking, "
        "or any decision where you want multiple model perspectives. "
        "agreement_score > 0.8 = strong consensus, < 0.5 = disagreement."
    ),
)
def tribunal_consensus(
    prompt: str,
    k: int = 3,
    tier: str = "cheap",
    mode: str = "local",
    system: str = "",
) -> str:
    """Multi-model consensus query."""
    result = _api_call("POST", "/tribunal", {
        "prompt": prompt,
        "k": k,
        "tier": tier,
        "mode": mode,
        "system": system,
    })
    if "error" in result and not result.get("consensus"):
        # Fallback to direct bridge
        try:
            bridge = _get_bridge()
            r = bridge.tribunal(prompt=prompt, k=k, tier=tier, mode=mode, system=system)
            return json.dumps({
                "consensus": r.consensus_report,
                "agreement_score": r.agreement_score,
                "confidence": r.confidence,
                "models_responded": len([x for x in r.responses if not x.error]),
                "responses": [
                    {"model": x.model, "provider": x.provider, "text": x.text[:500]}
                    for x in r.responses if not x.error
                ],
            }, indent=2)
        except Exception as e2:
            return json.dumps({"error": f"API: {result.get('error')}; Bridge: {str(e2)}"})
    # Format API response
    return json.dumps({
        "consensus": result.get("consensus", ""),
        "agreement_score": result.get("agreement_score", 0),
        "confidence": result.get("confidence", 0),
        "models_responded": result.get("models_responded", 0),
        "agreement_points": result.get("agreement_points", []),
        "divergence_points": result.get("divergence_points", []),
        "responses": [
            {"model": r["model"], "provider": r["provider"], "text": r["text"][:500]}
            for r in result.get("responses", [])
        ],
    }, indent=2)


@mcp.tool(
    name="tribunal_sceptic",
    description=(
        "Sceptic tribunal — models actively critique the consensus answer. "
        "Returns counterarguments and the strongest challenge. "
        "Use this when you need adversarial review of a claim or decision."
    ),
)
def tribunal_sceptic(
    prompt: str,
    k: int = 3,
    tier: str = "cheap",
    devil_advocate: bool = True,
) -> str:
    """Adversarial consensus with devil's advocate."""
    result = _api_call("POST", "/tribunal/sceptic", {
        "prompt": prompt,
        "k": k,
        "tier": tier,
        "devil_advocate": devil_advocate,
    })
    return json.dumps({
        "consensus": result.get("consensus", ""),
        "agreement_score": result.get("agreement_score", 0),
        "counterarguments": result.get("counterarguments", []),
        "strongest_challenge": result.get("strongest_challenge", ""),
    }, indent=2)


@mcp.tool(
    name="tribunal_ice",
    description=(
        "ICE (Iterative Critique and Enhancement) tribunal — multi-round "
        "consensus with critique loops. Models critique each other's answers "
        "across multiple rounds. More expensive but higher quality. "
        "Use for critical decisions."
    ),
)
def tribunal_ice(
    prompt: str,
    k: int = 3,
    rounds: int = 2,
    tier: str = "cheap",
    chairman_tier: str = "balanced",
) -> str:
    """ICE iterative consensus."""
    result = _api_call("POST", "/tribunal/ice", {
        "prompt": prompt,
        "k": k,
        "rounds": rounds,
        "tier": tier,
        "chairman_tier": chairman_tier,
    })
    return json.dumps({
        "final_consensus": result.get("final_consensus", ""),
        "agreement_score": result.get("agreement_score", 0),
        "rounds_completed": result.get("rounds_completed", 0),
        "critique_summary": result.get("critique_summary", ""),
    }, indent=2)


@mcp.tool(
    name="tribunal_pr_review",
    description=(
        "Multi-model code review for a git diff or PR. "
        "Sends the diff to k models, identifies disagreements as red flags. "
        "Returns structured review with consensus on: correctness, security, "
        "style, and suggested improvements."
    ),
)
def tribunal_pr_review(
    diff: str,
    context: str = "",
    k: int = 3,
    tier: str = "cheap",
) -> str:
    """Multi-model PR/diff review."""
    system = (
        "You are a code reviewer. Analyze the diff for: "
        "1) Correctness bugs 2) Security vulnerabilities 3) Performance issues "
        "4) Style/readability. Be specific about line numbers. "
        "Rate severity: critical/warning/info."
    )
    if context:
        system += f"\n\nProject context: {context}"

    result = _api_call("POST", "/tribunal", {
        "prompt": f"Review this code diff:\n\n```diff\n{diff}\n```",
        "k": k,
        "tier": tier,
        "mode": "local",
        "system": system,
    })
    return json.dumps({
        "consensus": result.get("consensus", ""),
        "agreement_score": result.get("agreement_score", 0),
        "reviews": [
            {"model": r["model"], "text": r["text"][:800]}
            for r in result.get("responses", [])
        ],
    }, indent=2)


@mcp.tool(
    name="aletheia_search",
    description=(
        "Search the Aletheia proof store for verified claims. "
        "Returns proofs with verification chains and consensus scores. "
        "Use this to check if a claim has been previously verified."
    ),
)
def aletheia_search(query: str, limit: int = 5) -> str:
    """Search verified proofs."""
    result = _api_call("GET", f"/aletheia/search?q={query}&limit={limit}")
    return json.dumps(result, indent=2)


@mcp.tool(
    name="aletheia_verify",
    description=(
        "Submit a claim to Aletheia for verification. "
        "Runs the claim through the tribunal and stores the result "
        "as a proof with a verification chain."
    ),
)
def aletheia_verify(claim: str, domain: str = "general") -> str:
    """Verify a claim and store proof."""
    result = _api_call("POST", "/aletheia/verify", {
        "claim": claim,
        "domain": domain,
    })
    return json.dumps(result, indent=2)


@mcp.tool(
    name="bridge_query",
    description=(
        "Direct query to a specific AI model via the Rhea Bridge. "
        "Supports 31+ models across 6 providers. "
        "Use when you need a specific model's perspective, not consensus."
    ),
)
def bridge_query(
    prompt: str,
    model: str = "",
    tier: str = "cheap",
    system: str = "",
) -> str:
    """Query a specific model."""
    result = _api_call("POST", "/relay/proxy", {
        "prompt": prompt,
        "model": model,
        "tier": tier,
        "system": system,
    })
    return json.dumps(result, indent=2)


@mcp.tool(
    name="bridge_models",
    description="List all available models, providers, and cost tiers.",
)
def bridge_models() -> str:
    """List available models."""
    result = _api_call("GET", "/models")
    return json.dumps(result, indent=2)


@mcp.tool(
    name="rhea_health",
    description="Check Rhea Tribunal API health and connectivity.",
)
def rhea_health() -> str:
    """Health check."""
    result = _api_call("GET", "/health")
    return json.dumps(result, indent=2)


@mcp.tool(
    name="ontology_switch",
    description=(
        "Switch the active ontology lens for all subsequent tribunal queries. "
        "Available: general, pharmacology, biochemistry, logic, topology, systems_biology. "
        "This changes how models interpret and analyze prompts."
    ),
)
def ontology_switch(ontology: str) -> str:
    """Switch active ontology."""
    result = _api_call("POST", "/ontology/switch", {"ontology": ontology})
    return json.dumps(result, indent=2)


@mcp.tool(
    name="salon_ask",
    description=(
        "Multi-character thinking salon. Ask multiple AI characters "
        "(with distinct personalities and expertise) to discuss a topic. "
        "Returns a structured dialogue with different perspectives."
    ),
)
def salon_ask(
    prompt: str,
    characters: str = "default",
    tier: str = "cheap",
) -> str:
    """Multi-character thinking salon."""
    result = _api_call("POST", "/salon/ask", {
        "prompt": prompt,
        "characters": characters,
        "tier": tier,
    })
    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# OpenAI-compatible Chat Completions (for Xcode custom provider)
# ---------------------------------------------------------------------------
@mcp.tool(
    name="chat_completions",
    description=(
        "OpenAI-compatible chat completion endpoint. "
        "Routes through Rhea Bridge to any available model. "
        "Compatible with Xcode's custom provider interface."
    ),
)
def chat_completions(
    messages: str,
    model: str = "auto",
    temperature: float = 0.7,
) -> str:
    """Chat completion via bridge."""
    try:
        msgs = json.loads(messages) if isinstance(messages, str) else messages
    except json.JSONDecodeError:
        msgs = [{"role": "user", "content": messages}]

    # Extract prompt from messages
    prompt = "\n".join(
        f"{m.get('role', 'user')}: {m.get('content', '')}" for m in msgs
    )
    system = next(
        (m["content"] for m in msgs if m.get("role") == "system"), ""
    )

    result = _api_call("POST", "/relay/proxy", {
        "prompt": prompt,
        "model": model if model != "auto" else "",
        "system": system,
    })
    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    mcp.run(transport="stdio")
