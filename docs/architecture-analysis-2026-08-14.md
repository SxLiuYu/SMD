# Charlie 语音助手 — 架构师深度分析报告

> 评估日期: 2026-08-14  
> 评估者: 架构师 (Architect)  
> 评估框架: Codebase-Design (interface, seam, depth, leverage)

---

## 一、总体架构评分: **7/10**

**优势**:
- 清晰的意图路由分层（快路径 + LLM 大脑）
- MCP 技能生态设计合理，核心/可选分层清晰
- 模块化边界基本明确（app/ vs agent/ vs skills/）
- 双版本架构（OOTB/CUSTOM）考虑了分发与开发隔离

**扣分点**:
- `voice_server.py` (3829行) 和 `voice_agent.py` (2589行) 严重膨胀
- 多处全局状态通过模块级变量共享（信息隐藏不足）
- 部分模块界面复杂度过高（浅层模块）

---

## 二、模块依赖关系图

```
┌─────────────────────────────────────────────────────────────────────┐
│                        voice_server.py (入口)                         │
│   FastAPI 路由层 │ WebSocket │ MQTT │ SSE │ 后台调度器                 │
└──────────────┬──────────────────────────────────────────────────────┘
               │
       ┌───────┴────────┐
       ▼                │
┌──────────────┐  ┌──────────────┐
│ voice_agent.py│  │ app.*       │
│ (大脑引擎)    │  │ ├── audio    │
└───────┬──────┘  │ ├── auth     │
        │         │ ├── brain_health│
        │         │ ├── config    │
        │         │ ├── env_catalog│
        │         │ ├── llm_config│
        │         │ ├── mcp_gate  │
        │         │ ├── mcp_registry│
        │         │ ├── reminders │
        │         │ ├── state     │
        │         │ ├── xiaozhi_ws│
        │         │ └── ... (30+) │
        │         └───────────────┘
        │
  ┌─────┴──────┐
  ▼            │
┌──────────────┐  ┌──────────────┐
│ agent.*      │  │ app.mqtt_push│
│ ├── asr_tts  │  │ app.feishu_bot│
│ ├── intent   │  │ app.state    │
│ ├── history  │  └──────────────┘
│ ├── cache    │
│ ├── retry    │
│ ├── preferences│
│ └── system_msg│
└──────────────┘
        │
        ▼
┌─────────────────────────────────────────┐
│            skills/ (MCP 技能)            │
│  magic-info │ magic-music │ ... (20+)    │
│  mcp_common.py (共享工具)                │
└─────────────────────────────────────────┘
```

### 关键依赖方向

