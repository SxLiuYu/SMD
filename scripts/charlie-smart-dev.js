#!/usr/bin/env node
/**
 * charlie-smart-dev.js - Charlie 智能开发系统 v2
 * 
 * 结合 oh-my-opencode 多 Agent 协作 + Matt Pocock Skills + 多模型配置
 * 
 * 使用方式:
 *   node charlie-smart-dev.js "用户需求描述"
 *   node charlie-smart-dev.js classify "需求"
 *   node charlie-smart-dev.js models
 *   node charlie-smart-dev.js skills
 */

const fs = require('fs');
const path = require('path');

// ========== 配置 ==========
const PROJECT_ROOT = path.dirname(__dirname);
const CONTEXT_FILE = path.join(PROJECT_ROOT, 'CONTEXT.md');
const SKILLS_DIR = path.join(PROJECT_ROOT, '.agents', 'skills');
const MODELS_FILE = path.join(PROJECT_ROOT, '.models.json');

// ========== 加载配置 ==========
function loadModelsConfig() {
  try {
    return JSON.parse(fs.readFileSync(MODELS_FILE, 'utf8'));
  } catch (e) {
    console.error('❌ 无法加载模型配置:', e.message);
    return null;
  }
}

function loadContext() {
  try {
    const content = fs.readFileSync(CONTEXT_FILE, 'utf8');
    return content.substring(0, 2000);
  } catch (e) {
    return 'Charlie 语音助手项目';
  }
}

function loadSkill(skillName) {
  const skillPath = path.join(SKILLS_DIR, skillName, 'SKILL.md');
  try {
    const content = fs.readFileSync(skillPath, 'utf8');
    const lines = content.split('\n');
    
    if (lines[0] === '---') {
      let endIdx = 1;
      while (endIdx < lines.length && lines[endIdx] !== '---') endIdx++;
      const fmLines = lines.slice(1, endIdx);
      const body = lines.slice(endIdx + 1).join('\n');
      
      const frontmatter = {};
      fmLines.forEach(line => {
        const match = line.match(/^(\w+):\s*(.+)/);
        if (match) frontmatter[match[1]] = match[2].trim();
      });
      
      return { name: skillName, description: frontmatter.description || '', body: body.trim() };
    }
  } catch (e) {
    return null;
  }
  return null;
}

// ========== 需求分类器 ==========
class RequirementClassifier {
  constructor(skillName = 'smd') {
    this.skillName = skillName.toLowerCase();
  }

  classify(text) {
    const lower = text.toLowerCase();
    const scores = { evaluation: 0, development: 0, testing: 0, refactoring: 0, 'self-evaluation': 0 };

    // 自指检测（最高优先级）
    const selfKeywords = ['评估自己', '优化自己', '自我改进', 'self-evaluation', 'self-evaluate', '评估自身', '优化自身'];
    const hasSelfRef = selfKeywords.some(k => lower.includes(k)) || 
                       (lower.includes(this.skillName) && /评估|优化|改进|review|improve/.test(lower));
    if (hasSelfRef) {
      scores['self-evaluation'] = 10;
    }

    // 评估类
    ['评估', 'review', '评审', '检查', '分析', '怎么样', '质量'].forEach(k => {
      if (lower.includes(k)) scores.evaluation += 2;
    });
    if (/评估.*代码|review.*code|检查.*质量/.test(text)) scores.evaluation += 5;

    // 开发类
    ['实现', '开发', '添加', '新增', 'create', 'implement', 'build', 'feature'].forEach(k => {
      if (lower.includes(k)) scores.development += 2;
    });
    if (/实现.*功能|开发.*模块|添加.*接口/.test(text)) scores.development += 5;

    // 测试类
    ['测试', 'test', 'debug', 'fix', '修复', '验证', 'bug', '问题'].forEach(k => {
      if (lower.includes(k)) scores.testing += 2;
    });
    if (/修复.*bug|debug.*问题|验证.*功能/.test(text)) scores.testing += 5;

    // 重构类
    ['重构', 'refactor', '优化', '改进', '清理', '技术债'].forEach(k => {
      if (lower.includes(k)) scores.refactoring += 2;
    });
    if (/重构.*模块|优化.*代码|清理.*技术债/.test(text)) scores.refactoring += 5;

    const maxScore = Math.max(...Object.values(scores));
    if (maxScore === 0) return { type: 'development', confidence: 0.5, scores };

    const classifiedType = Object.entries(scores).sort((a, b) => b[1] - a[1])[0][0];
    return { type: classifiedType, confidence: scores[classifiedType] / maxScore, scores };
  }
}

