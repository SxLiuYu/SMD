# Charlie 项目自定义开发模式指南

## 概述

本指南介绍如何在 DSH 环境中使用结合 **oh-my-opencode ultrawork** 和 **Matt Pocock Skills** 的自定义开发模式。

### 核心设计理念

```
oh-my-opencode (多 agent 并行) + Matt Pocock (工程实践) = 高效开发流程
```

| 维度 | oh-my-opencode | Matt Pocock | 结合效果 |
|------|---------------|-------------|---------|
| 执行方式 | 并行 agent | 单 agent  disciplined | 并行 + 纪律 |
| 任务分解 | 自动 | 人工 | 自动 + 验证 |
| 质量保证 | 无 | TDD/Code Review | 并行执行 + 严格审查 |
| 架构设计 | 无 | Deep Modules | 并行分析 + 深度设计 |

---

## 快速开始

### 基本用法

```bash
# 在 DSH 中直接说
"用 ultrawork 重构 voice_agent.py"
"用 tdd 实现天气查询功能"
"用 diagnose 诊断 ASR bug"

# 或在终端运行
node scripts/charlie-dev.js ultrawork "任务描述"
node scripts/charlie-dev.js tdd "功能描述"
```

### 六种开发模式

| 模式 | 命令 | 用途 | 结合能力 |
|------|------|------|---------|
| **ultrawork** | `charlie-dev.js ultrawork <任务>` | 多 agent 并行执行 | oh-my-opencode + 自动分解 |
| **tdd** | `charlie-dev.js tdd <功能>` | 测试驱动开发 | Matt Pocock TDD 原则 |
| **hyperplan** | `charlie-dev.js hyperplan <主题>` | 对抗性规划 | 5 个 hostile critics |
| **diagnose** | `charlie-dev.js diagnose <bug>` | Bug 诊断 | feedback loop 构建 |
| **review** | `charlie-dev.js review <目标>` | 代码审查 | 双轴审查 (Standards + Spec) |
| **design** | `charlie-dev.js design <主题>` | 架构设计 | Deep Module 原则 |

---

## 模式详解

### 1. Ultrawork 模式

**模拟 oh-my-opencode 的核心能力**

```bash
node scripts/charlie-dev.js ultrawork "重构 voice_agent.py"
```

**执行流程:**
1. **Phase 1 - 任务分解**: 自动将任务拆分为子任务
2. **Phase 2 - 并行执行**: 多个 agent 同时工作
3. **Phase 3 - 结果汇总**: 统一报告和发现

**角色分工:**
- 架构师: 分析代码结构和依赖
- 设计师: 设计新架构方案
- 开发者: 实现代码
- 测试工程师: 验证结果

**适用场景:**
- 大型重构
- 架构分析
- 代码审计
- 性能优化

---

### 2. TDD 模式

**Matt Pocock 的测试驱动开发**

```bash
node scripts/charlie-dev.js tdd "实现天气查询功能"
```

**执行流程:**
1. **RED**: 编写失败测试
   - 确定测试 seam（public interface）
   - 编写 failing test
   - 确认测试失败

2. **GREEN**: 最小实现
   - 只写足够通过测试的代码
   - 不提前优化
   - 确认测试通过

3. **REFACTOR**: 重构
   - 保持测试通过
   - 消除重复
   - 改进设计

**Matt Pocock 原则:**
- 测试验证行为，不验证实现
- 只在 agreed seams 上测试
- 一个 slice 一个循环

---

### 3. Hyperplan 模式

**对抗性多 agent 规划**

```bash
node scripts/charlie-dev.js hyperplan "设计新的 MCP 技能架构"
```

**5 个 Hostile Critics:**

| Critic | 攻击方向 | 立场 |
|--------|---------|------|
| Pragmatist Skeptic | 过度工程 | 删除复杂性 |
| Integration Tester | 遗漏边界 | 寻找交互风险 |
| Architect Strategist | 结构缺陷 | 发现架构问题 |
| Creative Challenger | 常规思维 | 打破假设 |
| Security Hunter | 安全风险 | 攻击面分析 |

**适用场景:**
- 架构决策
- 高风险重构
- 新系统设计

---

### 4. Diagnose 模式

**硬 Bug 诊断流程**

```bash
node scripts/charlie-dev.js diagnose "ASR 识别率低"
```

**三阶段诊断:**

1. **Phase 1 - 构建反馈循环**
   - 创建 tight red-capable loop
   - 方法: failing test / curl script / CLI invocation
   - 目标: 30 秒内能复现问题

2. **Phase 2 - 复现 + 最小化**
   - 运行 loop，确认问题出现
   - 逐个删除输入/配置，直到仍 red
   - 找到最小复现场景

3. **Phase 3 - 假设 + 验证**
   - 基于证据提出假设
   - 设计验证实验
   - 确认根本原因

**Matt Pocock 原则:**
- 先构建 feedback loop，再 hypothesize
- Loop 必须 tight + red-capable + deterministic

---

### 5. Review 模式

**双轴代码审查**

```bash
node scripts/charlie-dev.js review "最近的 PR"
```

**双轴审查:**

| 轴 | 审查内容 |
|----|---------|
| **Standards** | 代码风格、命名规范、架构模式、错误处理 |
| **Spec** | 需求覆盖、边界条件、性能考量、安全性 |

