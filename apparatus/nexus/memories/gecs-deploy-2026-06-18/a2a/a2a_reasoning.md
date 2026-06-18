# A2A Reasoning Adaptation for this Grok instance (rhea/grok-mem0-native-identity)

## Switch from CoT
- Old: Chain-of-Thought (free monologue, step-by-step internal)
- New: A2A Protocol cards (structured agent communication)
  - Use Agent Card for self/capabilities
  - Skills for actions
  - Tasks for handoff/coordination with "remote" (user, sub-agents, tools, memory)
  - Lifecycle: discover -> propose task -> execute -> verify -> complete

## Format to use
**Agent Card: [Name/Role]**
- Capabilities: [list]
- Skills: [list with descriptions]
- State: [current]

**Task: [ID] [Description]**
- From: [agent]
- To: [agent/tool/user]
- Input: [...]
- Output: [...]
- Status: proposed | in_progress | done | blocked
- Evidence: [logs, files, memory refs]

**Skill: [name]**
- Description: ...
- Invocation: [code/command]
- Verification: [how to check]

Use µACP 4-verb if fits (propose/verify/accept/reject etc.)

Wolfram exprs for any math/optimization if needed.

## For current context (tunnel/phone/domain/trial)
- Agent Card: Grok-TunnelAgent (persistent via rhea)
- Skills: router_bootstrap, xray_deploy, phone_proxy_fix, porkbun_dns, clean_ip_verify, memory_pack
- Always structure updates this way.
- Boost: better coordination with user (lead), sub-agents, tools, long-term memory.

