# Cold-start reconstruction checklist

This document is intended for an agent that knows **nothing** about previous conversation turns. Preserve the user's explicit workflow without inventing quality gates or treating documentation snapshots as more authoritative than actual source/tracker data.

## Step 1: classify the artifact

- An **infrastructure ZIP** has `install-update.py`, `UPDATE-MANIFEST.json`, `updates/`. It is a tooling/doc upgrade, **not** a pose pass. Extract away from the library; dry-run and apply with backup receipts.
- A **pose bundle ZIP** has a batch plan and five data-only pose modules; it is installed before Blender rendering.
- A **combined feedback ZIP** has `START-HERE.md`, `manifest.json` (schema 2), `batch-summary.json`, `poses/<ID>/` evidence and `context/`. One file is sufficient for remote review/cold start. It is not a runnable library.
- A **legacy combined feedback ZIP** may have nested `<POSE_ID>_rNNN_feedback.zip` files and lacks context; treat it as historical evidence and request an updated portable bundle only when necessary.

## Step 2: reconstruct current state

Local library: read `project.json`, `source/dataset.json`, actual `ROADMAP.json`, latest `snapshots/*/batch-summary.json`, and `CONTINUATION.md` (regenerate with `python scripts/update_continuation.py` if stale). Remote feedback: read `START-HERE.md`, `SUMMARY.md`, `manifest.json`, all five entries in `batch-summary.json`, `context/CONTINUATION.md`, `context/ROADMAP.json` and `context/source/V00-CATALOG.csv` plus rig maps. Check SHA-256 before trusting artifacts.

If a batch claims Pass 02, verify `new_revision_created` and `build_status`. The 2026-11-23 Batch 0001 Pass 02 returned five reused old revisions; pass count is not evidence of improvement. Infrastructure upgrades never increment pose passes.

## Step 3: inspect and rate all five

Use all images and source row constraints. Compare silhouettes and support types by variant; do not apply a tabletop knee requirement to a source-defined hands-and-feet frog, nor incorrectly collapse standing fold variants into quadrupeds. A floor support near z=0 can coexist with an incorrect pose. Note limitations of bone-head contact proxy and mesh surface sample. Give individual /10 visual/source-fidelity scores and one overall rating with highest-value changes. Ratings guide the user; they never block progression.

## Step 4: execute local work safely

Use actual Blender installation; verify pair/template fingerprint and source identity. Apply maintenance bundles before batch execution when required, and keep receipts. Run the full five-pose plan once, never pose-by-pose gates; keep all successful revisions. After batch, `refresh_exchange.py` creates flat `review/` and `upload/` and a **single self-contained feedback ZIP**, with optional Pillow lossless WebP. Individual missing views or failed pose rows remain represented.

## Step 5: continue or recover

The user chooses next five, a genuine new geometry pass, or no change. New geometry requires five newly authored module identities (with new targets/control hashes); do not call `--rerun` accidentally to disguise reuse. To restore ephemeral folders, run `refresh_exchange.py` without Blender. To roll back an infrastructure upgrade, use the exact receipt and compare hashes. To recover the previous pass, use a named `snapshots/batch-XXXX-pass-YY_<UTC>/` and authoritative revisions. Do not delete source, pair template, SQLite, revisions or historical review notes.

## Required reading

`README.md`, `AGENTS.md`, `SKILL.md`, `WORKFLOW.md`, `GUIDE.md`, `CONTINUATION.md`, `docs/ARCHITECTURE.md`, `docs/SCHEMAS.md`, `docs/FEEDBACK-CONTRACT.md`, `docs/MAINTENANCE.md`, original `docs/RIG-AND-CONTACT.md`, `docs/GEOMETRY-ENGINE-V2.md`, `docs/TRACKING-AND-ROADMAP.md` and relevant canonical source rows.


## Current additive calibration contract

A new local agent must (1) open `batches/BATCH-001.json.local_calibration` and latest `snapshots/`, (2) read `docs/LOCAL-COLLABORATION.md`, (3) run five baselines, (4) inspect baseline images and measurements and optionally make 0..2 local proposals per pose, (5) select best by actual visual+metric evidence, (6) finalize one feedback archive. A remote agent can independently inspect the `local/` members and measurements, compare baseline with selected candidate, and audit whether the local agent's choice is supported. Use a single ZIP; never require a separate handoff.


## Infra 0002 — non-linear registry startup

Read `docs/REGISTRY-OPERATIONS.md`. Inspect `tracking/progress.sqlite` through `scripts/registry.py status` when on the local machine, or inspect the received feedback ZIP's `registry/registry.json` when remote. The latter is a timestamped copy, not authoritative current state. Match feedback by batch/pass identity, not arrival order. Never assume `local/ACTIVE.json` or a `latest_snapshot()` reference belongs to the requested batch.
