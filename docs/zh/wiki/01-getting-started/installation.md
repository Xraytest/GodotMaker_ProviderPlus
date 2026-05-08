# 安装

GodotMaker 能把你用普通话描述的游戏想法，变成一个可以运行的 Godot 4 游戏。要做到这一点，需要五款软件协同工作：Godot（运行游戏的引擎）、Git（版本控制，让 AI 能安全地保存每一次改动）、Node.js（GodotMaker 用来从命令行与 Godot 通信的运行环境）、Python（负责素材生成流水线和环境检查）、以及 Claude Code（驱动整个流程的 AI 助手）。这篇指南会带你把五款软件都装好、填入图片生成所需的 API Key，并在制作第一款游戏前确认一切正常。

## 前置软件

| 工具 | 最低版本 | GodotMaker 为什么需要它 | 下载地址 |
|------|----------|------------------------|---------|
| Godot | 4.5+ | 编译并运行生成的游戏 | https://godotengine.org/download |
| Git | 2.30+ | 追踪每一个文件改动；让 AI 能并行工作而不冲突 | https://git-scm.com/downloads |
| Node.js | 18+ | 提供 `npx`，GodotMaker 用它把 Claude Code 连接到 Godot | https://nodejs.org（选 LTS 版本）|
| Python | 3.9+ | 生成美术素材、运行环境检查、驱动端到端测试 | https://python.org/downloads |
| Claude Code | 最新版 | 你输入指令的 AI 助手 | `npm install -g @anthropic-ai/claude-code` |

按照上面的链接把每款软件都装好，然后继续。

## API Key

GodotMaker 用 Google Gemini 来生成游戏里的美术素材（精灵图、背景、图标）。这需要一个免费的 API Key。另外两个 Key 是可选的，只是多了额外的图片生成方式。

| Key | 是否必填 | 解锁的功能 |
|-----|---------|-----------|
| `GOOGLE_API_KEY` | **必填** | 图片生成和视觉质量检查——每个项目都需要。免费获取地址：https://aistudio.google.com/apikey |
| `XAI_API_KEY` | 可选 | 用 xAI Grok 作为第二个图片生成选项（有时更便宜）。获取地址：https://console.x.ai |
| `TRIPO3D_API_KEY` | 可选 | 生成 3D 模型，仅在做 3D 游戏时有用。获取地址：https://www.tripo3d.ai |

### 在 Windows 上设置 Key（PowerShell）

下面的命令会把 Key 永久存入你的 Windows 用户账户，只需要做一次。

```powershell
[System.Environment]::SetEnvironmentVariable("GOOGLE_API_KEY", "your-key-here", "User")
```

如果要添加可选的 Key，用同样的命令换掉 Key 名称再运行一次即可。

运行这些命令后，关闭终端再重新打开，新的值才会生效。

### 在 macOS 或 Linux 上设置 Key

把下面几行加到你的 Shell 配置文件（用 Bash 就加到 `~/.bashrc`，用 Zsh 就加到 `~/.zshrc`），然后重启终端。

```bash
export GOOGLE_API_KEY="your-key-here"
# 可选：
# export XAI_API_KEY="your-key-here"
# export TRIPO3D_API_KEY="your-key-here"
```

## 分步安装

### 1. 克隆 GodotMaker 仓库

这一步把 GodotMaker 的工具和技能定义下载到你的电脑。只需要做一次。克隆下来的文件夹是 GodotMaker 框架本身——不是你的游戏项目。

```bash
git clone https://github.com/RandallLiuXin/GodotMaker.git
cd GodotMaker
```

### 2. 设置 Git 身份

Git 会记录每次改动是谁做的。如果你从来没设置过，运行：

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

### 3. 安装 Python 依赖

```bash
pip install -r tools/requirements.txt
```

这会安装负责图片生成、视觉质量检查和端到端测试的 Python 包。

### 4. 运行环境检查

```bash
python tools/check_env.py
```

检查工具会验证所有前置条件，并逐条打印结果：

- `[PASS]` — 没问题
- `[WARN]` — 某个可选功能缺失；游戏仍然能生成，但该功能不可用
- `[FAIL]` — 某个必要项缺失；必须修复后才能继续

继续之前，把所有 `[FAIL]` 都修好。`[WARN]` 可以暂时跳过，除非你确实需要它描述的可选功能。

## 下一步

环境检查没有 `[FAIL]` 之后，就可以开始制作第一款游戏了。前往[你的第一款游戏](first-game.md)。