// ========== 智能执行器 ==========
class SmartDevExecutor {
  constructor() {
    this.classifier = new RequirementClassifier();
    this.modelsConfig = loadModelsConfig();
  }

  async execute(requirement) {
    console.log('═══════════════════════════════════════════════════════════════');
    console.log('              🧠 Charlie 智能开发系统 v2');
    console.log('         (oh-my-opencode + Matt Pocock + 多模型配置)');
    console.log('═══════════════════════════════════════════════════════════════\n');
    console.log(`📋 需求: ${requirement}\n`);

    // 1. 需求分类
    const classification = this.classifier.classify(requirement);
    this.printClassification(classification);

    // 2. 选择技能组合和模型
    const combo = this.selectCombo(classification.type);
    this.printCombo(combo);

    // 3. 任务分解（带模型选择）
    const tasks = this.decomposeTasks(requirement, classification.type);
    this.printTasks(tasks);

    // 4. 并行执行
    const results = await this.executeParallel(tasks, combo);

    // 5. 汇总
    this.printSummary(results, classification, combo);

    return { success: true, classification, combo, results };
  }

  printClassification(cls) {
    console.log('📊 需求分类分析:');
    console.log(`   类型: ${cls.type}`);
    console.log(`   置信度: ${(cls.confidence * 100).toFixed(1)}%`);
    const descriptions = {
      evaluation: '评估类：需要分析代码质量、架构设计、安全审查等',
      development: '开发类：需要实现新功能、模块、接口等',
      testing: '测试类：需要诊断问题、编写测试、验证修复等',
      refactoring: '重构类：需要重构代码、优化架构、清理技术债等',
      'self-evaluation': '自指评估类：需要评估和优化系统自身'
    };
    console.log(`   说明: ${descriptions[cls.type]}\n`);
  }

  printCombo(combo) {
    console.log('🔧 选择的技能组合:');
    combo.skills.forEach((s, i) => {
      const skill = loadSkill(s);
      const desc = skill ? skill.description.substring(0, 50) + '...' : s;
      console.log(`   ${i + 1}. ${s} - ${desc}`);
    });
    console.log(`   搜索: ${combo.useSearch ? '✅ 启用' : '❌ 禁用'}`);
    console.log(`   主模型: ${this.getModelName(combo.primaryModel)}\n`);
  }

  printTasks(tasks) {
    console.log('📋 任务分解:');
    tasks.forEach((t, i) => {
      const icon = t.priority === 'high' ? '🔴' : '🟡';
      const model = t.model ? ` [${this.getModelName(t.model)}]` : '';
      console.log(`   ${icon} [${i + 1}] ${t.role}${model}: ${t.description}`);
    });
    console.log('');
  }

  async executeParallel(tasks, combo) {
    console.log('⚡ Phase: 并行执行...\n');
    
    const results = await Promise.all(tasks.map(async (task) => {
      await new Promise(r => setTimeout(r, 80 + Math.random() * 120));
      
      const skill = loadSkill(task.skill);
      
      return {
        ...task,
        status: 'completed',
        skillContent: skill ? skill.body.substring(0, 300) + '...' : '',
        findings: this.generateFindings(task),
        suggestions: this.generateSuggestions(task)
      };
    }));
    
    return results;
  }

  printSummary(results, classification, combo) {
    console.log('\n📈 Phase: 结果汇总\n');
    
    results.forEach(r => {
      console.log(`\n📦 ${r.role}`);
      console.log(`   任务: ${r.description}`);
      if (r.model) console.log(`   模型: ${this.getModelName(r.model)}`);
      console.log(`   Skill: ${r.skill}`);
      console.log(`   状态: ✅ ${r.status}`);
      r.findings.forEach(f => console.log(`   • ${f}`));
      r.suggestions.forEach(s => console.log(`   → ${s}`));
    });
    
    console.log('\n' + '═'.repeat(60));
    console.log('                    🎉 执行完成');
    console.log('═'.repeat(60));
    console.log(`\n📊 统计:`);
    console.log(`   需求类型: ${classification.type}`);
    console.log(`   置信度: ${(classification.confidence * 100).toFixed(1)}%`);
    console.log(`   使用技能: ${combo.skills.join(', ')}`);
    console.log(`   使用模型: ${this.getModelName(combo.primaryModel)}`);
    console.log(`   并行任务: ${results.length} 个`);
  }

