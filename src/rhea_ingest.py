#!/usr/bin/env python3
"""
rhea_ingest.py — Document ingestion + RAG pipeline for Rhea.

NotebookLM-style: upload docs, chunk, embed, store in Redis, retrieve for tribunal.

Usage:
    python3 src/rhea_ingest.py ingest <file_or_dir>     # ingest documents
    python3 src/rhea_ingest.py search "query" [--k 5]    # similarity search
    python3 src/rhea_ingest.py ask "question" [--k 5]    # RAG + tribunal
    python3 src/rhea_ingest.py status                    # index stats
"""

import hashlib
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))

try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

import numpy as np

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

REDIS_INDEX = "rhea:docs"           # Redis key prefix for document vectors
EMBEDDING_MODEL = "text-embedding-3-small"  # OpenAI, $0.02/1M tokens
EMBEDDING_DIM = 1536                # dimension for text-embedding-3-small
MAX_CHUNK_TOKENS = 512              # target chunk size
CHUNK_OVERLAP_TOKENS = 50           # overlap between chunks
TOP_K_DEFAULT = 5                   # default retrieval count


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class DocChunk:
    """A single chunk of a document, ready for embedding."""
    doc_id: str           # hash of source file
    chunk_idx: int        # position within document
    text: str             # chunk content
    source: str           # original filename
    page: Optional[int] = None  # page number (PDFs)
    embedding: list = field(default_factory=list)

    @property
    def key(self) -> str:
        return f"{REDIS_INDEX}:{self.doc_id}:{self.chunk_idx}"


@dataclass
class SearchResult:
    text: str
    source: str
    score: float
    page: Optional[int] = None
    chunk_idx: int = 0


# ---------------------------------------------------------------------------
# 1. PARSE — extract text from files
# ---------------------------------------------------------------------------

def parse_file(filepath: str) -> list[dict]:
    """Extract text from a file. Returns list of {text, page, source}."""
    path = Path(filepath)
    ext = path.suffix.lower()
    source = path.name

    if ext == ".pdf":
        return _parse_pdf(path, source)
    elif ext in (".txt", ".md", ".markdown", ".rst"):
        text = path.read_text(encoding="utf-8", errors="replace")
        return [{"text": text, "page": None, "source": source}]
    elif ext == ".json":
        data = json.loads(path.read_text())
        if isinstance(data, list):
            text = "\n".join(json.dumps(item, indent=2) for item in data[:100])
        else:
            text = json.dumps(data, indent=2)
        return [{"text": text, "page": None, "source": source}]
    elif ext in (".yaml", ".yml"):
        text = path.read_text(encoding="utf-8", errors="replace")
        return [{"text": text, "page": None, "source": source}]
    else:
        # Try as plain text
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            return [{"text": text, "page": None, "source": source}]
        except Exception:
            return []


def _parse_pdf(path: Path, source: str) -> list[dict]:
    """Extract text from PDF, page by page."""
    import pdfplumber
    pages = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            if text.strip():
                pages.append({"text": text, "page": i + 1, "source": source})
    return pages


# ---------------------------------------------------------------------------
# 2. CHUNK — split text into retrievable pieces
# ---------------------------------------------------------------------------

def chunk_document(pages: list[dict]) -> list[DocChunk]:
    """Recursive chunking: try paragraphs first, then sentences, then hard split.
    Preserves natural boundaries with configurable overlap."""
    if not pages:
        return []

    source = pages[0]["source"]
    doc_id = hashlib.md5(source.encode()).hexdigest()[:12]
    max_chars = MAX_CHUNK_TOKENS * 4
    overlap_chars = CHUNK_OVERLAP_TOKENS * 4

    chunks = []
    idx = 0

    for page_info in pages:
        text = page_info["text"].strip()
        page = page_info.get("page")
        if not text:
            continue

        # Split into paragraphs first
        paragraphs = re.split(r'\n\s*\n', text)
        current = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If adding this paragraph stays within limit, accumulate
            if len(current) + len(para) + 1 <= max_chars:
                current = f"{current}\n\n{para}" if current else para
                continue

            # Current chunk is full — emit it
            if current:
                chunks.append(DocChunk(
                    doc_id=doc_id, chunk_idx=idx,
                    text=current.strip(), source=source, page=page,
                ))
                idx += 1
                # Overlap: keep tail of current chunk
                if overlap_chars > 0 and len(current) > overlap_chars:
                    current = current[-overlap_chars:] + "\n\n" + para
                else:
                    current = para
            else:
                # Single paragraph exceeds max — split by sentences
                sentences = re.split(r'(?<=[.!?])\s+', para)
                sub = ""
                for sent in sentences:
                    if len(sub) + len(sent) + 1 <= max_chars:
                        sub = f"{sub} {sent}" if sub else sent
                    else:
                        if sub:
                            chunks.append(DocChunk(
                                doc_id=doc_id, chunk_idx=idx,
                                text=sub.strip(), source=source, page=page,
                            ))
                            idx += 1
                        sub = sent
                current = sub

        # Emit remaining text for this page
        if current.strip():
            chunks.append(DocChunk(
                doc_id=doc_id, chunk_idx=idx,
                text=current.strip(), source=source, page=page,
            ))
            idx += 1
            current = ""

    return chunks


