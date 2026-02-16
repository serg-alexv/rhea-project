# Rhea Custom ComfyUI Nodes

Place custom nodes here for Rhea-specific workflows:
- Circadian rhythm visualizations
- iOS app UI mockup generation via Flux
- Mathematics of Rhea paper diagrams
- Agent-driven ComfyUI workflow generation (ComfyGPT pattern)

## LiteLLM Bridge
Install ComfyUI-API-Manager or ComfyUI-OpenAI-Compat-LLM-Node
and point them at http://localhost:4000/v1 to route all LLM calls
through the Rhea LiteLLM proxy.
