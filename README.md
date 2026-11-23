> **INFRA 0002: non-linear registry active.** The old Batch 0001 Pass 05 headers below are preserved historical information, not a global work queue. Batch/pass operations now use `scripts/registry.py`, `scripts/run_registered_batch.py`, and `scripts/activate_batch.py`; read `docs/REGISTRY-OPERATIONS.md`.

> **ACTIVE: Batch 0001 Pass 05.** Read release `APPLY.md`, `LOCAL-WORKS.md` and installed `docs/PASS-05-CALIBRATION.md`; five new modules seeded from Pass04 selected local Attempt02 controls. Optional 0–2 guided local refinements per pose. Existing older pass instructions below are historical. All quality metrics are advisory.

# SPOSE remote library — operating map

**This is a standalone local Blender pose library.** The pair asset, Blender runtime, source catalog, SQLite tracker and all recorded revisions live on the owner's machine; this repository is not the same as the historical/original SPOSE library. There is no outer `remote/` folder in its canonical root.

## Start here (in this order)

1. `AGENTS.md` — authority, user requirements, non-destructive invariants and prohibitions.
2. `SKILL.md` — cold-start operating sequence, state discovery and tested command list.
3. `WORKFLOW.md` — five-pose batch process, two-pass target and no quality gates.
4. `GUIDE.md` — installation, batch execution, evidence, regeneration and recovery commands.
5. `CONTINUATION.md` — **generated live checkpoint**, not an authored source of truth.
6. `docs/ARCHITECTURE.md`, `docs/SCHEMAS.md`, `docs/FEEDBACK-CONTRACT.md`, `docs/MAINTENANCE.md` — implementation details.
7. Existing deeper design notes: `docs/GEOMETRY-ENGINE-V2.md`, `docs/RIG-AND-CONTACT.md`, `docs/TRACKING-AND-ROADMAP.md`, `docs/STATUS-AND-BATCH-SEMANTICS.md`, and source files. These are retained, not silently discarded.

## Library boundaries

| Directory | Purpose and authority | Disposable? |
|---|---|---|
| `source/` | Canonical catalog and source identity/fingerprints | **No** |
| `pairs/`, `body_profiles/`, `visual_profiles/`, `tooling/` | Shared Blender templates, rigs and character definitions | **No** |
| `tracking/` | Authoritative progress SQLite and trackers | **No** |
| `poses/` | Immutable revision directories; generated scenes, previews, inputs and measurements | **No** |
| `incoming/` | Staged individual *data-only* pose ZIP modules | Rebuildable, but preserve staged work intentionally |
| `batches/` | Batch plans and pose package references | **No** for planned work |
| `scripts/` | **Installed** runnable commands; one authoritative copy | **No** |
| `updates/installed/` | Infrastructure update receipts and pointers | **No** |
| `snapshots/` | Historical batch/pass evidence and feedback ZIPs | **No** |
| `review/` | Latest flat original PNG previews and summary for visual inspection | **Yes** |
| `upload/` | Latest flat original PNG previews plus **one** combined feedback ZIP | **Yes** |
| `history/update-backups/` | Original files and recovery receipts from upgrades | **No** |

The `updates/` directory **inside an incoming update ZIP** contains replacement payloads which are installed into canonical `scripts/`, docs, etc. Do not run a second permanently duplicated script tree from `updates/` after installation. Update receipts may be kept under `updates/installed/`.

## Identifiers and one-file exchange

- Current example: **batch-0001**, **pass-02**, five DOGG V00 poses.
- Batch ZIP: `spose-remote-bundle-batch-0001-pass-02_<UTC>.zip` (or `spose-remote-bundle-infra-0001_<UTC>.zip` for tooling-only update).
- One return ZIP: `spose-remote-feedback-batch-0001-pass-02_<UTC>.zip`.
- Pose module filename, internal to bundle: `{POSE_ID}_{YYYYMMDDTHHMMSSZ}.zip`.
- Individual images under `upload/` are directly uploadable for discussion. Normally upload **only the combined feedback ZIP**, which already embeds images, per-pose inputs, summary, and a portable source/docs handoff.

**Current pose quality:** The 2026-11-23 Pass 2 feedback reused Pass 1 pose revisions. A 5.1/10 assistant visual rating is a historical opinion, not a new Pass 2 geometry improvement, not a machine metric and not an approval gate. Infrastructure updates do not count as pose passes.

## Important boundaries

Integrity checks prevent corrupt ZIPs, wrong source/template dependencies, path escapes and accidental revision overwrites. **Geometry warnings, source `PASS/REVIEW/EXCLUDE`, optional acceptance, stability and V00 scheduling never prevent processing the next pose or batch.**

No remote artifact is a substitute for the local heavy Blender `template.blend` or the authoritative SQLite database. Offline tests do not establish visual/physical correctness.


## New: optional bounded local refinement

`local/` is an entirely disposable first-class workspace for `attempt-00`, `attempt-01`, `attempt-02`. Attempt 00 references the authoritative baseline; the other two are isolated experiments without tracking updates. Persistent `snapshots/` receives selected full target JSON, proposal deltas, measurements, all attempt outcomes, and a compact selection of images before cleaning `local/`. Flat `review/`/`upload/` display the selected candidate for each pose. Use `docs/LOCAL-COLLABORATION.md` and current `APPLY.md`. Default is enabled with a maximum of two local refinements per pose; CLI `--local-calibration off` or the batch plan disables this.


## Registry-driven production (Infra 0002)

SPOSE now supports multiple independent batch/pass jobs and out-of-order feedback. The shared flat `review/` and `upload/` are explicitly activated views of persistent `snapshots/`, never a global writer destination for overlapping jobs. Use `scripts/migrate_registry.py --apply` once, `scripts/registry.py status`, `scripts/run_registered_batch.py`, and `scripts/activate_batch.py`. The local SQLite tracker remains authoritative; `tracking/registry.json` and the JSON inside feedback are portable copies. See `docs/REGISTRY-OPERATIONS.md`.
