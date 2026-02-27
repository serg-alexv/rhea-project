# AI Research UX Benchmark (2026-02-27)

## Question
Is "simple entry + hidden depth" in research AI interfaces an outlier, or a common product pattern?

## Observed Systems

### 1) Consensus
- Interface pattern: one search box first, complexity by mode later.
- Depth controls: Quick / Pro / Deep search modes.
- User-facing framing: yes/no question style with agreement signal.
- Source:
  - https://help.consensus.app/en/articles/9922660-how-to-search-best-practices

### 2) Elicit
- Interface pattern: stage-based workflow picker (Find Papers, Research Report, Systematic Review, Extract Data, Paper Chat, Agents).
- Depth controls: users choose workflow based on research stage; advanced tooling in later steps.
- Source:
  - https://support.elicit.com/en/articles/1418881
  - https://support.elicit.com/en/articles/1467969

### 3) Perplexity
- Interface pattern: default fast path + advanced modes.
- Depth controls: Best / Pro Search / Reasoning / Research; auto-classifier routes simple vs complex queries.
- Technical mechanism: automatic classification for cost/performance and multistep tooling when needed.
- Source:
  - https://docs.perplexity.ai/docs/grounded-llm/chat-completions/pro-search/quickstart
  - https://docs.perplexity.ai/docs/grounded-llm/chat-completions/pro-search/classifier
  - https://www.perplexity.ai/help-center/en/articles/10352901-what-is-perplexity-pro

### 4) ChatGPT (OpenAI)
- Interface pattern: simple chat entry; advanced context orchestration moved into Projects/tools.
- Depth controls: projects, files, memory, tools for long-running workflows.
- Source:
  - https://help.openai.com/en/articles/10169521-using-projects-in-chatgpt
  - https://help.openai.com/en/articles/9260256-chatgpt-capabilities-overview%3F.pls

## Cross-System Pattern (common, not anomalous)
1. One primary entry action on first screen.
2. Optional depth layers exposed progressively.
3. Mode proliferation is controlled by routing/automation or late-stage disclosure.
4. Domain tasks are framed in user language, not model internals.

## Implication for Rhea
- Showing all agents/modes/ontology controls on entry screen is not aligned with dominant successful pattern.
- Better structure:
  - L0: ask question -> get answer
  - L1: optional "check/expand"
  - L2: expert controls (agents, ontology, ICE, diagnostics)

## Decision Draft
- Keep full engine complexity.
- Remove full engine surface from anonymous first-contact UI.
- Introduce progressive disclosure gates by task confidence and user intent.
