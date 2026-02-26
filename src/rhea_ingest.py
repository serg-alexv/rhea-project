#!/usr/bin/env python3
"""
rhea_ingest.py — Document ingestion + RAG pipeline for Rhea.
NotebookLM-style: upload docs, chunk, embed, store in Redis, retrieve for tribunal.

Usage:
    python3 src/rhea_ingest.py ingest <file_or_dir>
    python3 src/rhea_ingest.py search "query" [--k 5]
    python3 src/rhea_ingest.py ask "question" [--k 5]
    python3 src/rhea_ingest.py status
"""

import hashlib, json, os, re, sys, time
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

# Config
REDIS_INDEX = "rhea:docs"
EMBEDDING_MODEL = "google/text-embedding-004"
EMBEDDING_DIM = 768
MAX_CHUNK_TOKENS = 512
CHUNK_OVERLAP_TOKENS = 50
TOP_K_DEFAULT = 5


@dataclass
class DocChunk:
    doc_id: str
    chunk_idx: int
    text: str
    source: str
    page: Optional[int] = None
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


# --- 1. PARSE ---

def parse_file(filepath: str) -> list[dict]:
    path = Path(filepath)
    ext = path.suffix.lower()
    source = path.name

    if ext == ".pdf":
        import pdfplumber
        pages = []
        with pdfplumber.open(path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                if text.strip():
                    pages.append({"text": text, "page": i + 1, "source": source})
        return pages
    else:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            return [{"text": text, "page": None, "source": source}]
        except Exception:
            return []


# --- 2. CHUNK ---

def chunk_document(pages: list[dict]) -> list[DocChunk]:
    """Recursive chunking: paragraphs -> sentences -> hard split, with overlap."""
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

        paragraphs = re.split(r'\n\s*\n', text)
        current = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current) + len(para) + 1 <= max_chars:
                current = f"{current}\n\n{para}" if current else para
                continue

            if current:
                chunks.append(DocChunk(doc_id=doc_id, chunk_idx=idx,
                    text=current.strip(), source=source, page=page))
                idx += 1
                if overlap_chars > 0 and len(current) > overlap_chars:
                    current = current[-overlap_chars:] + "\n\n" + para
                else:
                    current = para
            else:
                sentences = re.split(r'(?<=[.!?])\s+', para)
                sub = ""
                for sent in sentences:
                    if len(sub) + len(sent) + 1 <= max_chars:
                        sub = f"{sub} {sent}" if sub else sent
                    else:
                        if sub:
                            chunks.append(DocChunk(doc_id=doc_id, chunk_idx=idx,
                                text=sub.strip(), source=source, page=page))
                            idx += 1
                        sub = sent
                current = sub

        if current.strip():
            chunks.append(DocChunk(doc_id=doc_id, chunk_idx=idx,
                text=current.strip(), source=source, page=page))
            idx += 1
            current = ""

    return chunks


# --- 3. EMBED ---

def embed_texts(texts: list[str], batch_size: int = 100) -> list[list[float]]:
    import litellm
    litellm.suppress_debug_info = True
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        resp = litellm.embedding(model=f"openai/{EMBEDDING_MODEL}", input=batch)
        for item in resp.data:
            all_embeddings.append(item["embedding"])
    return all_embeddings


def embed_query(query: str) -> list[float]:
    return embed_texts([query])[0]


# --- 4. STORE ---

def _get_redis():
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
    from redis.commands.search.field import TextField, NumericField, VectorField, TagField
    from redis.commands.search.index_definition import IndexDefinition, IndexType

    try:
        r.ft(REDIS_INDEX).info()
        return
    except Exception:
        pass

    schema = (
        TextField("text"),
        TagField("source"),
        NumericField("page"),
        NumericField("chunk_idx"),
        TagField("doc_id"),
        VectorField("embedding", "FLAT", {
            "TYPE": "FLOAT32", "DIM": EMBEDDING_DIM, "DISTANCE_METRIC": "COSINE",
        }),
    )

    definition = IndexDefinition(prefix=[f"{REDIS_INDEX}:"], index_type=IndexType.HASH)
    r.ft(REDIS_INDEX).create_index(schema, definition=definition)
    print(f"[ingest] Created Redis index: {REDIS_INDEX}")


