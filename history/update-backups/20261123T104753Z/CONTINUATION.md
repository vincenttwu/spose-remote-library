# SPOSE Standalone Remote Library — Continuation, Release 0.9 geometry repair

## Cold-start entrypoint and current state

This is a standalone library whose ZIPs/bundles have a **flat root** (no enclosing `remote/`). Folder name can be `SPOSE`, `my-library`, `remote`, etc.; all scripts resolve the root from their location. It was forked from the user's original mannequin Blender library. Do not merge or overwrite the independent local-origin branch.

**Reference identities**: `SRC003/v001`, SPOSE source checkpoint `20261122T013728Z`, catalog SHA-256 `a8fa0f89656dbc8505cdf6af64fc707ae377726bf1bfa3ea1bb72585720e10a6`, 28 families, 276 V00 bases, 3,036 rows, 51 columns. Shared `BP001/v001`, `CPL01/v001`, `RIG001/v001`, `VP001/v001`; A rear 1.85 m and B front 1.77 m. Blender 5.2.2 LTS was used to build historical character assets, not to test this upgrade in the assistant environment.

**Goal**: all 276 V00 first, with per-family groups as scheduling units. No V01–V10 until every V00 has local explicit acceptance *and* user unlocks phase. Variation count 2,760, deferred.

**Status authority**: `tracking/progress.sqlite` for actual import jobs/reviews, then generated `ROADMAP.md`/`ROADMAP.json`. Read their current values from a *new upload*, not this static release note. First remote baseline had 0 accepted. The user's first DOGG batch rendered as wrong standing postures and was explicitly rejected in conversation; local tracker may have created r001 records. This upgrade intentionally **does not alter old revisions or tracker**. If applicable, use `review_pose.py --decision blocked` on those previous revisions after checking statuses.

## Why geometry engine v2 is required

Old Batch 001 (`DOGG-DOGG-V00`, `DOGG-CLSD-V00`, `DOGG-DOWN-V00`) was generated with 19 controls per pose, mostly root offsets, torso *local rotations*, uncalibrated hand/foot IK values and no explicit Rigify mode initialization. User's rendered DOGG-DOGG and DOGG-CLSD were effectively standing, whereas the catalog demands rear kneeling/front quadruped. DOGG-DOWN should have standing rear/front forward-fold (standing itself was correct) but hands floated and foot regions penetrated the floor. The old offline dry-run passed JSON structure yet failed geometric fidelity. **Never represent that as a successful pose.**

Historical `tooling/scripts/build_pilot_underarm_pose.py` provides tested primitives: `pose_torso` world-head + pitch, Rigify `IK_FK=0`, `IK_Stretch=0`, pole vector toggles, constraint stretch disabling, palm orientation from rest frame, mesh material-region evaluation, floor calibration and elbow poles. This upgrade ports those mechanics into shared `scripts/rigify_floor_engine.py`, **not the old pose's final geometry** (historical pilot remained a draft with contact problems).

### Current upgrade deliverable

Batch archive itself is flat at root. `install-update.py` installs allowlisted replacements **in place** and copies five current candidate ZIPs into `<library>/incoming/` without importing them. Before application it checks `project.json` identity, source SHA, template/rig dependencies and ZIP/file SHA-256; it backs up previous replaced files under `history/update-backups/<UTC>/`. No full library rebuild, no shared `.blend` copying, no catalog/SQLite/ROADMAP overwrite.

Each new pose package has `rig-targets.json.engine=rigify_floor_v2` and `geometry_contract_version=2`. The previous legacy V1 batch will fail validation deliberately. Builder uses world-space torso placement, Rigify IK initialization, grounded material-region floor stages, hip-relative wrists and geometry hard gates. `review_pose.py` now refuses acceptance if geometry gate fails. Rendered but failing candidates are kept as `blocked` for feedback. No geometry is preapproved here.

### Batch candidate identities

- `DOGG-DOGG-V00`: A kneeling, B quadruped, B hands/knees floor, both forearms/hands of A aimed to B hips.
- `DOGG-CLSD-V00`: same as above, B knees constrained closer, A knees outside their corridor. The new numeric targets still require visual verification.
- `DOGG-FCDN-V00`: A kneeling, B lowered face-down fold; current v2 contract approximates the forearm support with low hand support plus visual review.
- `DOGG-FROG-V00`: A kneeling, B wide low frog-like hands-and-feet corridor.
- `DOGG-DOWN-V00`: A standing, B standing forward fold, palms/feet grounded; no bogus knee-support requirement.

All are **unexecuted best-effort v2 candidates**; their control geometry may still be wrong until local Blender runtime verifies the actual evaluated rig. Batch 001 now contains five poses but remains one family batch. If first DOGG-DOGG still fails a hard gate, adjust the *engine or that pose module* using its feedback, not blind batch-wide angle changes.

## Local installation and first test (from extracted update ZIP)

```powershell
python install-update.py --library "D:\path\to\your\standalone-library"       # preflight
python install-update.py --library "D:\path\to\your\standalone-library" --apply
```

Then change directory to installed library and run:

```powershell
python scripts/check_remote.py
python scripts/import_pose.py incoming/DOGG-DOGG-V00_<timestamp>.zip --dry-run
python scripts/import_pose.py incoming/DOGG-DOGG-V00_<timestamp>.zip --blender "C:\path\to\blender.exe" --save-blend
python scripts/export_feedback.py DOGG-DOGG-V00 --revision <N>
```

Use the actual new incoming filename; see `BATCH-001-REBUILD.md`. Start with DOGG-DOGG and inspect full preview/geometry results **before** running the other four. If blocked, send the feedback ZIP with `validation.json`, `blender-result.json`, build log and renders. The assistant cannot test Blender here.

## Portable handoffs for future sessions

From installed standalone library:

```powershell
python scripts/package-library-for-remote.py
```

New portable ZIP also has a **flat root**, includes docs, scripts, rig map and hashes, V00 source subset, ROADMAP and tracker snapshots, and excludes `.blend`, large catalog CSV, renderer PNGs and SQLite. It is *not* runnable and must never be overlaid on the full library. `scripts/check_handoff.py` validates an extracted handoff. In new ChatGPT session upload the latest handoff and a feedback ZIP if reviewing a failed pose. Script `scripts/package_pose_from_handoff.py` builds data-only modules offline (full library validates hashes at import).

## Canonical file priority

For latest state, read `ROADMAP.json`, `tracking/progress.csv`, `source/dataset.json`, `project.json`. For operating mechanics, read `SKILL.md`, `WORKFLOW.md`, `docs/GEOMETRY-ENGINE-V2.md`, `docs/POSE-MODULE-AND-FEEDBACK.md`, then source row and rig map. If these conflict with the running full library's SQLite state, the running library wins. Never claim a production pose is complete based on dry-run or thumbnails alone.

## Current release increment: Batch 001 geometry rebuild v2

An upgrade bundle (flat ZIP root) replaces the earlier local-rotation-only renderer and stages three revised V00 candidate ZIPs. Read `GUIDE.md` for local-agent action and `docs/GEOMETRY-ENGINE-V2.md` for limitations. The V2 engine restores world-space torso placement, Rigify IK settings, evaluated-mesh knee/hand/foot calibration, and posture hard gates. Offline package validation passes but the new Blender behavior is **not yet verified**. Run `DOGG-DOGG-V00` first and export feedback before trying CLSD/DOWN. `scripts/check_batch_001.py` checks batch contracts without Blender. All prior pose revisions, SQLite and original shared assets must remain unchanged. The standalone library itself need not be named `remote`; future handoff ZIPs are flat-root.
