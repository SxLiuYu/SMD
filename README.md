# SMD - Smart Development System

> Charlie 智能开发系统 - 自动需求分类 + Matt Pocock Skills 组合 + 并行执行 + Grilling 决策工作流

[![Node.js](https://img.shields.io/badge/Node.js-18+-green.svg)](https://nodejs.org/)
[![JavaScript](https://img.shields.io/badge/JavaScript-ES6-yellow.svg)](https://developer.mozilla.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 概述

**SMD (Smart Development)** 是一个结合 **oh-my-opencode 多 Agent 协作** + **Matt Pocock Skills** + **多模型配置** 的智能开发辅助系统。

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
node scripts/charlie-smart-dev.js "评估并优化 smd 系统"
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

## 🎯 Grilling 决策工作流

当报告包含待决策问题时，执行 4 阶段工作流：

1. **系统调研** - `research "<主题>"`
2. **问题分类** - 业务决策→提问用户，技术决策→提供方案
3. **提问用户** - 一次问完所有业务问题，给出推荐答案
4. **生成 ADR** - `adr "<标题>" "<内容>"`

参考：`.agents/skills/grilling/SKILL.md`

---

## ⚙️ 配置

### 模型配置

编辑 `.models.json`（从 `.env.example` 复制）：

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
  },
  "agnes_cn": {
    "api_key": "${AGNES_CN_API_KEY}",
    "models": {
      "agnes-2.5-flash": "https://api-cn.agnes.ai/v1/chat/completions"
    }
  }
}
```

### 搜索配置

编辑 `.smart-dev.json`：

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
export AGNES_CN_API_KEY="your-agnes-cn-key"
export TAVILY_API_KEY="your-tavily-key"
```

---

## 📦 Skills 目录

### SMD 核心 Skills (11 个)

| Skill | 用途 | 使用场景 |
|-------|------|---------|
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

### 完整 Matt Pocock Skills (36 个)

所有 Matt Pocock Skills 保留在 `.agents/skills/` 目录，SMD 自动调用上述 11 个核心 skills，其他 skills 可手动调用。

---

## 🏗️ 项目结构

```
smd/
├── scripts/
│   └── charlie-smart-dev.js    # 主执行脚本
├── .agents/
│   └── skills/                 # Matt Pocock Skills (36 个)
│       ├── smd/               # SMD 核心 skill
│       ├── code-review/
│       ├── tdd/
│       ├── grilling/
│       └── ...
├── docs/
│   └── adr/                   # Architecture Decision Records
├── .models.json               # 模型配置
├── .smart-dev.json            # 搜索配置
├── .env.example               # 配置模板
├── .gitignore
└── README.md
```

---

## 🔧 高级用法

### 自定义模型路由

在 `scripts/charlie-smart-dev.js` 中修改 `taskTemplates`：

```javascript
{
  role: '架构师',
  skill: 'codebase-design',
  priority: 'high',
  model: 'finna/deepseek-v4-pro'  // 修改模型
}
```

### 添加新 Skills

1. 在 `.agents/skills/` 创建 skill 目录
2. 添加 `SKILL.md` 文件
3. 在 SMD 的配置中添加新 skill

---

## 📝 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- [oh-my-opencode](https://github.com/EvalFall/oh-my-opencode) - 多 Agent 协作框架
- [Matt Pocock Skills](https://github.com/mattwmaclaren/matt-pocock-skills) - 高质量工程 Skills
- [DeepSeek](https://deepseek.com) - AI 模型提供商
- [Finna AI](https://finna.ai) - API 代理服务
- [Agnes AI](https://agnes.ai) - AI 模型提供商
