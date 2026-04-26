# Stage 2: Architecture

## Required Documents

| Document | Schema Check |
|----------|-------------|
| STRUCTURE.md | Required sections: Component Registry (≥1 game-specific component), System Schedule (≥1 system per phase: Input/Logic/Materialization/Cleanup), Entity Archetypes, Build Order |

Documents listed here are verified by the stage gate hook. Missing or malformed documents block stage transition.

---

Design the ECS architecture based on the confirmed GDD.md. Write STRUCTURE.md from `.claude/templates/STRUCTURE.md` template.

- Read GDD.md §3 (Mechanics) and §5 (Characters & Entities) as primary input
- Decompose the game into Components (pure data) and Systems (logic)
- Define the system schedule with read/write dependencies
- Define entity archetypes and scene markers
- Specify build order

Each task in PLAN.md must be specific: not "implement movement" but "implement PlayerMovementSystem: reads PlayerInput + Velocity, writes Transform".

**Output:** STRUCTURE.md with complete Component Registry, System Schedule, Entity Archetypes, Build Order.

**Gate 2:**
- [ ] STRUCTURE.md has Component Registry with at least 1 game-specific component
- [ ] STRUCTURE.md has System Schedule with at least 1 system per phase (Input/Logic/Materialization/Cleanup)
- [ ] STRUCTURE.md has Entity Archetypes section
- [ ] STRUCTURE.md has Build Order section
- [ ] PLAN.md Task Status updated — each system has a corresponding task

**After passing Gate 2:** Update `.godotmaker/stage.json` — read existing (or create `{"completed_stages": {}}`), add `"2": "<UTC timestamp>"` to `completed_stages`, write back. Then proceed to Stage 3.
