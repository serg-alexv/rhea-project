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
    """Manages dynamic operator constraints and Memory Entities (Nexus Protocol)."""

    def __init__(self, profile_path: Path = DEFAULT_PROFILE):
        self.profile_path = profile_path
        self._cache: Dict[str, Any] = {}
        self._mtime: float = 0.0
        self._active_memory_context: str = ""
        self._active_memory_id: str = "NONE"
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

    def list_memory_entities(self) -> list[dict]:
        """Scans for all loadable memory entities (Nexus branches, snapshots)."""
        entities = []
        
        # 1. Nexus Memories
        nexus_dir = Path(__file__).parent.parent / "rhea-nexus/memories"
        if nexus_dir.exists():
            for f in nexus_dir.glob("*.md"):
                entities.append({
                    "id": f.name,
                    "type": "NEXUS_BRANCH",
                    "path": str(f),
                    "size": f.stat().st_size
                })
                
        # 2. Snapshots (Entire.io)
        snap_dir = Path(__file__).parent.parent / ".entire/snapshots"
        if snap_dir.exists():
            # Get latest 10 snapshots
            snaps = sorted(snap_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:10]
            for s in snaps:
                entities.append({
                    "id": s.name,
                    "type": "SNAPSHOT",
                    "path": str(s),
                    "size": s.stat().st_size
                })
                
        return entities

    def hydrate_memory(self, entity_id: str) -> bool:
        """Loads a memory entity and arms the context engine."""
        if entity_id == "NONE":
            self._active_memory_context = ""
            self._active_memory_id = "NONE"
            return True

        entities = self.list_memory_entities()
        target = next((e for e in entities if e["id"] == entity_id), None)
        
        if not target:
            return False
            
        try:
            with open(target["path"], "r") as f:
                content = f.read()
            
            # Simple truncation for safety if file is huge
            self._active_memory_context = content[:15000] 
            self._active_memory_id = entity_id
            print(f"[RheaProfileManager] ARMED with memory: {entity_id}")
            return True
        except Exception as e:
            print(f"[RheaProfileManager] Hydration failed: {e}")
            return False

    def get_active_mode(self) -> str:
        """Returns the currently active default mode."""
        self.reload()
        return self._cache.get("polymorphic_modes", {}).get("active_toggles", {}).get("default", "operator_first")

    def get_available_modes(self) -> list[str]:
        """Returns a list of available mode keys."""
        self.reload()
        modes = self._cache.get("polymorphic_modes", {}).get("modes", {})
        return list(modes.keys())

    def set_active_mode(self, mode: str) -> bool:
        """Sets the active default mode and persists to disk while preserving comments."""
        self.reload()
        modes = self.get_available_modes()
        if mode not in modes:
            return False
        
        # We use Regex to update the file to preserve Mika's beautiful comments
        import re
        try:
            with open(self.profile_path, "r") as f:
                content = f.read()
            
            # Pattern to find 'default = "any_mode"' under '[polymorphic_modes.active_toggles]'
            pattern = r'(default\s*=\s*")[^"]+(")'
            new_content = re.sub(pattern, rf'\1{mode}\2', content)
            
            with open(self.profile_path, "w") as f:
                f.write(new_content)
            
            # Update cache and mtime
            self._cache["polymorphic_modes"]["active_toggles"]["default"] = mode
            self._mtime = self.profile_path.stat().st_mtime
            return True
        except Exception as e:
            print(f"[RheaProfileManager] Error saving profile safely: {e}")
            return False

    def get_constraints(self, mode: Optional[str] = None) -> str:
        """
        Generates the System Prompt Suffix for the given mode (or default).
        Includes ARMED memory context if available.
        """
        self.reload()
        
        if not mode:
            mode = self.get_active_mode()
            
        lines = []

        # --- Memory Hydration Block ---
        if self._active_memory_context:
            lines.append("\n=== ACTIVE MEMORY ENTITY (ARMED) ===")
            lines.append(f"ID: {self._active_memory_id}")
            lines.append(self._active_memory_context)
            lines.append("=== END ARMED MEMORY ===\n")
        # ------------------------------

        modes_config = self._cache.get("polymorphic_modes", {}).get("modes", {})
        mode_data = modes_config.get(mode, {})
        
        if not mode_data:
            return "\n".join(lines) if lines else ""
            
        # Build the constraint block
        lines.append(f"=== OPERATIONAL CONSTRAINTS (MODE: {mode.upper()}) ===")
        
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
