# tools/retriever.py — hybrid BM25 + vector retriever with optional rerank
from typing import List

from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.retrievers import BM25Retriever
from loguru import logger

from config import (
    OLLAMA_BASE_URL,
    EMBEDDING_MODEL,
    CHROMA_DIR,
    COLLECTION_NAME,
    TOP_K,
    RETRIEVAL_MODE,
    RERANK_ENABLED,
)


def build_vectorstore(chunks: List[Document]) -> Chroma:
    embeddings = OllamaEmbeddings(
        model=EMBEDDING_MODEL,
        base_url=OLLAMA_BASE_URL,
    )
    vs = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(CHROMA_DIR),
        collection_name=COLLECTION_NAME,
    )
    logger.info(f"VectorStore built with {len(chunks)} chunks → {CHROMA_DIR}")
    return vs


def load_vectorstore() -> Chroma:
    embeddings = OllamaEmbeddings(
        model=EMBEDDING_MODEL,
        base_url=OLLAMA_BASE_URL,
    )
    vs = Chroma(
        persist_directory=str(CHROMA_DIR),
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME,
    )
    return vs


def _hybrid_retrieve(chunks: List[Document], query: str, k: int) -> List[Document]:
    """Manual hybrid: merge BM25 sparse + ChromaDB dense results, deduplicate."""
    # Sparse BM25
    sparse = BM25Retriever.from_documents(chunks)
    sparse.k = k
    bm25_docs = sparse.invoke(query)

    # Dense vector (load from persisted store if available)
    try:
        vs = load_vectorstore()
        dense_docs = vs.similarity_search(query, k=k)
    except Exception:
        dense_docs = []

    # Merge: BM25 weight 40%, dense weight 60% via simple score fusion
    seen: dict[str, Document] = {}
    for rank, doc in enumerate(bm25_docs):
        key = doc.page_content[:100]
        score = 0.4 * (k - rank) / k
        if key not in seen:
            seen[key] = (doc, score)
        else:
            seen[key] = (seen[key][0], seen[key][1] + score)

    for rank, doc in enumerate(dense_docs):
        key = doc.page_content[:100]
        score = 0.6 * (k - rank) / k
        if key not in seen:
            seen[key] = (doc, score)
        else:
            seen[key] = (seen[key][0], seen[key][1] + score)

    merged = sorted(seen.values(), key=lambda x: x[1], reverse=True)
    return [doc for doc, _ in merged[:k]]


def build_retriever(chunks: List[Document] | None = None, vectorstore: Chroma | None = None):
    if vectorstore is None and chunks is not None:
        vectorstore = build_vectorstore(chunks)
    elif vectorstore is None:
        vectorstore = load_vectorstore()

    if RETRIEVAL_MODE == "hybrid" and chunks is not None:
        logger.info("Using hybrid retriever (BM25 + vector, manual fusion)")
        # Return a callable wrapper that matches retriever interface
        class _HybridRetriever:
            def invoke(self, query: str) -> List[Document]:
                return _hybrid_retrieve(chunks, query, TOP_K)
        return _HybridRetriever()
    else:
        logger.info("Using dense vector retriever only")
        return vectorstore.as_retriever(search_kwargs={"k": TOP_K})


def rerank_docs(docs: List[Document], query: str, top_n: int = 3) -> List[Document]:
    """Simple cross-encoder-style rerank by keyword overlap (lightweight, no external model)."""
    if not RERANK_ENABLED:
        return docs[:top_n]
    query_tokens = set(query.lower().split())
    scored = []
    for doc in docs:
        text_tokens = set(doc.page_content.lower().split())
        score = len(query_tokens & text_tokens) / (len(query_tokens) + 1e-6)
        scored.append((score, doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    reranked = [d for _, d in scored[:top_n]]
    logger.debug(f"Reranked {len(docs)} → {len(reranked)} docs")
    return reranked

