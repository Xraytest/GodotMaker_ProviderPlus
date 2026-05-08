# GodotMaker

[![License: BUSL 1.1](https://img.shields.io/badge/License-BUSL_1.1-orange.svg)](LICENSE)
[![Godot 4.x](https://img.shields.io/badge/Godot-4.x-blue?logo=godotengine)](https://godotengine.org)
[![CI](https://github.com/RandallLiuXin/GodotMaker/actions/workflows/ci.yml/badge.svg)](https://github.com/RandallLiuXin/GodotMaker/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-online-teal)](https://RandallLiuXin.github.io/GodotMaker/zh/)

[English](README.md) | **中文**

> **描述你的游戏。运行它。它属于你。** —— 源码可见、本地优先，产物归你。

GodotMaker 把一句话描述变成真正能跑的 Godot 游戏。输入 *"做一个吸血鬼幸存者风格的游戏，三种武器，能升级"*，等几分钟，打开 Godot 就能玩。不需要会做游戏，不收订阅费，不锁平台。整个项目就在你电脑上，归你所有，随你修改、发布、分享。

## 你能拿到什么

- **一个真正的 Godot 项目** 在你电脑上。随时用 Godot 编辑器打开，想改什么改什么。
- **完全免费**。在你自己电脑上跑，用你已经有的 AI 工具。没有平台费，没有调用次数上限。
- **源码可见**，采用 BUSL 1.1。没有黑盒，也不是封闭平台转卖。
- **整个 Godot 生态都能用** —— 各种插件、导出工具、编辑器本身。你的游戏能走多远完全看你自己。

## 适合谁用？

- 你有游戏想法，但从没学过游戏引擎。
- 你是设计师、爱好者、学生、内容创作者，想看看自己的点子能不能跑起来。
- 你想要一个能玩的原型，并且 AI 做完之后还能继续往下做。

GodotMaker 解决的是从 *"我有个想法"* 到 *"我有个能玩的东西"* 这一段。之后，整个 Godot 生态都在你手里 —— 在编辑器里继续打磨、接入社区插件、边做边学，把一个原型养成你真正想发布的游戏。

## 大致流程（30 秒看懂）

1. 在一个空文件夹里安装 GodotMaker。一行命令。
2. 在那个文件夹里打开 Claude Code，输入 `/gm-scaffold`。AI 把 Godot 项目、插件、目录结构搭好。然后 `/gm-gdd` 会问你一些问题，搞清楚你想做什么样的游戏。
3. 接下来七个命令一个个跑。每个命令之间，AI 自己干活 —— 写代码、生成美术、构建项目、跑游戏、截图、给结果打分。
4. 你觉得满意了就接受、归档。打开 Godot 就能玩。

一个小游戏通常只需要你花大概 30 分钟时间（分散在整个会话里）—— 命令之间 AI 在后台跑，你不用盯着。

[完整教程 →](https://RandallLiuXin.github.io/GodotMaker/zh/wiki/01-getting-started/first-game/)

## 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/RandallLiuXin/GodotMaker.git
cd GodotMaker

# 2. 安装依赖并检查环境
pip install -r tools/requirements.txt
python tools/check_env.py

# 3. 把 GodotMaker 部署到一个新游戏文件夹
python tools/publish.py /path/to/my-game
cd /path/to/my-game
claude
```

进入 Claude Code 后，从 `/gm-scaffold` 开始按顺序输入九个命令。完整教程见 [你的第一款游戏](https://RandallLiuXin.github.io/GodotMaker/zh/wiki/01-getting-started/first-game/)。

## 你需要准备

| 工具 | 用途 |
|---|---|
| [Godot 4.5+](https://godotengine.org)（推荐；4.3/4.4 仍然支持） | 你的游戏会跑在这个引擎里 |
| [Claude Code](https://claude.ai/code) | 你和 AI 对话的入口 |
| Python 3.10+ | 跑那些帮你串起流水线的脚本 |
| `GOOGLE_API_KEY` | 免费额度；用来生成游戏的美术资源 |

可选：.NET SDK 8.0+ —— 如果你想要 C# 项目而不是 GDScript。

## 文档

- [**30 分钟上手**](https://RandallLiuXin.github.io/GodotMaker/zh/wiki/01-getting-started/first-game/) —— 第一款游戏，一步步来
- [工作原理](https://RandallLiuXin.github.io/GodotMaker/zh/wiki/02-concepts/how-it-works/) —— 每个命令做了什么、为什么这么设计
- [常见问题](https://RandallLiuXin.github.io/GodotMaker/zh/wiki/04-troubleshooting/common-problems/) —— 出问题的时候看这里
- [完整 wiki](https://RandallLiuXin.github.io/GodotMaker/zh/) —— 所有页面

## 路线图

接下来要做的：

- **更多优质插件技能接入** —— 一线接入 Godot 社区主流插件（Phantom Camera、Dialogic、Beehave、GodotSteam ……）。
- **更多美术资源生成工作流** —— 更全面的精灵、动画、tileset、音频、3D 模型生成管线。
- **多平台发布** —— 一键导出到 Steam、iOS、Google Play、Web。
- **图形化界面** —— 不用命令行也能用的可视化前端。

完整清单和已完成项见 [`ROADMAP.md`](ROADMAP.md)。

## 参与贡献

欢迎贡献 —— bug 修复、新的评审技能、插件集成、翻译，什么都行。从 [开发环境](https://RandallLiuXin.github.io/GodotMaker/zh/wiki/07-contributing/development-setup/) 和 [贡献指南](CONTRIBUTING.md) 开始。

## 许可证

Business Source License 1.1。见 [LICENSE](LICENSE)。每个发布版本会在首次公开发布 4 年后自动转为 Apache License 2.0。**用 GodotMaker 做出来的游戏不是 GodotMaker，本身完全属于你**，但仍需遵守第三方引擎、素材、模型 provider、runtime 或依赖项可能适用的条款。
