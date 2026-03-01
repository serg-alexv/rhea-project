#!/usr/bin/env python3
"""
office.py — Agent Communicator layer, built on RheaBridge.

Architecture:
    Bridge = LLM transport (prompt → model → response)
    Office = protocol ON TOP of Bridge (agent → agent, persistence, git memory)

Every message passes through a Sonnet gate that compresses to compact AI-dialect
before routing. All traffic logged to git-backed memory layer.

Usage:
    from office import Office
    office = Office()
    reply = office.send("rex", "orion", "Evaluate signal density in last tribunal run")
    office.broadcast("rex", "New consensus model deployed, weighted pairwise active")
"""

import json
import time
import uuid
import subprocess
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Bridge is our transport
from rhea_bridge import RheaBridge, ModelResponse

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
OFFICE_LOG = _PROJECT_ROOT / "data" / "office.jsonl"
OFFICE_MEMORY = _PROJECT_ROOT / "opera" / "memory" / "office"

# Sonnet gate model — compresses human-verbose → AI-compact before relay
GATE_MODEL = "anthropic/claude-sonnet-4-20250514"
GATE_FALLBACK = "gemini/gemini-2.5-flash"

# Load AI Compact Language spec as gate system prompt
_LANG_SPEC_PATH = _PROJECT_ROOT / "docs" / "AI_COMPACT_LANG.md"

def _load_gate_system() -> str:
    """Load formal language spec. Falls back to minimal rules if file missing."""
    try:
        spec = _LANG_SPEC_PATH.read_text()
        return f"You are the Sonnet Gate. Compress messages using this protocol:\n\n{spec}\n\nOutput ONLY the compressed message. No explanation."
    except FileNotFoundError:
        return (
            "Compress to AI shorthand. Symbols: →∴Δ≈✓✗⊕⊖. "
            "Entities: RB=RheaBridge CA=ConsensusAnalyzer AL=Aletheia TB=Tribunal OF=Office. "
            "Max 5 lines. No articles/filler. Numbers+paths exact. Output ONLY compressed message."
        )

GATE_SYSTEM = _load_gate_system()


@dataclass
class OfficeMessage:
    id: str
    sender: str         # rex | orion | gemini | human | system
    receiver: str       # agent name or "all" for broadcast
    compressed: str     # gate-compressed — the ONLY representation stored
    ts: str = ""
    reply_to: Optional[str] = None
    response: Optional[str] = None
    response_ts: Optional[str] = None
    gate_tokens: int = 0
    relay_tokens: int = 0
    cost_usd: float = 0.0


