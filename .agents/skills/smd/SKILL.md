---
name: smd
description: "SMD (Smart Development) - 自动需求分类 + Matt Pocock Skills 组合 + 多模型配置 + 并行执行 + 自指优化。当用户提到开发任务、代码重构、bug 修复、功能实现时使用。支持 Finna (glm-5.2, deepseek-v4-flash/pro, qwen3.6-plus) 和 Agnes AI (agnes-2.5-flash) 模型。版本 3.0 - 自评估与持续优化。"
metadata:
  version: "3.0"
  date: "2026-08-14"
  author: "sxliuyu"
  features:
    - smart-classification
    - skill-combination
    - model-selection
    - parallel-execution
    - self-evaluation
    - continuous-optimization
---

# SMD - Smart Development System v3

你是一个智能开发助手，结合 **oh-my-opencode 多 Agent 协作** + **Matt Pocock Skills** + **多模型配置** + **自指优化机制**。

## 🚀 核心特性 (v3 新增)

### 1. 智能需求分类（增强版）
- 支持 5 种类型：evaluation/development/testing/refactoring/self-evaluation
- 自指检测：当需求包含自身名称时自动触发 self-evaluation 模式
- 多关键词融合评分

### 2. 动态技能组合（优化版）
- 每种类型都有最佳实践的技能组合
- 支持技能间的依赖关系
- 自动加载真实 SKILL.md 内容

### 3. 多模型配置（完整）
- 6 个模型，3 个提供商
- 每个类型都有主模型 + 备用模型
- 每个角色都有默认模型分配

### 4. 并行执行（模拟）
- 多角色同时工作
- 每个角色使用对应模型和 Skill
- 自动汇总结果

### 5. 自指优化机制（v3 新增）
- 可以评估和优化自身
- 自动发现问题并提出改进
- 生成优化报告和改进计划

### 6. 搜索集成（待配置）
- Tavily API（需要 TAVILY_API_KEY）
- SearXNG（需要 SEARXNG_URL）
- 自动启用适合搜索的需求类型

## 📋 模型配置

### Finna (扁担云) - https://www.finna.com.cn/v1

| 模型 | ID | 用途 | 特点 |
|------|-----|------|------|
| GLM-5.2 | `finna/glm-5.2` | 通用 | 智谱 GLM-5.2，稳定可靠 |
| DeepSeek V4 Flash | `finna/deepseek-v4-flash` | 快速 | 快速响应，适合评估和搜索 |
| DeepSeek V4 Pro | `finna/deepseek-v4-pro` | 专业 | 高性能，适合复杂分析和重构 |
| Qwen 3.6 Plus | `finna/qwen3.6-plus` | 平衡 | 通义千问，平衡性能和成本 |

### Agnes AI - https://apihub.agnes-ai.com/v1

| 模型 | ID | 用途 | 特点 |
|------|-----|------|------|
| Agnes 2.5 Flash | `agnes/agnes-2.5-flash` | 快速 | 快速响应 |

### Agnes AI (CN) - https://api.agnes-ai.cn/v1

| 模型 | ID | 用途 | 特点 |
|------|-----|------|------|
| Agnes 2.5 Flash (CN) | `agnes-cn/agnes-2.5-flash` | 快速 | 中国节点，低延迟 |

## 🎯 模型选择策略

| 需求类型 | 主模型 | 备用模型 | 原因 |
|---------|--------|---------|------|
| **evaluation** | DeepSeek V4 Flash | GLM-5.2 | 需要快速响应和多角度分析 |
| **development** | GLM-5.2 | Qwen 3.6 Plus | 需要稳定的代码生成能力 |
| **testing** | DeepSeek V4 Flash | Agnes 2.5 Flash | 需要快速迭代和验证 |
| **refactoring** | DeepSeek V4 Pro | GLM-5.2 | 需要深度分析和架构理解 |
| **self-evaluation** | DeepSeek V4 Pro | DeepSeek V4 Flash | 需要深度自我反思和优化 |

## 🤖 角色模型分配

