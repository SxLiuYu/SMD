# Agent Skills

## 🧠 Charlie 智能开发系统 (DSH 集成版)

> **已集成到 DSH** - 直接说需求即可自动分类、组合技能、并行执行

### 使用方法

**方式 1: DSH 对话（推荐）**
```
直接用自然语言描述需求：
- "评估 voice_agent.py 的代码质量"
- "实现新的天气查询功能"
- "修复 ASR 识别率低的问题"
- "重构 MCP 注册表模块"
```

**方式 2: 命令行**
```bash
node scripts/charlie-smart-dev.js "需求描述"
node scripts/charlie-smart-dev.js classify "这个 PR 怎么样"
node scripts/charlie-smart-dev.js skills
node scripts/charlie-smart-dev.js search status
```

### 智能分类与技能组合

| 需求类型 | 触发词 | 自动选择的 Skills | 搜索 |
|---------|--------|------------------|------|
| **evaluation** | 评估、review、检查、分析 | code-review + codebase-design + grilling | ✅ |
| **development** | 实现、开发、添加、create | implement + tdd + codebase-design | ✅ |
| **testing** | 测试、debug、fix、验证、bug | tdd + diagnosing-bugs + code-review | ❌ |
| **refactoring** | 重构、优化、改进、清理 | codebase-design + improve-codebase-architecture + tdd | ✅ |

### 执行流程

```
用户需求 → 自动分类 → 选择技能组合 → 任务分解 → 并行执行 → 结果汇总
   ↓           ↓            ↓             ↓           ↓           ↓
"评估..."  evaluation   code-review   审查员      并行执行    3 个发现
                      codebase-design 架构师       (3 agent)   3 个建议
                      grilling        安全专家
```

## Matt Pocock Skills (DSH 内置)

- **tdd** - 测试驱动开发，red-green-refactor 循环
- **code-review** - 双轴审查：Standards + Spec
- **diagnosing-bugs** - 硬 bug 诊断，构建反馈循环优先
- **domain-modeling** - 领域模型构建，Glossary + ADRs
- **grilling** - 压力测试想法，设计树探索
- **implement** - 基于 spec/tickets 实现
- **prototype** - 快速原型验证设计假设
- **to-spec** - 将需求转为可执行规格
- **codebase-design** - 深层模块设计词汇（interface, seam, depth, leverage）
- **improve-codebase-architecture** - 扫描架构深化机会
- **charlie-smart-dev** ⭐ - 智能开发系统（自动分类 + 技能组合）

## oh-my-opencode 原生功能 (OpenCode CLI)

> 以下功能在 OpenCode CLI 中完整可用

- **ultrawork** / **ulw** - 激活所有 agent 并行工作，持续直到完成
- **hyperplan** / **hpp** - 对抗性多 agent 规划，5 个 hostile agents 交叉审查
- **work-with-pr** - 完整 PR 生命周期：实现 → 测试 → PR → 验证 → 合并
- **security-research** - 并行安全审计，3 hunters + 2 PoC engineers
- **remove-deadcode** - 批量移除未使用代码，LSP 验证安全性

## 使用示例

### 示例 1：评估需求
```
用户: "评估 voice_agent.py 的代码质量"

系统:
📊 需求分类分析:
   类型: evaluation (100%)
   说明: 评估类：需要分析代码质量、架构设计、安全审查等

🔧 选择的技能组合:
   1. code-review - 双轴审查
   2. codebase-design - Deep Module 设计
   3. grilling - 压力测试

📋 任务分解:
   🔴 [1] 审查员: 评估代码质量
   🟡 [2] 架构师: 分析架构影响
   🟡 [3] 安全专家: 检查安全风险

🎉 执行完成
   发现: 12 个问题
   建议: 10 个改进点
```

### 示例 2：开发需求
```
用户: "实现新的天气查询功能"

系统:
📊 需求分类分析:
   类型: development (100%)
   说明: 开发类：需要实现新功能、模块、接口等

🔧 选择的技能组合:
   1. implement - 功能实现
   2. tdd - 测试驱动开发
   3. codebase-design - 架构设计

📋 任务分解:
   🔴 [1] 产品经理: 编写规格说明
   🟡 [2] 开发者: 实现核心逻辑
   🟡 [3] 测试工程师: 编写测试用例
```

### 示例 3：测试需求
```
用户: "修复 ASR 识别率低的问题"

系统:
📊 需求分类分析:
   类型: testing (85%)
   说明: 测试类：需要诊断问题、编写测试、验证修复

🔧 选择的技能组合:
   1. tdd - 测试驱动开发
   2. diagnosing-bugs - Bug 诊断
   3. code-review - 代码审查

📋 任务分解:
   🔴 [1] 调试专家: 诊断 ASR 问题根因
   🟡 [2] 开发者: 实现修复
   🟡 [3] 测试工程师: 验证修复效果
```

### 示例 4：重构需求
```
用户: "重构 MCP 注册表模块"

系统:
📊 需求分类分析:
   类型: refactoring (100%)
   说明: 重构类：需要重构代码、优化架构、清理技术债

🔧 选择的技能组合:
   1. codebase-design - Deep Module 设计
   2. improve-codebase-architecture - 架构深化
   3. tdd - 测试驱动重构

📋 任务分解:
   🔴 [1] 架构师: 分析重构范围
   🟡 [2] 设计师: 设计重构方案
   🟡 [3] 开发者: 实施重构
   🟡 [4] 测试工程师: 验证重构结果
```

## 搜索集成

### 启用搜索
```bash
# 检查状态
node scripts/charlie-smart-dev.js search status

# 启用搜索
node scripts/charlie-smart-dev.js search on

# 配置 API Key
export TAVILY_API_KEY="your-key"
# 或
export SEARXNG_URL="http://localhost:8080"
```

### 搜索用途
- **评估类**：搜索最佳实践、类似项目
- **开发类**：搜索 API 文档、技术方案
- **重构类**：搜索重构模式、架构案例

## Workflow 组合

| 场景 | 推荐流程 |
|------|---------|
| 新功能开发 | 直接说需求 → 自动开发流程 |
| Bug 修复 | 直接说需求 → 自动测试流程 |
| 架构重构 | 直接说需求 → 自动重构流程 |
| 代码审查 | 直接说需求 → 自动评估流程 |
| 复杂规划 | `charlie-smart-dev` + `hyperplan` |
