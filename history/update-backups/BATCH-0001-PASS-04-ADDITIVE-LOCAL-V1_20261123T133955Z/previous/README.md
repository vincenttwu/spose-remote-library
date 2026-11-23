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
