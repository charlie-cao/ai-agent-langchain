# agent.py — Agentic RAG with self-correction loop (LangGraph)
from __future__ import annotations

import json
import time
from typing import Generator, TypedDict, Annotated, List

from langchain_community.chat_models import ChatOllama
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.documents import Document
from langgraph.graph import StateGraph, END
from loguru import logger

from config import OLLAMA_BASE_URL, DEFAULT_MODEL, TEMPERATURE, TOP_K
from prompts.rag_prompts import rag_prompt, grade_prompt, rewrite_prompt
from tools.retriever import build_retriever, rerank_docs, load_vectorstore


# ── State ──────────────────────────────────────────────────────────────────────
class RAGState(TypedDict):
    question: str
    rewritten_question: str
    chat_history: List[BaseMessage]
    context_docs: List[Document]
    answer: str
    grade: str          # "yes" | "no"
    iterations: int
    sources: List[str]
    latency_ms: float


MAX_ITERATIONS = 2      # max self-correction loops


# ── LLM factory ───────────────────────────────────────────────────────────────
def _llm(streaming: bool = False) -> ChatOllama:
    return ChatOllama(
        model=DEFAULT_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=TEMPERATURE,
        streaming=streaming,
    )


# ── Nodes ──────────────────────────────────────────────────────────────────────
def node_rewrite(state: RAGState) -> RAGState:
    question = state["question"]
    if state.get("iterations", 0) == 0:
        state["rewritten_question"] = question
        return state
    chain = rewrite_prompt | _llm()
    result = chain.invoke({"question": question})
    state["rewritten_question"] = result.content.strip()
    logger.debug(f"Rewritten: {state['rewritten_question']}")
    return state


def node_retrieve(state: RAGState) -> RAGState:
    try:
        vs = load_vectorstore()
        retriever = build_retriever(vectorstore=vs)
        docs = retriever.invoke(state["rewritten_question"])
        docs = rerank_docs(docs, state["rewritten_question"], top_n=TOP_K)
        state["context_docs"] = docs
        state["sources"] = list({d.metadata.get("source", "unknown") for d in docs})
    except Exception as e:
        logger.warning(f"Retrieval failed: {e}")
        state["context_docs"] = []
        state["sources"] = []
    return state


def node_generate(state: RAGState) -> RAGState:
    t0 = time.perf_counter()
    context = "\n\n---\n\n".join(d.page_content for d in state["context_docs"])
    chain = rag_prompt | _llm()
    result = chain.invoke({
        "context": context or "(no context retrieved)",
        "question": state["question"],
        "chat_history": state.get("chat_history", []),
    })
    state["answer"] = result.content
    state["latency_ms"] = round((time.perf_counter() - t0) * 1000)
    return state


def node_grade(state: RAGState) -> RAGState:
    context = "\n\n".join(d.page_content for d in state["context_docs"])
    chain = grade_prompt | _llm()
    try:
        result = chain.invoke({"context": context, "answer": state["answer"]})
        data = json.loads(result.content)
        state["grade"] = data.get("score", "yes")
    except Exception:
        state["grade"] = "yes"   # default to passing if grading fails
    state["iterations"] = state.get("iterations", 0) + 1
    logger.debug(f"Grade: {state['grade']}  iter={state['iterations']}")
    return state


def _should_retry(state: RAGState) -> str:
    if state["grade"] == "no" and state["iterations"] < MAX_ITERATIONS:
        return "rewrite"
    return END


# ── Build Graph ────────────────────────────────────────────────────────────────
def build_rag_graph():
    g = StateGraph(RAGState)
    g.add_node("rewrite", node_rewrite)
    g.add_node("retrieve", node_retrieve)
    g.add_node("generate", node_generate)
    g.add_node("grade", node_grade)

    g.set_entry_point("rewrite")
    g.add_edge("rewrite", "retrieve")
    g.add_edge("retrieve", "generate")
    g.add_edge("generate", "grade")
    g.add_conditional_edges("grade", _should_retry, {"rewrite": "rewrite", END: END})

    return g.compile()


_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_rag_graph()
    return _graph


# ── Public API ─────────────────────────────────────────────────────────────────
def ask(question: str, chat_history: list | None = None) -> dict:
    """Non-streaming: returns full answer dict."""
    state = get_graph().invoke({
        "question": question,
        "chat_history": chat_history or [],
        "iterations": 0,
    })
    return {
        "answer": state["answer"],
        "sources": state["sources"],
        "latency_ms": state.get("latency_ms", 0),
        "iterations": state.get("iterations", 1),
    }


def ask_stream(question: str, chat_history: list | None = None) -> Generator[str, None, None]:
    """Streaming version — yields answer tokens, then a JSON metadata line."""
    context_docs: List[Document] = []
    sources: List[str] = []

    # 1. rewrite + retrieve (non-streaming, fast)
    temp_state = {"question": question, "iterations": 0}
    node_rewrite(temp_state)
    node_retrieve(temp_state)
    context_docs = temp_state.get("context_docs", [])
    sources = temp_state.get("sources", [])

    context = "\n\n---\n\n".join(d.page_content for d in context_docs)
    chain = rag_prompt | _llm(streaming=True)

    t0 = time.perf_counter()
    full = ""
    for chunk in chain.stream({
        "context": context or "(no context retrieved)",
        "question": question,
        "chat_history": chat_history or [],
    }):
        token = chunk.content
        full += token
        yield token

    latency_ms = round((time.perf_counter() - t0) * 1000)
    # Yield metadata as a special sentinel line
    meta = json.dumps({"sources": sources, "latency_ms": latency_ms, "__meta__": True})
    yield f"\n\n__META__{meta}"
