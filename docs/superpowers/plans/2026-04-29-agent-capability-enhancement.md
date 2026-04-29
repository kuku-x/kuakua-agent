# 夸夸 Agent 技术栈应用计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将夸夸 Agent 项目从"LLM 驱动的自动化系统"升级为"真正的 Agent 系统"，具备 Tool Calling、自我评估循环、条件推理能力。

**核心目标**：让项目在简历中可以自信地写"AI Agent"而不是"AI 应用"。

---

## 升级目标

| Agent 特征 | 当前项目 | 升级后 |
|------------|---------|--------|
| 感知环境 | ActivityWatch ✅ | ActivityWatch ✅ |
| 记忆 | SQLite milestone ✅ | SQLite + 向量检索 ✅ |
| 自主行动 | 调度器触发 ✅ | 调度器触发 ✅ |
| **工具调用** | 只有通知 + TTS ❌ | MCP 工具调用 ✅ |
| **多步推理** | 线性流程 ❌ | LangGraph 工作流 ✅ |
| **自我评估** | 无 ❌ | 自评循环 ✅ |
| **规划能力** | 规则引擎 ❌ | LLM 决策 ✅ |

---

## 技术框架

| 框架 | 用途 | 优先级 |
|------|------|--------|
| **LangGraph** | 工作流编排、自评循环、条件分支 | P0 |
| **MCP** | 标准化工具调用协议 | P1 |
| **LlamaIndex** | 向量检索、RAG、跨时间上下文 | P2 |

---

## 第一步：LangGraph 工作流编排（P0）

### 目标

改造夸夸生成流程，从"线性流程"升级为"可条件分支、可循环、可自评的工作流"。

```
改造前（线性）：
milestone → 收集上下文 → 生成 → 输出

改造后（工作流）：
milestone → 收集上下文
                ↓
            生成草稿
                ↓
            自我评估
                ↓
        ┌───────┴───────┐
        ↓               ↓
    质量差           质量好
        ↓               ↓
    重写（最多3次）  格式化 → 输出
        ↑
        └────────────────┘
```

### 新增文件

```
kuakua_agent/services/brain/graph/
├── __init__.py
├── state.py      # PraiseState 类型定义
├── nodes.py      # 各节点实现
├── edges.py      # 边和条件边定义
└── builder.py    # 图构建器
```

### 核心代码

```python
# kuakua_agent/services/brain/graph/state.py
from typing import TypedDict

class PraiseState(TypedDict):
    milestone: dict           # 当前里程碑
    context: str            # 上下文
    draft_praise: str       # 草稿
    evaluation: str         # 自我评估结果
    final_praise: str       # 最终输出
    iteration: int          # 迭代次数（最多3次）
```

```python
# kuakua_agent/services/brain/graph/nodes.py

async def gather_context_node(state: PraiseState) -> PraiseState:
    """收集上下文"""
    context = await context_builder.build_proactive_context(state["milestone"])
    return {"context": context, "iteration": 0}


async def generate_draft_node(state: PraiseState) -> PraiseState:
    """生成草稿"""
    draft = await model_adapter.complete_async(
        prompt=f"根据以下上下文生成夸夸：\n{state['context']}"
    )
    return {"draft_praise": draft}


async def self_evaluate_node(state: PraiseState) -> PraiseState:
    """自我评估"""
    evaluation_prompt = f"""
评估以下夸夸的质量：

夸夸：{state['draft_praise']}
上下文：{state['context']}

评估维度：
1. 相关性：夸的是今天真实发生的事吗？
2. 真诚度：听起来像真心的还是套话？
3. 多样性：和历史夸夸比有变化吗？

返回格式：
评估结果：PASS/FAIL
问题（如有）：
质量分数：0-10
    """
    result = await model_adapter.complete_async(evaluation_prompt)
    return {"evaluation": result}


async def refine_praise_node(state: PraiseState) -> PraiseState:
    """重写夸夸"""
    refined = await model_adapter.complete_async(
        prompt=f"""
之前的夸夸有问题，需要重写：
原文：{state['draft_praise']}
问题：{state['evaluation']}
请生成一个更好的版本。
        """
    )
    return {
        "draft_praise": refined,
        "iteration": state["iteration"] + 1
    }


async def format_output_node(state: PraiseState) -> PraiseState:
    """格式化输出"""
    return {"final_praise": state["draft_praise"]}
```

```python
# kuakua_agent/services/brain/graph/edges.py
from langgraph.graph import END

def should_refine(state: PraiseState) -> str:
    """条件边判断"""
    if state["iteration"] >= 3:
        return "approve"  # 最多3轮，强制通过
    if "FAIL" in state["evaluation"] or "套话" in state["evaluation"]:
        return "refine"  # 质量不佳，重写
    return "approve"
```