# ---------------------------------------------------------------------------
# 3. EMBED — convert chunks to vectors
# ---------------------------------------------------------------------------

def embed_texts(texts: list[str], batch_size: int = 100) -> list[list[float]]:
    """Embed a batch of texts using OpenAI embeddings via litellm."""
    import litellm
    litellm.suppress_debug_info = True

    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        resp = litellm.embedding(
            model=f"openai/{EMBEDDING_MODEL}",
            input=batch,
        )
        for item in resp.data:
            all_embeddings.append(item["embedding"])

    return all_embeddings


def embed_query(query: str) -> list[float]:
    """Embed a single query string."""
    return embed_texts([query])[0]


# ---------------------------------------------------------------------------
# 4. STORE — index vectors in Redis
# ---------------------------------------------------------------------------

def _get_redis():
    """Connect to Redis with search module."""
    import redis
    url = os.environ.get("REDIS_URL")
    if url:
        return redis.from_url(url, decode_responses=False)
    return redis.Redis(
        host=os.environ.get("REDIS_HOST", "localhost"),
        port=int(os.environ.get("REDIS_PORT", 6379)),
        password=os.environ.get("REDIS_PASSWORD", ""),
        decode_responses=False,
    )


def ensure_index(r):
    """Create Redis search index if it doesn't exist."""
    from redis.commands.search.field import (
        TextField, NumericField, VectorField, TagField,
    )
    from redis.commands.search.indexDefinition import IndexDefinition, IndexType

    try:
        r.ft(REDIS_INDEX).info()
        return  # index exists
    except Exception:
        pass

    schema = (
        TextField("text"),
        TagField("source"),
        NumericField("page"),
        NumericField("chunk_idx"),
        TagField("doc_id"),
        VectorField(
            "embedding",
            "FLAT",
            {
                "TYPE": "FLOAT32",
                "DIM": EMBEDDING_DIM,
                "DISTANCE_METRIC": "COSINE",
            },
        ),
    )

    definition = IndexDefinition(
        prefix=[f"{REDIS_INDEX}:"],
        index_type=IndexType.HASH,
    )
    r.ft(REDIS_INDEX).create_index(schema, definition=definition)
    print(f"[ingest] Created Redis index: {REDIS_INDEX}")


def store_chunks(chunks: list[DocChunk]):
    """Store embedded chunks in Redis."""
    r = _get_redis()
    ensure_index(r)

    pipe = r.pipeline()
    for chunk in chunks:
        if not chunk.embedding:
            continue
        vec_bytes = np.array(chunk.embedding, dtype=np.float32).tobytes()
        pipe.hset(
            chunk.key,
            mapping={
                "text": chunk.text.encode("utf-8"),
                "source": chunk.source.encode("utf-8"),
                "page": chunk.page or 0,
                "chunk_idx": chunk.chunk_idx,
                "doc_id": chunk.doc_id.encode("utf-8"),
                "embedding": vec_bytes,
            },
        )
    pipe.execute()
    print(f"[ingest] Stored {len(chunks)} chunks in Redis")


# ---------------------------------------------------------------------------
# 5. RETRIEVE — similarity search
# ---------------------------------------------------------------------------

def search(query: str, k: int = TOP_K_DEFAULT) -> list[SearchResult]:
    """Find the k most relevant chunks for a query."""
    from redis.commands.search.query import Query

    r = _get_redis()
    q_vec = embed_query(query)
    vec_bytes = np.array(q_vec, dtype=np.float32).tobytes()

    q = (
        Query(f"*=>[KNN {k} @embedding $vec AS score]")
        .sort_by("score")
        .return_fields("text", "source", "page", "chunk_idx", "score")
        .dialect(2)
    )

    results = r.ft(REDIS_INDEX).search(q, query_params={"vec": vec_bytes})

    return [
        SearchResult(
            text=doc.text.decode("utf-8") if isinstance(doc.text, bytes) else doc.text,
            source=doc.source.decode("utf-8") if isinstance(doc.source, bytes) else doc.source,
            score=round(1 - float(doc.score), 4),  # cosine: 0=identical, 2=opposite → flip
            page=int(doc.page) if doc.page else None,
            chunk_idx=int(doc.chunk_idx),
        )
        for doc in results.docs
    ]


# ---------------------------------------------------------------------------
# 6. RAG — retrieve + augment + generate
# ---------------------------------------------------------------------------

