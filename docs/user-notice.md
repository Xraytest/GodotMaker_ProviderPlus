# User Notice

Things GodotMaker does automatically during setup, and why.

## Publish Script Auto-Actions

The publish script (`tools/publish.py`) performs the following actions in your
game project directory to lower the setup barrier. If you are experienced with
these tools, feel free to manage them yourself — the script skips steps that
are already done.

### Git Repository Initialization

**What happens:** If your project directory does not have a `.git/` folder,
the publish script runs `git init` and creates an initial empty commit.

**Why:** GodotMaker uses parallel workers that run in isolated git worktrees
(`git worktree add`). Git worktrees require at least one commit to exist —
without it, the command fails with:

```
fatal: not a valid object name: 'HEAD'
```

This has nothing to do with pushing code to GitHub or any remote server.
The commit is purely local and exists only to enable the parallel worker
infrastructure.

**What if I already have a git repo?** The script detects `.git/` and skips
`git init`. If a commit already exists, it skips that too. Your existing
history is never modified.

**What if I don't want git?** Parallel workers will fall back to sequential
execution if worktree creation fails. The game will still be generated, but
implementation may take longer since workers run one at a time.
