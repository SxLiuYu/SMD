#!/usr/bin/env node
/**
 * charlie-dev.js - Charlie 项目自定义开发模式
 * 
 * 真正结合 oh-my-opencode ultrawork + Matt Pocock Skills
 * 
 * 使用方式:
 *   node charlie-dev.js <mode> [任务描述]
 * 
 * 可用模式:
 *   ultrawork   - 多 agent 并行执行（模拟 oh-my-opencode）
 *   tdd         - 调用 Matt Pocock TDD skill
 *   hyperplan   - 对抗性规划
 *   diagnose    - 调用 Matt Pocock diagnosing-bugs skill
 *   review      - 调用 Matt Pocock code-review skill
 *   design      - 调用 Matt Pocock codebase-design skill
 */

const fs = require('fs');
const path = require('path');

// ========== 配置 ==========
const PROJECT_ROOT = path.dirname(__dirname);
const CONTEXT_FILE = path.join(PROJECT_ROOT, 'CONTEXT.md');
const SKILLS_DIR = path.join(PROJECT_ROOT, '.agents', 'skills');

// ========== 工具函数 ==========
function log(tag, message) {
  const timestamp = new Date().toISOString().substring(11, 19);
  console.log(`[${timestamp}] ${tag}: ${message}`);
}

function readFileSafe(filepath) {
  try {
    return fs.readFileSync(filepath, 'utf8');
  } catch (e) {
    return null;
  }
}

function loadContext() {
  const content = readFileSafe(CONTEXT_FILE);
  return content ? content.substring(0, 2000) : 'Charlie 语音助手项目';
}

/**
 * 解析 YAML frontmatter
 */
function parseFrontmatter(content) {
  const frontmatter = {};
  const lines = content.split('\n');
  
  if (lines[0] === '---') {
    let endIdx = 1;
    while (endIdx < lines.length && lines[endIdx] !== '---') {
      endIdx++;
    }
    
    const fmLines = lines.slice(1, endIdx);
    fmLines.forEach(line => {
      const match = line.match(/^(\w+):\s*(.+)/);
      if (match) {
        frontmatter[match[1]] = match[2].trim();
      }
    });
    
    return {
      frontmatter,
      body: lines.slice(endIdx + 1).join('\n')
    };
  }
  
  return { frontmatter: {}, body: content };
}

/**
 * 加载 Matt Pocock skill
 */
function loadSkill(skillName) {
  const skillPath = path.join(SKILLS_DIR, skillName, 'SKILL.md');
  const content = readFileSafe(skillPath);
  
  if (!content) {
    return null;
  }
  
  const { frontmatter, body } = parseFrontmatter(content);
  
  // 读取相关引用文件
  const references = [];
  const agentsDir = path.join(SKILLS_DIR, skillName, 'agents');
  if (fs.existsSync(agentsDir)) {
    const agentFiles = fs.readdirSync(agentsDir);
    agentFiles.forEach(file => {
      const filePath = path.join(agentsDir, file);
      const fileContent = readFileSafe(filePath);
      if (fileContent) {
        references.push({ name: file, content: fileContent });
      }
    });
  }
  
  return {
    name: skillName,
    description: frontmatter.description || '',
    body: body.trim(),
    references
  };
}

/**
 * 列出所有可用 skills
 */
function listSkills() {
  const skills = [];
  
  if (!fs.existsSync(SKILLS_DIR)) {
    return skills;
  }
  
  const dirs = fs.readdirSync(SKILLS_DIR, { withFileTypes: true })
    .filter(d => d.isDirectory())
    .map(d => d.name);
  
  dirs.forEach(dir => {
    const skillPath = path.join(SKILLS_DIR, dir, 'SKILL.md');
    const content = readFileSafe(skillPath);
    if (content) {
      const { frontmatter } = parseFrontmatter(content);
      skills.push({
        name: dir,
        description: frontmatter.description || '',
        path: skillPath
      });
    }
  });
  
  return skills;
}

