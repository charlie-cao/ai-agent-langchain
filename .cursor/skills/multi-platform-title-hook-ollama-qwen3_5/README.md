# multi-platform-title-hook (Ollama / qwen3.5)

这个文件夹提供一套**专门给本地 Ollama（`qwen3.5:latest`）**使用的运行方式，让你在不依赖 Claude 的情况下，稳定产出：
- Titles（20）
- Hooks（10）
- Cover copy（6）
- Pinned comment（3）
- Mini test plan（A/B）

并强制执行“合规/营销味/可兑现承诺”自检与固定输出结构。

---
## 你需要什么
- Windows + PowerShell
- 已安装 Ollama（建议先运行一次 `ollama run qwen3.5:latest` 确保本机可加载模型）
- 已拉取模型：`ollama pull qwen3.5:latest`
- 本机内存：qwen3.5 约需 2GB+ 可用内存，不足时会出现 "model requires more system memory"；可关掉其它占内存程序或改用更小模型（需改 `run.ps1` 的 `-Model`）

可用性检查：
```powershell
ollama --version
ollama list
.\test-connection.ps1
```

---
## 快速开始（推荐）

### 1) 直接跑交互版（手动粘贴输入）
```powershell
ollama run qwen3.5:latest
```
然后把 `prompts/system.txt` 整段粘贴进去（当作“规则/系统提示”），再粘贴你的任务输入（见 `prompts/user-template.md`）。

### 2) 一键运行（通过 Ollama HTTP API，单次请求拿满量输出）
在本文件夹打开 PowerShell（确保 Ollama 已在运行，如已打开过 Ollama 应用或执行过 `ollama run` 即可）：
```powershell
.\run.ps1 -Topic "在美国卖栅栏，我怎么在小红书推广" -Goal "私信咨询" -Audience "在美华人屋主/新房主" -Tone "专业克制、实操" -Constraints "不夸大承诺；不写最低价；不强引流"
```
可选：`-TimeoutSec 180`、`-Model "其他模型"`、`-OllamaHost "http://localhost:11434"`

---
## 文件说明
- `prompts/system.txt`：给本地模型的“精简常驻规则”（尽量短但约束强）
- `prompts/user-template.md`：你复制粘贴时的输入模板
- `prompts/examples/`：示例输入（复制即可跑）
- `run.ps1`：把参数拼成 system + user prompt，通过 **Ollama HTTP API**（`/api/generate`）一次性请求，避免交互等待；输出完整内容
- `test-connection.ps1`：检查 Ollama 是否可达、模型是否在列表中（不跑生成）

---
## 常见问题

### Q1：输出结构乱/漏块
做法：
- 把 `prompts/system.txt` 放在最前面
- 你的输入里加一句：**“必须严格按输出格式输出，不要解释过程，不要省略任何区块。”**

### Q2：容易写得很营销/夸大
做法：
- 在你的输入里追加：**“不要写保证收益、暴涨、躺赚、最低价、全网第一。”**
- 或把 `prompts/system.txt` 末尾的“合规自检”段落复制再贴一次（加强约束）

### Q3：你想把仓库里的 Skill 原文一起喂给模型
不推荐（会占上下文）。更推荐用本文件夹的精简 system prompt。

