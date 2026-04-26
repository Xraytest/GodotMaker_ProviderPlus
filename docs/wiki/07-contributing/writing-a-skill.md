# Writing a Skill

This guide covers how to create a new skill for GodotMaker. Skills are prompt bundles that Claude reads at task time -- they deliver domain knowledge, step-by-step procedures, and known pitfalls to the AI agents.

## Directory Structure

Create a new directory under the appropriate layer:

```
skills/core/<skill-name>/       # For procedural skills (how to do something)
skills/reviewer/<skill-name>/   # For post-implementation reviewers (what to check)
```

Skill names use lowercase kebab-case: `headless-build`, `visual-qa`, `game-planner`.

## Required File: SKILL.md

Every skill must have a `SKILL.md` at its root. This is the prompt that Claude reads when the skill is invoked.

### Frontmatter

Start with a YAML frontmatter block:

```yaml
---
name: my-skill
description: |
  One paragraph explaining what this skill does and when to use it.
  Include concrete trigger phrases so the orchestrator can match tasks to this skill.
  Be specific: "Use when..." and "Triggers: ..." help with automatic dispatch.
  Also specify what this skill does NOT cover to prevent false matches.
context: fork          # Optional. Runs in a subagent (isolated context).
model: sonnet          # Optional. Override model (default is the lead agent's model).
agent: Explore         # Optional. Agent mode hint.
---
```

The `description` field is critical -- it determines when the orchestrator dispatches this skill. Write it as if answering: "Under exactly what circumstances should Claude use this skill instead of another?"

### Body

The body contains the instructions Claude follows. Guidelines:

1. **State the purpose clearly** in the first paragraph. What does this skill produce?
2. **Provide step-by-step instructions**. Number the steps. Claude follows them sequentially.
3. **Include example outputs** where possible. Show what correct output looks like.
4. **Specify failure modes**. What should Claude do when a step fails?
5. **Reference other skills** by name when there are handoff points (e.g., "After scaffolding, run `headless-build` to verify compilation").
6. **Use `$ARGUMENTS`** as a placeholder for runtime arguments passed to the skill.

### Example: minimal core skill

```markdown
---
name: my-tool
description: |
  Runs my-tool against the project. Use when the user says "check X"
  or after modifying X-related files. Does NOT handle Y -- use other-skill for that.
---

# My Tool

$ARGUMENTS

## Step 1 -- Locate the project

Read `.godotmaker/config.yaml` to find the project path.

## Step 2 -- Run the check

\```bash
my-tool --project "${PROJECT_PATH}" 2>&1
\```

## Step 3 -- Parse results

If the tool exits 0, report success. If non-zero, extract error lines
and present them as a numbered list with file paths and line numbers.

## Step 4 -- Fix guidance

For each error, suggest a fix. Reference the relevant Godot docs if applicable.
```

## Optional Files

### references/

A directory for supporting documents the skill references. Examples:

- API excerpts that Claude needs but cannot reliably recall
- Configuration file format specifications
- Protocol documentation for external tools

Keep reference files focused. A 200-line API excerpt is better than a 5000-line full dump.

### gotchas.md

A curated list of known engine pitfalls. Primarily used by reviewer skills but also useful for core skills like `gecs` that have their own gotchas.

Format each entry consistently:

```markdown
## G1. Short descriptive title [GDScript] [C#]

**Symptom**: What goes wrong from the developer's perspective.

**Root cause**: Why the engine behaves this way.

**Correct approach**: The right pattern to use.

**Wrong approach**: What LLMs typically generate (and why it fails).
```

Tag entries with `[GDScript]`, `[C#]`, or both to indicate which languages are affected.

### checklist.md

Automated check procedures that map back to gotchas. Used by reviewer skills to systematically verify code.

```markdown
## Static Checks

### S1. Check name -> G1
Grep for [specific pattern]:
- [condition that indicates a problem]
- [expected correct pattern]

### S2. Another check -> G2
For every [node type] in the project:
- [property] is not [bad value]
- [property] is explicitly set
```

Number checks with `S` prefix (static) or `R` prefix (runtime). Map each to a gotcha with `-> G{n}`.

### templates/

File templates with `{{placeholder}}` syntax, used by skills like `project-scaffold` that generate project files. The skill's SKILL.md instructions should document which placeholders are available and how they are filled.

### scripts/

Helper scripts (Python, Bash) that the skill invokes. Keep scripts small and focused on a single operation.

### evals/

Test cases for measuring skill accuracy. Used during skill development to verify the skill produces correct outputs.

## Creating a Reviewer Skill

Reviewer skills follow a strict pattern. All three files are expected:

```
skills/reviewer/my-domain/
    SKILL.md
    checklist.md
    gotchas.md
```

### Reviewer SKILL.md template

```markdown
---
name: my-domain-review
description: |
  Reviews Godot {domain} implementation for known pitfalls.
  Triggers AFTER implementation, when code involves {list of relevant classes,
  methods, and properties}.
  Do NOT use this skill for planning or teaching -- only for post-implementation review.
---

# {Domain} Review

Post-implementation reviewer for Godot {domain} code. Checks against known
gotchas that LLMs consistently get wrong.

## When to trigger

After {domain}-related code is written or modified. Look for:
- {Node types}
- {Method calls}
- {Property assignments}

## Review procedure

1. Read `gotchas.md` in this skill directory
2. Read `checklist.md` in this skill directory
3. For each static check in the checklist:
   a. Grep the files under review for the specified patterns
   b. Flag any matches as potential issues
   c. Reference the corresponding gotcha ID in the report
4. Compile a report with: file path, line number, issue description, gotcha reference

## Report format

For each issue found:
- **File**: path/to/file.gd:42
- **Issue**: [description of what is wrong]
- **Gotcha**: G{n} -- [gotcha title]
- **Fix**: [concrete fix suggestion]
```

### Building the gotcha database

Good gotchas come from:

1. **Godot migration guides** -- API changes between versions that LLMs trained on old docs get wrong.
2. **GitHub issues** -- Recurring bugs reported by users that stem from API misunderstanding.
3. **Forum patterns** -- Questions asked repeatedly on Godot forums and Reddit.
4. **LLM testing** -- Run Claude/GPT against Godot tasks without the skill and catalog the mistakes.

Each gotcha should be something an LLM would plausibly get wrong, not something obvious. "Call `queue_free()` to delete a node" is not a gotcha. "Calling `queue_free()` inside `body_entered` crashes because the physics space is locked" is.

## Testing a Skill

### Manual testing

1. Publish skills to a test project:
   ```bash
   python tools/publish.py /path/to/test-project
   ```

2. Open Claude Code in the test project directory.

3. Invoke the skill directly or trigger it through the orchestrator.

4. Verify:
   - The skill activates on the expected triggers
   - The instructions produce correct output
   - Edge cases are handled (missing files, compilation errors, empty results)

### Eval testing

For skills with an `evals/` directory, run the eval suite to measure accuracy against known-good outputs. This is particularly important for API reference skills where hallucination is the primary risk.

## Registration

Skills auto-deploy via `publish.py`. There is no manual registration step. When you run:

```bash
python tools/publish.py /path/to/project
```

The script walks `skills/core/` and `skills/reviewer/`, copies every skill directory into `<project>/.claude/skills/`, and Claude Code picks them up automatically based on their SKILL.md frontmatter.

To add a new skill to the deployment:

1. Create the directory under `skills/core/` or `skills/reviewer/`.
2. Add at minimum a `SKILL.md` with valid frontmatter.
3. Run `publish.py` -- the new skill is included automatically.

No changes to publish.py or any configuration file are needed.
