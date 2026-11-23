# Registry schema and provenance (v1, Infrastructure 0002)

The authoritative database is `tracking/progress.sqlite`. The registry tables are additive, using stable IDs and transactional updates:

| Table | Primary key | Contents |
|---|---|---|
| `registry_batches` | `batch_id` | Family, ordered pose IDs, plan reference, metadata |
| `registry_passes` | `(batch_id,pass_id)` | Plan hash, local calibration configuration, status and optional subjective rating |
| `registry_runs` | `run_id` | Persistent snapshot path and batch summary hash, genuine new vs reused revision counts |
| `registry_attempts` | `(run_id,pose_id,attempt_no)` | Baseline/local trial inventory and selected flag |
| `registry_artifacts` | `artifact_id` | File role, relative path, SHA-256, size; e.g. ZIP and batch summary |
| `registry_events` | `event_id` | Append-only history of plan registration, snapshot import, quality notes |

The legacy `jobs`, `events`, and `metadata` tables are **not** altered. Most records are discovered from actual existing plans and saved batch snapshots. If a past run's exact evidence is missing, it remains unknown. The migration does not infer accepted status from build status.

## Transactional behavior

- `sqlite3.connect(timeout=30)` and `PRAGMA busy_timeout=30000` make writers tolerate brief lock contention.
- `BEGIN IMMEDIATE` serializes writes. Foreign keys and unique snapshot paths prevent duplicate ownership.
- `register-plan` refuses to reuse an existing batch ID with a different set/order of five pose IDs. It does not inspect geometric quality.
- `ingest-snapshot` is idempotent. If exporter metadata later changes `batch-summary.json` it refreshes its recorded hash and creates an event, without inventing a second run.
- `add-artifact` computes SHA-256 and stores a relative path; if a ZIP is changed, its new hash receives its own record. Historical files are never deleted.
- The registry itself is not a distributed lock scheduler. Different batch/pass jobs write to separate snapshot directories, and only `activate_batch.py` changes the shared flat exchange view.

## Portable JSON

`python scripts/export_registry.py` writes `tracking/registry.json`. The exporter embeds read-only `registry/registry.json` in feedback ZIPs; this is a *snapshot*, not the local truth. To compare reports received out of order, match their batch and pass identifiers, source and template fingerprints, and artifact hashes. Do not treat receipt order as execution order.

## Intentional omissions

The registry stores neither binary `.blend` assets nor preview images. It indexes their persistent filesystem locations. It does not assign human visual scores automatically, generate new controls, approve geometry, or decide when to move to another family.