| 源模块 | 目标模块 | 依赖性质 | 耦合度 |
|--------|----------|----------|--------|
| voice_server.py | voice_agent.py | 核心调用 | **紧耦合** |
| voice_agent.py | agent.* (6个) | 内部依赖 | 紧耦合 |
| voice_agent.py | app.llm_config | 配置注入 | 紧耦合 |
| voice_agent.py | app.mcp_registry | MCP解析 | 松耦合 (已改善) |
| voice_server.py | app.* (30+) | 功能模块 | **中-紧耦合** |
| agent.system_msg | app.mcp_gate | 系统提示构建 | 中耦合 |
| skills/* | mcp_common.py | 共享工具 | 松耦合 |

---

## 三、深度 vs 浅层模块分析

### 深层模块 (Deep Modules) — 优秀

#### 1. `agent/intent.py` (78行)
```
接口: strip_wake_word() / is_low_intent_asr() / is_garbled_asr()
实现: 唤醒词剥离正则 + 低意图判断 + 乱码检测
```
- ✅ **小接口 + 大量实现**: 3个函数处理复杂的 ASR 后处理逻辑
- ✅ **信息隐藏好**: 正则表达式模式、有效字符集全部私有化
- ✅ **高杠杆**: 被 `voice_agent.py` 和外部测试复用

#### 2. `app/mcp_registry.py` (83行)
```
接口: resolve(mcp_set) -> dict
实现: 全量MCP配置 + frozen探测 + profile合并
```
- ✅ **重构成功案例**: 从 `voice_agent._build_brain` 抽出，消除重复代码
- ✅ **单一职责**: 只负责MCP配置解析，不执行启动
- ✅ **深度体现在**: 一行调用解决多平台兼容 (frozen/开发环境)

#### 3. `app/mcp_gate.py` (107行)
```
接口: resolve_mcp_profile() / filter_optional_mcp()
实现: 核心/可选分层 + key依赖过滤
```
- ✅ **清晰的边界**: 仅做 profile 解析，不关心MCP实现
- ✅ **高杠杆**: 控制20+技能的加载策略

#### 4. `mcp_common.py` (66行)
```
接口: aliyun_chat() / _safe_math_eval() / _ensure_https()
实现: 各MCP共享的底层工具
```
- ✅ **消除重复**: 避免每个skill重复实现相同逻辑
- ✅ **小接口大实现**: 数学AST求值、HTTPS强制等

#### 5. `agent/cache.py` (30行)
```
接口: _cache_get() / _cache_set() / _cache_lock()
实现: LRU缓存 + TTL过期
```
- ✅ **简洁抽象**: 隐藏缓存淘汰策略和并发控制

### 浅层模块 (Shallow Modules) — 需改进

#### 1. `voice_server.py` (3829行) ⚠️ 核心问题
```
接口: FastAPI路由 (大量POST/GET/WS)
实现: 业务逻辑 + 调度器 + 路由注册 混杂
```
**问题**:
- 3829行单文件违反单一职责
- 路由注册散布在文件中（第300行后继续注册）
- 调度器逻辑与HTTP处理混在一起
- **违反 "删除测试"**: 如果删除此文件，所有复杂性会消失，说明它是 pass-through

**建议**: 拆分为 `routes/`, `schedulers/`, `lifespan.py` 子模块

#### 2. `voice_agent.py` (2589行) ⚠️ 核心问题
```
接口: asr() / tts() / brain_process() / _build_brain() / _classify_intent()
实现: 意图路由 + LLM调用 + MCP触发 + 历史管理 + 重试逻辑
```
**问题**:
- 意图分类逻辑(第282-300行)过于庞大（关键词映射30+条规则）
- 大脑构建逻辑(第183-211行)包含内存检查、LLM配置、MCP解析等多职责
- 全局状态过多（`_brains`, `_brain_failures`, `_intent_failures`等）
- **信息泄露**: 模块级变量同时承担缓存、锁、状态机角色

**建议**: 
- 拆分 `intent_classifier.py` (意图分类逻辑)
- 拆分 `brain_builder.py` (大脑构建)
- 状态对象化（用类封装 `_brain_*` 系列变量）

#### 3. `app/state.py` (370行)
```
接口: _metrics / _ws_clients / register_sse_client() / ...
实现: WebSocket连接管理 + 指标追踪 + 限流桶
```
**问题**:
- 既是"状态存储"又是"指标系统"又是"连接管理"
- 多个不相关概念混在单一模块
- 全局可变状态（`_ws_clients`, `_rate_buckets`）难以测试

**建议**: 拆分为 `app/connection_pool.py`, `app/metrics.py`, `app/rate_limiter.py`

#### 4. `app/xiaozhi_ws.py` (46872 bytes)
```
接口: register_xiaozhi_routes() / WS协议处理
实现: WebSocket协议 + 音频编解码 + ESP32通信
```
**问题**: 文件体积大，WebSocket协议处理与业务逻辑耦合

---

## 四、Seam 质量评估

### 良好设计的 Seam

| Seam 位置 | 质量 | 理由 |
|-----------|------|------|
| `agent/intent.py` ↔ `voice_agent.py` | ⭐⭐⭐ | 清晰的后处理接口，测试友好 |
| `app/mcp_registry.py` ↔ `voice_agent._build_brain` | ⭐⭐⭐ | 重构后分离良好，单职责 |
| `skills/*` ↔ `mcp_common.py` | ⭐⭐⭐ | 共享工具层，低耦合 |
| `app/auth.py` ↔ `voice_server.py` | ⭐⭐ | 认证逻辑封装良好 |

### 问题 Seam

| Seam 位置 | 问题 | 建议 |
|-----------|------|------|
| `voice_server.py` ↔ `voice_agent.py` | 紧耦合，互相导入 | 引入中间层 `agent_pipeline.py` |
| `app/state.py` 全局状态 | 隐式共享，难测试 | 改为依赖注入或上下文对象 |
| `agent/system_msg.py` ↔ `app/mcp_gate.py` | 双向依赖风险 | 提取 `MCP_SYSTEM_PROMPTS` 到独立常量模块 |
| `voice_agent.py` 全局变量 | `_brains`, `_brain_lock` 等散落在模块顶层 | 封装为 `BrainManager` 类 |

### Seaming 原则遵循情况

```
✅ "一个适配器意味着假想 seam，两个适配器意味着真实 seam"
   - MCP 注册表确实需要支持 core/all/custom 三种 profile

✅ "接口是测试表面"
   - agent/intent.py 可独立测试（无外部依赖）
   - app/mcp_registry.py 可 mock 测试

❌ "接受依赖，不创建依赖"
   - voice_server.py 直接实例化 ThreadPoolExecutor（全局）
   - voice_agent.py 创建全局 requests.Session

❌ "返回结果，不产生副作用"
   - 多处直接修改全局状态（_intent_cache, _brains 等）
   - 应为纯函数 + 显式副作用管理
```

---

## 五、高杠杆模块评估

| 模块 | 杠杆率 | 评估 |
|------|--------|------|
| `app/mcp_registry.py` | ⭐⭐⭐⭐⭐ | 一行 resolve() 控制20+技能加载 |
| `agent/intent.py` | ⭐⭐⭐⭐ | 3函数处理ASR后处理全部逻辑 |
| `mcp_common.py` | ⭐⭐⭐⭐ | 20个skill共享工具，消除重复 |
| `app/llm_config.py` | ⭐⭐⭐ | 支持ARK/Ollama/GLM多后端 |
| `agent/cache.py` | ⭐⭐⭐ | 意图缓存消除重复LLM调用 |
| `agent/retry.py` | ⭐⭐⭐ | 统一重试策略，多处复用 |
| `app/state.py` | ⭐⭐ | 被大量导入，但职责混杂 |

**高杠杆模块设计质量**: 大部分优秀，但 `app/state.py` 作为高杠杆模块却职责不清，是主要问题。

---

## 六、信息隐藏评估

### 隐藏良好

| 知识领域 | 隐藏位置 | 说明 |
|----------|----------|------|
| ASR后处理正则 | `agent/intent.py` | `_WAKE_STRIP_RE`, `_LOW_INTENT_*` 全部私有 |
| 意图分类映射 | `agent/intent.py` + `voice_agent._normalize_intent` | 关键词→MCP名映射集中管理 |
| MCP配置结构 | `app/mcp_registry.py` | ALL_MCP 字典对外隐藏 |
| 缓存淘汰策略 | `agent/cache.py` | LRU + TTL 对调用方透明 |

### 信息泄露

| 泄露内容 | 位置 | 影响 |
|----------|------|------|
| `_brains` 字典 | `voice_agent.py` 模块级 | 调用方需理解大脑缓存生命周期 |
| `_intent_cache` | `voice_agent.py` 模块级 | 缓存状态外部可见，难测试 |
| `ALL_MCP` 配置 | `app/mcp_registry.py` 模块级 | 调用方知晓内部实现细节 |
| 全局 `_session` (requests) | `voice_agent.py` 第110行 | 连接池配置全局可见 |
| `_io_pool` 线程池 | `voice_server.py` 第131行 | 资源配置散落在入口文件 |

---

## 七、架构异味 (Architecture Smells)

### 1. 上帝模块 (God Modules)

**voice_server.py** (3829行)
- 同时负责: HTTP路由、WebSocket、MQTT启动、调度器、指标、缓存
- **违反**: 单一职责原则
- **风险**: 变更困难，测试困难，维护成本高

**voice_agent.py** (2589行)
- 同时负责: 意图分类、大脑构建、MCP解析、历史管理、重试逻辑
- **违反**: 高内聚原则
- **风险**: 意图分类逻辑膨胀（30+关键词规则）

### 2. 依赖循环风险

```
voice_server.py → voice_agent.py → app.llm_config
voice_server.py → app.mcp_registry → app.mcp_gate → app.env_catalog
```
当前无显式循环，但 `voice_agent` 与 `app.*` 的交互日益紧密，需警惕。

### 3. 特性嫉妒 (Feature Envy)

`voice_agent.py` 中大量调用 `app.*` 模块：
```python
from app.llm_config import resolve as resolve_llm
from app.mcp_registry import resolve as resolve_mcps
from app.brain_health import _brain_is_warm, _warmup_brain
```
**问题**: Agent 模块过度依赖 App 模块，违反分层架构。

### 4. _shotgun Surgery (霰弹式手术) 风险

意图分类规则散落在 `voice_agent.py` 的 `_normalize_intent()` 函数（第252-279行）：
```python
elif "music" in raw: return "magic-music"
elif "remind" in raw: return "magic-reminder"
# ... 30+ 条规则
```
**问题**: 新增技能需同时修改多处（`mcp_gate.py`, `system_msg.py`, `_normalize_intent()`）。

### 5. 全局状态过多

```python
# voice_agent.py 模块级全局
_brains = {}              # 大脑缓存
_intent_cache = OrderedDict()  # 意图缓存
_session = requests.Session()     # HTTP连接池
_io_pool = ThreadPoolExecutor()   # 线程池 (在 voice_server.py)
```
**问题**: 难以测试、难以并行、状态污染风险。

---

## 八、架构改进建议

### 优先级 1: 拆分上帝模块

**目标**: 将 `voice_server.py` 和 `voice_agent.py` 拆分为职责单一的子模块

#### 方案 A: 按职责拆分

```
charlie/
├── voice_server.py          # 仅保留 FastAPI 应用创建 + 路由注册
├── voice_agent.py           # 核心管道编排
├── app/
│   ├── routes/              # 路由模块
│   │   ├── voice.py         # /api/voice 路由
│   │   ├── chat.py          # /api/chat 路由
│   │   ├── reminders.py     # /api/reminders 路由
│   │   └── system.py        # 系统路由
│   ├── schedulers/          # 后台调度器
│   │   ├── reminder_scheduler.py
│   │   ├── evolution_scheduler.py
│   │   └── decision_engine.py
│   ├── lifecycle.py         # lifespan 生命周期管理
│   └── state.py             # 保持现状（但简化）
├── agent/
│   ├── pipeline.py          # 新: 意图→大脑→动作完整管道
│   ├── intent_classifier.py # 新: 从 voice_agent 抽出意图分类
│   ├── brain_builder.py     # 新: 从 voice_agent 抽出大脑构建
│   ├── intent.py            # 保持（深度好）
│   └── ...                  # 其他保持
```

#### 方案 B: 引入管道对象

```python
# agent/pipeline.py
class VoicePipeline:
    """语音处理完整管道: ASR → 意图 → 大脑 → 动作 → TTS"""
    
    def __init__(self, intent_classifier, brain_manager, asr_tts, history):
        self.classifier = intent_classifier
        self.brain = brain_manager
        self.audio = asr_tts
        self.history = history
    
    async def process(self, audio_data: bytes) -> AudioResponse:
        # 完整管道逻辑
        pass
```

**理由**: 符合 "深度模块" 原则 — 调用方只需 `pipeline.process(audio)` 一行。

### 优先级 2: 状态对象化

**目标**: 将模块级全局变量封装为类

```python
# agent/brain_manager.py
class BrainManager:
    """大脑构建与管理"""
    
    def __init__(self):
        self._brains = {}
        self._failures = 0
        self._lock = threading.Lock()
    
    def get_or_build(self, mcp_set: str) -> Assistant:
        # 缓存 + 熔断 + 重建逻辑
        pass

# agent/intent_cache.py
class IntentCache:
    """意图分类缓存"""
    
    def __init__(self, max_size=100, ttl=3600):
        self._cache = OrderedDict()
        self._max = max_size
        self._ttl = ttl
        self._lock = threading.Lock()
    
    def get(self, text: str) -> str | None:
        pass
```

**理由**: 提高可测试性（可实例化多个副本），消除全局状态污染。

### 优先级 3: 消除霰弹式手术

**目标**: 将意图分类规则外化为配置

```python
# agent/intent_rules.py
INTENT_RULES = [
    {"keywords": {"天气", "气温", "下雨"}, "mcp": "amap-maps"},
    {"keywords": {"音乐", "歌", "播放"}, "mcp": "magic-music"},
    {"keywords": {"提醒", "定时"}, "mcp": "magic-reminder"},
    # ... 其他规则
]

def classify_intent(text: str) -> str:
    for rule in INTENT_RULES:
        if rule["keywords"] & set(text):
            return rule["mcp"]
    return "none"
```

**理由**: 新增技能只需添加规则条目，无需修改多处代码。

### 优先级 4: 接口深化

**目标**: 增加深度模块，减少浅层调用

#### 建议: 创建 `agent/brain_orchestrator.py`

```python
class BrainOrchestrator:
    """大脑编排 — 隐藏构建、缓存、熔断、重试的复杂性"""
    
    def process(self, text: str, context: ConversationContext) -> Response:
        """一行调用完成完整大脑处理"""
        pass
```

**杠杆率提升**: 调用方只需了解 `orchestrator.process(text, context)`，无需关心：
- 内存检查
- LLM 配置选择
- MCP 解析
- 失败熔断
- 结果缓存

### 优先级 5: 修复 Seam 顺序

当前存在 **反向依赖**:
```
voice_server.py (高层) → voice_agent.py (中层) → app.* (底层)
voice_agent.py (中层) → app.llm_config (底层)
```

这导致 Agent 层过于依赖 App 层。建议：
1. 将 `app.llm_config` 提升为独立配置层
2. `voice_agent.py` 通过接口接收配置（依赖注入）
3. 消除 `voice_agent` 对 `app.*` 的直接导入

---

## 九、总结与建议优先级

| 优先级 | 改进项 | 预估收益 | 风险 |
|--------|--------|----------|------|
| P0 | 拆分 `voice_server.py` | 高 (降低维护成本) | 中 (需回归测试) |
| P0 | 拆分 `voice_agent.py` | 高 (提升可测试性) | 中 |
| P1 | 状态对象化 | 中 (提升可测试性) | 低 |
| P1 | 意图规则外化 | 中 (消除霰弹手术) | 低 |
| P2 | 创建管道对象 | 高 (提升深度) | 中 |
| P2 | 修复依赖顺序 | 低 (架构整洁) | 高 (需重构大量代码) |

**核心建议**: 优先处理 P0 的两处上帝模块拆分，这是当前架构最大的技术债。建议在拆分过程中同步引入管道对象（P2），以确保拆分后仍能保持深度模块的特性。

---

*报告生成时间: 2026-08-14*  
*基于代码版本: charlie/ (开发源)*