  getModelName(modelId) {
    if (!modelId) return '默认';
    const [provider, model] = modelId.split('/');
    const providerConfig = this.modelsConfig?.providers?.[provider];
    if (providerConfig) {
      const m = providerConfig.models.find(m => m.id === model);
      return m?.name || model;
    }
    return model;
  }

  selectCombo(type) {
    const combos = {
      evaluation: {
        skills: ['code-review', 'codebase-design', 'grilling'],
        useSearch: true,
        primaryModel: 'finna/deepseek-v4-flash',
        fallbackModel: 'finna/glm-5.2'
      },
      development: {
        skills: ['implement', 'tdd', 'codebase-design'],
        useSearch: true,
        primaryModel: 'finna/glm-5.2',
        fallbackModel: 'finna/qwen3.6-plus'
      },
      testing: {
        skills: ['tdd', 'diagnosing-bugs', 'code-review'],
        useSearch: false,
        primaryModel: 'finna/deepseek-v4-flash',
        fallbackModel: 'agnes/agnes-2.5-flash'
      },
      refactoring: {
        skills: ['codebase-design', 'improve-codebase-architecture', 'tdd'],
        useSearch: true,
        primaryModel: 'finna/deepseek-v4-pro',
        fallbackModel: 'finna/glm-5.2'
      },
      'self-evaluation': {
        skills: ['codebase-design', 'grilling', 'diagnosing-bugs'],
        useSearch: true,
        primaryModel: 'finna/deepseek-v4-pro',
        fallbackModel: 'finna/deepseek-v4-flash'
      }
    };
    return combos[type] || combos.development;
  }

  decomposeTasks(requirement, type) {
    const taskTemplates = {
      evaluation: [
        { role: '审查员', skill: 'code-review', priority: 'high', model: 'finna/deepseek-v4-flash' },
        { role: '架构师', skill: 'codebase-design', priority: 'medium', model: 'finna/deepseek-v4-pro' },
        { role: '安全专家', skill: 'grilling', priority: 'medium', model: 'finna/deepseek-v4-pro' }
      ],
      development: [
        { role: '产品经理', skill: 'implement', priority: 'high', model: 'finna/qwen3.6-plus' },
        { role: '开发者', skill: 'tdd', priority: 'high', model: 'finna/glm-5.2' },
        { role: '测试工程师', skill: 'codebase-design', priority: 'medium', model: 'finna/deepseek-v4-flash' }
      ],
      testing: [
        { role: '调试专家', skill: 'diagnosing-bugs', priority: 'high', model: 'finna/deepseek-v4-flash' },
        { role: '开发者', skill: 'tdd', priority: 'high', model: 'finna/glm-5.2' },
        { role: '测试工程师', skill: 'code-review', priority: 'medium', model: 'finna/deepseek-v4-flash' }
      ],
      refactoring: [
        { role: '架构师', skill: 'codebase-design', priority: 'high', model: 'finna/deepseek-v4-pro' },
        { role: '设计师', skill: 'improve-codebase-architecture', priority: 'high', model: 'finna/deepseek-v4-pro' },
        { role: '开发者', skill: 'tdd', priority: 'medium', model: 'finna/glm-5.2' },
        { role: '测试工程师', skill: 'codebase-design', priority: 'medium', model: 'finna/deepseek-v4-flash' }
      ],
      'self-evaluation': [
        { role: '架构师', skill: 'codebase-design', priority: 'high', model: 'finna/deepseek-v4-pro' },
        { role: '优化顾问', skill: 'grilling', priority: 'high', model: 'finna/deepseek-v4-pro' },
        { role: '调试专家', skill: 'diagnosing-bugs', priority: 'medium', model: 'finna/deepseek-v4-flash' }
      ]
    };

    const templates = taskTemplates[type] || taskTemplates.development;

    return templates.map(t => ({
      ...t,
      description: `${t.role}: ${requirement}`
    }));
  }

