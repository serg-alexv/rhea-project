# Sandboxed Execution for Agents (Advanced)

SYSTEM:
Assume the model will eventually attempt something unsafe by accident. Contain blast radius.

USER:
Propose a sandbox strategy for any code/tool execution:
- read-only by default
- allow-list commands with exact args
- run in container / restricted user / no network unless required
- filesystem jail to repo workspace only
- secrets never exposed to the model directly
Output: layers of defense + failure modes + how to test containment.
