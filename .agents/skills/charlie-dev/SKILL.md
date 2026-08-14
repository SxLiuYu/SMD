---
name: charlie-dev
description: "CharlieDev (Charlie Smart Development) - 自动需求分类 + Matt Pocock Skills 组合 + 并行执行。当用户提到开发任务、代码重构、bug 修复、功能实现时使用。"
metadata:
  version: "3.0"
  date: "2026-08-14"
  author: "sxliuyu"
---

# CharlieDev - Charlie Smart Development System

结合 **oh-my-opencode 多 Agent 协作** + **Matt Pocock Skills** + **多模型配置**。

## 核心能力

### 1. 智能需求分类（扩展版）

| 类型 | 触发词 | 技能组合 |
|------|--------|---------|
| **evaluation** | 评估、review、检查、分析 | code-review + codebase-design + grilling + triage |
| **development** | 实现、开发、添加 | implement + tdd + codebase-design + to-spec + prototype + domain-modeling |
| **testing** | 测试、debug、fix、验证 | tdd + diagnosing-bugs + code-review + research |
| **refactoring** | 重构、优化、改进 | codebase-design + improve-codebase-architecture + tdd + to-tickets + domain-modeling |
| **self-evaluation** | 评估自己、优化自身 | codebase-design + grilling + diagnosing-bugs + research |

### 2. 并行执行

每个子任务分配给不同角色，使用对应模型和 Skill 并行执行。

## 使用方式

### DSH 对话（推荐）

```
"评估 voice_agent.py 的代码质量"
"实现新的天气查询功能"
"修复 ASR 识别率低的问题"
"重构 MCP 注册表模块"
"评估并优化 smd 系统"
```

### 命令行

```bash
node scripts/charlie-smart-dev.js "需求描述"
node scripts/charlie-smart-dev.js classify "这个 PR 怎么样"
node scripts/charlie-smart-dev.js models
node scripts/charlie-smart-dev.js skills
node scripts/charlie-smart-dev.js search status
```

## Grilling 决策工作流

当报告包含待决策问题时，执行 4 阶段工作流：

1. **系统调研** - `research "<主题>"`
2. **问题分类** - 业务决策→提问用户，技术决策→提供方案
3. **提问用户** - 一次问完所有业务问题，给出推荐答案
4. **生成 ADR** - `adr "<标题>" "<内容>"`

参考：`.agents/skills/grilling/SKILL.md`

## 配置

- `.models.json` - 模型配置（环境变量引用 API Keys）
- `.smart-dev.json` - 搜索和代理配置
- `.env.example` - 配置模板

## 触发条件

- "帮我开发/实现..."
- "评估/分析/检查..."
- "修复/调试/解决 bug..."
- "重构/优化/改进..."
- "用智能系统处理..."
- 任何涉及代码开发、测试、重构的需求