```python
# kuakua_agent/services/brain/graph/builder.py
from langgraph.graph import StateGraph, END

def build_praise_graph():
    graph = StateGraph(PraiseState)

    # 添加节点
    graph.add_node("gather_context", gather_context_node)
    graph.add_node("generate_draft", generate_draft_node)
    graph.add_node("self_evaluate", self_evaluate_node)
    graph.add_node("refine_praise", refine_praise_node)
    graph.add_node("format_output", format_output_node)

    # 设置入口
    graph.set_entry_point("gather_context")

    # 普通边
    graph.add_edge("gather_context", "generate_draft")
    graph.add_edge("generate_draft", "self_evaluate")

    # 条件边
    graph.add_conditional_edges(
        "self_evaluate",
        should_refine,
        {"refine": "refine_praise", "approve": "format_output"}
    )

    # 循环边
    graph.add_edge("refine_praise", "generate_draft")
    graph.add_edge("format_output", END)

    return graph.compile()
```

### 改造文件

- `services/scheduler/scheduler.py` — 接入 LangGraph 工作流

### 实施检查清单

- [ ] 安装 langgraph
- [ ] 创建 `services/brain/graph/` 目录
- [ ] 实现 PraiseState 类型定义
- [ ] 实现各节点函数
- [ ] 实现条件边判断
- [ ] 实现图构建器
- [ ] 改造 scheduler.py 调用新工作流
- [ ] 编写单元测试
- [ ] 对比新旧输出质量

---

## 第二步：MCP 工具调用（P1）

### 目标

给 Agent 装上"USB 接口"，通过 MCP 协议调用外部工具（天气、日历等）。

```
Agent 思考：
"用户今天天气很好，应该提到这个"
        ↓
调用 get_weather 工具
        ↓
获取天气：晴，22度
        ↓
结合上下文生成夸夸：
"今天阳光明媚，你也精力充沛地开始了..."
```

### 新增文件

```
kuakua_agent/services/mcp/
├── __init__.py
├── client.py      # MCP Client
├── server.py      # MCP Server
├── tools/
│   ├── __init__.py
│   ├── weather.py     # 天气查询工具
│   ├── calendar.py    # 日历查询工具
│   └── notification.py # 通知增强工具
└── registry.py    # 工具注册表
```

### 核心代码

```python
# kuakua_agent/services/mcp/client.py
from mcp import Client
from typing import Any

class MCPClient:
    def __init__(self):
        self.client = Client()
        self._tools = {}

    async def connect(self, server_script: str):
        """连接 MCP Server"""
        await self.client.connect_to_server(server_script)

    async def list_tools(self) -> list[dict]:
        """列出所有可用工具"""
        return await self.client.list_tools()

    async def call_tool(self, tool_name: str, arguments: dict) -> Any:
        """调用工具"""
        return await self.client.call_tool(tool_name, arguments)
```

```python
# kuakua_agent/services/mcp/server.py
from mcp.server import Server
from mcp.types import Tool, TextContent

server = Server("kuakua-agent")

@server.list_tools()
async def list_tools():
    return [get_weather_tool(), get_calendar_tool()]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "get_weather":
        return await handle_weather(arguments)
    elif name == "get_calendar":
        return await handle_calendar(arguments)
```

```python
# kuakua_agent/services/mcp/tools/weather.py
from mcp.types import Tool, TextContent

def get_weather_tool():
    return Tool(
        name="get_weather",
        description="查询用户所在地的当前天气",
        inputSchema={
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "位置，默认 Shanghai"}
            }
        }
    )

async def handle_weather(arguments: dict):
    from kuakua_agent.services.weather import WeatherService
    weather = WeatherService()
    result = await weather.get_current_weather(arguments.get("location", "Shanghai"))
    return TextContent(type="text", text=str(result))
```

### 改造文件

- `services/brain/adapter.py` — 支持 tools 参数，处理 tool_calls

```python
# services/brain/adapter.py 改造
async def complete_with_tools(self, prompt: str, tools: list[dict]):
    """带工具调用的生成"""
    response = await self.llm.chat(
        messages=[{"role": "user", "content": prompt}],
        tools=tools,
    )

    # 处理工具调用循环
    while response.tool_calls:
        for call in response.tool_calls:
            result = await mcp_client.call_tool(call.name, call.arguments)
            response = await self.llm.continue_chat(tool_result=result)

    return response.content
```

### 实施检查清单

- [ ] 安装 mcp
- [ ] 创建 MCP Server
- [ ] 实现天气查询工具
- [ ] 实现日历查询工具（可选）
- [ ] 实现 MCP Client
- [ ] 改造 ModelAdapter 支持工具调用
- [ ] 测试工具调用链路
- [ ] 测量延迟指标

---

## 第三步：LlamaIndex RAG（P2）

### 目标

给 Agent 加上"长期记忆"，实现夸夸历史的语义相似召回。

```
Agent 思考：
"用户之前也做到过专注编码"
        ↓
向量检索历史 milestone
        ↓
找到：3天前专注2小时
        ↓
生成夸夸：
"你3天前也专注编码了2小时，今天又做到了..."
```