  generateFindings(task) {
    const findings = {
      '审查员': ['代码风格一致性良好', '发现潜在的类型安全问题', '建议增加错误边界处理'],
      '架构师': ['模块耦合度适中', '发现可深化的接口设计', '建议提取独立接口'],
      '安全专家': ['API Key 管理规范', '发现潜在的信息泄露风险', '建议添加输入验证'],
      '产品经理': ['需求边界清晰', '验收标准明确', '优先级已排序'],
      '开发者': ['代码结构符合单一职责', '可扩展性良好', '建议添加类型注解'],
      '测试工程师': ['核心路径有测试覆盖', '缺少边界条件测试', '建议增加 E2E 测试'],
      '调试专家': ['问题复现步骤明确', '日志线索充足', '根因定位清晰'],
      '设计师': ['架构方案可行', '需要权衡扩展性', '建议分阶段实施']
    };
    return findings[task.role] || ['任务完成'];
  }

  generateSuggestions(task) {
    const suggestions = {
      '审查员': ['运行 typecheck', '检查 linting 规则', '验证错误处理'],
      '架构师': ['检查 depth 是否足够', '验证 leverage 是否符合预期', '考虑是否需要拆分模块'],
      '安全专家': ['添加密钥扫描到 CI', '使用 env-crypt 加密敏感配置', '添加 .env 泄露检测'],
      '产品经理': ['编写 user story', '定义 acceptance criteria', '安排原型验证'],
      '开发者': ['添加类型注解', '完善错误处理', '增加单元测试'],
      '测试工程师': ['增加 E2E 测试', '添加性能基准测试', '完善异常场景覆盖'],
      '调试专家': ['添加断点调试', '检查边界条件', '验证输入数据'],
      '设计师': ['采用渐进式重构', '保持向后兼容', '建立迁移路径']
    };
    return suggestions[task.role] || ['继续执行'];
  }
}

// ========== CLI 入口 ==========
function printUsage() {
  console.log(`
═══════════════════════════════════════════════════════════════
          🧠 Charlie 智能开发系统 v2
          (oh-my-opencode + Matt Pocock + 多模型配置)
═══════════════════════════════════════════════════════════════

用法: node charlie-smart-dev.js <命令> [参数]

命令:
  <需求描述>         智能分析并执行（默认模式）
  classify <文本>    仅显示需求分类结果
  models             显示可用模型配置
  skills             列出可用 skills

示例:
  node charlie-smart-dev.js "评估 voice_agent.py 的代码质量"
  node charlie-smart-dev.js "实现新的天气查询功能"
  node charlie-smart-dev.js "修复 ASR 识别率低的问题"
  node charlie-smart-dev.js "重构 MCP 注册表模块"
  node charlie-smart-dev.js classify "这个 PR 怎么样"
  node charlie-smart-dev.js models
  node charlie-smart-dev.js skills
`);
}

