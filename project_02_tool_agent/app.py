# app.py — Streamlit UI for Multi-Tool ReAct Agent
import json
import streamlit as st

st.set_page_config(
    page_title="Multi-Tool ReAct Agent",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from config import DEFAULT_MODEL, OLLAMA_BASE_URL
from agent import run, ALL_TOOLS

# ── Session init ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "metrics" not in st.session_state:
    st.session_state.metrics = []

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛠️ Multi-Tool ReAct Agent")
    st.caption("多工具调用 · 网络搜索 · 计算器 · 文件读写")
    st.divider()

    st.markdown("### ⚙️ Settings")
    model_name = st.text_input("Ollama Model", value=DEFAULT_MODEL)

    st.divider()
    st.markdown("### 🧰 Available Tools")
    for tool in ALL_TOOLS:
        with st.expander(f"`{tool.name}`"):
            st.caption(tool.description[:200])

    st.divider()
    st.markdown("### 📊 Session Metrics")
    if st.session_state.metrics:
        total = len(st.session_state.metrics)
        avg_lat = sum(m["latency_ms"] for m in st.session_state.metrics) / total
        avg_tools = sum(m["tool_calls"] for m in st.session_state.metrics) / total
        st.metric("Queries", total)
        st.metric("Avg Latency", f"{avg_lat:.0f} ms")
        st.metric("Avg Tool Calls", f"{avg_tools:.1f}")
    else:
        st.caption("No queries yet")

    if st.button("🗑️ Clear conversation"):
        st.session_state.messages = []
        st.session_state.metrics = []
        st.rerun()

# ── Main ──────────────────────────────────────────────────────────────────────
st.markdown("# 🛠️ Multi-Tool ReAct Agent")
st.caption(f"Powered by **{model_name}** @ {OLLAMA_BASE_URL}")

# Example prompts
with st.expander("💡 Example prompts"):
    st.markdown("""
- `What is today's date in Los Angeles?`
- `Search the web: latest LangChain release`
- `Calculate: (6.674e-11 * 5.972e24) / (6.371e6 ** 2)`
- `Write a haiku to workspace/haiku.txt, then read it back`
- `Search for the current Bitcoin price and calculate 0.5 BTC in USD`
""")

# Chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and "steps" in msg and msg["steps"]:
            with st.expander(f"🔍 Tool calls ({len(msg['steps'])})  ·  {msg.get('latency_ms', 0)}ms"):
                for i, step in enumerate(msg["steps"], 1):
                    st.markdown(f"**Step {i}: `{step['tool']}`**")
                    st.code(str(step["input"]), language="text")
                    st.info(str(step["output"])[:500])

# Input
if prompt := st.chat_input("Ask me anything — I have tools!"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking and using tools..."):
            try:
                result = run(prompt)
                answer = result["answer"]
                steps = result["steps"]
                latency_ms = result["latency_ms"]
                tool_calls = result["tool_calls"]
            except Exception as e:
                answer = f"⚠️ Error: {e}"
                steps = []
                latency_ms = 0
                tool_calls = 0

        st.markdown(answer)

        if steps:
            with st.expander(f"🔍 Tool calls ({tool_calls})  ·  {latency_ms}ms"):
                for i, step in enumerate(steps, 1):
                    st.markdown(f"**Step {i}: `{step['tool']}`**")
                    st.code(str(step["input"]), language="text")
                    st.info(str(step["output"])[:500])

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "steps": steps,
        "latency_ms": latency_ms,
        "tool_calls": tool_calls,
    })
    st.session_state.metrics.append({"latency_ms": latency_ms, "tool_calls": tool_calls})
