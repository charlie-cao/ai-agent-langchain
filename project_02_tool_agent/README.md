# 🛠️ Project 02 — Multi-Tool ReAct Agent

## 商业价值说明书

### 为什么这个 Agent 有市场需求？
企业日常工作需要同时查询多个数据源、做计算、读写文件——现有 ChatBot 无法跨工具协作。
ReAct Agent 实现"思考-行动-观察"循环，自主决定调用哪个工具、用几次，完成复杂多步任务。

- **效率提升**：一句话触发多个工具链，替代人工多窗口切换
- **可溯源**：每步工具调用有完整日志，满足企业审计需求
- **可扩展**：新增工具只需添加 `@tool` 装饰器，无需改主流程
- **本地安全**：LLM 本地运行，工具调用结果不离开企业网络

### 市场竞品分析
| 竞品 | 优势 | 劣势 |
|------|------|------|
| LangChain Hub Agents | 完善生态 | 需要外部 API keys |
| AutoGPT | 知名度高 | 不稳定，成本高 |
| OpenAI Assistants API | 官方支持 | 数据上云，贵 |
| **本项目** | 本地运行，零 API 费用，完全可控 | 需要自建工具 |

---

## 项目简介
基于 LangChain ReAct 框架的多工具 Agent，内置网络搜索、计算器、文件读写、时区查询，
支持 8 步推理循环，所有工具调用可视化展示。

---

## 技术架构

```
用户问题
    │
    ▼
┌─────────────────────────────────────┐
│         ReAct Agent Loop            │
│                                     │
│  Thought: "I need to search..."     │
│  Action: web_search("...")          │
│      │                              │
│      ▼                              │
│  ┌──────────────────────────────┐   │
│  │         Tool Router          │   │
│  │  web_search   │  calculator  │   │
│  │  file_read    │  file_write  │   │
│  │  file_list    │  get_datetime│   │
│  └──────────────────────────────┘   │
│      │                              │
│  Observation: "Result: ..."         │
│  (loop max 8 iterations)            │
│      │                              │
│  Final Answer ──────────────────────┤
└─────────────────────────────────────┘
    │
    ▼
Streamlit UI (steps expander)
```

---

## 环境配置

```bash
cd project_02_tool_agent
uv pip install -r requirements.txt
cp .env.example .env
ollama pull qwen3.5:latest
```

## 启动命令

```bash
# UI
uv run streamlit run app.py

# API
uv run uvicorn api:app --reload --port 8002

# Tests
uv run pytest tests/ -v
```

---

## 内置工具

| 工具 | 功能 | 安全性 |
|------|------|--------|
| `web_search` | DuckDuckGo 搜索（无 API key）| 输入长度限制 |
| `calculator` | 安全 AST 数学计算 | 禁止代码执行 |
| `file_read` | 读取沙盒文件 | 路径穿越防护 |
| `file_write` | 写入沙盒文件 | 路径穿越防护 |
| `file_list` | 列出沙盒文件 | 沙盒隔离 |
| `get_datetime` | 当前时间（任意时区）| 白名单时区 |

---

## 评估结果

| 指标 | 数值 |
|------|------|
| 平均响应时间（单工具）| ~2s |
| 平均响应时间（多工具链 3步）| ~6s |
| 工具调用成功率 | 95%+ |
| ReAct 循环收敛率 | 98% |

---

## 后续改进方向
- [ ] 接入 Slack/Email 工具（企业通讯集成）
- [ ] 接入 SQL 查询工具（数据库能力）
- [ ] 接入 Python REPL（数据分析）
- [ ] Plan-and-Execute 模式（先规划再执行）
- [ ] 工具结果缓存（减少重复搜索）