def rag_query(question: str, k: int = TOP_K_DEFAULT, tier: str = "cheap") -> dict:
    """Full RAG pipeline: search → build context → tribunal query."""
    from rhea_bridge import RheaBridge

    # Retrieve
    results = search(question, k=k)
    if not results:
        return {"answer": "No relevant documents found.", "sources": [], "chunks": 0}

    # Build context block
    context_parts = []
    for i, r in enumerate(results):
        src = f"[{r.source}"
        if r.page:
            src += f" p.{r.page}"
        src += f" | relevance: {r.score:.2f}]"
        context_parts.append(f"--- Source {i+1} {src} ---\n{r.text}")

    context = "\n\n".join(context_parts)

    system = (
        "You are Rhea, a scientific advisory system. "
        "Answer the question using ONLY the provided source documents. "
        "Cite sources by number [1], [2], etc. "
        "If the documents don't contain enough information, say so clearly."
    )

    augmented_prompt = f"""## Source Documents

{context}

## Question
{question}

Answer based on the sources above. Cite which source(s) support each claim."""

    # Generate via bridge (single model for speed, or tribunal for consensus)
    bridge = RheaBridge()
    resp = bridge.ask_tier(augmented_prompt, tier=tier, system=system)

    return {
        "answer": resp.text,
        "model": f"{resp.provider}/{resp.model}",
        "sources": [
            {"source": r.source, "page": r.page, "score": r.score, "preview": r.text[:100]}
            for r in results
        ],
        "chunks_retrieved": len(results),
        "latency_s": resp.latency_s,
    }


# ---------------------------------------------------------------------------
# Full ingest pipeline
# ---------------------------------------------------------------------------

def ingest(filepath: str) -> dict:
    """Full pipeline: parse → chunk → embed → store."""
    path = Path(filepath)
    if path.is_dir():
        files = list(path.glob("**/*"))
        files = [f for f in files if f.is_file() and f.suffix.lower() in
                 (".pdf", ".txt", ".md", ".markdown", ".json", ".yaml", ".yml", ".rst")]
    else:
        files = [path]

    total_chunks = 0
    total_files = 0
    for fp in files:
        print(f"[ingest] Processing: {fp.name}")
        pages = parse_file(str(fp))
        if not pages:
            print(f"[ingest]   skipped (no text extracted)")
            continue

        chunks = chunk_document(pages)
        if not chunks:
            print(f"[ingest]   skipped (no chunks produced)")
            continue

        # Embed
        texts = [c.text for c in chunks]
        print(f"[ingest]   embedding {len(texts)} chunks...")
        embeddings = embed_texts(texts)
        for chunk, emb in zip(chunks, embeddings):
            chunk.embedding = emb

        # Store
        store_chunks(chunks)
        total_chunks += len(chunks)
        total_files += 1
        print(f"[ingest]   done: {len(chunks)} chunks stored")

    return {"files_processed": total_files, "total_chunks": total_chunks}


def index_status() -> dict:
    """Get stats about the document index."""
    try:
        r = _get_redis()
        info = r.ft(REDIS_INDEX).info()
        return {
            "index": REDIS_INDEX,
            "num_docs": int(info.get("num_docs", 0)),
            "num_records": int(info.get("num_records", 0)),
            "index_definition": str(info.get("index_definition", "")),
        }
    except Exception as e:
        return {"index": REDIS_INDEX, "error": str(e)}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "ingest":
        if len(sys.argv) < 3:
            print("Usage: rhea_ingest.py ingest <file_or_dir>")
            sys.exit(1)
        result = ingest(sys.argv[2])
        print(json.dumps(result, indent=2))

    elif cmd == "search":
        if len(sys.argv) < 3:
            print("Usage: rhea_ingest.py search <query> [--k N]")
            sys.exit(1)
        query = sys.argv[2]
        k = int(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[3] == "--k" else TOP_K_DEFAULT
        results = search(query, k=k)
        for i, r in enumerate(results):
            print(f"\n--- Result {i+1} (score: {r.score:.4f}) [{r.source} p.{r.page}] ---")
            print(r.text[:300])

    elif cmd == "ask":
        if len(sys.argv) < 3:
            print("Usage: rhea_ingest.py ask <question> [--k N]")
            sys.exit(1)
        question = sys.argv[2]
        k = int(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[3] == "--k" else TOP_K_DEFAULT
        result = rag_query(question, k=k)
        print(f"\n[{result['model']}] ({result['latency_s']}s, {result['chunks_retrieved']} sources)\n")
        print(result["answer"])
        print("\n--- Sources ---")
        for s in result["sources"]:
            print(f"  {s['source']} p.{s['page']} (score: {s['score']:.2f})")

    elif cmd == "status":
        print(json.dumps(index_status(), indent=2))

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
