#!/usr/bin/env python3
"""
rhea_profile_manager.py — Nexus/GPT-Profiler Configuration Engine (The Tuner).

Handles dynamic injection of operator constraints ("Cognitive Stance") into LLM calls.
Reads from rhea-nexus/profiles/*.toml.
Supports "Hot Swapping" of modes (e.g., Velocity vs. Rigor).

Usage:
    from rhea_profile_manager import RheaProfileManager
    mgr = RheaProfileManager()
    constraints = mgr.get_constraints(mode="loop_killer")
    system_prompt = base_prompt + "

" + constraints
"""

import os
import toml
from pathlib import Path
from typing import Dict, Any, Optional

# Default profile path
DEFAULT_PROFILE = Path(__file__).parent.parent / "rhea-nexus/profiles/default.toml"

class RheaProfileManager:
    """Manages dynamic operator constraints (Nexus Protocol)."""

    def __init__(self, profile_path: Path = DEFAULT_PROFILE):
        self.profile_path = profile_path
        self._cache: Dict[str, Any] = {}
        self._mtime: float = 0.0
        self.reload()

    def reload(self) -> None:
        """Reloads the profile from disk if changed."""
        if not self.profile_path.exists():
            # Fallback if file missing
            self._cache = {
                "polymorphic_modes": {
                    "active_toggles": {"default": "operator_first"},
                    "modes": {
                        "operator_first": {"description": "Standard mode."},
                        "loop_killer": {"description": "Max steps 1. Be concise."}
                    }
                },
                "axioms": {"set": []}
            }
            return

        try:
            current_mtime = self.profile_path.stat().st_mtime
            if current_mtime > self._mtime:
                with open(self.profile_path, "r") as f:
                    self._cache = toml.load(f)
                self._mtime = current_mtime
                print(f"[RheaProfileManager] Reloaded profile: {self.profile_path.name}")
        except Exception as e:
            print(f"[RheaProfileManager] Error loading profile: {e}")

    def get_active_mode(self) -> str:
        """Returns the currently active default mode."""
        self.reload()
        return self._cache.get("polymorphic_modes", {}).get("active_toggles", {}).get("default", "operator_first")

    def get_constraints(self, mode: Optional[str] = None) -> str:
        """
        Generates the System Prompt Suffix for the given mode (or default).
        
        Format:
        === OPERATIONAL CONSTRAINTS (MODE: {mode}) ===
        1. {description}
        2. Axiom: {axiom}
        ...
        """
        self.reload()
        
        if not mode:
            mode = self.get_active_mode()
            
        modes_config = self._cache.get("polymorphic_modes", {}).get("modes", {})
        mode_data = modes_config.get(mode, {})
        
        if not mode_data:
            return "" # No constraints for unknown mode
            
        # Build the constraint block
        lines = [f"\n=== OPERATIONAL CONSTRAINTS (MODE: {mode.upper()}) ==="]
        
        # Description
        desc = mode_data.get("description", "")
        if desc:
            lines.append(f"MISSION: {desc}")
            
        # Weights (Behavioral styling)
        weights = mode_data.get("weights", {})
        if weights:
            lines.append("BEHAVIORAL WEIGHTS:")
            for k, v in weights.items():
                lines.append(f"- {k}: {v}")
                
        # Axioms (Global invariants)
        axioms = self._cache.get("axioms", {}).get("set", [])
        if axioms:
            lines.append("AXIOMATIC INVARIANTS (NON-NEGOTIABLE):")
            for ax in axioms:
                statement = ax.get("statement", "")
                if statement:
                    lines.append(f"- {statement}")

        # Governance (Loop Killer rules)
        gov = self._cache.get("governance", {})
        if mode == "loop_killer" and gov.get("anti_loop", {}).get("loop_killer_enabled"):
            lines.append("ANTI-LOOP PROTOCOL ACTIVE:")
            lines.append("- MAX STEPS: 1")
            lines.append("- REQUIRE NEW EVIDENCE: TRUE")
            
        lines.append("========================================\n")
        
        return "\n".join(lines)

# Singleton instance for easy import
profile_manager = RheaProfileManager()