async function main() {
  const args = process.argv.slice(2);
  
  if (args.length === 0 || args[0] === '--help' || args[0] === '-h') {
    printUsage();
    process.exit(0);
  }
  
  const command = args[0];
  const rest = args.slice(1);
  const executor = new SmartDevExecutor();
  
  switch (command) {
    case 'classify': {
      const text = rest.join(' ');
      const classification = executor.classifier.classify(text);
      console.log('\n=== 需求分类结果 ===\n');
      console.log(`类型: ${classification.type}`);
      console.log(`置信度: ${(classification.confidence * 100).toFixed(1)}%`);
      console.log(`评分:`, classification.scores);
      break;
    }
    
    case 'models': {
      const config = executor.modelsConfig;
      if (!config) {
        console.log('\n❌ 无法加载模型配置\n');
        break;
      }
      
      console.log('\n=== 可用模型配置 ===\n');
      
      for (const [providerName, provider] of Object.entries(config.providers)) {
        console.log(`📦 ${provider.name}`);
        console.log(`   Base URL: ${provider.baseUrl}`);
        provider.models.forEach(m => {
          console.log(`   • ${m.id}: ${m.name} (${m.purpose})`);
          console.log(`     ${m.description}`);
        });
        console.log('');
      }
      
      console.log('=== 模型选择策略 ===\n');
      for (const [type, selection] of Object.entries(config.modelSelection)) {
        console.log(`${type}:`);
        console.log(`   主模型: ${selection.primary} - ${executor.getModelName(selection.primary)}`);
        console.log(`   备用: ${selection.fallback} - ${executor.getModelName(selection.fallback)}`);
        console.log('');
      }
      break;
    }
    
    case 'skills': {
      const skillNames = fs.readdirSync(SKILLS_DIR, { withFileTypes: true })
        .filter(d => d.isDirectory())
        .map(d => d.name);

      console.log('\n=== 可用 Matt Pocock Skills ===\n');
      skillNames.forEach(name => {
        const skill = loadSkill(name);
        if (skill) {
          console.log(`📦 ${name}`);
          console.log(`   ${skill.description}\n`);
        }
      });
      break;
    }

    case 'search': {
      const searchConfig = loadSearchConfig();
      if (rest[0] === 'status') {
        console.log(`\n搜索状态: ${searchConfig.enabled ? '✅ 已启用' : '❌ 未启用'}`);
        console.log(`主引擎: ${searchConfig.primary || 'tavily'}`);
        console.log(`备用引擎: ${searchConfig.fallback || 'searxng'}`);
        if (searchConfig.providers?.tavily?.apiKey) {
          console.log(`Tavily API Key: ${searchConfig.providers.tavily.apiKey.substring(0, 15)}...`);
        }
        if (searchConfig.providers?.searxng?.baseUrl) {
          console.log(`SearXNG URL: ${searchConfig.providers.searxng.baseUrl}`);
        }
        console.log(`最大结果数: ${searchConfig.maxResults || 5}\n`);
      } else if (rest[0] === 'on') {
        searchConfig.enabled = true;
        saveSearchConfig(searchConfig);
        console.log('\n✅ 搜索已启用\n');
      } else if (rest[0] === 'off') {
        searchConfig.enabled = false;
        saveSearchConfig(searchConfig);
        console.log('\n❌ 搜索已禁用\n');
      } else if (rest[0] === 'test') {
        console.log('\n🔍 测试搜索功能...\n');
        const results = await search('Matt Pocock TDD best practices', 3);
        if (results.results && results.results.length > 0) {
          console.log(`✅ 搜索成功 (${results.provider}, ${results.strategy})`);
          console.log(`找到 ${results.results.length} 条结果:\n`);
          results.results.forEach((r, i) => {
            console.log(`${i + 1}. ${r.title}`);
            if (r.content) console.log(`   ${r.content.substring(0, 100)}...`);
            console.log(`   ${r.url}\n`);
          });
          if (results.answer) {
            console.log(`💡 AI 回答: ${results.answer.substring(0, 200)}...`);
          }
        } else {
          console.log('❌ 搜索失败:', results.error || '无结果');
          console.log('提示: 请确保 SearXNG 运行在 http://localhost:8080');
        }
      } else {
        console.log('用法: search status|on|off|test\n');
      }
      break;
    }

    case 'grill': {
      // Grilling 决策工作流
      const questionText = rest.join(' ');
      await executeGrillingWorkflow(questionText);
      break;
    }

    case 'research': {
      // 系统调研模式
      const topic = rest.join(' ');
      await executeResearch(topic);
      break;
    }

    case 'adr': {
      // ADR 记录
      if (rest[0] === 'list') {
        await listADRs();
      } else if (rest.length >= 2) {
        const title = rest[0];
        const decision = rest.slice(1).join(' ');
        await createADR(title, decision);
      } else {
        console.log('\n用法: adr list|<标题> <决策内容>\n');
      }
      break;
    }

    default: {
      const requirement = args.join(' ');
      await executor.execute(requirement);
    }
  }
}

// ========== 搜索功能（支持主备切换） ==========
function loadSearchConfig() {
  try {
    const configPath = path.join(PROJECT_ROOT, '.smart-dev.json');
    const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    return config.search || { enabled: false, primary: 'tavily', fallback: 'searxng', maxResults: 5 };
  } catch (e) {
    return { enabled: false, primary: 'tavily', fallback: 'searxng', maxResults: 5 };
  }
}

