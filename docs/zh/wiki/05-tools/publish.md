# 发布

`publish.py` 将 GodotMaker 框架安装到目标 Godot 项目文件夹中。创建新项目时运行一次，以后每次升级 GodotMaker 时再次运行。

## 全新安装

把 `publish.py` 指向一个空文件夹（或已有的 Godot 项目文件夹），它会自动创建所需的一切：

```bash
python tools/publish.py /path/to/my-game
```

Windows 上：

```powershell
python tools\publish.py C:\Games\my-game
```

第一次运行时，脚本会询问你的 Godot 可执行文件完整路径。按提示输入即可——每个项目只需输入一次。

**会创建哪些内容：**

| 位置 | 说明 |
|----------|------------|
| `.claude/skills/` | 所有 GodotMaker 斜杠命令（`/gm-*` 系列命令及配套技能） |
| `.claude/agents/` | worker、verifier、reviewer、analyst 等 helper 的定义文件 |
| `.claude/settings.json` | 告知 Claude Code 要运行哪些 hook 脚本以及何时运行 |
| `.claude/godotmaker.yaml` | 你的 Godot 可执行文件路径（仅对本机有效） |
| `.godotmaker/hooks/` | 让 AI 保持正轨的约束脚本 |
| `.godotmaker/config.yaml` | 项目级配置（模型选择、素材生成提供商等） |
| `.godotmaker/version` | 记录当前项目安装的 GodotMaker 版本 |
| `tools/` | 实用脚本（`check_env.py`、`check_project.py`、`asset_gen.py` 等） |
| `.claude/templates/` | `/gm-gdd` 等命令使用的文档模板 |
| `CLAUDE.md` | 项目专属指令，Claude Code 每次会话开始时都会读取 |
| `assets/sprites`、`assets/audio`、`assets/fonts`、`assets/ui`、`references/` | 标准素材文件夹 |

脚本还会注册 `godot-mcp` 服务器（让 Claude Code 能与 Godot 编辑器通信），若项目中尚无 git 仓库则自动初始化，并创建包含正确条目的 `.gitignore`。

## 升级已有项目

在已经发布过的项目里再次运行同一条命令。GodotMaker 会对比自身版本号与 `.godotmaker/version` 中记录的版本号，然后决定如何处理：

| 升级类型 | 处理方式 |
|--------------|--------------|
| **Patch**（如 0.3.0 → 0.3.1） | 自动执行——向后兼容的 bug 修复。执行所有未应用的迁移脚本 |
| **Minor**（如 0.3.0 → 0.4.0） | 展示变更日志，要求确认。执行所有未应用的迁移脚本 |
| **Major**（如 0.x → 1.x） | 需要加 `--force`——破坏性变更，需要干净的重新初始化。跳过迁移，重装后重新 baseline |
| **版本相同** | 始终执行——适合在本地修改框架后重新部署。本地新加但未 bump `VERSION` 的迁移脚本也会被执行 |
| **降级** | 默认阻止，需要 `--force` 才能强制执行。迁移不会回滚（无反向迁移机制），如需回滚请从 VCS 恢复 |

> 迁移脚本与 bump 级别相互独立。每个迁移都是 `migrations/` 下的带时间戳脚本；
> 目标项目在 `.godotmaker/applied_migrations.json` 里记录已应用过哪些。
> PATCH 和 MINOR 都会执行所有未应用的脚本。完整策略见
> [`../../versioning.md`](../../versioning.md)。

完整的升级策略与迁移脚本说明请参见 [`../../versioning.md`](../../versioning.md)。各版本变更内容请查阅[更新日志](../08-reference/changelog.md)。

## 选项

```bash
python tools/publish.py --force /path/to/my-game
```

`--force` 同时做四件事：

1. 重新部署前清空 `.claude/skills/`，移除旧版本遗留的技能文件。
2. 即使你已自定义过 `.claude/settings.json`，也会强制覆盖。
3. 跳过 minor 和 major 升级的确认提示。
4. 允许降级。

对于加了 `--force` 的 **major** 升级，清理范围更大：`.claude/skills/`、`.claude/agents/`、`.claude/config/`、`.claude/templates/`、`.godotmaker/hooks/`、`tools/` 以及运行时状态文件都会被清空并从头重建。

## 升级时哪些内容会被保留

正常发布不会覆盖以下文件（只有 `--force` 才能改动 `settings.json`）：

| 文件 | 保留原因 |
|------|---------------|
| `CLAUDE.md` | 你可能添加了项目专属指令 |
| `.claude/settings.json` | 你可能调整过 hook 行为 |
| `.claude/godotmaker.yaml` | 包含本机专属的 Godot 路径 |
| `.godotmaker/config.yaml` | 包含项目专属的偏好设置 |

你的游戏代码、场景、素材以及规划文档（`GDD.md`、`PLAN.md` 等）不受 publish 影响——它只管理框架层。
