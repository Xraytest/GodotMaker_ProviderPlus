# 检查项目

`check_project.py` 检查已生成的游戏项目，查找缺失文件、结构损坏及其他不一致问题。构建结果异常时，或在封口 tag 之前，都可以运行它。

```bash
python tools/check_project.py /path/to/my-game
```

不加任何标志时，所有检查都会运行。也可以只运行特定类别：

```bash
python tools/check_project.py /path/to/my-game --ecs --tests
python tools/check_project.py /path/to/my-game --all
```

## 类别标志

| 标志 | 检查内容 |
|------|---------------|
| `--build` | `project.godot` 是否存在，且包含有效的 `[application]` 节 |
| `--ecs` | gecs 插件是否存在；游戏代码中是否有 Component 和 System 文件 |
| `--tests` | gdUnit4 插件是否存在；每个 System 是否都有对应的单元测试文件 |
| `--e2e` | godot-e2e 插件是否已启用；`e2e/` 中是否有真实的测试函数而非占位符 |
| `--plan` | `PLAN.md` 和 `STRUCTURE.md` 是否存在且包含正确的章节 |
| `--mcp` | `godot-mcp` 服务器是否已注册到 `.mcp.json` |
| `--all` | 执行以上全部检查 |

## 能发现哪些问题

**构建就绪性** — 确认 `project.godot` 存在且结构有效。项目文件缺失意味着 Godot 根本无法打开该项目。

**ECS 配置** — 确认 `addons/gecs/` 已安装，且游戏中确实存在 `extend Component` 和 `extend System` 的 GDScript 文件。两者都没有，说明项目尚未开始构建（或构建被中断了）。

**单元测试覆盖率** — 检查每个 System 文件是否都有对应的测试文件。匹配规则包括 `test_movement_system.gd`、`movement_system_test.gd`、`testmovementsystem.gd` 等形式。没有测试文件的 System 会按名称列出。

**端到端测试** — 检查 `e2e/conftest.py` 是否存在，`e2e/` 目录下是否有 `test_*.py` 文件，以及这些文件中是否包含真实的 `def test_` 函数而不是空的桩代码。文件过短或含有 "todo"/"stub" 关键字的占位文件会触发警告。

**规划文档** — 确认 `PLAN.md` 存在且包含任务状态标记（`pending`、`in_progress`、`completed` 等），`STRUCTURE.md` 包含 Component Registry 和 System Schedule。这两份文档是 `/gm-build` 和 `/gm-fixgap` 的执行依据。

**MCP 注册** — 检查 `.mcp.json` 中是否包含 `"godot"` 服务器条目，这是由 `publish.py` 创建的。没有它，Claude Code 就无法向 Godot 编辑器发送命令。

## 何时运行

- 构建出现报错或意外行为之后。
- 运行 `/gm-finalize` 之前，确认项目已完整。
- 搁置较久后重新打开项目时，了解当前状态。
- 手动添加或重命名文件之后，确认没有引入问题。

## 读懂输出结果

```
[PASS] project.godot exists
[FAIL] No System files found (files extending System)
[WARN] MEMORY.md not found (optional but recommended)
```

失败项会在末尾汇总展示：

```
==================================================
Total: 18 checks
  PASS: 15
  FAIL: 2
  WARN: 1

Result: CHECKS FAILED
Failed checks:
  - No System files found (files extending System)
  - Systems without test files: movement_system, spawn_system
```

## 退出码

| 退出码 | 含义 |
|------|---------|
| 0 | 所有检查通过 |
| 1 | 一项或多项检查失败 |
| 2 | 项目目录不存在 |
