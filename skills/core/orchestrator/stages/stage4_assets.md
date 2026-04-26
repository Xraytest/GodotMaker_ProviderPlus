# Stage 4: Assets

## Required Documents

| Document | Schema Check |
|----------|-------------|
| `references/scene_{name}.png` | One reference image per scene listed in SCENES.md (or scene explicitly marked N/A with user approval recorded in ASSETS.md) |
| `assets/manifest.json` | Required only if user provides art/audio files; must be valid JSON with `assets` array containing `file`, `type`, `role` fields |

Documents listed here are verified by the stage gate hook. Missing or malformed documents block stage transition.

---

Generate missing visual assets identified in ASSETS.md (created during Stage 1b).

## Step 0: Collect User Assets

Ask the user to provide any art and audio files before AI generation begins.

- **Audio:** AI audio generation is NOT supported — audio must be user-provided. Remind the user.
- **Art:** providing own assets is optional but recommended for consistent style. Missing art will be AI-generated in later steps.

**If user provides assets:**

1. Ask them to place files into the `assets/` directory.
2. Dispatch an **analyst subagent** (Sonnet worker) to analyze the provided files and generate `assets/manifest.json`.
   - **Orchestrator MUST NOT read image files in `assets/` directly.** Delegate all image analysis to the analyst subagent.
   - Analyst extracts: type, role, dimensions, color palette, line weight, proportions, mood, style characteristics.
   - Show the generated manifest to the user for confirmation before proceeding.
3. Update GDD §9 — mark provided assets as `provided` in the Asset Table.
4. The extracted art style (palette, line weight, proportions, mood) becomes the reference style for all AI-generated assets.
   Record it in ASSETS.md Art Direction. **All later AI-generated assets MUST match this style.**

**Recommended manifest.json format** (share with user — saves time if they pre-fill it):
```json
{
  "assets": [
    {"file": "sprites/player.png", "type": "sprite", "role": "Player character sprite sheet", "frames": 4},
    {"file": "audio/bgm.ogg", "type": "audio", "role": "Background music for gameplay"}
  ]
}
```

**If user provides no assets:** Note in GDD §9 that all assets will be AI-generated. Proceed using GDD §4 art direction as the style reference.

## Step 1: Generate Scene Reference Images

For each scene listed in SCENES.md:

1. Read the scene's Elements table and Mood field from SCENES.md.
2. Generate a reference image using `tools/asset_gen/asset_gen.py`:
   - If user provided art assets, pass them as style reference to the generation prompt.
   - If no user assets, use the GDD §4 art direction description as the style prompt.
3. Save to `references/scene_{name}.png` (use the scene name from SCENES.md, lowercase, spaces → underscores).
4. Show each reference image to the user for approval before proceeding.
5. If user rejects a reference image, regenerate with their feedback before moving on.

For text-only or minimal-art games, mark all scenes as `N/A` in ASSETS.md with user approval recorded, and skip to Step 2.

## Step 2: Review ASSETS.md

Read ASSETS.md and identify assets with `status = pending`:
- **Art assets (pending):** These need AI generation
- **Audio assets (pending):** Remind user these must be user-provided (no AI audio generation). Ask user to provide them now or mark as deferred.
- **Art assets (provided):** Already in place — no action needed

If all assets are `provided` or marked N/A, skip to Gate 4.

## Step 3: Confirm AI Generation Plan

Present the list of missing art assets to the user:

> The following art assets still need to be created:
> {list from ASSETS.md where status = pending AND type != audio}
>
> I'll generate these using AI (Gemini API). {if user provided art: "All generated assets
> will match the style of your existing art (color palette, line weight, proportions, mood)."}
>
> Should I proceed? You can also provide any of these yourself instead.

If user provides additional assets at this point:
1. Update ASSETS.md status to `provided`
2. If new assets lack manifest entries, dispatch analyst subagent to analyze and update `assets/manifest.json`
3. Re-evaluate remaining pending assets

## Step 4: Generate Missing Art Assets

For remaining pending art assets:

1. Dispatch a Sonnet worker for asset generation (follow `asset-planner.md` + `asset-gen.md`)
   - **If user provided art:** Worker brief MUST include: "Match the style of existing user assets: {list user asset files}". Worker receives user asset samples as style anchors.
   - **If no user art:** Worker generates from GDD §4 art direction description and ASSETS.md Art Direction.

For text-only or minimal-art games, mark ASSETS.md as "N/A — no generated assets needed" and proceed.

## Step 5: Update ASSETS.md

After generation:
- Update status of generated assets from `pending` to `generated`
- Fill in file paths and generation params
- Verify all art assets are accounted for (provided + generated + N/A = total required)

---

**Gate 4:**
- [ ] All art assets in ASSETS.md have status `provided`, `generated`, or `N/A`
- [ ] Reference images exist for each scene in SCENES.md (`references/scene_{name}.png`), or explicitly marked N/A with user approval recorded in ASSETS.md
- [ ] ASSETS.md art direction section is filled
- [ ] If user provided assets: `assets/manifest.json` exists and was confirmed by user; AI-generated assets are visually consistent with user's style
- [ ] Audio assets: user provided them, or they are marked as deferred with user acknowledgment

**After passing Gate 4:** Update `.godotmaker/stage.json` — read existing (or create `{"completed_stages": {}}`), add `"4": "<UTC timestamp>"` to `completed_stages`, write back. Then proceed to Stage 5.
