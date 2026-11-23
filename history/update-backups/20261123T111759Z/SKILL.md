# SKILL — SPOSE autonomous batch operation and cold start

## Required cold-start reading

1. Read `GUIDE.md`, `WORKFLOW.md`, `CONTINUATION.md`, `docs/STATUS-AND-BATCH-SEMANTICS.md`.
2. Inspect `project.json`, `ROADMAP.json`, `tracking/progress.csv`, `CURRENT-INSTALL.json` and the latest batch manifest if available.
3. Confirm full versus portable handoff: full library contains `.blend` and full CSV; portable handoff intentionally does not.
4. Read source rows from `source/V00-CATALOG.csv` in handoff, or full catalog in installed library. For each package, the exact `specification` and dependency hash are authoritative; reference generation gates are descriptive only.

## One-pass batch contract

- A batch means all five items are attempted in a **single command** and represented in a **single report**. Never stop at item 1 due to contact/geometry/approval warnings.
- A failed item may be retried later. It must not prevent processing siblings or scheduling the next batch.
- Keep per-pose versioned history; do not overwrite scenes, approvals, tracker, or shared pair assets.
- `draft` is a usable build. `needs_work` records quality and is not an action permission.
- Only label `accepted` when the user explicitly chooses to record it, but acceptance is **never required to proceed**.
- Do not infer Blender correctness from a ZIP dry-run. Rendered images and numeric proxies are evidence, not guarantees.

## Commands for local operator

```powershell
python install-update.py --library "<FULL_LIBRARY>"           # read-only preflight
python install-update.py --library "<FULL_LIBRARY>" --apply   # safe update
cd "<FULL_LIBRARY>"
python scripts/run_pose_batch.py --plan batches/BATCH-001.json --dry-run
python scripts/run_pose_batch.py --plan batches/BATCH-001.json --blender "<BLENDER>"
python scripts/update_roadmap.py
python scripts/package-library-for-remote.py
```

Send `reports/*combined_feedback.zip` and the latest handoff ZIP for cross-session continuation. If the user asks for another batch before the previous poses are stable, proceed with the next batch; preserve unresolved issues as annotations.

## Principles

Maintain authoritative source hashes, no code execution from incoming modules, independent library identity, version history, and reliable backup. There are **no source, geometry, review, milestone, or batch progression gates**. Preserve optional quality information and never quietly claim an untested pose is stable.
