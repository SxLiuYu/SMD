# Charlie 智能开发系统

## 概述

**Charlie 智能开发系统** 是一个结合多 Agent 协作、Matt Pocock Skills 和智能搜索的开发辅助工具。

### 核心特性

| 特性 | 说明 |
|------|------|
| **智能需求分类** | 自动识别评估/开发/测试/重构四类需求 |
| **动态技能组合** | 根据需求类型自动选择最佳 Skill 组合 |
| **并行 Agent 执行** | 多 Agent 同时工作，加速任务完成 |
| **搜索集成** | 支持 Tavily 和 SearXNG 搜索（可选） |
| **真实 Skill 调用** | 直接读取和执行 Matt Pocock Skills |

---

## 快速开始

### 基本用法

```bash
# 智能执行（自动分类 + 组合技能 + 并行执行）
node scripts/charlie-smart-dev.js "评估 voice_agent.py 的代码质量"
node scripts/charlie-smart-dev.js "实现新的天气查询功能"
node scripts/charlie-smart-dev.js "修复 ASR 识别率低的问题"
node scripts/charlie-smart-dev.js "重构 MCP 注册表模块"
```

### 其他命令

```bash
# 仅显示分类结果
node scripts/charlie-smart-dev.js classify "这个 PR 怎么样"

# 列出所有可用 Skills
node scripts/charlie-smart-dev.js skills

# 搜索状态管理
node scripts/charlie-smart-dev.js search status
node scripts/charlie-smart-dev.js search on    # 启用搜索
node scripts/charlie-smart-dev.js search off   # 禁用搜索
```

---

## 需求分类

系统自动将需求分为四类：

| 类型 | 关键词 | 典型场景 | 技能组合 |
|------|--------|---------|---------|
| **evaluation** | 评估、review、检查、分析 | 代码评审、架构分析、质量检查 | code-review, codebase-design, grilling |
| **development** | 实现、开发、添加、create | 新功能开发、模块实现 | implement, tdd, codebase-design |
| **testing** | 测试、debug、fix、验证 | Bug 修复、测试编写、验证 | tdd, diagnosing-bugs, code-review |
| **refactoring** | 重构、优化、改进、清理 | 代码重构、架构优化、技术债清理 | codebase-design, improve-codebase-architecture, tdd |

### 分类示例

```bash
# 评估类
node scripts/charlie-smart-dev.js classify "评估这段代码的质量"
# → evaluation (100%)

# 开发类
node scripts/charlie-smart-dev.js classify "实现用户登录功能"
# → development (100%)

# 测试类
node scripts/charlie-smart-dev.js classify "修复 ASR 识别问题"
# → testing (50%) 或 development (50%) - 取决于上下文

# 重构类
node scripts/charlie-smart-dev.js classify "重构音频处理模块"
# → refactoring (100%)
```

---

## 搜索集成

### 支持的服务

| 服务 | 说明 | 配置 |
|------|------|------|
| **Tavily** | AI 优化的网页搜索 | 需要 `TAVILY_API_KEY` |
| **SearXNG** | 自建搜索引擎实例 | 需要 `SEARXNG_URL` |

### 启用搜索

```bash
# 1. 设置环境变量
export TAVILY_API_KEY="your-api-key"
# 或
export SEARXNG_URL="http://localhost:8080"

# 2. 启用搜索
node scripts/charlie-smart-dev.js search on

# 3. 查看状态
node scripts/charlie-smart-dev.js search status
```

### 搜索用途

搜索功能在以下场景自动启用：
- **评估类**：搜索最佳实践、类似项目
- **开发类**：搜索 API 文档、技术方案
- **重构类**：搜索重构模式、架构案例

---

## 任务分解示例

### 示例 1：评估需求

```
需求: "评估 voice_agent.py 的代码质量"

分类: evaluation (100%)
技能: code-review, codebase-design, grilling
搜索: ✅ 启用

任务分解:
  🔴 [1] 审查员 (code-review): 评估需求
  🟡 [2] 架构师 (codebase-design): 分析架构影响
  🟡 [3] 安全专家 (grilling): 检查安全风险
```

### 示例 2：开发需求

```
需求: "实现新的天气查询功能"

分类: development (100%)
技能: implement, tdd, codebase-design
搜索: ✅ 启用

任务分解:
  🔴 [1] 产品经理 (implement): 编写规格说明
  🟡 [2] 开发者 (tdd): 实现功能
  🟡 [3] 测试工程师 (codebase-design): 编写测试用例
```

### 示例 3：重构需求

