# Session Context

**Session ID:** 261278d3-25c3-4789-93e7-bfcc23c40cd5

**Commit Message:** "Document ingestion pipeline — NotebookLM's core: upload PDFs/docs, chun

## Prompt

"Document ingestion pipeline — NotebookLM's core: upload PDFs/docs, chunk, embed, retrieve" -- show me

## Summary

All 5 pipeline components verified: parse, embed, redis, search schema, and RAG query structure. The only missing piece is the **chunking strategy** — and that's yours.

---

**Learn by Doing**

**Context:** I've built the full NotebookLM-style RAG pipeline — parse (PDF/TXT/MD/JSON), embed (OpenAI `text-embedding-3-small`, 1536 dims), store (Redis vectorset with cosine similarity), retrieve (KNN search), and generate (tribunal-augmented). The entire pipeline flows through `ingest()` → `search()` → `rag_query()`. The one missing piece is how documents get split into chunks — this single function determines whether retrieval finds the right context or misses it entirely.

**Your Task:** In `src/rhea_ingest.py`, implement the `chunk_document(pages)` function. Look for `TODO(human)`. It takes a list of `{"text", "page", "source"}` dicts and returns a list of `DocChunk` objects. Use constants `MAX_CHUNK_TOKENS` (512) and `CHUNK_OVERLAP_TOKENS` (50).

**Guidance:** Consider these tradeoffs:
- **Fixed-size** (every N chars) is simple but splits mid-sentence → poor retrieval
- **Paragraph-based** (split on `\n\n`) respects natural boundaries but gives uneven sizes
- **Recursive** (try paragraphs first, then sentences, then chars) is what LangChain does — best quality but more complex
- The `~4 chars/token` approximation is good enough (or import `tiktoken` for exact counts)
- Overlap matters: too little (0) loses cross-boundary context, too much (>20%) wastes storage
- For scientific PDFs, preserving section headers with their content helps retrieval significantly

## Key Actions

- - **Task**: Explore RAG/embedding infrastructure
- - **Bash**: Install PDF parsing library
- - **Write**: /Users/sa/rh.1/src/rhea_ingest.py
- - **Bash**: Verify pipeline components work
