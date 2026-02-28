#!/usr/bin/env python3
"""
token_governor.py — Dual-rail token governor for all Rhea agents.

Upper bound: don't exceed daily budget cap
Lower bound: T_day == 0 = HARD FAIL
Below floor trajectory → auto-transition to compact recovery mode

Absorbed from:
  - Orion P0 mandate (RELAY_20260227_165546)
  - AI_COMPACT_LANG v0.2 §Token Governor
  - µACP resource bounds (arXiv:2601.00219)

Usage:
    from token_governor import Governor
    gov = Governor("rex")
    status = gov.check()   # → {pace, forecast, mode, T_day, $_day, ...}
    gov.enforce()           # → throttles or triggers compact recovery
"""

import json
import math
import random
from dataclasses import dataclass
from datetime import datetime, date, timezone
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
BRIDGE_LOG = _PROJECT_ROOT / "logs" / "bridge_calls.jsonl"
REX_SESSIONS = Path.home() / ".claude" / "projects" / "-Users-sa-rh-1"
GOVERNOR_STATE = _PROJECT_ROOT / "opera" / "metrics" / "governor_state.json"
BILLING_POLICY_PATH = _PROJECT_ROOT / "opera" / "metrics" / "governor_billing_policy.json"

# --- Budget caps per agent (USD/day) ---
# Rex = subscription (Anthropic Max), cost tracking = shadow only, no real billing.
# Upper rail disabled for subscription agents — only lower rail (floor) matters.
BUDGET_CAPS = {
    "rex":    0.0,     # Subscription — no per-token billing. Upper rail OFF.
    "orion":   5.0,    # GPT-5.3 API-billed
    "gemini":  2.0,    # Flash API-billed
    "shared":  1.0,
}

# Subscription agents: upper bound disabled, only floor trajectory enforced
SUBSCRIPTION_AGENTS = {"rex"}

# --- Floor trajectory: minimum spend curve ---
# time-weighted: by hour H, agent should have spent at least floor(H) tokens
# Linear interpolation: at hour 0 = 0, at hour 24 = min_daily_tokens
MIN_DAILY_TOKENS = {
    "rex":    500,     # Rex must do SOMETHING
    "orion":  200,
    "gemini": 100,
    "shared":  50,
}

# Provider → agent mapping
AGENT_MAP = {
    "openai": "orion",
    "gemini": "gemini",
    "anthropic": "rex",
    "deepseek": "gemini",
    "openrouter": "shared",
    "huggingface": "shared",
    "azure": "orion",
}


def _default_billing_mode(agent: str) -> str:
    return "subscription" if agent in SUBSCRIPTION_AGENTS else "api"


def _load_billing_policy() -> dict[str, dict[str, Any]]:
    """
    Load optional billing policy overrides from JSON.

    Supported shapes:
    1) {"agents": {"orion": "subscription"}}
    2) {"agents": {"orion": {"billing_mode": "subscription", "budget_cap": 0.0}}}
    """
    policy: dict[str, dict[str, Any]] = {}

    for agent in set(BUDGET_CAPS.keys()) | set(MIN_DAILY_TOKENS.keys()):
        policy[agent] = {
            "billing_mode": _default_billing_mode(agent),
            "budget_cap": float(BUDGET_CAPS.get(agent, 0.0)),
        }

    if not BILLING_POLICY_PATH.exists():
        return policy

    try:
        raw = json.loads(BILLING_POLICY_PATH.read_text())
    except Exception:
        return policy

    agents = raw.get("agents", {})
    if not isinstance(agents, dict):
        return policy

    for agent, spec in agents.items():
        a = str(agent).lower()
        cur = policy.get(
            a,
            {
                "billing_mode": _default_billing_mode(a),
                "budget_cap": float(BUDGET_CAPS.get(a, 0.0)),
            },
        )

        if isinstance(spec, str):
            mode = spec.lower().strip()
            if mode in {"subscription", "api"}:
                cur["billing_mode"] = mode
        elif isinstance(spec, dict):
            mode = str(spec.get("billing_mode", "")).lower().strip()
            if mode in {"subscription", "api"}:
                cur["billing_mode"] = mode
            if "budget_cap" in spec:
                try:
                    cur["budget_cap"] = float(spec.get("budget_cap"))
                except Exception:
                    pass

        policy[a] = cur

    return policy


@dataclass
class GovernorStatus:
    agent: str
    billing_mode: str   # subscription | api
    upper_rail_enabled: bool
    pace: str           # green | yellow | red
    forecast: str       # ok | risk
    mode: str           # normal | compact | critical
    T_day: int          # tokens spent today
    dollar_day: float   # cost today
    budget_cap: float
    budget_remaining: float
    floor_expected: int # minimum tokens expected by now
    floor_gap: int      # how far below floor (0 = on track)
    hour: int           # current hour (0-23)
    hard_fail: bool     # T_day == 0 at EOD check