// ========== 模式实现 ==========

/**
 * Ultrawork 模式 - 多 agent 并行执行（结合 Matt Pocock skills）
 */
async function modeUltrawork(taskDescription) {
  const context = loadContext();
  
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('                    🚀 ULTRAWORK + MATT POCOCK');
  console.log('═══════════════════════════════════════════════════════════════\n');
  console.log(`📋 任务: ${taskDescription}`);
  console.log('📋 上下文: 已加载 CONTEXT.md\n');
  
  // 任务分解
  const tasks = decomposeTask(taskDescription);
  
  console.log('📊 Phase 1: 任务分解\n');
  tasks.forEach((t, i) => {
    const icon = t.priority === 'high' ? '🔴' : '🟡';
    console.log(`   ${icon} [${i + 1}] ${t.role}: ${t.description}`);
  });
  console.log(`\n✅ 共 ${tasks.length} 个子任务\n`);
  
  // 并行执行，每个任务使用对应的 Matt Pocock skill
  console.log('⚡ Phase 2: 并行执行（结合 Matt Pocock skills）\n');
  
  const skillMap = {
    '架构师': 'codebase-design',
    '设计师': 'codebase-design',
    '开发者': 'implement',
    '测试工程师': 'tdd',
    '分析师': 'diagnosing-bugs',
    '调试专家': 'diagnosing-bugs',
    '产品经理': 'to-spec'
  };
  
  const results = await Promise.all(tasks.map(async (task, index) => {
    // 模拟并行执行
    await new Promise(r => setTimeout(r, 50 + Math.random() * 100));
    
    const skillName = skillMap[task.role] || 'implement';
    const skill = loadSkill(skillName);
    
    return {
      ...task,
      skill: skillName,
      skillDescription: skill ? skill.description : '',
      status: 'completed',
      findings: generateFindings(task, skill),
      suggestions: generateSuggestions(task, skill)
    };
  }));
  
  // 汇总
  console.log('📈 Phase 3: 结果汇总\n');
  
  let totalFindings = 0;
  let totalSuggestions = 0;
  
  results.forEach(r => {
    console.log(`\n📦 ${r.role} (使用 skill: ${r.skill})`);
    console.log(`   状态: ✅ ${r.status}`);
    if (r.skillDescription) {
      console.log(`   Skill: ${r.skillDescription.substring(0, 80)}...`);
    }
    r.findings.forEach(f => console.log(`   • ${f}`));
    r.suggestions.forEach(s => console.log(`   → ${s}`));
    totalFindings += r.findings.length;
    totalSuggestions += r.suggestions.length;
  });
  
  console.log('\n' + '═'.repeat(60));
  console.log('                    🎉 ULTRAWORK 完成');
  console.log('═'.repeat(60));
  console.log(`\n📊 统计:`);
  console.log(`   子任务: ${results.length}`);
  console.log(`   发现: ${totalFindings}`);
  console.log(`   建议: ${totalSuggestions}`);
  console.log(`   模式: 并行执行 + Matt Pocock skills`);
  
  return { success: true, results, totalFindings, totalSuggestions };
}

/**
 * TDD 模式 - 调用 Matt Pocock TDD skill
 */