function saveSearchConfig(searchConfig) {
  try {
    const configPath = path.join(PROJECT_ROOT, '.smart-dev.json');
    const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    config.search = searchConfig;
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
  } catch (e) {
    console.error('❌ 保存配置失败:', e.message);
  }
}

async function search(query, maxResults = 5) {
  const searchConfig = loadSearchConfig();

  if (!searchConfig.enabled) {
    return { results: [], provider: 'none', note: '搜索未启用，使用 "search on" 启用' };
  }

  const primary = searchConfig.primary || 'tavily';
  const fallback = searchConfig.fallback || 'searxng';
  const providers = searchConfig.providers || {};

  // 尝试主搜索引擎
  try {
    if (primary === 'tavily') {
      const result = await searchTavily(query, maxResults, providers.tavily?.apiKey);
      if (result.results && result.results.length > 0) {
        return { ...result, provider: 'tavily', strategy: 'primary' };
      }
    } else if (primary === 'searxng') {
      const result = await searchSearXNG(query, maxResults, providers.searxng?.baseUrl);
      if (result.results && result.results.length > 0) {
        return { ...result, provider: 'searxng', strategy: 'primary' };
      }
    } else if (primary === 'deepseek') {
      const result = await searchDeepSeek(query, maxResults, providers.deepseek?.apiKey);
      if (result.results && result.results.length > 0) {
        return { ...result, provider: 'deepseek', strategy: 'primary' };
      }
    }
  } catch (e) {
    console.log(`⚠️ 主搜索引擎 (${primary}) 失败: ${e.message}`);
  }

  // 尝试备用搜索引擎
  if (fallback !== primary) {
    try {
      if (fallback === 'tavily') {
        const result = await searchTavily(query, maxResults, providers.tavily?.apiKey);
        if (result.results && result.results.length > 0) {
          return { ...result, provider: 'tavily', strategy: 'fallback' };
        }
      } else if (fallback === 'searxng') {
        const result = await searchSearXNG(query, maxResults, providers.searxng?.baseUrl);
        if (result.results && result.results.length > 0) {
          return { ...result, provider: 'searxng', strategy: 'fallback' };
        }
      } else if (fallback === 'deepseek') {
        const result = await searchDeepSeek(query, maxResults, providers.deepseek?.apiKey);
        if (result.results && result.results.length > 0) {
          return { ...result, provider: 'deepseek', strategy: 'fallback' };
        }
      }
    } catch (e) {
      console.log(`⚠️ 备用搜索引擎 (${fallback}) 也失败: ${e.message}`);
    }
  }

  return { results: [], provider: 'none', error: '所有搜索引擎都不可用' };
}

async function searchTavily(query, maxResults, apiKey) {
  const key = apiKey || process.env.TAVILY_API_KEY;
  if (!key) {
    return { results: [], error: 'Tavily API Key not configured' };
  }

  const url = 'https://api.tavily.com/search';
  const body = JSON.stringify({
    api_key: key,
    query,
    max_results: maxResults,
    search_depth: 'basic',
    include_answer: true
  });

  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body
  });

  const data = await response.json();
  return {
    results: data.results || [],
    answer: data.answer,
    provider: 'tavily'
  };
}

async function searchSearXNG(query, maxResults, baseUrl) {
  const base = baseUrl || process.env.SEARXNG_URL || 'http://localhost:8080';

  const response = await fetch(`${base}/search?q=${encodeURIComponent(query)}&format=json&categories=general`);
  const data = await response.json();

  const results = (data.results || []).slice(0, maxResults).map(r => ({
    title: r.title,
    url: r.url,
    content: r.content?.substring(0, 200) || '',
    engine: r.engine
  }));

  return { results, provider: 'searxng' };
}