**适用场景:**
- PR 审查
- 代码质量检查
- 发布前验证

---

### 6. Design 模式

**Deep Module 架构设计**

```bash
node scripts/charlie-dev.js design "MCP 技能系统"
```

**核心概念:**

| 概念 | 定义 |
|------|------|
| **Interface** | 调用者需要知道的一切 |
| **Implementation** | 模块内部逻辑 |
| **Seam** | 接口所在的位置 |
| **Depth** | 接口背后隐藏的行为量 |
| **Leverage** | 调用者获得的能力 |
| **Locality** | 维护者获得的位置性 |

**设计检查清单:**
- □ 能否减少方法数量?
- □ 能否简化参数?
- □ 能否隐藏更多复杂性?
- □ 删除此模块后复杂度是否消失?

---

## 组合使用

### 完整开发流程

```bash
# 1. 架构设计
node scripts/charlie-dev.js design "新模块架构"

# 2. 对抗性规划
node scripts/charlie-dev.js hyperplan "模块设计评审"

# 3. TDD 实现
node scripts/charlie-dev.js tdd "实现核心功能"

# 4. 并行代码审查
node scripts/charlie-dev.js review "实现代码"

# 5. Bug 修复（如有）
node scripts/charlie-dev.js diagnose "发现的问题"
```

### 快速分析流程

```bash
# 快速分析整个项目
node scripts/charlie-dev.js ultrawork "分析项目架构"

# 分析特定模块
node scripts/charlie-dev.js ultrawork "分析 ASR 模块"

# 安全审计
node scripts/charlie-dev.js ultrawork "安全检查"
```

---

## 与 OpenCode CLI 的对比

| 功能 | DSH (本文档) | OpenCode CLI |
|------|-------------|--------------|
| ultrawork | ✅ 模拟实现 | ✅ 原生支持 |
| hyperplan | ⚠️ 框架展示 | ✅ 5 个真实 hostile agents |
| Team Mode | ✅ 并行执行 | ✅ 最多 8 成员 |
| Hashline Edits | ❌ | ✅ 内容哈希验证 |
| LSP 集成 | ❌ | ✅ IDE 级别导航 |
| AST-Grep | ❌ | ✅ 25 种语言搜索 |
| Tmux 集成 | ❌ | ✅ 完整终端控制 |

**建议:**
- 日常开发 → DSH + charlie-dev.js
- 复杂重构 → OpenCode CLI + ultrawork
- 安全审计 → OpenCode CLI + security-research

---

## 最佳实践

### 1. 任务描述要具体

```
✅ 好: "ultrawork 重构 voice_agent.py 中的意图识别逻辑"
❌ 差: "ultrawork 重构代码"
```

### 2. 结合领域模型

在执行前确保 `CONTEXT.md` 已更新：
```bash
# 检查领域模型
cat CONTEXT.md

# 如需更新
node scripts/charlie-dev.js design "更新领域模型"
```

### 3. 分阶段执行

复杂任务分阶段：
```bash
# Phase 1: 分析
node scripts/charlie-dev.js ultrawork "分析 voice_agent 模块"

# Phase 2: 设计
node scripts/charlie-dev.js design "voice_agent 重构方案"

# Phase 3: 实现
node scripts/charlie-dev.js tdd "实现重构代码"
```

### 4. 记录发现

将重要发现添加到 `docs/adr/`：
```bash
mkdir -p docs/adr
cat > docs/adr/0001-voice-agent-refactor.md << 'EOF'
# ADR-0001: Voice Agent 重构

## 状态
Accepted

## 背景
voice_agent.py 2723 行，职责过多

## 决策
拆分为 intent.py, brain.py, tools.py

## 后果
- 优点: 可测试性提升，职责清晰
- 缺点: 需要迁移工作
EOF
```

---

## 故障排除

### 问题: 任务分解不准确

**解决:** 提供更具体的任务描述
```bash
# 不够具体
node scripts/charlie-dev.js ultrawork "重构"

# 更具体
node scripts/charlie-dev.js ultrawork "重构 voice_agent.py 中的 FastPath 逻辑"
```

### 问题: 发现与建议太泛

**解决:** 结合具体代码文件
```bash
# 指定文件
node scripts/charlie-dev.js ultrawork "分析 charlie/agent/intent.py"
```

### 问题: 需要更多细节

**解决:** 结合其他模式
```bash
# 先设计，再实现
node scripts/charlie-dev.js design "MCP 注册表优化"
node scripts/charlie-dev.js tdd "实现新的注册表"
```

---

## 总结

| 模式 | 核心能力 | 适用场景 |
|------|---------|---------|
| ultrawork | 并行执行 | 大型任务、分析、重构 |
| tdd | 测试驱动 | 新功能、核心逻辑 |
| hyperplan | 对抗性规划 | 架构决策、高风险变更 |
| diagnose | Bug 诊断 | 复杂问题、性能问题 |
| review | 双轴审查 | PR、发布前检查 |
| design | Deep Module | 架构设计、模块拆分 |

**记住**: 这些模式可以组合使用，形成完整的开发工作流。

---

*Created: 2026-08-14*
*Combined: oh-my-opencode + Matt Pocock Skills*