### 新增文件

```
kuakua_agent/services/memory/
├── vector_store.py    # LlamaIndex 封装
```

### 核心代码

```python
# kuakua_agent/services/memory/vector_store.py
from llama_index.core import VectorStoreIndex, Document
from llama_index.llms.deepseek import DeepSeek
from llama_index.embeddings.deepseek import DeepSeekEmbedding

class VectorStoreManager:
    def __init__(self):
        self.llm = DeepSeek(api_key=settings.llm_api_key, model=settings.llm_model_id)
        self.embedding = DeepSeekEmbedding(api_key=settings.llm_api_key)
        self.milestone_index = None

    def build_milestone_index(self, milestones: list[dict]):
        """从 milestone 构建向量索引"""
        docs = [
            Document(
                text=f"时间：{m['occurred_at']} | 类型：{m['event_type']} | 成就：{m['description']}",
                metadata={"id": m["id"], "type": m["event_type"]}
            )
            for m in milestones
        ]
        self.milestone_index = VectorStoreIndex.from_documents(docs, embed_model=self.embedding)

    def retrieve_similar_milestones(self, milestone_type: str, top_k: int = 3) -> list[dict]:
        """检索相似的里程碑"""
        if not self.milestone_index:
            return []

        retriever = self.milestone_index.as_retriever(similarity_top_k=top_k)
        nodes = retriever.retrieve(f"用户达成了{milestone_type}类型的成就")
        return [{"id": n.metadata["id"], "text": n.text, "score": n.score} for n in nodes]

    def build_praise_context(self, current: dict, recent: list[dict]) -> str:
        """构建包含历史相似成就的上下文"""
        similar = self.retrieve_similar_milestones(current["event_type"], top_k=2)

        parts = []
        if recent:
            parts.append(f"用户最近的成就：\n" + "\n".join([f"- {m['description']}" for m in recent[:5]]))
        if similar:
            parts.append(f"\n用户过去的类似成就：\n" + "\n".join([f"- {s['text']}" for s in similar]))
        parts.append(f"\n当前成就：{current['description']}")

        return "\n".join(parts)
```

### 改造文件

- `services/brain/context.py` — 集成向量上下文

```python
# services/brain/context.py 改造
async def build_proactive_context(self, milestone: dict) -> str:
    # ... 原有逻辑 ...

    # 新增：向量检索相似历史
    recent = await milestone_store.get_recent(hours=24, limit=10)
    vector_context = self.vector_store.build_praise_context(
        milestone,
        [m.__dict__ for m in recent]
    )

    return f"{base_context}\n\n{vector_context}"
```

### 实施检查清单

- [ ] 安装 llama-index
- [ ] 创建 VectorStoreManager 类
- [ ] 实现 milestone 索引构建
- [ ] 实现相似检索
- [ ] 改造 ContextBuilder 集成向量上下文
- [ ] 添加索引更新机制（定期重建）
- [ ] 编写单元测试
- [ ] 对比检索效果

---

## 实施优先级

| 步骤 | 内容 | 时间投入 | 简历价值 |
|------|------|---------|---------|
| **第一步** | LangGraph 工作流编排 | 2-3 天 | ⭐⭐⭐⭐⭐ |
| **第二步** | MCP 工具调用 | 2-3 天 | ⭐⭐⭐⭐ |
| **第三步** | LlamaIndex RAG | 1-2 天 | ⭐⭐⭐⭐ |

---

## 简历项目描述最终版

完成上述优化后，简历项目描述可以这样写：

> **夸夸Agent — AI 驱动的行为分析助手（真 Agent）**
> - 设计并实现了完整的 **Agent 架构**：感知(brain/activitywatch) → 记忆(memory/SQLite) → 推理(LangGraph) → 工具调用(MCP) → 输出(output)
> - 基于 **LangGraph** 构建了支持自我反思的工作流引擎，实现"生成→自评→条件重写"循环（最多3轮），具备条件分支决策能力
> - 基于 **MCP 协议**实现了标准化工具调用框架，已接入天气、日历等外部工具，支持多轮 Tool Calling
> - 基于 **LlamaIndex** 构建了 milestone 向量检索系统，支持夸夸历史的语义相似召回，实现跨时间上下文联想能力
> - 接入 ActivityWatch 行为数据流，实现基于事件驱动的 milestone 记忆系统，支持 30s 粒度主动夸夸触发
> - 全栈落地：FastAPI + SQLite + Electron/Vue，端到端全链路自主开发

---

## 总结

| 能力 | 技术 | 升级前 | 升级后 |
|------|------|--------|--------|
| 工作流编排 | LangGraph | 线性流程 | 条件分支 + 循环 |
| 自我评估 | LangGraph | 无 | 自评循环 |
| 工具调用 | MCP | 写死调用 | 标准化协议 |
| 长期记忆 | LlamaIndex | 精确匹配 | 语义检索 |
| **Agent 成熟度** | — | **LLM 应用** | **真 Agent** |