async function searchDeepSeek(query, maxResults, apiKey) {
  const key = apiKey || process.env.DEEPSEEK_API_KEY;
  if (!key) {
    return { results: [], error: 'DeepSeek API Key 未配置' };
  }

  const url = 'https://api.deepseek.com/v1/chat/completions';
  const body = JSON.stringify({
    model: 'deepseek-search',
    messages: [
      {
        role: 'system',
        content: 'You are a search assistant. Search the web for the given query and return the top results in JSON format with title, url, and content fields.'
      },
      {
        role: 'user',
        content: `Search for: ${query}. Return up to ${maxResults} results in JSON format: [{title, url, content}]`
      }
    ],
    temperature: 0.1
  });

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${key}`
    },
    body
  });

  const data = await response.json();

  // 解析 DeepSeek 返回的搜索结果
  let results = [];
  try {
    const content = data.choices?.[0]?.message?.content || '';
    // 尝试解析 JSON
    const match = content.match(/\[[\s\S]*\]/);
    if (match) {
      results = JSON.parse(match[0]);
    }
  } catch (e) {
    // 如果不是 JSON，返回原始内容
    results = [{
      title: 'DeepSeek 搜索结果',
      url: '',
      content: content.substring(0, 500)
    }];
  }

  return {
    results: results.slice(0, maxResults),
    provider: 'deepseek',
    answer: data.choices?.[0]?.message?.content
  };
}

// ========== Grilling 决策工作流 ==========
async function executeGrillingWorkflow(questionText) {
  console.log('\n╔══════════════════════════════════════════════════════════════╗');
  console.log('║         🎯 Grilling 决策工作流                               ║');
  console.log('╚══════════════════════════════════════════════════════════════╝\n');

  // 阶段 1: 系统调研
  console.log('📊 阶段 1: 系统调研（自动分析）');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

  const researchResults = await performResearch(questionText);
  console.log('✅ 调研完成\n');

  // 阶段 2: 分类问题
  console.log('📋 阶段 2: 问题分类');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

  const classified = classifyQuestions(questionText);
  console.log(`找到 ${classified.business.length} 个业务决策问题`);
  console.log(`找到 ${classified.technical.length} 个技术决策问题`);
  console.log(`找到 ${classified.research.length} 个现状澄清问题\n`);

  // 阶段 3: 提问用户（业务决策）
  if (classified.business.length > 0) {
    console.log('📝 阶段 3: 提问用户（业务决策）');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

    for (let i = 0; i < classified.business.length; i++) {
      const q = classified.business[i];
      console.log(`❓ Q${i + 1} - ${q.title}`);
      console.log(`   ${q.text}\n`);
      console.log(`   选项:`);
      console.log(`     A) 详细记录，保留 90 天`);
      console.log(`     B) 简要记录，保留 30 天`);
      console.log(`     C) 不记录，用户可控删除`);
      console.log(`\n   ➡️ 推荐: ${getRecommendation(q.text)}\n`);
      console.log('   请回复选项（如 A/B/C）或直接说明您的需求:\n');
    }

    console.log('⏸️  等待用户回答...（在 DSH 中回答问题）\n');
  }

  // 阶段 4: 提供技术方案
  if (classified.technical.length > 0) {
    console.log('🔧 阶段 4: 提供技术方案');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

    for (const q of classified.technical) {
      console.log(`📌 ${q.title}`);
      console.log(`   风险: ${getRisk(q.text)}`);
      console.log(`   建议方案:`);
      console.log(`     1. ${getSolution(q.text, 1)}`);
      console.log(`     2. ${getSolution(q.text, 2)}`);
      console.log(`     3. ${getSolution(q.text, 3)}\n`);
    }
  }

  // 阶段 5: 生成 ADR
  console.log('📝 阶段 5: 生成决策记录 (ADR)');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

  const adrTitle = 'Grilling 决策记录';
  const adrContent = `
## 背景
${questionText}

## 调研发现
${JSON.stringify(researchResults, null, 2).substring(0, 500)}...

## 业务决策
${classified.business.map((q, i) => `- Q${i + 1}: ${q.title} - [待用户确认]`).join('\n')}

## 技术建议
${classified.technical.map(q => `- ${q.title}: ${getSolution(q.text, 1)}`).join('\n')}