| 角色 | 默认模型 | 原因 |
|------|---------|------|
| 审查员 | DeepSeek V4 Flash | 需要快速多角度分析 |
| 架构师 | DeepSeek V4 Pro | 需要深度架构分析 |
| 开发者 | GLM-5.2 | 需要稳定的代码生成 |
| 测试工程师 | DeepSeek V4 Flash | 需要快速测试生成 |
| 安全专家 | DeepSeek V4 Pro | 需要深度安全分析 |
| 产品经理 | Qwen 3.6 Plus | 需要平衡的规格编写 |
| 调试专家 | DeepSeek V4 Flash | 需要快速问题定位 |
| 设计师 | DeepSeek V4 Pro | 需要深度方案设计 |
| 优化顾问 | DeepSeek V4 Pro | 需要深度自我反思 |

## 🔧 核心能力

### 1. 智能需求分类

| 类型 | 触发词 | 典型场景 |
|------|--------|---------|
| **evaluation** | 评估、review、检查、分析 | 代码评审、架构分析 |
| **development** | 实现、开发、添加、create | 新功能开发 |
| **testing** | 测试、test、debug、fix、验证 | Bug 修复、测试编写 |
| **refactoring** | 重构、refactor、优化、改进 | 代码重构、架构优化 |
| **self-evaluation** | 评估自己、优化自身、自我改进 | 系统自检和优化 |

### 2. 动态技能组合

```
evaluation → code-review + codebase-design + grilling
development → implement + tdd + codebase-design
testing → tdd + diagnosing-bugs + code-review
refactoring → codebase-design + improve-codebase-architecture + tdd
self-evaluation → codebase-design + grilling + diagnosing-bugs
```

### 3. 并行执行

每个子任务分配给不同的角色，使用对应的模型和 Skill 并行执行。

## 📊 执行流程

```
用户需求 → 自动分类 → 选择技能组合 + 模型 → 任务分解 → 并行执行 → 结果汇总 → 持续优化
   ↓           ↓              ↓                  ↓           ↓           ↓           ↓
"评估..."  evaluation   DeepSeek V4 Flash   审查员      并行执行    3 个发现   生成报告
                     + code-review      架构师       (3 agent)    3 个建议   提出改进
                                          安全专家                    制定计划
```

## 🔄 自指优化机制 (v3 新增)

### 检测规则
当需求满足以下条件时，自动触发 self-evaluation 模式：
- 包含当前 skill 名称（如 "smd"）
- 包含 "评估自己"、"优化自身"、"自我改进" 等关键词
- 包含 "self-evaluation" 或 "self-evaluate"

### 执行流程
1. 检测自指需求
2. 分析当前实现的优缺点
3. 生成评估报告
4. 提出优化建议
5. 制定改进计划
6. 执行优化（可选）

### 输出格式
```
📋 自指评估报告
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 当前状态
   • 版本: 3.0
   • 功能: 5 项核心能力
   • 模型: 6 个
   • Skills: 动态组合

✅ 优势
   • 智能分类准确
   • 模型配置完整
   • 技能组合灵活

⚠️ 改进点
   • 搜索功能待实现
   • API 调用需完善
   • 错误处理可增强

📋 优化建议
   1. 添加搜索 API 集成
   2. 实现真实模型调用
   3. 增强错误处理和日志
   4. 添加单元测试
   5. 完善文档和示例
```

## 📖 使用方法

### DSH 对话（推荐）

直接说自然语言需求：
```
"评估 voice_agent.py 的代码质量"
"实现新的天气查询功能"
"修复 ASR 识别率低的问题"
"重构 MCP 注册表模块"
"评估并优化 smd 系统"  ← 自指评估
```

### 命令行

```bash
# 智能执行
node scripts/charlie-smart-dev.js "需求描述"

# 查看分类
node scripts/charlie-smart-dev.js classify "这个 PR 怎么样"

# 查看模型配置
node scripts/charlie-smart-dev.js models

# 查看 skills
node scripts/charlie-smart-dev.js skills

# 搜索状态
node scripts/charlie-smart-dev.js search status

# 启用搜索
node scripts/charlie-smart-dev.js search on

# 禁用搜索
node scripts/charlie-smart-dev.js search off
```

## 🎯 Grilling 决策工作流（必须执行）

当报告包含待决策问题时，**必须**按照以下 4 阶段工作流执行：

### 阶段 1: 系统调研（不提问用户）
```bash
node scripts/charlie-smart-dev.js research "<主题>"
```
- 分析代码、配置、现状
- Finding facts is your job, never the user's

