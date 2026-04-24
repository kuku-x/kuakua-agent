# 夸夸Agent 架构升级规格文档

> 日期：2026-04-24
> 状态：已确认，待实现

---

## 一、架构选择

**方案一：单体分层架构** — 在现有 FastAPI 单体项目内按四层拆分，不改动原有业务。

```
services/
├── brain/              # 本地大脑层
│   ├── __init__.py
│   ├── router.py       # 意图分流：解析用户/系统指令
│   ├── context.py     # 上下文组装器：拼接系统提示词+用户偏好+环境数据+历史记忆
│   ├── prompt.py      # 夸夸Prompt模板管理
│   └── adapter.py     # 大模型调用适配器（对接Ark API）
│
├── memory/             # 状态记忆层
│   ├── __init__.py
│   ├── database.py    # SQLite连接管理
│   ├── models.py      # 数据表模型定义
│   ├── milestone.py    # 行为里程碑读写
│   ├── preference.py   # 夸夸偏好读写
│   ├── profile.py      # 场景标签画像读写
│   └── feedback.py    # 用户反馈记忆读写
│
├── scheduler/          # 节律调度层
│   ├── __init__.py
│   ├── rules.py       # 触发规则定义（时间节点+行为组合）
│   ├── scheduler.py    # 调度中心：定时检查+事件触发
│   ├── cooldown.py    # 冷却时间、每日上限、免打扰时段
│   └── events.py      # 调度事件定义
│
└── output/             # 多模态输出层
    ├── __init__.py
    ├── base.py        # 输出基类/接口
    ├── notifier.py    # 桌面系统通知
    └── tts.py         # Fish Audio TTS语音输出
```

---

## 二、数据表设计（SQLite）

### 2.1 milestones（行为里程碑）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增ID |
| event_type | TEXT | 事件类型：focus/coding/discipline/exercise等 |
| title | TEXT | 里程碑标题 |
| description | TEXT | 详细描述 |
| occurred_at | DATETIME | 发生时间，默认 CURRENT_TIMESTAMP |
| created_at | DATETIME | 记录时间，默认 CURRENT_TIMESTAMP |
| is_recalled | BOOLEAN | 是否已被提起过，默认 FALSE |

### 2.2 praise_history（夸夸历史）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增ID |
| content | TEXT | 夸夸内容 |
| trigger_type | TEXT | 触发类型：active/proactive/scheduled |
| context_snapshot | TEXT | 触发时的上下文快照JSON |
| created_at | DATETIME | 发送时间，默认 CURRENT_TIMESTAMP |

### 2.3 user_preferences（用户偏好）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增ID |
| key | TEXT UNIQUE | 偏好键 |
| value | TEXT | 偏好值JSON |
| updated_at | DATETIME | 更新时间，默认 CURRENT_TIMESTAMP |

**内置全局偏好键：**
- `praise_auto_enable`: bool — 全局开关，控制是否开启主动触发夸夸调度（默认 true）
- `tts_enable`: bool — TTS语音开关（默认 false）
- `tts_voice`: str — TTS音色ID
- `tts_speed`: float — TTS语速（默认 1.0）
- `do_not_disturb_start`: str — 免打扰开始时间（如 "22:00"）
- `do_not_disturb_end`: str — 免打扰结束时间（如 "08:00"）
- `max_praises_per_day`: int — 每日主动夸夸上限（默认 10）
- `global_cooldown_minutes`: int — 全局冷却分钟数（默认 30）

### 2.4 scene_profiles（场景画像）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增ID |
| scene | TEXT | 场景标签：work/dev/rest/entertainment |
| weight | REAL | 权重0-1 |
| keywords | TEXT | 关联关键词JSON |
| updated_at | DATETIME | 更新时间，默认 CURRENT_TIMESTAMP |

### 2.5 feedback_logs（反馈记忆）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增ID |
| praise_id | INTEGER FK | 关联夸夸ID |
| reaction | TEXT | 反应类型：liked/disliked/neutral |
| created_at | DATETIME | 反馈时间，默认 CURRENT_TIMESTAMP |

---

## 三、Brain 层（本地大脑）

### 3.1 意图分流（router.py）
- 解析用户输入，识别意图：聊天/设置/查询记忆/反馈
- 系统事件触发时，直接路由到对应处理器

### 3.2 上下文组装（context.py）
每次生成夸夸时，聚合以下6部分：
1. 系统提示词（固定人设 + 夸夸规则）
2. 用户偏好（从memory读取）
3. 环境数据（时间、ActivityWatch状态）
4. 历史记忆（里程碑 + 已发送夸夸）
5. 当前上下文（用户输入或触发事件）
6. 场景画像（当前活跃场景标签）

**防重复机制：**
- 短期（1小时内）同类型里程碑仅保留最新一条
- 夸夸历史摘要压缩：同风格文案近期出现超过2次时，在摘要中标记"避免重复提及"，提醒大模型换角度夸
- 同一 milestone 被提起后标记 `is_recalled=True`，短期内不重复提起

