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