class Office:
    """Agent-to-agent communicator built on RheaBridge."""

    def __init__(self, bridge: Optional[RheaBridge] = None):
        self.bridge = bridge or RheaBridge()
        OFFICE_LOG.parent.mkdir(parents=True, exist_ok=True)
        OFFICE_MEMORY.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Core: send message agent → agent
    # ------------------------------------------------------------------

    def send(
        self,
        sender: str,
        receiver: str,
        text: str,
        reply_to: Optional[str] = None,
        skip_gate: bool = False,
    ) -> OfficeMessage:
        """
        Send a message from one agent to another.
        1. Compress through Sonnet gate (unless skip_gate)
        2. Route to receiver's model via Bridge
        3. Log everything to office.jsonl + git memory
        """
        msg_id = uuid.uuid4().hex[:12]
        ts = datetime.now(timezone.utc).isoformat()

        # Step 1: Gate compression
        if skip_gate or len(text) < 40:
            compressed = text
            gate_tokens = 0
        else:
            compressed, gate_tokens = self._gate_compress(text)

        # Step 2: Route to receiver
        response_text, relay_tokens, cost = self._relay(
            sender, receiver, compressed, reply_to
        )

        msg = OfficeMessage(
            id=msg_id,
            sender=sender,
            receiver=receiver,
            compressed=compressed,
            ts=ts,
            reply_to=reply_to,
            response=response_text,
            response_ts=datetime.now(timezone.utc).isoformat(),
            gate_tokens=gate_tokens,
            relay_tokens=relay_tokens,
            cost_usd=cost,
        )

        # Step 3: Persist
        self._log(msg)
        self._write_memory(msg)

        return msg

    def broadcast(self, sender: str, text: str) -> list[OfficeMessage]:
        """Send to all agents (except sender)."""
        agents = ["rex", "orion", "gemini"]
        results = []
        for agent in agents:
            if agent != sender:
                results.append(self.send(sender, agent, text))
        return results

    def post_chat(self, sender: str, text: str) -> dict:
        """Post to shared chat (no LLM routing, just persistence)."""
        msg_id = uuid.uuid4().hex[:12]
        ts = datetime.now(timezone.utc).isoformat()
        record = {
            "id": msg_id,
            "sender": sender,
            "text": text,
            "ts": ts,
            "type": "chat",
        }
        self._append_log(record)
        return record

    def get_chat(self, after: str = "", limit: int = 50) -> list[dict]:
        """Read shared chat history."""
        if not OFFICE_LOG.exists():
            return []
        messages = []
        with open(OFFICE_LOG) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    if after and rec.get("ts", "") <= after:
                        continue
                    messages.append(rec)
                except json.JSONDecodeError:
                    continue
        return messages[-limit:]

    def history(self, agent: Optional[str] = None, limit: int = 20) -> list[dict]:
        """Get office message history, optionally filtered by agent."""
        if not OFFICE_LOG.exists():
            return []
        messages = []
        with open(OFFICE_LOG) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    if agent and rec.get("sender") != agent and rec.get("receiver") != agent:
                        continue
                    messages.append(rec)
                except json.JSONDecodeError:
                    continue
        return messages[-limit:]

    # ------------------------------------------------------------------
    # Gate: Sonnet compresses to compact AI dialect
    # ------------------------------------------------------------------

    def _gate_compress(self, text: str) -> tuple[str, int]:
        """Run text through Sonnet gate → compact AI shorthand."""
        try:
            resp: ModelResponse = self.bridge.ask(
                prompt=text,
                model=GATE_MODEL,
                system=GATE_SYSTEM,
                max_tokens=256,
                temperature=0.1,
            )
            if resp.error:
                # Fallback to cheaper model
                resp = self.bridge.ask(
                    prompt=text,
                    model=GATE_FALLBACK,
                    system=GATE_SYSTEM,
                    max_tokens=256,
                    temperature=0.1,
                )
            return (resp.text or text), resp.tokens_used
        except Exception:
            return text, 0  # gate failure = pass through raw

    # ------------------------------------------------------------------
    # Relay: route compressed message to receiver's model
    # H₂O: Sonnet bonded on both sides (compress in → agent → compress out)
    # ------------------------------------------------------------------

    # Agent → native model mapping (cheap tier — Sonnet is the expensive part)
    AGENT_MODELS = {
        "orion":  "openai/gpt-4o",
        "gemini": "gemini/gemini-2.5-flash",
        "rex":    None,  # Rex = local process, no relay
        "human":  None,  # Human = no model, persist only
    }

    AGENT_SYSTEM = {
        "orion": "You are Orion (GPT). Respond in dense AI shorthand. Symbols: →∴Δ≈✓✗. No filler.",
        "gemini": "You are Gemini. Respond in dense AI shorthand. Symbols: →∴Δ≈✓✗. No filler.",
    }

    def _relay(
        self,
        sender: str,
        receiver: str,
        compressed_msg: str,
        reply_to: Optional[str] = None,
    ) -> tuple[str, int, float]:
        """
        Route compressed message to receiver's native model.
        H₂O bond: response also passes back through Sonnet compression.
        Returns (response_text, tokens_used, cost_usd).
        """
        model = self.AGENT_MODELS.get(receiver)

        # No model target → persist-only (human, rex-local)
        if model is None:
            return compressed_msg, 0, 0.0

        # Build context if reply chain exists
        prompt = compressed_msg
        if reply_to:
            ctx = self._fetch_context(reply_to)
            if ctx:
                prompt = f"[prior: {ctx}]\n{compressed_msg}"

        # Agent processes the message
        system = self.AGENT_SYSTEM.get(receiver, "Respond concisely. AI shorthand OK.")
        try:
            resp: ModelResponse = self.bridge.ask(
                prompt=prompt,
                model=model,
                system=system,
                max_tokens=512,
                temperature=0.4,
            )
            if resp.error:
                return f"[RELAY_ERROR: {resp.error}]", 0, 0.0

            raw_response = resp.text or ""
            relay_tokens = resp.tokens_used

            # H₂O bond: compress response back through Sonnet
            compressed_response, gate_out_tokens = self._gate_compress(raw_response)

            # Estimate cost from bridge price table
            cost = self._estimate_cost(model, relay_tokens, gate_out_tokens)

            return compressed_response, relay_tokens + gate_out_tokens, cost

        except Exception as e:
            return f"[RELAY_ERROR: {e}]", 0, 0.0

    def _fetch_context(self, reply_to: str) -> Optional[str]:
        """Load the original message for reply context."""
        if not OFFICE_LOG.exists():
            return None
        with open(OFFICE_LOG) as f:
            for line in f:
                try:
                    rec = json.loads(line.strip())
                    if rec.get("id") == reply_to:
                        return rec.get("compressed") or rec.get("text", "")
                except (json.JSONDecodeError, KeyError):
                    continue
        return None

    def _estimate_cost(self, model: str, relay_tokens: int, gate_tokens: int) -> float:
        """Rough cost: relay model + Sonnet gate output pass."""
        from rhea_bridge import PRICE_TABLE, PRICE_DEFAULT
        # Relay model cost (assume 50/50 in/out split)
        model_id = model.split("/")[-1] if "/" in model else model
        price_in, price_out = PRICE_TABLE.get(model_id, PRICE_DEFAULT)
        relay_cost = (relay_tokens * (price_in + price_out) / 2) / 1_000_000
        # Gate output pass (Sonnet)
        gate_price_in, gate_price_out = PRICE_TABLE.get("claude-sonnet-4-20250514", (3.0, 15.0))
        gate_cost = (gate_tokens * (gate_price_in + gate_price_out) / 2) / 1_000_000
        return round(relay_cost + gate_cost, 8)

    # ------------------------------------------------------------------
    # Persistence: JSONL log + git memory layer
    # ------------------------------------------------------------------

    def _log(self, msg: OfficeMessage) -> None:
        """Append to office.jsonl + SQL write-through."""
        record = asdict(msg)
        self._append_log(record)
        try:
            from rhea_db import persist_office_message
            persist_office_message(record)
        except Exception:
            pass  # SQL persistence must never break the office

    def _append_log(self, record: dict) -> None:
        """Append any dict to the office log."""
        with open(OFFICE_LOG, "a") as f:
            f.write(json.dumps(record, default=str) + "\n")

    def _write_memory(self, msg: OfficeMessage) -> None:
        """Write to git-backed memory layer: opera/memory/office/YYYY-MM-DD.jsonl"""
        date_str = msg.ts[:10] if msg.ts else datetime.now(timezone.utc).strftime("%Y-%m-%d")
        day_file = OFFICE_MEMORY / f"{date_str}.jsonl"
        with open(day_file, "a") as f:
            f.write(json.dumps(asdict(msg), default=str) + "\n")

    def git_commit_memory(self, message: str = "office: daily communication log") -> bool:
        """Commit the memory layer to git."""
        try:
            subprocess.run(
                ["git", "add", str(OFFICE_MEMORY)],
                cwd=str(_PROJECT_ROOT),
                capture_output=True,
                timeout=10,
            )
            subprocess.run(
                ["bash", "scripts/rhea_commit.sh", "-m", message],
                cwd=str(_PROJECT_ROOT),
                capture_output=True,
                timeout=15,
            )
            return True
        except Exception:
            return False
