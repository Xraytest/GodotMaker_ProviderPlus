# {System/Module Name}

<!-- Sub-system memory file. Created when a system is implemented.
     Placed in memory/ directory alongside MEMORY.md.
     e.g., MEMORY.md is at project root, this file at memory/{name}.md -->

## Overview

- **Files:** {list of source files this system owns}
- **Components read:** {which Components this system reads}
- **Components written:** {which Components this system writes}
- **Dependencies:** {other systems this depends on, execution order constraints}

## Design Decisions

<!-- Why this system was built this way. Key tradeoffs and rationale. -->

- {decision}: {rationale}

## Implementation Notes

<!-- How the system works at a high level. Enough for another agent to understand
     without reading every line of code. -->

{Brief description of the algorithm/approach, 3-5 sentences max.}

## Test Coverage

- **Unit tests:** {test file path, number of test cases, what they cover}
- **E2E coverage:** {which e2e scenarios exercise this system, if any}

## Discoveries

<!-- What was learned during implementation that wasn't obvious beforehand. -->

- {discovery}

## Gotchas

<!-- Pitfalls specific to this system. Things a future modifier must know. -->

- {gotcha}: {workaround or correct approach}

## Open Issues

<!-- Known limitations, TODOs, or deferred work. -->

- {issue}: {status or plan}
