# SPOSE remote change log

## 0.9.2 — Five-pose batch without quality gates

- Removed source `REVIEW`/`EXCLUDE` import prohibition and V00-only import permission checks; reference metadata remains visible.
- Removed geometry `hard_gate_pass` and human acceptance restrictions from workflow progression; successful renders are usable `draft` even when warnings exist.
- Removed review-time geometry restrictions; explicit human review remains optional, never mandatory for progress.
- Added generic `scripts/run_pose_batch.py` with five-item plan, `--dry-run`, continue-on-error, combined feedback ZIP, and optional `--rerun`.
- Updated generated ROADMAP checkbox semantics to **built** versus accepted, preserving historical blocked builds as built.
- Added r002-informed candidate geometry parameters to five timestamped packages, preserving distinct pose silhouettes.
- Fixed self-referential manifest inventory: UPDATE-MANIFEST.json is never listed inside its own SHA-256 map.
- Kept integrity checks and installer backups/rollback.