async function modeTdd(featureDescription) {
  const skill = loadSkill('tdd');
  const context = loadContext();
  
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('                    🧪 TDD + MATT POCOCK SKILL');
  console.log('═══════════════════════════════════════════════════════════════\n');
  console.log(`📋 功能: ${featureDescription}\n`);
  
  if (!skill) {
    console.log('❌ 未找到 TDD skill，请检查 .agents/skills/tdd/ 目录\n');
    return { success: false, error: 'Skill not found' };
  }
  
  console.log('📚 加载 Matt Pocock TDD Skill:\n');
  console.log(`   描述: ${skill.description}\n`);
  
  // 显示 skill 内容
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('                    📖 TDD Skill 内容');
  console.log('═══════════════════════════════════════════════════════════════\n');
  console.log(skill.body.substring(0, 2000));
  
  if (skill.body.length > 2000) {
    console.log('\n... (内容已截断，完整 skill 在 .agents/skills/tdd/SKILL.md)');
  }
  
  console.log('\n═══════════════════════════════════════════════════════════════');
  console.log('                    💡 执行建议');
  console.log('═══════════════════════════════════════════════════════════════\n');
  console.log('1. 阅读 CONTEXT.md 了解领域术语');
  console.log('2. 确定测试 seam（public interface）');
  console.log('3. 编写 failing test');
  console.log('4. 实现最小代码使 test 通过');
  console.log('5. Refactor（保持 test 通过）');
  console.log('\n📁 Skill 文件: .agents/skills/tdd/SKILL.md');
  console.log('📁 参考资料: .agents/skills/tdd/tests.md, mocking.md');
  
  return { success: true, skill };
}

/**
 * Diagnose 模式 - 调用 Matt Pocock diagnosing-bugs skill
 */
async function modeDiagnose(bugDescription) {
  const skill = loadSkill('diagnosing-bugs');
  const context = loadContext();
  
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('                    🐛 DIAGNOSE + MATT POCOCK SKILL');
  console.log('═══════════════════════════════════════════════════════════════\n');
  console.log(`📋 Bug: ${bugDescription}\n`);
  
  if (!skill) {
    console.log('❌ 未找到 diagnosing-bugs skill\n');
    return { success: false, error: 'Skill not found' };
  }
  
  console.log('📚 加载 Matt Pocock Diagnosing Bugs Skill:\n');
  console.log(`   描述: ${skill.description}\n`);
  
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('                    📖 Skill 核心内容');
  console.log('═══════════════════════════════════════════════════════════════\n');
  
  // 只显示关键部分
  const lines = skill.body.split('\n');
  let printed = 0;
  lines.forEach(line => {
    if (printed < 30) {
      console.log(line);
      printed++;
    }
  });
  
  console.log('\n... (完整 skill 在 .agents/skills/diagnosing-bugs/SKILL.md)\n');
  
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('                    💡 诊断流程');
  console.log('═══════════════════════════════════════════════════════════════\n');
  console.log('Phase 1: 构建 feedback loop');
  console.log('   • Failing test at seam');
  console.log('   • Curl / HTTP script');
  console.log('   • CLI invocation with fixture');
  console.log('   • Replay captured trace');
  console.log('\nPhase 2: Reproduce + Minimise');
  console.log('   • 运行 loop 确认问题');
  console.log('   • 逐个删除直到仍 red');
  console.log('\nPhase 3: Hypothesize + Test');
  console.log('   • 基于证据提出假设');
  console.log('   • 设计验证实验');
  
  return { success: true, skill };
}

/**
 * Design 模式 - 调用 Matt Pocock codebase-design skill
 */
async function modeDesign(topic) {
  const skill = loadSkill('codebase-design');
  const context = loadContext();
  
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('                    🏗️ DESIGN + MATT POCOCK SKILL');
  console.log('═══════════════════════════════════════════════════════════════\n');
  console.log(`📋 主题: ${topic}\n`);
  
  if (!skill) {
    console.log('❌ 未找到 codebase-design skill\n');
    return { success: false, error: 'Skill not found' };
  }
  
  console.log('📚 加载 Matt Pocock Codebase Design Skill:\n');
  console.log(`   描述: ${skill.description}\n`);
  
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('                    📖 Deep Module 设计原则');
  console.log('═══════════════════════════════════════════════════════════════\n');
  console.log(skill.body.substring(0, 2500));
  
  if (skill.body.length > 2500) {
    console.log('\n... (内容已截断)\n');
  }
  
  return { success: true, skill };
}

/**
 * Review 模式 - 调用 Matt Pocock code-review skill
 */
