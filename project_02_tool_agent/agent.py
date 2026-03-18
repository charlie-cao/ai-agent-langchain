# agent.py — ReAct Agent with multiple tools (LangGraph) v2.0
from __future__ import annotations

import json
import time
from typing import Generator, List, Optional
from langchain_ollama import ChatOllama
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent
from loguru import logger

from config import settings, OLLAMA_BASE_URL, DEFAULT_MODEL, TEMPERATURE
from tools.search_tool import web_search
from tools.calculator_tool import calculator
from tools.file_tool import file_read, file_write, file_list
from tools.datetime_tool import get_datetime


# All available tools
ALL_TOOLS = [web_search, calculator, file_read, file_write, file_list, get_datetime]


# ── LLM Factory ────────────────────────────────────────────────────────────────
def _llm(streaming: bool = False) -> ChatOllama:
    return ChatOllama(
        model=DEFAULT_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=TEMPERATURE,
        streaming=streaming,
    )


# ── Global Agent Cache ────────────────────────────────────────────────────────
_agent = None


def get_agent():
    """Get or create the agent singleton."""
    global _agent
    if _agent is None:
        _agent = create_react_agent(
            model=_llm(),
            tools=ALL_TOOLS,
        )
        logger.info("Agent initialized")
    return _agent


def reset_agent():
    """Reset agent (useful for testing)."""
    global _agent
    _agent = None
    logger.info("Agent reset")


# ── Run Functions ─────────────────────────────────────────────────────────────
def run(question: str, chat_history: Optional[List[BaseMessage]] = None) -> dict:
    """Non-streaming agent run. Returns answer + tool trace."""
    t0 = time.perf_counter()
    
    agent = get_agent()
    
    # Build input as messages
    messages = []
    if chat_history:
        messages.extend(chat_history)
    messages.append(HumanMessage(content=question))
    
    # Run agent
    result = agent.invoke({"messages": messages}, stream_mode="values")
    
    latency_ms = round((time.perf_counter() - t0) * 1000)
    
    # Extract tool calls from messages
    steps = []
    result_messages = result.get("messages", [])
    for msg in result_messages:
        if hasattr(msg, "type") and msg.type == "tool":
            steps.append({
                "tool": getattr(msg, "name", "unknown"),
                "input": str(getattr(msg, "tool_input", ""))[:200],
                "output": str(getattr(msg, "content", ""))[:500],
            })
    
    # Final answer is the last AI message
    answer = ""
    for msg in reversed(result_messages):
        if hasattr(msg, "type") and msg.type == "ai":
            answer = getattr(msg, "content", "")
            break
    
    return {
        "answer": answer,
        "steps": steps,
        "latency_ms": latency_ms,
        "tool_calls": len(steps),
    }


def run_stream(question: str, chat_history: Optional[List[BaseMessage]] = None) -> Generator[dict, None, None]:
    """Streaming version - yields events as they happen."""
    t0 = time.perf_counter()
    tool_calls = 0
    
    agent = get_agent()
    
    messages = []
    if chat_history:
        messages.extend(chat_history)
    messages.append(HumanMessage(content=question))
    
    for event in agent.stream({"messages": messages}, stream_mode="updates"):
        for node_name, node_output in event.items():
            if node_name == "agent":
                msgs = node_output.get("messages", [])
                for msg in msgs:
                    if hasattr(msg, "type") and msg.type == "ai":
                        content = getattr(msg, "content", "")
                        if content:
                            yield {"type": "token", "content": content}
            elif node_name.startswith("tools_"):
                msgs = node_output.get("messages", [])
                for msg in msgs:
                    if hasattr(msg, "type") and msg.type == "tool":
                        tool_calls += 1
                        yield {
                            "type": "tool_end",
                            "tool": getattr(msg, "name", "unknown"),
                            "output": str(getattr(msg, "content", ""))[:300],
                        }
    
    latency_ms = round((time.perf_counter() - t0) * 1000)
    yield {
        "type": "done",
        "latency_ms": latency_ms,
        "tool_calls": tool_calls,
    }


# ── Utility ───────────────────────────────────────────────────────────────────
def get_stats() -> dict:
    """Get agent stats."""
    return {
        "num_tools": len(ALL_TOOLS),
        "tool_names": [t.name for t in ALL_TOOLS],
        "model": DEFAULT_MODEL,
        "ollama_url": OLLAMA_BASE_URL,
    }
