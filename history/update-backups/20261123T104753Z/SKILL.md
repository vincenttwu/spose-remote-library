# SPOSE Remote Library — Operational Skill v2 (cold-start authoritative)

## Identity and scope

This is a **self-contained SPOSE Blender library**, regardless of its filesystem folder name. There is **no mandatory `remote/` wrapper**. `project.json`, `SKILL.md`, `scripts/`, `poses/`, `source/`, and `tracking/` are directly at the library root. The independent local-origin library is a separate branch and must not be overwritten. `scripts/pose_common.py` discovers the library root relative to itself; never hardcode a user drive letter or an enclosing `remote/` directory.

**Goal:** complete all **276 V00 base poses across 28 families** before generating any V01–V10 variations. Full active source `SRC003/v001`, catalog checkpoint `20261122T013728Z`, 3,036 rows / 51 columns, catalog SHA-256 `a8fa0f89656dbc8505cdf6af64fc707ae377726bf1bfa3ea1bb72585720e10a6`. `ACTOR_1 = A` (rear), `ACTOR_2 = B` (front), unless the catalog explicitly dictates otherwise. Shared pair `CPL01/v001`, rig `RIG001/v001`, 1.85 m A and 1.77 m B. Blender observed 5.2.2 LTS. Shared character assets are provisional; do not state approved.

## Read these in order at cold start

1. `CONTINUATION.md`: current release, last mistakes, active next action and limitations.
2. `ROADMAP.md` + `ROADMAP.json`: derived status from the SQLite tracker; never manually tick checkboxes.
3. `WORKFLOW.md`: each local execution step; failed geometry decisions and feedback loop.
4. `docs/GEOMETRY-ENGINE-V2.md`: v2 control contract, historical pilot evidence, known geometric risks.
5. `docs/POSE-MODULE-AND-FEEDBACK.md`, `schemas/pose-package-README.md`: exact package and feedback formats.
6. `source/V00-CATALOG.csv` (portable handoff) or `source/SPOSE-FULL-20261122T013728Z.csv` (full library); `source/pose-dependencies.json` if using a handoff.
7. `tooling/scripts/build_pilot_underarm_pose.py` and `tooling/scripts/build_pilot_floor_pose.py` in **full** library (historical references, not production successes).

A portable context ZIP is adequate for authoring data-only V00 pose ZIPs and identifying the latest status; it cannot render, numerically solve or verify Blender geometry. The standalone full library remains the only execution authority. If the handoff is stale, user should regenerate it with `python scripts/package-library-for-remote.py`.

## Current milestone and delivery convention

- User wants **one batch bundle only**, not separate user-visible download links per pose.
- Each actual pose remains a separate, flat `{POSE_ID}_{YYYYMMDDTHHMMSSZ}.zip` inside the batch, because `scripts/import_pose.py` processes exactly one data-only pose at a time.
- A **batch upgrade** ZIP is flat at root: `SKILL.md`, `WORKFLOW.md`, `CONTINUATION.md`, `scripts/`, `docs/`, `pose-packages/`, `install-update.py`, etc., **no `remote/` directory**. The updater copies only allowlisted replacement files, never whole directories and never the source CSV, templates, SQLite or pre-existing revisions.
- New revision is allocated by local importer in `poses/<POSE_ID>/CPL01/v001/rNNN`. Existing r001/r002 are immutable. Option `--save-blend` for debugging only.
- `production_enabled=false`, `variation_phase_authorized=false`; `ROADMAP` accepted count must only increase with explicit reviewed decision.

## Geometry-engine v2 strictness — mandatory

The first Batch 001 failed **fundamentally**: local-only torso rotations left kneeling poses standing, raw hand/foot IK targets did not orient palms/feet or calibrate evaluated mesh, and the prior validation failed to detect wrong posture. Never repeat that strategy. Legacy Batch 001 modules lack `rig-targets.json.engine=rigify_floor_v2` and `geometry_contract_version=2` and MUST be rejected before a Blender job.

For every candidate:

