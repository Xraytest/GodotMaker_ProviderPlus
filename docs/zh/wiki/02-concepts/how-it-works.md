# 工作原理

GodotMaker 把你的游戏描述变成真正可运行的游戏，靠的是按顺序执行 9 个小步骤。每个步骤对应一条斜杠命令，你输入命令，它做完一件事就停下来。

```mermaid
flowchart TD
    A[/gm-scaffold] --> B[/gm-gdd]
    B --> C[/gm-asset]
    C --> D[/gm-build]
    D --> E[/gm-verify]
    E --> F[/gm-evaluate]
    F --> G{approve?}
    G -- yes --> H[/gm-accept]
    G -- no --> I[/gm-fixgap]
    H --> J[/gm-finalize]
    I --> E
```

每次跳到下一步都由你来决定。在你没有主动输入命令之前，什么都不会自动运行——准备好了再继续就行。

---

## 四个阶段

### 准备阶段 — `/gm-scaffold`、`/gm-gdd`、`/gm-asset`

这三条命令负责在正式写游戏代码之前把所有东西都备齐。

`/gm-scaffold` 创建一个空的 Godot 项目：建好正确的目录结构，安装所需的插件，并提交第一个 git commit。每个项目只在最开始运行一次。

`/gm-gdd` 会问你一些关于游戏的问题，然后写出一套策划文档：游戏设计文档（`GDD.md`）、任务计划（`PLAN.md`）、目录结构（`STRUCTURE.md`）、场景列表（`SCENES.md`）以及资源清单（`ASSETS.md`）。这套文档就是后续所有步骤共同遵守的"合同"。

`/gm-asset` 读取资源清单，要么自动生成美术文件，要么分析你已经准备好的图片。构建阶段需要真实的美术资源才能运转——这条命令负责确保这些资源都到位。

### 构建阶段 — `/gm-build`

`/gm-build` 读取 `PLAN.md`，实现整个游戏。它不会自己直接写代码，而是把每项任务交给专门的 Worker（执行者）——一个聚焦的辅助 Agent，每次只负责实现一个游戏系统并附带单元测试，完成后汇报结果。每完成大约 5 个 Worker 之后，Verifier（验证者）会启动，无界面运行 Godot 构建并检查测试是否通过。接着，Reviewer（评审者）会根据 Godot 特有的易错点（物理陷阱、UI 布局规则、动画注意事项等）检查代码质量。如果 Reviewer 发现问题，新任务会被追加到计划中，循环继续，直到全部清零。

### 检查阶段 — `/gm-verify`、`/gm-evaluate`

`/gm-verify` 做快速机械检查：项目能不能编译，单元测试能不能过，有没有文件缺失。

`/gm-evaluate` 则是一次完全独立的审视。它对整个构建过程一无所知，从零出发——运行游戏、截图、写端到端测试，对照 `GDD.md` 的承诺给结果打分。一旦发现不符合预期的地方——某个功能缺失、某个场景显示异常、游戏崩溃——就会输出一份拒绝报告，列出具体问题清单。

### 交付阶段 — `/gm-accept`、`/gm-fixgap`、`/gm-finalize`

如果 `/gm-evaluate` 通过，你运行 `/gm-accept`。GodotMaker 展示结果并请你确认，你的决定会被记录下来。

如果 `/gm-evaluate` 拒绝，你改为运行 `/gm-fixgap`。它读取评估报告的问题列表，生成修复计划，派 Worker 逐一处理，然后重新回到 `/gm-verify` 和 `/gm-evaluate`。这个循环一直持续，直到你拿到通过结果。

通过之后，`/gm-finalize` 收尾：把当前 tag 的工作文档归档到 `docs/tags/<Tag>/`、写一份按 tag 的 changelog、在本地执行 `git tag <Tag>`，并重置每 tag 的运行时状态。然后你可以用下一个 `/gm-gdd` 开启下一个 tag，或者就停在这里。

---

## 为什么这不只是个花哨的聊天机器人

### 文件锁权限

当你运行某个角色命令时，GodotMaker 会把该角色的名字写入 `.godotmaker/current_role` 文件。每次有文件即将被写入时，一个小型 Python 脚本都会检查——不属于这个角色权限范围的写操作一律拒绝。举个例子：在 `/gm-evaluate` 阶段，评估者只能写入 `e2e/` 和 `.godotmaker/`，碰不到任何游戏代码；在 `/gm-build` 阶段，主 Agent 不能直接写 `.gd` 或 `.tscn` 文件，必须通过 Worker 来写。这样就防止了 AI 走捷径或在错误角色下搞破坏。

### Worker-Verifier-Reviewer 循环

在 `/gm-build` 和 `/gm-fixgap` 内部，质量检查不是可选项。当会话试图结束时，一个"完成检查" hook 会触发。如果 Worker 运行了但 Verifier 和 Reviewer 还没跑，会话就会被阻止退出。AI 不能宣布构建完成然后跳过检查。

### 独立评估环节

`/gm-evaluate` 全程从零开始——它读取 GDD 和游戏文件时就像第一次见到它们一样。它不被允许复用构建阶段得出的任何结论。这给了你一个真实的第二意见：问的不是"我们是不是把代码都写完了"，而是"游戏有没有真正按描述运转"。

---

要查看每条命令的详细说明，参见 [the-9-roles.md](the-9-roles.md)。
