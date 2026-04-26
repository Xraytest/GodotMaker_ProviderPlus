# Scene Descriptions: {Name}

<!-- Generated during Stage 1b. One section per game screen/scene.
     Each scene describes layout, elements with position/size, mood, and transitions.
     Workers use this for implementation; verifiers cross-check against reference images + screenshots. -->

## Scene: {Scene Name}

- **Type:** menu | gameplay | hud | overlay | cutscene
- **Resolution reference:** 1920×1080
- **Layout:** vertical-center | horizontal-center | edge-anchored | grid | freeform
- **Background:** {description of background — color, gradient, image, particles}
- **Mood:** {visual/emotional tone}

### Elements

| Element | Position | Size | Description |
|---------|----------|------|-------------|
| {element name} | {top-center, bottom-left, center, etc.} | {width% × height%} | {what it is and looks like} |

### Transitions
- {Element} → Scene: {target scene name}

<!-- Copy this section for each screen/scene in the game.
     Minimum scenes: Main Menu + Gameplay HUD + Game Over.
     Position uses anchor terms: top/bottom/center + left/right/center.
     Size is percentage of viewport: "40%w × 15%h" means 40% width, 15% height. -->
