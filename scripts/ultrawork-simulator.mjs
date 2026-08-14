/**
 * ultrawork-simulator.mjs
 * 在 DSH 中模拟 oh-my-opencode 的 ultrawork 功能
 * 
 * 功能：
 * 1. 接收任务描述
 * 2. 自动分解为子任务
 * 3. 并行调度多个 subagent
 * 4. 汇总结果
 */

import fs from 'fs';
import path from 'path';

/**
 * 解析任务并生成子任务列表
 */
function parseTask(taskDescription) {
  const tasks = [];
  
  // 简单的任务分解逻辑
  const lower = taskDescription.toLowerCase();
  
  if (lower.includes('重构') || lower.includes('refactor')) {
    tasks.push({
      id: 'analyze',
      role: 'analyst',
      description: '分析代码结构和依赖关系',
      priority: 'high'
    });
    tasks.push({
      id: 'design',
      role: 'architect',
      description: '设计新的架构方案',
      priority: 'high'
    });
    tasks.push({
      id: 'implement',
      role: 'developer',
      description: '实现重构代码',
      priority: 'medium'
    });
    tasks.push({
      id: 'test',
      role: 'qa',
      description: '运行测试验证',
      priority: 'high'
    });
  } else if (lower.includes('bug') || lower.includes('诊断')) {
    tasks.push({
      id: 'reproduce',
      role: 'debugger',
      description: '复现问题并收集日志',
      priority: 'high'
    });
    tasks.push({
      id: 'analyze-root',
      role: 'analyst',
      description: '分析根本原因',
      priority: 'high'
    });
    tasks.push({
      id: 'fix',
      role: 'developer',
      description: '实现修复',
      priority: 'medium'
    });
  } else if (lower.includes('feature') || lower.includes('功能')) {
    tasks.push({
      id: 'spec',
      role: 'planner',
      description: '编写规格说明',
      priority: 'medium'
    });
    tasks.push({
      id: 'implement-a',
      role: 'developer',
      description: '实现核心逻辑',
      priority: 'high'
    });
    tasks.push({
      id: 'implement-b',
      role: 'developer',
      description: '实现集成逻辑',
      priority: 'medium'
    });
    tasks.push({
      id: 'test',
      role: 'qa',
      description: '测试验证',
      priority: 'high'
    });
  } else {
    // 默认分解
    tasks.push({
      id: 'analyze',
      role: 'analyst',
      description: '分析问题并制定方案',
      priority: 'high'
    });
    tasks.push({
      id: 'implement',
      role: 'developer',
      description: '实现解决方案',
      priority: 'high'
    });
    tasks.push({
      id: 'verify',
      role: 'qa',
      description: '验证结果',
      priority: 'medium'
    });
  }
  
  return tasks;
}

/**
 * 为每个子任务生成 agent prompt
 */
function generateAgentPrompt(task, projectContext) {
  return `你是一个专业的 ${task.role}。

任务：${task.description}
项目上下文：${projectContext}

请完成以下工作：
1. 阅读相关代码文件
2. 分析当前状态
3. 执行任务要求的操作
4. 输出关键发现和结果

保持简洁，专注于你的角色职责。`;
}

/**
 * 主函数：模拟 ultrawork
 */
export async function ultrawork(taskDescription, projectPath = '.') {
  console.log('═══════════════════════════════════════════════════════════');
  console.log('           🚀 ultrawork - 多 agent 并行执行模式');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('');
  console.log('📋 任务:', taskDescription);
  console.log('📁 项目:', projectPath);
  console.log('');
  
  // 分解任务
  const tasks = parseTask(taskDescription);
  console.log(`✅ 任务分解完成，共 ${tasks.length} 个子任务`);
  console.log('');
  
  // 收集项目上下文
  let projectContext = '';
  try {
    const contextFile = path.join(projectPath, 'CONTEXT.md');
    if (fs.existsSync(contextFile)) {
      projectContext = fs.readFileSync(contextFile, 'utf8').substring(0, 500);
    }
  } catch (e) {
    projectContext = 'Charlie 语音助手项目';
  }
  
  // 显示任务计划
  console.log('📊 执行计划:');
  tasks.forEach((t, i) => {
    const icon = t.priority === 'high' ? '🔴' : '🟡';
    console.log(`   ${icon} [${i + 1}] ${t.role}: ${t.description}`);
  });
  console.log('');
  
  // 返回配置供 workflow 使用
  return {
    taskDescription,
    tasks,
    projectContext,
    parallel: true,
    maxConcurrent: Math.min(tasks.length, 3) // 最多同时 3 个
  };
}

// CLI 入口
if (process.argv[1]?.endsWith('ultrawork-simulator.mjs')) {
  const task = process.argv[2] || '分析项目结构';
  const project = process.argv[3] || '.';
  
  ultrawork(task, project).then(config => {
    console.log('\n⚡ ultrawork 配置已生成');
    console.log('   使用 workflow 工具执行并行任务...');
  }).catch(err => {
    console.error('❌ 错误:', err.message);
    process.exit(1);
  });
}
