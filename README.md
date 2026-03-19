# AI Agent 工程实战合集 🤖

> 基于 LangGraph + LangChain + Ollama 的生产级 AI Agent 项目集，共 10 个独立可运行项目，**133 个单元测试全部通过**。

---

## 技术栈

| 层级 | 技术 |
|------|------|
| LLM 底座 | Ollama + qwen3.5:latest（本地，数据不外传） |
| Agent 框架 | LangChain v1.x + LangGraph |
| UI | Streamlit |
| API | FastAPI + SSE 流输出 |
| 包管理 | uv |
| Python | 3.11+ |

---

## 项目总览

| # | 项目 | 优先级 | 测试 | 核心特性 |
|---|------|--------|------|---------|
| 01 | [RAG Agent](project_01_rag_agent/) | P0 ✅ | 3/3 | Agentic RAG, 混合检索, 引用溯源 |
| 02 | [Tool Agent](project_02_tool_agent/) | P0 ✅ | 6/6 | ReAct 6工具, 安全沙箱 |
| 03 | [Multi Agent](project_03_multi_agent/) | P0 ✅ | 5/5 | LangGraph 多节点协作 |
| 04 | [Deep Research](project_04_deep_research/) | P0 ✅ | 7/7 | 迭代搜索+报告生成 |
| 05 | [Enterprise Bot](project_05_enterprise_bot/) | P1 ✅ | 11/11 | RBAC+工单+知识库 |
| 06 | [Code Agent](project_06_code_agent/) | P1 ✅ | 15/15 | 安全代码执行+Lint |
| 07 | [Finance Agent](project_07_finance_agent/) | P1 ✅ | 17/17 | DCF+合规+组合分析 |
| 08 | [Customer Service](project_08_customer_service/) | P1 ✅ | 23/23 | 情绪分析+全链路客服 |
| 09 | [Browser Agent](project_09_browser_agent/) | P2 ✅ | 24/24 | 网页抓取+ReAct自动化 |
| 10 | [HR Agent](project_10_hr_agent/) | P2 ✅ | 22/22 | 多维简历评分+候选人CRUD |

**合计：133 / 133 测试通过 ✅**

---

## 快速启动

```bash
# 1. 启动 Ollama
ollama serve && ollama pull qwen3.5:latest

# 2. 检查环境
uv run python scripts/check_ollama.py

# 3. 运行任意项目
cd project_01_rag_agent
uv run streamlit run app.py
```

---

## 目录结构

```
ai_agent_dev/
├── plan001.md              # 项目规划文档
├── scripts/                # 公共工具脚本
│   ├── check_ollama.py     # 检查 Ollama 状态
│   ├── setup_env.py        # 初始化环境变量
│   ├── benchmark.py        # 跨项目性能评估
│   └── run_all.bat         # 批量启动
├── project_01_rag_agent/   # 企业级 RAG Agent
├── project_02_tool_agent/  # 多工具 ReAct Agent
├── project_03_multi_agent/ # 多智能体协作
├── project_04_deep_research/ # 深度研究 Agent
├── project_05_enterprise_bot/ # 企业自动化助手
├── project_06_code_agent/  # 代码/DevOps Agent
├── project_07_finance_agent/ # 金融合规 Agent
├── project_08_customer_service/ # 客服全链路
├── project_09_browser_agent/ # 浏览器自动化
└── project_10_hr_agent/    # HR招聘筛选
```

---

## 运行所有测试

```bash
cd ai_agent_dev
foreach ($p in @("project_01_rag_agent","project_02_tool_agent","project_03_multi_agent",
  "project_04_deep_research","project_05_enterprise_bot","project_06_code_agent",
  "project_07_finance_agent","project_08_customer_service","project_09_browser_agent",
  "project_10_hr_agent")) { uv run pytest "${p}/tests/" -q --tb=no }
```

