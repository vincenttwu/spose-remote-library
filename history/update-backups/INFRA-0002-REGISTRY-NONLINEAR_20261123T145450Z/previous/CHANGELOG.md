> **ACTIVE: Batch 0001 Pass 05.** Read release `APPLY.md`, `LOCAL-WORKS.md` and installed `docs/PASS-05-CALIBRATION.md`; five new modules seeded from Pass04 selected local Attempt02 controls. Optional 0–2 guided local refinements per pose. Existing older pass instructions below are historical. All quality metrics are advisory.

# CHANGELOG — infrastructure branch

## Infra 0001: operational/cold-start overhaul (2026-11-23)

- Added top-level flat `snapshots/` (persistent), `review/` and `upload/` (disposable).
- Added lossless verified WebP compressor (`scripts/compress_images.py`), with original PNG fallback and no mutation of authoritative PNGs.
- Added single-feedback builder (`scripts/feedback_bundle.py`) with per-pose folders, SHA-256 inventory and embedded portable project context; removed nested feedback ZIPs from the default batch workflow.
- Added `scripts/refresh_exchange.py` to recreate disposable files from recorded revisions, without Blender.
- Added `scripts/verify_feedback.py`, `scripts/update_continuation.py`, `scripts/check_documentation.py`.
- Updated batch runner to record `reused_existing_package` separately from newly created revisions. Failed poses never stop remaining poses; exporter failure does not discard builds.
- Added detailed architecture, schema, maintenance, feedback and cold-start documentation; preserved existing deeper geometry/rig/tracking documents not specifically replaced.
- Installed through an explicit file-manifest dry-run/apply/rollback update with backup receipts. No geometry pass or pose import is part of infrastructure installation.

## Known prior lineage retained

- Batch 0001 Pass 02 (before infra 0001) standardized pass labels and `snapshots/`, `review/`, `upload/` and attempted one combined export, but reused old pose packages and continued nesting per-pose feedback ZIPs.
- Batch 0001 Pass 01 five-pack used Rigify floor engine V2, retained drafts/diagnostics without quality gates, and staged five pose modules.

See existing `docs/GEOMETRY-ENGINE-V2.md`, `docs/STATUS-AND-BATCH-SEMANTICS.md` and archived installer receipts for prior detailed geometry revisions. Historical statuses are not rewritten.


## 2026-11-23 — Batch 0001 Pass 03 geometry update
- Added evaluated lateral pelvis / wrist-near palm region contact approach and quantified gap diagnostics.
- Added VP001 forearm region support and approximate side-of-head near-floor measurement.
- Added declarative bounded `styling_controls`, local-axis additive head orientation, and post-styling floor recheck.
- Refined five pose modules with new package identities; preserving five distinct support topologies.
- Kept the improved infrastructure exporter and flat ephemeral folders; no gates and no acceptance records.

## Batch 0001 Pass 04
- Added read-only rig and rendered-scene calibration collector; persisted versioned control/body measurements.
- Added measured signed head aiming and area-based palm/pelvis contact diagnostics.
- Added one-command five-pose render + probe + single-feedback pipeline.
- Added calibration data to feedback payload and cold-start documentation; no gates.


## Additive workflow update — Batch 0001 Pass 04 (same five pose modules)

- Integrated complete Infra 0001 utility/documentation payload and Pass-04 measured geometry upgrade into one installable ZIP.
- Added `scripts/local_refinement.py`: disposable proposal-based, bounded data-only scratch renderer, per-scene measurements, per-pose candidate selection, persistent evidence export.
- `scripts/run_calibrated_batch.py`: optional local enable/disable, baseline vs finalize stages, maximum two local refinements per pose.
- Combined feedback and verifier now include local candidate evidence, selected full rig targets, attempt JSON/probe readings, and compact lossless intermediate images.
- `review/` and `upload/` show selected pose preview images, while authoritative pose revisions remain unchanged.
- Updated cold-start workflow, schema, and local agent instructions; no quality/approval gates.

## 2026-11-23 — Batch 0001 Pass 05

- Created five genuinely new timestamped pose packages seeded from Pass04 selected Attempt02 rig controls.
- Added bounded optional neck-assisted head-aim search for FROG, to address failed head-only gaze correction.
- Added final support calibration after hand/pelvis solver, targeting DOWN/FROG hands and FCDN forearms.
- Updated additive guidance, selection targets, package/pass labels and full local work procedure.
- Quality checks remain diagnostic only; no automatic promotion of scratch scenes.
