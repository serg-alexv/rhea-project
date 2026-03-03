# WOW Landing Variant

- animated hero with radial gradients, orbiting frame, and language tone adjustments.
- repository cards with hidden explainers describing each surface (Atlas, RheaKit, CLI, memory) to expose Git context.
- Gemini/explain cards and motion sections for surfaces, plus hiddable explanation timeline and stats.
- language switcher toggles hero tone and text accent to match selected locale.
- keeps all content inside `rhea-atlas` so we can restore by re-deploying the branch.

Deploy instructions:
1. `cd rhea-atlas && npm run build`
2. Trigger Fly.io deploy (Rex owns) to serve at https://rhea-tribunal.fly.dev/
