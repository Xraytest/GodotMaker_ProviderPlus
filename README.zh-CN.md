# GodotMaker

[![License: BUSL 1.1](https://img.shields.io/badge/License-BUSL_1.1-orange.svg)](LICENSE)
[![Godot 4.x](https://img.shields.io/badge/Godot-4.x-blue?logo=godotengine)](https://godotengine.org)
[![CI](https://github.com/RandallLiuXin/GodotMaker/actions/workflows/ci.yml/badge.svg)](https://github.com/RandallLiuXin/GodotMaker/actions/workflows/ci.yml)

[English](README.md) | **中文**

**基于 ECS 的自然语言生成游戏框架，适用于 Godot 引擎。**

GodotMaker 将自然语言的游戏描述转化为可运行的 Godot 项目。它结合 AI 编排器（Claude Code skills）与实体组件系统（[gecs](https://github.com/csprance/gecs)），自动生成 GDScript 代码、场景和资产——全部在 Godot 编辑器内完成。

## 特性

- **文字转游戏流水线** — 描述游戏概念，GodotMaker 自动搭建项目、生成 ECS 组件/系统、连接场景。
- **ECS 优先架构** — 基于 gecs 构建。Component 仅存数据，System 声明查询；场景树仅保留给 UI/菜单。
- **场景即生成器** — 场景仅包含标记节点（元数据），运行时将其转换为 ECS 实体。
- **两层技能系统** — 核心技能（编排、构建、测试、ECS、资产管线、e2e）+ 审查技能（物理、动画、UI、音频、tilemap、navigation、shader、particles）。
- **Hook 强制流水线** — 8 个 hook 把守流水线：文件权限、阶段前置、报告校验、完成检查。Orchestrator 不能跳过阶段也不能自我认证。
- **自动化验证** — `godot --headless --quit` 构建、gdUnit4 单测、godot-e2e 集成测、截图视觉对照。

## 环境要求

| 依赖 | 版本 |
|------|------|
| [Godot Engine](https://godotengine.org) | 4.x |
| [gecs](https://github.com/csprance/gecs) | 最新 |
| [gdUnit4](https://github.com/MikeSchulze/gdUnit4) | 最新（Godot 4.4 用 v5.x，4.5+ 用 v6.x） |
| [Claude Code](https://claude.ai/code) | 最新 |
| Python | 3.10+ |
| .NET SDK | 8.0+（仅 C# 项目需要） |

## 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/RandallLiuXin/GodotMaker.git
cd GodotMaker

# 2. 安装 Python 依赖
pip install -r tools/requirements.txt

# 3. 安装 git hooks（包含 gitleaks 密钥扫描）
bash scripts/install-hooks.sh

# 4. 将 GodotMaker 技能部署到 Claude Code
python tools/publish.py

# 5. 打开目标 Godot 项目，通过 Claude Code 使用 GodotMaker
```

## 项目结构

```
skills/
  core/         # 编排器、godot-api、无头构建、gdunit 驱动、
                # gdtoolkit、gecs、游戏规划、项目脚手架、
                # 视觉 QA、截图、mcp 驱动、godot-e2e
  reviewer/     # 物理、动画、UI、瓦片地图、导航、着色器、音频、粒子
  pattern/      # 游戏类型模板（计划中）
shell/          # publish.sh / publish.ps1、_read_config.sh
tools/          # publish.py、check_env.py、asset_gen、rembg、check_project
templates/      # PLAN / STRUCTURE / ASSETS / MEMORY 文档模板
docs/           # getting-started.md、wiki/、reference/
```

## 架构概览

```
自然语言描述
      |
      v
游戏规划器  ──>  项目脚手架  ──>  ECS 代码生成
      |                                |
      v                                v
资产生成                          无头构建 + 测试
      |                                |
      v                                v
场景组装  ──────────────────>  E2E 与视觉校验
      |                                |
      v                                v
可运行的 Godot 项目  <──  MCP 调试（升级路径）
```

**路线图与设计笔记** 见 [`ROADMAP.md`](ROADMAP.md) 与 [wiki](docs/wiki/)。

## 测试

GodotMaker 使用 [gdUnit4](https://github.com/MikeSchulze/gdUnit4)，遵循 TDD 方法。

```bash
# 运行单个测试文件
godot --headless -s addons/gdunit4/bin/gdunit4_run.gd --single --file res://test/xxx.gd

# 运行 Python 工具测试
pytest
```

## 贡献

欢迎贡献！请在提交 PR 前阅读 [贡献指南](CONTRIBUTING.md)。

## 许可证

本项目基于 [Business Source License 1.1](LICENSE) 许可。
