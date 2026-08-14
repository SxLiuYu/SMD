# CharlieDev - Charlie Smart Development System

> Charlie 智能开发系统 - 自动需求分类 + Matt Pocock Skills 组合 + 并行执行 + Grilling 决策工作流

---

## 📋 概述

**CharlieDev (Charlie Smart Development)** 是一个结合 **oh-my-opencode 多 Agent 协作** + **Matt Pocock Skills** + **多模型配置** 的智能开发辅助系统。

### 核心特性

| 特性 | 说明 |
|------|------|
| **智能需求分类** | 自动识别评估/开发/测试/重构/自指评估五类需求 |
| **动态技能组合** | 根据需求类型自动选择最佳 Matt Pocock Skills 组合 |
| **并行 Agent 执行** | 多角色同时工作，使用不同模型加速任务完成 |
| **Grilling 决策工作流** | 4 阶段强制流程：调研→分类→提问→ADR |
| **多模型支持** | 支持 Finna (GLM/DeepSeek/Qwen) 和 Agnes AI |
| **双搜索引擎** | Tavily (主) + SearXNG (备用)，自动 failover |

---

## 🚀 快速开始

### 基本用法

```bash
# 智能执行（自动分类 + 组合技能 + 并行执行）
node scripts/charlie-smart-dev.js "评估 voice_agent.py 的代码质量"
node scripts/charlie-smart-dev.js "实现新的天气查询功能"
node scripts/charlie-smart-dev.js "修复 ASR 识别率低的问题"
node scripts/charlie-smart-dev.js "重构 MCP 注册表模块"
node scripts/charlie-smart-dev.js "评估并优化 charlie-dev 系统"
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

# Grilling 工作流
node scripts/charlie-smart-dev.js grill "评估代码安全"
node scripts/charlie-smart-dev.js research "多租户隔离"
node scripts/charlie-smart-dev.js adr list
node scripts/charlie-smart-dev.js adr create "标题" "内容"
```

---

## 📊 需求分类

系统自动将需求分为五类：

| 类型 | 触发词 | 技能组合 |
|------|--------|---------|
| **evaluation** | 评估、review、检查、分析 | code-review + codebase-design + grilling + triage |
| **development** | 实现、开发、添加 | implement + tdd + codebase-design + to-spec + prototype + domain-modeling |
| **testing** | 测试、debug、fix、验证 | tdd + diagnosing-bugs + code-review + research |
| **refactoring** | 重构、优化、改进 | codebase-design + improve-codebase-architecture + tdd + to-tickets + domain-modeling |
| **self-evaluation** | 评估自己、优化自身 | codebase-design + grilling + diagnosing-bugs + research |

---

## ⚙️ 配置

### 模型配置

创建 `.models.json`（参考 `.env.example`）：

```json
{
  "finna": {
    "api_key": "${FINNA_API_KEY}",
    "models": {
      "glm-5.2": "https://api.finna.ai/v1/chat/completions",
      "deepseek-v4-flash": "https://api.finna.ai/v1/chat/completions",
      "deepseek-v4-pro": "https://api.finna.ai/v1/chat/completions",
      "qwen3.6-plus": "https://api.finna.ai/v1/chat/completions"
    }
  },
  "agnes": {
    "api_key": "${AGNES_API_KEY}",
    "models": {
      "agnes-2.5-flash": "https://api.agnes.ai/v1/chat/completions"
    }
  }
}
```

### 搜索配置

创建 `.smart-dev.json`：

```json
{
  "search": {
    "tavily": {
      "api_key": "${TAVILY_API_KEY}",
      "enabled": true
    },
    "searxng": {
      "url": "http://localhost:8080",
      "enabled": true
    }
  }
}
```

### 环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 填入真实 API Keys
export FINNA_API_KEY="your-finna-key"
export AGNES_API_KEY="your-agnes-key"
export TAVILY_API_KEY="your-tavily-key"
```

---

## 📦 Skills 目录

所有 Skills 位于 `.agents/skills/`：

| Skill | 用途 | 使用场景 |
|-------|------|---------|
| **charlie-dev** | CharlieDev 核心 skill | 所有开发任务 |
| code-review | 代码审查 | evaluation, testing |
| codebase-design | 架构设计 | 所有类型 |
| grilling | 压力测试/决策 | evaluation, self-evaluation |
| implement | 功能实现 | development |
| tdd | 测试驱动开发 | development, testing, refactoring |
| diagnosing-bugs | Bug 诊断 | testing, self-evaluation |
| improve-codebase-architecture | 架构改进 | refactoring |
| to-spec | 需求转规格 | development |
| to-tickets | 需求转任务 | refactoring |
| research | 信息调研 | testing, self-evaluation |
| domain-modeling | 领域模型 | development, refactoring |
| prototype | 快速原型 | development |
| triage | 优先级排序 | evaluation, development |

---

## 🏗️ 项目结构

```
charlie-dev/
├── scripts/
│   ├── charlie-dev.js          # 传统模式 CLI
│   ├── charlie-smart-dev.js    # 智能开发主脚本
│   └── charlie-smart-dev.sh    # Shell 快捷入口
├── .agents/
│   └── skills/                 # Skills (Matt Pocock + CharlieDev)
│       ├── charlie-dev/        # CharlieDev 核心 skill
│       ├── code-review/
│       ├── tdd/
│       ├── grilling/
│       └── ...
├── .env.example               # 配置模板
├── .gitignore
└── README.md
```

---

## 📝 License

MIT License

## 🙏 Acknowledgments

- [oh-my-opencode](https://github.com/EvalFall/oh-my-opencode) - 多 Agent 协作框架
- [Matt Pocock Skills](https://github.com/mattwmaclaren/matt-pocock-skills) - 高质量工程 Skills