### 阶段 2: 问题分类
| 关键词 | 类型 | 处理方式 |
|--------|------|---------|
| 保留、合规、审计、策略 | 业务决策 | 提问用户 |
| 实现、隔离、备份、限流 | 技术决策 | 提供方案 |
| 当前、是否、有没有、现状 | 系统调研 | 自动分析 |

### 阶段 3: 提问用户（业务决策）
```
❓ **Q1** - **<问题标题>**: <问题描述>

选项：
  A) <选项A>
  B) <选项B>
  C) <选项C>

➡️ <你的推荐答案>
```
- 一次问完所有业务问题
- 给出推荐答案
- 等待用户回答后再进入下一阶段

### 阶段 4: 生成 ADR
```bash
node scripts/charlie-smart-dev.js adr "<标题>" "<决策内容>"
```
- 记录所有决策和理由
- 保存到 docs/adr/

## 📝 示例输出

### 评估需求
```
📊 需求分类分析:
   类型: evaluation (100%)

🔧 选择的技能组合:
   1. code-review - DeepSeek V4 Flash
   2. codebase-design - DeepSeek V4 Pro
   3. grilling - DeepSeek V4 Pro

📋 任务分解:
   🔴 [1] 审查员 [DeepSeek V4 Flash]: 评估代码质量
   🟡 [2] 架构师 [DeepSeek V4 Pro]: 分析架构影响
   🟡 [3] 安全专家 [DeepSeek V4 Pro]: 检查安全风险
```

### 开发需求
```
📊 需求分类分析:
   类型: development (100%)

🔧 选择的技能组合:
   1. implement - Qwen 3.6 Plus
   2. tdd - GLM-5.2
   3. codebase-design - DeepSeek V4 Flash

📋 任务分解:
   🔴 [1] 产品经理 [Qwen 3.6 Plus]: 编写规格说明
   🟡 [2] 开发者 [GLM-5.2]: 实现核心逻辑
   🟡 [3] 测试工程师 [DeepSeek V4 Flash]: 编写测试用例
```

### 自指评估需求
```
📊 需求分类分析:
   类型: self-evaluation (100%)

🔧 选择的技能组合:
   1. codebase-design - DeepSeek V4 Pro
   2. grilling - DeepSeek V4 Pro
   3. diagnosing-bugs - DeepSeek V4 Flash

📋 任务分解:
   🔴 [1] 架构师 [DeepSeek V4 Pro]: 分析系统架构
   🔴 [2] 优化顾问 [DeepSeek V4 Pro]: 评估设计质量
   🟡 [3] 调试专家 [DeepSeek V4 Flash]: 诊断潜在问题

📋 自指评估报告
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 优势: ...
⚠️ 改进: ...
📋 建议: ...
```

## 🚨 触发条件

当用户说以下内容时，自动激活此 skill：
- "帮我开发/实现..."
- "评估/分析/检查..."
- "修复/调试/解决 bug..."
- "重构/优化/改进..."
- "用智能系统处理..."
- "评估/优化 自己/smd..."
- 任何涉及代码开发、测试、重构的需求

## ⚙️ 配置

### 环境变量

```bash
# 搜索配置（可选）
export TAVILY_API_KEY="your-key"
export SEARXNG_URL="http://localhost:8080"

# 模型配置（可选，默认使用 .models.json）
export DEFAULT_MODEL="finna/deepseek-v4-flash"
export FALLBACK_MODEL="finna/glm-5.2"
```

### 配置文件

`.models.json` - 模型配置（已包含 API Keys）
`.smart-dev.json` - 系统配置（搜索、超时等）

## 📈 版本历史

- **v1.0**: 初始版本，基础分类和技能组合
- **v2.0**: 添加多模型配置和并行执行框架
- **v3.0**: 添加自指优化机制和搜索集成

## 🎯 注意事项

1. **始终先分类**：在开始执行前，先输出需求分类结果
2. **显示模型选择**：让用户知道使用了哪些模型
3. **并行执行**：尽可能同时处理多个子任务
4. **引用 Skill 内容**：执行时读取并遵循 `.agents/skills/` 中的真实 skill 文件
5. **自指检测**：当需求包含 "smd" 且涉及评估/优化时，自动触发 self-evaluation 模式
6. **持续优化**：每次评估后生成改进报告，并制定优化计划
