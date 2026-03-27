"""
RAG pipeline: ChromaDB + sentence-transformers + OpenAI
"""

import os
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
COLLECTION_NAME = "jenkins_docs"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")

# ── Embedding model (local, no API key needed) ──────────────────────────────
_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# ── ChromaDB client ──────────────────────────────────────────────────────────
_client = chromadb.PersistentClient(
    path=CHROMA_PATH,
    settings=Settings(anonymized_telemetry=False)
)
_collection = _client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=_ef,
    metadata={"hnsw:space": "cosine"},
)

# ── OpenAI client (optional) ─────────────────────────────────────────────────
_openai = OpenAI(api_key=OPENAI_KEY) if OPENAI_KEY and not OPENAI_KEY.startswith("sk-your") else None


SYSTEM_PROMPT = """You are the Jenkins AI Assistant - a helpful, concise expert on
Jenkins CI/CD. You answer questions based ONLY on the provided context chunks.
Rules:
- If the context contains the answer, give a clear, direct response with a Jenkinsfile
  snippet when applicable.
- If the context does NOT contain enough information, say:
  "I'm not confident about this - please check https://www.jenkins.io/doc"
- Always cite the source URL at the end as: **Source:** <url>
- Keep answers under 150 words unless a code snippet is needed.
- Never invent plugin names or configuration keys.
"""


def retrieve(query: str, page_context: str = "", n_results: int = 5) -> list[dict]:
    """Retrieve top-N relevant chunks from ChromaDB."""
    where = None
    # Boost pipeline-related docs when on a pipeline config page
    if "pipeline" in page_context.lower():
        where = {"category": {"$in": ["pipeline", "general"]}}

    results = _collection.query(
        query_texts=[query],
        n_results=n_results,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    if results and results["documents"]:
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            chunks.append({"content": doc, "metadata": meta, "score": 1 - dist})
    return chunks


def build_prompt(query: str, chunks: list[dict], page_context: str, history: list[dict]) -> list[dict]:
    context_text = "\n\n---\n\n".join(
        f"[Source: {c['metadata'].get('url', 'jenkins.io')}]\n{c['content']}"
        for c in chunks
    )
    page_info = f"\nUser is currently on: {page_context}" if page_context else ""

    messages = [{"role": "system", "content": SYSTEM_PROMPT + page_info}]
    # Last 4 turns of history
    for turn in history[-4:]:
        messages.append(turn)
    messages.append({
        "role": "user",
        "content": f"Context:\n{context_text}\n\nQuestion: {query}",
    })
    return messages


def stream_answer(query: str, page_context: str = "", history: list[dict] = None):
    """
    Generator that yields response tokens.
    Falls back to returning retrieved docs if no OpenAI key is set.
    """
    history = history or []
    chunks = retrieve(query, page_context)

    if not chunks:
        yield "I couldn't find relevant Jenkins documentation for that question. "
        yield "Please check https://www.jenkins.io/doc for more information."
        return

    # No-LLM fallback: act like a smart bot quoting the docs directly
    if not _openai:
        top = chunks[0]
        # Strip the "Q/A" prefix from the seeded text to make it read naturally
        content = top["content"].replace("Q: ", "").replace("\n\nA: ", "\n\n")
        
        yield f"Based on the Jenkins documentation, here is what I found:\n\n---\n\n{content}\n\n---\n\n"
        yield f"**Source:** {top['metadata'].get('url', 'https://www.jenkins.io/doc')}"
        return

    messages = build_prompt(query, chunks, page_context, history)

    try:
        with _openai.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            stream=True,
            max_tokens=400,
            temperature=0.2,
        ) as stream:
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
    except Exception as e:
        yield f"\n\n⚠️ LLM unavailable ({type(e).__name__}). Top result:\n\n"
        yield chunks[0]["content"]
        yield f"\n\n**Source:** {chunks[0]['metadata'].get('url', 'https://www.jenkins.io/doc')}"
