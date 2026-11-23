# Architecture — SPOSE standalone remote pose library

## 1. Components and ownership

The full **installed** library is the only runnable local Blender workspace. Heavy Blender assets live under `pairs/CPL01/v001/template.blend`; two actor rigs A/B are governed by current `RIG001/v001` and body/visual profiles. Blender 5.2.2 LTS was used for Batch 0001. Rig and floor-calibration implementation remains in `scripts/rigify_floor_engine.py` and associated Blender build/validation scripts.

**Source:** `source/dataset.json` registers the full canonical CSV (checkpoint `20261122T013728Z`; 28 families, 276 V00 bases, 3,036 records, 51 columns at the original checkpoint). For any later update, rely on the actual dataset/source fingerprints instead of hardcoding these numbers in code. `source/V00-CATALOG.csv` and `source/POSE-INDEX.csv` in portable context are derived compact copies, not a replacement source.

**Tracker:** `tracking/progress.sqlite` is authoritative. `ROADMAP.md`, `ROADMAP.json`, progress CSV and `CONTINUATION.md` are generated projections. Source editorial REVIEW/EXCLUDE, geometry warnings and acceptance are separate annotations, never work permission gates.

**Pose module:** one data-only ZIP with JSON controls, contact anchors, validation plan and fingerprints. An installed importer interprets it against the local Blender rig, creates a new immutable revision, renders four views and stores validation/logs. New geometry pass requires changed package identity and content; pass naming alone does not create a revision.

## 2. One-batch dataflow

```text
Remote assistant: five source rows + previous feedback
    -> five new data-only pose modules + one batch plan
    -> ONE outbound pose bundle ZIP
Local installed library:
    incoming/ modules -> scripts/run_pose_batch.py
    -> import_pose.py -> Blender shared pair + rigs
    -> poses/<POSE_ID>/CPL01/v001/rNNN/ (permanent)
    -> snapshots/batch-XXXX-pass-YY_<UTC>/ (permanent)
    -> refresh_exchange.py
       -> review/ flat prefixed original PNGs (disposable)
       -> upload/ same PNGs + ONE combined feedback ZIP (disposable)
              -> images: per-pose lossless WebP (or original PNG fallback)
              -> JSON, build logs, batch state
              -> context/ complete portable source/docs/rig handoff
Remote assistant: review all five images/data, give ratings and next options
```

The ZIP can be examined and scored on a machine without Blender, but cannot establish actual 3D correctness without the rendered evidence. The embedded context is read-only and omits `.blend`, the full CSV and SQLite. When source/rig design changes, a new handoff must be produced from the live library.

## 3. Four-view contract

Render views ordinarily include `front.png`, `side.png`, `three-quarter.png` and `qa-regions.png`. `qa-regions` is a material/contact-region diagnostic, not proof of correct pose silhouette. Floor support measurements, knee angle, pelvis/head height, penetration samples, mesh proximity and bone-head anchor distances must be interpreted separately. A mesh distance cannot replace a human assessment of support and coherent articulated posture.

## 4. Folder lifecycle and safety

- **Persistent:** `source/`, `pairs/`, `tooling/`, `poses/`, `tracking/`, `batches/`, `snapshots/`, `updates/installed/`, `history/update-backups/`.
- **Disposable:** `review/` and `upload/`. The latter contains a full return ZIP and individual uncompressed PNGs for discussion. No additional `current/` subfolder.
- **Shared executables:** `scripts/`, not a duplicate persistent `updates/scripts/` runtime. Incoming infrastructure update ZIPs contain `updates/scripts/` as **payload**, installed to `scripts/`.
- **Do not automatically delete:** original pose revisions, canonical source CSV, pair template, SQLite, review decisions, immutable backups.

An infrastructure update changes docs/utilities only. It does not create geometry revisions, import modules or modify canonical source/rig files. The installer performs checksum and dependency preflight, backups and recovery receipts. Individual batch poses may fail without halting later poses; damage to source/template fingerprints is an integrity failure, not a geometry gate.

## 5. Cold start and schema versioning

A new remote session receives **one combined feedback ZIP**. Read top-level `START-HERE.md`, `manifest.json`, `SUMMARY.md` and `batch-summary.json`, then `context/AGENTS.md`, `context/SKILL.md`, `context/CONTINUATION.md`, source/rig descriptions and each pose's `inputs/`. Validate member checksums first. `manifest.schema_version=2` distinguishes the new flat feedback from the legacy schema containing nested per-pose ZIPs. Do not infer a new revision from ZIP timestamp alone.

See `docs/SCHEMAS.md`, `docs/FEEDBACK-CONTRACT.md`, `docs/MAINTENANCE.md` and existing geometry/rig documentation for details.