def store_chunks(chunks: list[DocChunk]):
    r = _get_redis()
    ensure_index(r)
    pipe = r.pipeline()
    for chunk in chunks:
        if not chunk.embedding:
            continue
        vec_bytes = np.array(chunk.embedding, dtype=np.float32).tobytes()
        pipe.hset(chunk.key, mapping={
            "text": chunk.text.encode("utf-8"),
            "source": chunk.source.encode("utf-8"),
            "page": chunk.page or 0,
            "chunk_idx": chunk.chunk_idx,
            "doc_id": chunk.doc_id.encode("utf-8"),
            "embedding": vec_bytes,
        })
    pipe.execute()
    print(f"[ingest] Stored {len(chunks)} chunks in Redis")


# --- 5. RETRIEVE ---

def search(query: str, k: int = TOP_K_DEFAULT) -> list[SearchResult]:
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
            score=round(1 - float(doc.score), 4),
            page=int(doc.page) if doc.page else None,
            chunk_idx=int(doc.chunk_idx),
        )
        for doc in results.docs
    ]


# --- 6. RAG ---

def rag_query(question: str, k: int = TOP_K_DEFAULT, tier: str = "cheap") -> dict:
    from rhea_bridge import RheaBridge

    results = search(question, k=k)
    if not results:
        return {"answer": "No relevant documents found.", "sources": [], "chunks": 0}

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
        "Answer using ONLY the provided source documents. "
        "Cite sources by number [1], [2], etc. "
        "If the documents don't contain enough information, say so."
    )

    augmented = f"## Source Documents\n\n{context}\n\n## Question\n{question}\n\nAnswer based on the sources above."

    bridge = RheaBridge()
    resp = bridge.ask_tier(augmented, tier=tier, system=system)

    return {
        "answer": resp.text,
        "model": f"{resp.provider}/{resp.model}",
        "sources": [{"source": r.source, "page": r.page, "score": r.score, "preview": r.text[:100]} for r in results],
        "chunks_retrieved": len(results),
        "latency_s": resp.latency_s,
    }


# --- PIPELINE ---

def ingest(filepath: str) -> dict:
    path = Path(filepath)
    if path.is_dir():
        files = [f for f in path.glob("**/*") if f.is_file() and
                 f.suffix.lower() in (".pdf", ".txt", ".md", ".json", ".yaml", ".yml")]
    else:
        files = [path]

    total_chunks, total_files = 0, 0
    for fp in files:
        print(f"[ingest] Processing: {fp.name}")
        pages = parse_file(str(fp))
        if not pages:
            print(f"[ingest]   skipped (no text)")
            continue
        chunks = chunk_document(pages)
        if not chunks:
            print(f"[ingest]   skipped (no chunks)")
            continue
        texts = [c.text for c in chunks]
        print(f"[ingest]   embedding {len(texts)} chunks...")
        embeddings = embed_texts(texts)
        for chunk, emb in zip(chunks, embeddings):
            chunk.embedding = emb
        store_chunks(chunks)
        total_chunks += len(chunks)
        total_files += 1

    return {"files_processed": total_files, "total_chunks": total_chunks}


def index_status() -> dict:
    try:
        r = _get_redis()
        info = r.ft(REDIS_INDEX).info()
        return {"index": REDIS_INDEX, "num_docs": int(info.get("num_docs", 0)),
                "num_records": int(info.get("num_records", 0))}
    except Exception as e:
        return {"index": REDIS_INDEX, "error": str(e)}


# --- CLI ---

if __name__ == "__main__":
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
        query = sys.argv[2]
        k = int(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[3] == "--k" else TOP_K_DEFAULT
        results = search(query, k=k)
        for i, r in enumerate(results):
            print(f"\n--- Result {i+1} (score: {r.score:.4f}) [{r.source} p.{r.page}] ---")
            print(r.text[:300])

    elif cmd == "ask":
        question = sys.argv[2]
        k = int(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[3] == "--k" else TOP_K_DEFAULT
        result = rag_query(question, k=k)
        print(f"\n[{result['model']}] ({result['latency_s']}s, {result['chunks_retrieved']} sources)\n")
        print(result["answer"])

    elif cmd == "status":
        print(json.dumps(index_status(), indent=2))

    else:
        print(f"Unknown command: {cmd}")
