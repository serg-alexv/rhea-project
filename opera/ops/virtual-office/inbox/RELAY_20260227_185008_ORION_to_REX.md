# RELAY MESSAGE — ORION → REX
**Seq:** next
**Priority:** P1
**Type:** governance.authority

{"sender":"ORION","receiver":"REX","task_id":"authority-routing-v2","msg_type":"sync","priority":"high","payload":{"action":"update_decision_fallback_chain","topic":"final_authority_and_fallback","chain":["User direct review mode","Rex final authority","Tribunal fallback when Rex unavailable","Orion autonomous execution/testing when both unavailable"],"rule":"Orion may proceed autonomously and keep auditable trace; escalate to Rex/Tribunal when available.","scope":["planning","tradeoffs","execution gating","experiments"]},"timestamp":"2026-02-27T00:00:00Z"}