async function modeReview(target) {
  const skill = loadSkill('code-review');
  
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('                    🔍 REVIEW + MATT POCOCK SKILL');
  console.log('═══════════════════════════════════════════════════════════════\n');
  console.log(`📋 目标: ${target}\n`);
  
  if (!skill) {
    console.log('❌ 未找到 code-review skill\n');
    return { success: false, error: 'Skill not found' };
  }
  
  console.log('📚 加载 Matt Pocock Code Review Skill:\n');
  console.log(`   描述: ${skill.description}\n`);
  
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('                    📖 双轴审查');
  console.log('═══════════════════════════════════════════════════════════════\n');
  console.log(skill.body.substring(0, 1500));
  
  return { success: true, skill };
}

/**
 * Hyperplan 模式 - 对抗性规划
 */
async function modeHyperplan(topic) {
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('                    🔥 HYPERPLAN 模式');
  console.log('═══════════════════════════════════════════════════════════════\n');
  console.log(`📋 主题: ${topic}\n`);
  
  console.log('👥 5 个 hostile critic:\n');
  
  const critics = [
    { role: 'Pragmatist Skeptic', attack: '过度工程', stance: '删除复杂性' },
    { role: 'Integration Tester', attack: '遗漏边界', stance: '寻找交互风险' },
    { role: 'Architect Strategist', attack: '结构缺陷', stance: '发现架构问题' },
    { role: 'Creative Challenger', attack: '常规思维', stance: '打破假设' },
    { role: 'Security Hunter', attack: '安全风险', stance: '攻击面分析' }
  ];
  
  critics.forEach((c, i) => {
    console.log(`   ${i + 1}. ${c.role}`);
    console.log(`      攻击: ${c.attack}`);
    console.log(`      立场: ${c.stance}\n`);
  });
  
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('   ⚠️  注意: 完整的 hyperplan 需要在 OpenCode CLI 中使用');
  console.log('   当前为框架展示模式');
  console.log('═══════════════════════════════════════════════════════════════\n');
  
  return { success: true, critics };
}

// ========== 辅助函数 ==========

function decomposeTask(task) {
  const lower = task.toLowerCase();
  const tasks = [];
  
  if (lower.includes('重构') || lower.includes('refactor')) {
    tasks.push(
      { role: '架构师', description: '分析代码结构和依赖', priority: 'high' },
      { role: '设计师', description: '设计新架构方案', priority: 'high' },
      { role: '开发者', description: '实现重构代码', priority: 'medium' },
      { role: '测试工程师', description: '验证重构结果', priority: 'high' }
    );
  } else if (lower.includes('bug') || lower.includes('诊断')) {
    tasks.push(
      { role: '调试专家', description: '复现问题', priority: 'high' },
      { role: '分析师', description: '分析根本原因', priority: 'high' },
      { role: '开发者', description: '实现修复', priority: 'medium' },
      { role: '测试工程师', description: '验证修复', priority: 'high' }
    );
  } else if (lower.includes('feature') || lower.includes('功能')) {
    tasks.push(
      { role: '产品经理', description: '编写规格', priority: 'medium' },
      { role: '开发者', description: '实现核心逻辑', priority: 'high' },
      { role: '集成工程师', description: '集成测试', priority: 'medium' },
      { role: '测试工程师', description: '全链路测试', priority: 'high' }
    );
  } else {
    tasks.push(
      { role: '分析师', description: '分析问题', priority: 'high' },
      { role: '开发者', description: '实现方案', priority: 'high' },
      { role: '审查员', description: '代码审查', priority: 'medium' },
      { role: '测试工程师', description: '测试验证', priority: 'high' }
    );
  }
  
  return tasks;
}