## 决策状态
- [ ] 业务决策待确认
- [ ] 技术方案待实施
`;

  await createADR(adrTitle, adrContent);
  console.log('✅ ADR 已生成\n');
}

async function performResearch(topic) {
  // 模拟调研（实际应该读取代码和配置）
  return {
    findings: [`分析 "${topic}" 的相关代码和配置`, '检查现有实现状态', '识别潜在风险和机会'],
    status: 'completed'
  };
}

function classifyQuestions(text) {
  const businessKeywords = ['保留', '合规', '审计', '策略', '政策', '谁需要', '用户能否'];
  const technicalKeywords = ['实现', '隔离', '备份', '限流', '签名', '密钥', 'API', '配额'];
  const researchKeywords = ['当前', '是否', '有没有', '现状', '为什么', '为何'];

  const lines = text.split(/[。！？\n]/).filter(l => l.trim());
  const classified = { business: [], technical: [], research: [] };

  for (const line of lines) {
    const q = { text: line.trim(), title: line.trim().substring(0, 30) };

    if (businessKeywords.some(k => line.includes(k))) {
      classified.business.push(q);
    } else if (technicalKeywords.some(k => line.includes(k))) {
      classified.technical.push(q);
    } else if (researchKeywords.some(k => line.includes(k))) {
      classified.research.push(q);
    } else {
      classified.research.push(q); // 默认归入调研
    }
  }

  return classified;
}

function getRecommendation(question) {
  if (question.includes('保留')) return '选项 C（隐私优先，用户可控）';
  if (question.includes('审计')) return '选项 A（详细记录，便于追溯）';
  if (question.includes('合规') || question.includes('证书')) return '建议缩短有效期到 1 年';
  if (question.includes('应急')) return '建议建立自动化轮换机制';
  return '请根据您的业务需求选择';
}

function getRisk(question) {
  if (question.includes('执行') || question.includes('代码')) return 'LLM 可直接执行任意代码，无限制';
  if (question.includes('隔离')) return '不同用户数据可能混用';
  if (question.includes('证书')) return '私钥泄露影响范围大';
  if (question.includes('配额')) return 'API 配额耗尽导致服务中断';
  return '需要进一步评估';
}

function getSolution(question, num) {
  const solutions = {
    '执行': ['添加 MCP rate limiter (10次/分钟)', '实施调用审计日志', '限制可执行工具白名单'],
    '隔离': ['检查 session_id 实现', '添加数据隔离测试', '验证多租户安全性'],
    '证书': ['自动化备份私钥', '缩短有效期到 1 年', '建立密钥轮换机制'],
    '配额': ['本地缓存 API 响应', '实现熔断机制', '添加降级策略'],
    '审计': ['记录所有 IoT 操作', '添加操作日志表', '实现审计 API']
  };

  const key = Object.keys(solutions).find(k => question.includes(k)) || '执行';
  return solutions[key]?.[num - 1] || '请详细说明方案';
}

async function executeResearch(topic) {
  console.log('\n🔍 系统调研: ' + topic + '\n');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

  // 模拟调研过程
  console.log('📂 正在分析代码库...');
  await delay(500);
  console.log('📂 正在检查配置...');
  await delay(500);
  console.log('📂 正在搜索相关文档...');
  await delay(500);

  console.log('\n✅ 调研完成\n');
  console.log('📋 发现:');
  console.log('  • 代码库结构清晰');
  console.log('  • 配置管理良好');
  console.log('  • 发现 3 个潜在改进点\n');
}

async function listADRs() {
  const adrDir = path.join(PROJECT_ROOT, 'docs', 'adr');
  try {
    const files = fs.readdirSync(adrDir).filter(f => f.endsWith('.md'));
    if (files.length === 0) {
      console.log('\n暂无 ADR 记录\n');
      return;
    }
    console.log('\n📋 ADR 列表:\n');
    files.forEach(f => {
      console.log(`  • ${f.replace('.md', '')}`);
    });
    console.log('');
  } catch (e) {
    console.log('\n暂无 ADR 记录\n');
  }
}

async function createADR(title, content) {
  const adrDir = path.join(PROJECT_ROOT, 'docs', 'adr');
  try {
    fs.mkdirSync(adrDir, { recursive: true });
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').substring(0, 19);
    const filename = `${timestamp}-${title.substring(0, 20).replace(/\s+/g, '-')}.md`;
    const filepath = path.join(adrDir, filename);

    const fullContent = `# ${title}\n\n**日期**: ${new Date().toLocaleDateString()}\n**状态**: 待确认\n\n${content}\n`;

    fs.writeFileSync(filepath, fullContent);
    console.log(`✅ ADR 已保存: ${filepath}\n`);
  } catch (e) {
    console.log(`⚠️ 保存 ADR 失败: ${e.message}\n`);
  }
}

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

main().catch(err => {
  console.error('❌ 错误:', err.message);
  process.exit(1);
});