```
需求: "重构 MCP 注册表模块"

分类: refactoring (100%)
技能: codebase-design, improve-codebase-architecture, tdd
搜索: ✅ 启用

任务分解:
  🔴 [1] 架构师 (codebase-design): 分析重构范围
  🟡 [2] 设计师 (improve-codebase-architecture): 设计重构方案
  🟡 [3] 开发者 (tdd): 实施重构
  🟡 [4] 测试工程师 (codebase-design): 验证重构结果
```

---

## 配置文件

`.smart-dev.json` - 系统配置

```json
{
  "search": {
    "enabled": false,
    "provider": "tavily",
    "maxResults": 5
  },
  "agents": {
    "maxParallel": 5,
    "timeout": 60000
  },
  "skills": {
    "directory": ".agents/skills",
    "autoLoad": true
  }
}
```

---

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    Charlie 智能开发系统                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  需求输入    │ →  │  分类器      │ →  │  技能组合    │  │
│  │  Requirement │    │  Classifier  │    │  Combo       │  │
│  └──────────────┘    └──────────────┘    └──────┬───────┘  │
│                                                 │           │
│                                          ┌──────▼───────┐  │
│                                          │  任务分解    │  │
│                                          │ Decomposer   │  │
│                                          └──────┬───────┘  │
│                                                 │           │
│                    ┌────────────────────────────┼───────────┤
│                    │                │           │           │
│              ┌─────▼─────┐    ┌─────▼─────┐ ┌───▼─────┐    │
│              │  Agent 1  │    │  Agent 2  │ │ Agent N │    │
│              │ (并行)    │    │ (并行)    │ │ (并行)  │    │
│              └─────┬─────┘    └─────┬─────┘ └───┬─────┘    │
│                    │                │           │           │
│                    └────────────────┴───────────┘           │
│                             │                              │
│                    ┌────────▼────────┐                     │
│                    │   结果汇总      │                     │
│                    │  Summary        │                     │
│                    └─────────────────┘                     │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Matt Pocock Skills                     │   │
│  │  .agents/skills/tdd/SKILL.md                        │   │
│  │  .agents/skills/code-review/SKILL.md                │   │
│  │  .agents/skills/diagnosing-bugs/SKILL.md            │   │
│  │  ... (35 个 skills)                                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Search Engines                         │   │
│  │  • Tavily (AI-optimized web search)                 │   │
│  │  • SearXNG (self-hosted metasearch)                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 与 oh-my-opencode 的对比

| 功能 | DSH 智能系统 | OpenCode CLI |
|------|-------------|--------------|
| 需求分类 | ✅ 自动 | ❌ 需手动 |
| 技能组合 | ✅ 动态选择 | ✅ 固定 agent |
| 并行执行 | ✅ 多 agent | ✅ Team Mode |
| 搜索集成 | ✅ Tavily/SearXNG | ❌ 需额外配置 |
| 真实 Skill | ✅ 读取 SKILL.md | ⚠️ 内置模式 |
| 部署方式 | Node.js 脚本 | OpenCode 插件 |

---

## 使用建议

### 何时使用智能系统

- ✅ 需求明确，需要快速分析和执行
- ✅ 需要并行处理多个子任务
- ✅ 需要搜索辅助信息
- ✅ 希望自动化技能选择

### 何时使用 OpenCode CLI

- ✅ 需要完整的 oh-my-opencode 功能（ultrawork, hyperplan）
- ✅ 需要 Team Mode（最多 8 个并行成员）
- ✅ 需要 LSP 集成、Hashline Edits 等高级功能
- ✅ 需要与 OpenCode 生态集成

---

## 故障排除

### 问题：分类不准确

**原因**：关键词匹配规则可能不够完善  
**解决**：
```bash
# 使用 classify 命令查看详细评分
node scripts/charlie-smart-dev.js classify "你的需求"

# 查看评分详情，调整关键词
```

### 问题：搜索失败

**原因**：API Key 未配置或服务不可用  
**解决**：
```bash
# 检查状态
node scripts/charlie-smart-dev.js search status

# 配置 API Key
export TAVILY_API_KEY="your-key"

# 或使用 SearXNG
export SEARXNG_URL="http://localhost:8080"
```

### 问题：Skill 未找到

**原因**：Skill 目录配置错误  
**解决**：
```bash
# 检查 skills 目录
ls .agents/skills/

# 重新安装 skills
npx skills@latest add mattpocock/skills
```

---

*Created: 2026-08-14*
*Combining: oh-my-opencode + Matt Pocock Skills + Search Engines*