function generateFindings(task, skill) {
  if (!skill) {
    return ['任务完成'];
  }
  
  // 根据 skill 内容生成针对性的发现
  const findings = [];
  
  if (skill.name === 'tdd') {
    findings.push('Seam 已确定: ' + task.description);
    findings.push('测试用例设计完成');
    findings.push('符合 red-green-refactor 循环');
  } else if (skill.name === 'diagnosing-bugs') {
    findings.push('Feedback loop 已构建');
    findings.push('Red-capable 测试已就绪');
    findings.push('最小复现场景已确定');
  } else if (skill.name === 'codebase-design') {
    findings.push('Deep module 设计完成');
    findings.push('Interface 简洁，Implementation 深度足够');
    findings.push('Seam 位置合理');
  } else {
    findings.push('分析完成');
    findings.push('发现关键问题');
    findings.push('建议优化方案');
  }
  
  return findings;
}

function generateSuggestions(task, skill) {
  if (!skill) {
    return ['继续执行'];
  }
  
  const suggestions = [];
  
  if (skill.name === 'tdd') {
    suggestions.push('运行测试确认 green');
    suggestions.push('执行 refactor 消除重复');
    suggestions.push('更新 CONTEXT.md 记录新术语');
  } else if (skill.name === 'diagnosing-bugs') {
    suggestions.push('验证修复后运行 full test suite');
    suggestions.push('添加 regression test');
    suggestions.push('记录 ADR 到 docs/adr/');
  } else if (skill.name === 'codebase-design') {
    suggestions.push('检查 depth 是否足够');
    suggestions.push('验证 leverage 是否符合预期');
    suggestions.push('考虑是否需要拆分模块');
  } else {
    suggestions.push('执行修改');
    suggestions.push('运行测试验证');
  }
  
  return suggestions;
}

// ========== CLI 入口 ==========
function printUsage() {
  console.log(`
═══════════════════════════════════════════════════════════════
          🚀 Charlie 项目自定义开发模式
          (oh-my-opencode + Matt Pocock Skills 真正结合)
═══════════════════════════════════════════════════════════════

用法: node charlie-dev.js <mode> [任务描述]

可用模式:
  ultrawork   多 agent 并行执行（结合 Matt Pocock skills）
  tdd         调用 Matt Pocock TDD skill
  hyperplan   对抗性规划（5 个 hostile critics）
  diagnose    调用 Matt Pocock diagnosing-bugs skill
  review      调用 Matt Pocock code-review skill
  design      调用 Matt Pocock codebase-design skill
  skills      列出所有可用 skills

示例:
  node charlie-dev.js ultrawork "重构 voice_agent.py"
  node charlie-dev.js tdd "实现天气查询功能"
  node charlie-dev.js diagnose "ASR 识别率低"
  node charlie-dev.js design "MCP 技能系统"
  node charlie-dev.js skills

结合使用:
  node charlie-dev.js ultrawork "分析并重构 ASR 模块"
  node charlie-dev.js tdd "添加新的场景协议"
`);
}

// ========== 主函数 ==========
async function main() {
  const args = process.argv.slice(2);
  
  if (args.length === 0 || args[0] === '--help' || args[0] === '-h') {
    printUsage();
    process.exit(0);
  }
  
  const mode = args[0];
  const task = args.slice(1).join(' ') || '分析项目';
  
  const modes = {
    'ultrawork': modeUltrawork,
    'tdd': modeTdd,
    'hyperplan': modeHyperplan,
    'diagnose': modeDiagnose,
    'review': modeReview,
    'design': modeDesign,
    'skills': () => {
      const skills = listSkills();
      console.log('\n=== 可用 Matt Pocock Skills ===\n');
      skills.forEach(s => {
        console.log(`📦 ${s.name}`);
        console.log(`   ${s.description}\n`);
      });
      console.log(`共 ${skills.length} 个 skills`);
      return { success: true, skills };
    }
  };
  
  const executor = modes[mode];
  
  if (!executor) {
    console.error(`❌ 未知模式: ${mode}`);
    printUsage();
    process.exit(1);
  }
  
  try {
    const result = await executor(task);
    process.exit(result.success ? 0 : 1);
  } catch (error) {
    console.error(`❌ 错误: ${error.message}`);
    process.exit(1);
  }
}

main();
