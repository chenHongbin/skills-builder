# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个 Skills 构建器项目，用于创建和管理 Claude Code 技能。

当前包含的 skill：
- **claude-md-generator**: 通过对话为各类项目生成定制化 CLAUDE.md 文件

## Skill 开发

本项目使用 TDD for Skills 方法开发 skills：
- RED: 创建测试场景并记录基线
- GREEN: 编写 skill
- REFACTOR: 测试和完善

### 项目结构

```
Skills构建器/
├── skills/                          # Skill 源码（版本控制）
│   └── claude-md-generator/
│       └── skill.md                 # Skill 文档
├── tests/                           # 测试相关
│   ├── scenarios/                   # 测试场景
│   │   ├── react-project/          # React 项目测试
│   │   ├── data-analysis/          # 数据分析项目测试
│   │   └── content-creation/       # 内容创作项目测试
│   ├── baselines/                   # 基线测试结果
│   ├── results/                     # 改进后的测试结果
│   ├── test-prompts.md             # 测试提示
│   └── final-validation.md         # 最终验证文档
├── docs/                            # 文档
│   └── plans/                       # 实现计划
└── CLAUDE.md                        # 本文件
```

### 测试 Skill

#### 1. 测试场景
```bash
# React 项目测试
cd tests/scenarios/react-project
# 启动 Claude Code，测试 skill

# 数据分析项目测试
cd tests/scenarios/data-analysis
# 启动 Claude Code，测试 skill

# 内容创作项目测试
cd tests/scenarios/content-creation
# 启动 Claude Code，测试 skill
```

#### 2. 查看测试结果
```bash
# 基线测试（无 skill）
cat tests/baselines/react-baseline.md

# 改进后的测试（使用 skill）
cat tests/results/react-with-skill.md

# 最终验证
cat tests/final-validation.md
```

### Skill 位置

- **开发版本**: `skills/claude-md-generator/` （版本控制）
- **部署位置**: `~/.claude/skills/claude-md-generator/` （实际使用）
- **测试场景**: `tests/scenarios/`
- **测试结果**: `tests/results/`

### 部署 Skill

Skill 已部署到 `~/.claude/skills/claude-md-generator/`，可以在任何项目中使用。

### 开发规范

#### Git 提交规范
- `test: 测试相关变更`
- `feat: 新功能`
- `refactor: 重构`
- `docs: 文档更新`

#### Skill 开发流程
1. 创建测试场景
2. 运行基线测试（记录问题）
3. 编写 skill
4. 运行改进后的测试
5. 基于反馈完善
6. 最终验证
7. 文档和部署

## 测试结果

### claude-md-generator Skill
- **版本**: 1.0
- **测试覆盖**: React 项目完整测试
- **改进效果**:
  - 文档精简度: -70%（97 行 → 29 行）
  - 消除通用建议: -100%（68 行 → 0 行）
  - 命令准确性: 100%
- **评分**: 8/10 分
- **状态**: ✅ 已部署，可用于生产