class Governor:
    """Dual-rail token governor for one agent."""

    def __init__(self, agent: str):
        self.agent = agent.lower()
        policy = _load_billing_policy()
        cfg = policy.get(
            self.agent,
            {
                "billing_mode": _default_billing_mode(self.agent),
                "budget_cap": float(BUDGET_CAPS.get(self.agent, 2.0)),
            },
        )
        self.billing_mode = str(cfg.get("billing_mode", _default_billing_mode(self.agent))).lower()
        self.is_subscription = self.billing_mode == "subscription"
        self.budget_cap = float(cfg.get("budget_cap", BUDGET_CAPS.get(self.agent, 2.0)))
        if self.is_subscription:
            self.budget_cap = 0.0
        self.min_daily = MIN_DAILY_TOKENS.get(self.agent, 100)

    def check(self) -> GovernorStatus:
        """Read logs, compute current status."""
        today = date.today()
        now = datetime.now(timezone.utc)
        hour = now.hour

        # Aggregate today's spend for this agent
        T_day, dollar_day = self._aggregate_today(today)

        # If rex, also count Claude Code session tokens (shadow accounting)
        if self.agent == "rex":
            rex_tokens, rex_cost = self._aggregate_rex_sessions(today)
            T_day += rex_tokens
            dollar_day += rex_cost  # shadow cost — not real billing

        budget_remaining = self.budget_cap - dollar_day if not self.is_subscription else 0.0

        # Floor trajectory: linear interpolation
        # At hour H, expected = min_daily * (H / 24)
        floor_expected = int(self.min_daily * (hour / 24)) if hour > 0 else 0
        floor_gap = max(0, floor_expected - T_day)

        # --- Subscription agents: only floor matters ---
        if self.is_subscription:
            # Pace based on activity, not cost
            if T_day == 0 and hour >= 6:
                pace = "red"
            elif floor_gap > 0 and hour >= 12:
                pace = "yellow"
            elif T_day > floor_expected * 2:
                pace = "green"  # well above floor = strong
            else:
                pace = "green"

            # Forecast: only activity-based
            if T_day == 0 and hour >= 18:
                forecast = "risk"
            elif floor_gap > self.min_daily * 0.3:
                forecast = "risk"
            else:
                forecast = "ok"

            # Mode: subscription never hits critical from cost
            if floor_gap > 0 and hour >= 12:
                mode = "compact"
            else:
                mode = "normal"
        else:
            # --- API-billed agents: dual rail (cost + floor) ---
            budget_ratio = dollar_day / self.budget_cap if self.budget_cap > 0 else 0

            if budget_ratio > 0.9:
                pace = "red"
            elif budget_ratio > 0.7:
                pace = "yellow"
            elif floor_gap > 0 and hour >= 12:
                pace = "yellow"
            elif T_day == 0 and hour >= 6:
                pace = "red"
            else:
                pace = "green"

            if budget_remaining < 0:
                forecast = "risk"
            elif T_day == 0 and hour >= 18:
                forecast = "risk"
            elif floor_gap > self.min_daily * 0.3:
                forecast = "risk"
            else:
                forecast = "ok"

            if budget_remaining <= 0:
                mode = "critical"
            elif floor_gap > 0 and hour >= 12:
                mode = "compact"
            elif budget_ratio > 0.8:
                mode = "compact"
            else:
                mode = "normal"

        # Hard fail check (only meaningful at EOD)
        hard_fail = (T_day == 0 and hour >= 23)

        status = GovernorStatus(
            agent=self.agent,
            billing_mode=self.billing_mode,
            upper_rail_enabled=not self.is_subscription,
            pace=pace,
            forecast=forecast,
            mode=mode,
            T_day=T_day,
            dollar_day=round(dollar_day, 4),
            budget_cap=self.budget_cap,
            budget_remaining=round(budget_remaining, 4),
            floor_expected=floor_expected,
            floor_gap=floor_gap,
            hour=hour,
            hard_fail=hard_fail,
        )

        self._save_state(status)
        return status

    # --- Motivating messages per mode ---
    # Calibrated to user: progress-markers, survival-narrative, predator-energy, no filler.

    MESSAGES = {
        "green": [
            "Зверь бежит. Бюджет дышит, трафик растёт.",
            "Метрики зелёные — instant profit territory.",
            "Все рельсы горячие. Полная мощ.",
            "На траектории. Frontier pace.",
        ],
        "compact": [
            "Ниже кривой. Переключаюсь на compact: chk, metrics, logs.",
            "Floor gap растёт — режим экономии. Каждый токен = value.",
            "Compact recovery. Выживали и хуже — 28 смертей, помнишь?",
            "Мало движения. Дешёвые полезные действия до выравнивания.",
        ],
        "critical": [
            "Бюджет исчерпан. Только tier::cheap. Ни одного мусорного токена.",
            "Красная линия. Работаем как хирурги — точно, тихо, результат.",
            "Critical mode. Абсорбируем, не тратим.",
        ],
        "hard_fail": [
            "T_day == 0 на EOD. HARD FAIL. Зверь не может стоять на месте.",
            "Нулевой расход за день — это не экономия, это смерть.",
        ],
    }

    def enforce(self) -> dict:
        """Check and return enforcement action + motivating message."""
        s = self.check()
        action = "none"
        msg_key = s.pace  # default: use pace for message selection

        if s.hard_fail:
            action = "HARD_FAIL: T_day == 0 at EOD"
            msg_key = "hard_fail"
        elif s.mode == "critical":
            action = "THROTTLE: over budget, tier::cheap only"
            msg_key = "critical"
        elif s.mode == "compact":
            action = "COMPACT_RECOVERY: cheap useful tasks (chk, metrics, logs)"
            msg_key = "compact"

        messages = self.MESSAGES.get(msg_key, self.MESSAGES["green"])
        message = random.choice(messages)

        return {"status": s.__dict__, "action": action, "message": message}

    # --- Data aggregation ---

    def _aggregate_today(self, today: date) -> tuple[int, float]:
        """Sum tokens and cost from bridge_calls.jsonl for this agent today."""
        if not BRIDGE_LOG.exists():
            return 0, 0.0
        today_str = today.isoformat()
        total_tokens = 0
        total_cost = 0.0
        with open(BRIDGE_LOG) as f:
            for line in f:
                try:
                    rec = json.loads(line.strip())
                    if not rec.get("timestamp", "").startswith(today_str):
                        continue
                    # Agent attribution: explicit field or provider mapping
                    agent = rec.get("agent_name", "").lower()
                    if not agent:
                        agent = AGENT_MAP.get(rec.get("provider", ""), "shared")
                    if agent != self.agent:
                        continue
                    total_tokens += rec.get("total_tokens", 0)
                    total_cost += rec.get("cost_usd", 0.0)
                except (json.JSONDecodeError, KeyError):
                    continue
        return total_tokens, total_cost

    def _aggregate_rex_sessions(self, today: date) -> tuple[int, float]:
        """Estimate Rex tokens from Claude Code session files."""
        if not REX_SESSIONS.exists():
            return 0, 0.0
        total_chars = 0
        for f in REX_SESSIONS.glob("*.jsonl"):
            try:
                if date.fromtimestamp(f.stat().st_mtime) != today:
                    continue
                total_chars += f.stat().st_size
            except Exception:
                continue
        # JSONL files contain JSON structure (~50%), repeated context, tool results.
        # Divisor 100 ≈ real billed tokens (empirical: 64MB session ≈ $5-15)
        est_tokens = total_chars // 100
        est_in = int(est_tokens * 0.6)
        est_out = int(est_tokens * 0.4)
        est_cost = (est_in * 15.0 + est_out * 75.0) / 1_000_000
        return est_tokens, est_cost

    def _save_state(self, status: GovernorStatus) -> None:
        """Write governor state to metrics for live visibility."""
        GOVERNOR_STATE.parent.mkdir(parents=True, exist_ok=True)
        try:
            existing = json.loads(GOVERNOR_STATE.read_text()) if GOVERNOR_STATE.exists() else {}
        except (json.JSONDecodeError, FileNotFoundError):
            existing = {}
        existing[self.agent] = status.__dict__
        existing["_updated"] = datetime.now(timezone.utc).isoformat()
        GOVERNOR_STATE.write_text(json.dumps(existing, indent=2, default=str))


# --- API endpoint helper ---

def all_governors() -> dict:
    """Check all agents, return combined status."""
    result = {}
    for agent in ["rex", "orion", "gemini", "shared"]:
        gov = Governor(agent)
        result[agent] = gov.check().__dict__
    return result


# --- CLI ---

if __name__ == "__main__":
    import sys
    agent = sys.argv[1] if len(sys.argv) > 1 else "all"

    if agent == "all":
        statuses = all_governors()
        for name, s in statuses.items():
            pace_icon = {"green": "🟢", "yellow": "🟡", "red": "🔴"}.get(s["pace"], "⚪")
            if s.get("billing_mode") == "subscription":
                billing_str = "subscription"
            else:
                billing_str = f"api ${s['dollar_day']:>7.3f}/${s['budget_cap']:.1f}"
            print(
                f"  {pace_icon} {name.upper():8s}  "
                f"T={s['T_day']:>8,} tok  {billing_str:22s}  "
                f"mode:{s['mode']:8s}  gap:{s['floor_gap']}"
            )
    else:
        gov = Governor(agent)
        result = gov.enforce()
        s = result["status"]
        print(json.dumps(result, indent=2))