1. **Source-trace** the specific V00 row: posture, load-bearing surfaces, relative facing, pelvic alignment, hand destination, environment. A suffix or filename is not a substitute for source reading; e.g. `DOGG-DOWN-V00` really is *standing* rear + *forward-fold standing* front, while `DOGG-DOGG-V00` and `DOGG-CLSD-V00` are rear-kneeling/front-quadruped.
2. Use world-space `POSE_WORLD_HEAD_ROT_X_DEG` to place **torso controls** (including pelvis height), not merely `POSE_LOCAL_ROTATION_DEG`. Initialize both arm and leg Rigify IK, set `IK_FK=0`, disable `IK_Stretch`, enable `pole_vector`, disable constraint stretch, then place feet, palms, and poles. Historical reference uses L=positive world X and R=negative world X.
3. Pose floor support as separate **evaluated mesh regions** (`hands`, `feet`, `knees`). Calibrate knee contact by moving torso world height, then independently trim palm and foot IK heights. Knee region must be a local mesh patch near `DEF-shin.*` head, not the shin or ankle minimum.
4. Apply bounded evaluated pelvis-region Y proximity alignment and then rear-to-front hip-relative hand controls **after** floor calibration. Check head/hips proximity, knee angle and height, grounded hand regions, support regions, foot penetration, and any persistent gaps. A proxy distance under threshold does **not** prove lack of clipping.
5. `scripts/validate_pose.py` must yield hard posture/support gate pass before local human review can mark a candidate validated or accepted. On failure, still render images for feedback, but mark the local job `blocked` with diagnostic reasons.
6. Never claim physical/anatomical validation, working rig results, approved contact, or an accepted pose until actual Blender 5.2.2 render feedback and explicit human decision are available.

## Local commands (from the library root)

```powershell
python scripts/check_remote.py
python scripts/import_pose.py incoming/DOGG-DOGG-V00_<UTC>.zip --dry-run
python scripts/import_pose.py incoming/DOGG-DOGG-V00_<UTC>.zip --blender "C:\path\to\blender.exe" --save-blend
python scripts/export_feedback.py DOGG-DOGG-V00 --revision <rNNN NUMBER>
python scripts/review_pose.py DOGG-DOGG-V00 --revision <N> --decision blocked --reviewer user --note "Standing instead of kneeling" --confirm-reviewed
python scripts/package-library-for-remote.py
```

Do not mass-import all five until a local V00 rebuild generates geometrically credible feedback. The import command does not automatically approve anything. For final acceptance, require actual inspection of front, side, three-quarter, QA-regions renders and `validation.json`. `review_pose.py` rejects failed geometry gates.

## Troubleshooting decision tree

- **Kneeling mannequin still standing:** inspect `posture_assertions`, torso world control, leg `IK_FK`, `thigh_ik_target` and `DEF-shin` knee height/angle. Hard gate must report `STANDING_INSTEAD_OF_KNEELING` / `KNEE_NOT_FLEXED`.
- **Foot/hand sinks or floats:** inspect `validation.json > technical_checks > geometry > supports`, floor calibration log, material `region` availability and foot/palm orientation. Do not "fix" via global root z shift.
- **Hand misses receiver:** inspect hip-relative hand controls, wrist direction and normal, elbow poles. Fix after primary floor supports and pelvis positioning; do not place grips from hardcoded stale world coordinates.
- **Blender exception:** inspect `build.log` and `blender-result.json`. `blocked`/`failed` must not become `accepted`.
- **Unexpected future package rejection:** compare ZIP manifest template/source SHA and contract version. Never patch a hash without matching source.
- **Context-only handoff:** do not import it into full library; it has no `.blend`/SQLite. It now has flat ZIP root too. Use `scripts/check_handoff.py` after extraction.

## Feedback and iteration

The user operates the full Blender library. Assistant produces scripts and data, offline dry-run tests. User provides images/feedback after run. Assistant compares contact surfaces and selects a new UTC-stamped pose ZIP for next rNNN. A single revision might be fundamentally wrong; keep its historical evidence, never silently rewrite it. Track every actual acceptance in SQLite and auto-regenerate ROADMAP. **All V00 before variations** remains binding.

## Local-agent batch handling

A user may give the local agent just the batch upgrade ZIP. Read the root `GUIDE.md` first, extract separately, run `install-update.py --library PATH` dry-run, then `--apply`; verify with `check_remote.py` and `check_batch_001.py`. Only render `DOGG-DOGG-V00` initially; export feedback and stop on blocked/failure. Never accept a revision without explicit user approval. Bundle and future handoff ZIPs are flat-root, not nested under `remote/`.