### 3.3 Prompt模板（prompt.py）
```python
PRAISE_SYSTEM_PROMPT = """你是一个温暖治愈的AI夸夸助手，名为"夸夸"。..."""
```

模板变量占位符：
- `{user_name}` - 用户称呼
- `{recent_milestones}` - 最近里程碑
- `{scene_context}` - 当前场景
- `{praise_history_summary}` - 过往夸夸风格摘要
- `{time_of_day}` - 时段（早间/日间/晚间）
- `{weather}` - 天气（可选）

### 3.4 模型适配器（adapter.py）
- 封装Ark API调用
- 支持流式/非流式
- 错误重试逻辑

---

## 四、Scheduler 层（节律调度）

### 4.1 触发规则（rules.py）
```python
class TriggerRule:
    name: str
    time_conditions: List[TimeCondition]   # 时间条件组合
    behavior_conditions: List[BehaviorCondition]  # 行为条件组合
    cooldown_minutes: int
    max_per_day: int
```

时间条件示例：
- `TimeCondition(type="time_range", start="07:00", end="09:00", days=[1,2,3,4,5])` # 工作日早间
- `TimeCondition(type="moment", moment="first_awake")` # 首次亮屏

行为条件示例：
- `BehaviorCondition(type="focus_duration", min_minutes=60)` # 专注60分钟
- `BehaviorCondition(type="app_category", category="development", min_minutes=30)` # 开发30分钟

### 4.2 组合校验逻辑
- 时间条件 AND 行为条件同时满足才触发
- 均需满足，不可单一触发

### 4.3 冷却控制（cooldown.py）
- 全局冷却时间（默认30分钟）
- 每条规则独立冷却
- 每日上限（默认10次）
- 免打扰时段（默认22:00-08:00）
- **全局开关**：`praise_auto_enable`，一键关闭所有主动触发调度，后台轮询立即停止
- **调度轮询间隔**：默认30秒，轻量化资源占用

---

## 五、Output 层（多模态输出）

### 5.1 输出接口（base.py）
```python
class OutputChannel(ABC):
    @abstractmethod
    async def send(self, content: str, metadata: dict) -> bool: ...

    @abstractmethod
    def supports(self, channel_type: str) -> bool: ...
```

### 5.2 桌面通知（notifier.py）
- 使用 `plyer` 或系统原生通知
- 支持标题+内容+图标
- 点击回调（可跳转聊天窗口）

### 5.3 TTS语音（tts.py）
- 对接 Fish Audio API
- 音频文件缓存（hash-based）
- 配置项：音色选择、语速、开关
- 异步调用，不阻塞主流程
- **静默兜底**：Fish Audio 接口异常或网络失败时，自动降级为仅发送桌面通知，不抛异常、不打断主流程

---

## 六、模块间依赖关系

```
外部触发（用户聊天 / 定时器 / ActivityWatch事件）
       │
       ▼
┌─────────────────┐
│   Scheduler     │ ← 读取 cooldown 配置
│  校验触发规则    │
└────────┬────────┘
         │ 触发事件
         ▼
┌─────────────────┐
│     Brain       │
│ 1. Router分流   │
│ 2. Context组装  │
│ 3. Prompt生成   │
│ 4. Adapter调用  │
└────────┬────────┘
         │ 夸夸内容
         ▼
┌─────────────────┐
│    Memory       │
│ 记录本次夸夸    │
│ 更新反馈记忆    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Output       │
│ 通知 +/ TTS     │
└─────────────────┘
```

---

## 七、API 扩展（新增接口）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /settings/praise | 获取夸夸配置（开关、TTS配置等） |
| PUT | /settings/praise | 更新夸夸配置 |
| GET | /memory/milestones | 获取里程碑列表 |
| POST | /memory/milestones | 新增里程碑 |
| GET | /memory/profiles | 获取场景画像 |
| POST | /feedback | 提交夸夸反馈 |

---

## 八、开发顺序

1. **memory 层** — 数据库初始化 + 基础CRUD + 内置偏好初始化
2. **brain 层** — Prompt模板 + 上下文组装（含去重）+ 模型适配
3. **output 层** — 通知 + TTS封装（含静默兜底）
4. **scheduler 层** — 规则 + 调度循环（30s间隔）+ 全局开关 + 冷却控制
5. **接入现有项目** — 对接 routes + chat_service
6. **前端对接** — 配置面板（全局开关、TTS开关、免打扰时段）+ 反馈入口

---

## 九、约束与注意事项

1. **不破坏现有功能** — 所有改动在新增模块内，原有 `chat_service.py` 保留
2. **数据库兼容** — 复用现有数据库，不新建；DATETIME字段默认 CURRENT_TIMESTAMP
3. **配置集中管理** — 所有配置项在 `config.py` 和 Settings API 内
4. **异步优先** — 调度和TTS使用 asyncio，不阻塞 FastAPI 事件循环
5. **可测试性** — 核心模块（router、context、rules）需可单独测试
6. **TTS静默兜底** — TTS异常时降级为纯通知，不向主流程抛异常
7. **调度轻量化** — 轮询间隔30秒，避免桌面常驻资源占用
