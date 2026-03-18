# agent.py — ReAct Agent with multiple tools (LangChain structured tool calling)
from __future__ import annotations

import json
import time
from typing import Generator, List

from langchain_community.chat_models import ChatOllama
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from loguru import logger

from config import OLLAMA_BASE_URL, DEFAULT_MODEL, TEMPERATURE
from prompts.agent_prompts import react_prompt
from tools.search_tool import web_search
from tools.calculator_tool import calculator
from tools.file_tool import file_read, file_write, file_list
from tools.datetime_tool import get_datetime

ALL_TOOLS = [web_search, calculator, file_read, file_write, file_list, get_datetime]


def _llm(streaming: bool = False) -> ChatOllama:
    return ChatOllama(
        model=DEFAULT_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=TEMPERATURE,
        streaming=streaming,
    )


def _build_executor(streaming: bool = False) -> AgentExecutor:
    llm = _llm(streaming=streaming)
    agent = create_react_agent(llm=llm, tools=ALL_TOOLS, prompt=react_prompt)
    return AgentExecutor(
        agent=agent,
        tools=ALL_TOOLS,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=8,
        return_intermediate_steps=True,
    )


def run(question: str, chat_history: List[BaseMessage] | None = None) -> dict:
    """Non-streaming agent run. Returns answer + tool trace."""
    t0 = time.perf_counter()
    executor = _build_executor()
    result = executor.invoke({
        "input": question,
        "chat_history": chat_history or [],
    })
    latency_ms = round((time.perf_counter() - t0) * 1000)

    steps = []
    for action, obs in result.get("intermediate_steps", []):
        steps.append({
            "tool": action.tool,
            "input": action.tool_input,
            "output": str(obs)[:500],
        })

    return {
        "answer": result.get("output", ""),
        "steps": steps,
        "latency_ms": latency_ms,
        "tool_calls": len(steps),
    }


def run_stream(question: str, chat_history: List[BaseMessage] | None = None) -> Generator[dict, None, None]:
    """Streaming generator. Yields:
      {"type": "token", "content": "..."}
      {"type": "tool_start", "tool": "...", "input": "..."}
      {"type": "tool_end", "output": "..."}
      {"type": "done", "latency_ms": ..., "tool_calls": ...}
    """
    t0 = time.perf_counter()
    tool_calls = 0

    # Use callbacks for tool event streaming
    from langchain_core.callbacks import BaseCallbackHandler

    class _StreamHandler(BaseCallbackHandler):
        def __init__(self, gen_fn):
            self._emit = gen_fn

        def on_llm_new_token(self, token: str, **kwargs):
            self._emit({"type": "token", "content": token})

        def on_tool_start(self, serialized, input_str, **kwargs):
            tool_name = serialized.get("name", "unknown")
            self._emit({"type": "tool_start", "tool": tool_name, "input": str(input_str)[:200]})

        def on_tool_end(self, output, **kwargs):
            nonlocal tool_calls
            tool_calls += 1
            self._emit({"type": "tool_end", "output": str(output)[:300]})

    events: List[dict] = []

    def _emit(event: dict):
        events.append(event)

    handler = _StreamHandler(_emit)
    llm = ChatOllama(
        model=DEFAULT_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=TEMPERATURE,
        streaming=True,
        callbacks=[handler],
    )
    agent = create_react_agent(llm=llm, tools=ALL_TOOLS, prompt=react_prompt)
    executor = AgentExecutor(
        agent=agent,
        tools=ALL_TOOLS,
        verbose=False,
        handle_parsing_errors=True,
        max_iterations=8,
        return_intermediate_steps=True,
        callbacks=[handler],
    )

    # Run in same thread (synchronous) but yield accumulated events
    result = executor.invoke({
        "input": question,
        "chat_history": chat_history or [],
    })

    for event in events:
        yield event

    latency_ms = round((time.perf_counter() - t0) * 1000)
    steps = []
    for action, obs in result.get("intermediate_steps", []):
        steps.append({"tool": action.tool, "input": action.tool_input, "output": str(obs)[:300]})

    yield {
        "type": "final",
        "answer": result.get("output", ""),
        "steps": steps,
        "latency_ms": latency_ms,
        "tool_calls": len(steps),
    }
