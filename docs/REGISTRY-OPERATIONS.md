# SPOSE Registry — non-linear production operations (Infra 0002)

## Purpose and authority

The locally installed standalone library is authoritative. `tracking/progress.sqlite` already contains `metadata`, `jobs` and `events`; Infra 0002 adds independent `registry_*` tables to the **same database**. These new tables index batches, passes, saved runs, local attempts, artifacts, and optional quality notes. They do not govern whether an unstable pose may be used or whether the next batch may run.

`tracking/registry.json` is a read-only portable export. Every new registered feedback ZIP also contains `registry/registry.json`, along with source/rig documentation and pose evidence. A feedback uploaded in any order identifies its own `batch_label`, `pass_label`, `snapshot`, package inputs and registry state. A remote assistant must not treat its registry export as newer than the user's current local registry just because the ZIP is uploaded later.

## IDs and state

- Batch identity: `batch-0001`, `batch-0002`, ... (stable, never repurpose the five pose IDs).
- Pass identity: `pass-01`, `pass-02`, ... within a batch. A historical snapshot with missing pass metadata may be `pass-legacy`, not a fabricated pass.
- Run identity: SHA-based ID derived from its uniquely named persistent `snapshots/batch-XXXX-pass-YY_<timestamp>/` folder.
- Attempt identity: (run ID, pose ID, attempt 00/01/02). Attempt 00 is the remote baseline; later attempts are disposable and never automatically promoted.
- Artifact identity: SHA-256 of batch+pass+role+relative path+content hash; repeated import is idempotent.
- Quality: optional `visual_score` 0–10 and notes, descriptive only; statuses do not block execution.

The registry does not infer that Pass 2 exists merely because Pass 1 exists. Bundle preparation and feedback reception are distinct events; use `register-plan`, `ingest-snapshot` and `add-artifact` accordingly.

## Folder contracts

| Folder | Persistence | Role |
|---|---|---|
| `tracking/progress.sqlite` | Persistent | Authoritative poses/jobs, registry tables and events |
| `tracking/registry.json` | Regenerable | Portable JSON index; **not** another authority |
| `batches/` | Persistent | Data-only batch/pass plans; each pass has its own JSON, do not overwrite an older pass plan |
| `snapshots/` | Persistent | Per-run record, selected controls/evidence, feedback archives |
| `poses/` | Persistent | Authoritative rig/render revisions |
| `local/` | Disposable | Bounded scratch experiments, one session per snapshot |
| `review/` | Disposable | Flat selected images for deliberately activated batch |
| `upload/` | Disposable | Flat images and exactly one selected feedback ZIP |
| `incoming/` | Staging | Immutable timestamped pose ZIPs |
| `history/update-backups/` | Persistent | Script update receipts/rollback files |
| `history/registry-migration-backups/` | Persistent | Pre-migration SQLite copy |

## Commands

```powershell
python scripts/migrate_registry.py             # no mutations
python scripts/migrate_registry.py --apply     # schema + honest observed history
python scripts/registry.py status
python scripts/registry.py next
python scripts/registry.py show --batch 0001
python scripts/registry.py register-plan --plan batches/BATCH-002.json
python scripts/registry.py ingest-snapshot --snapshot snapshots/batch-0002-pass-01_<RUN>
python scripts/registry.py set-quality --batch 0001 --pass 05 --score 6.2 --notes "Selected candidates, subjective audit"
python scripts/registry.py export --output tracking/registry.json
python scripts/activate_batch.py --batch 0001 --pass 04
```

**Registered baseline:** `python scripts/run_registered_batch.py --phase baseline --plan batches/BATCH-002.json --blender "<BLENDER_EXE>"`

**Finalize matching run:** `python scripts/run_registered_batch.py --phase finalize --snapshot "snapshots/<RUN>"`

**Per-run experiment:** `python scripts/local_refinement.py --session-snapshot "snapshots/<RUN>" status`; use matching `run` and `select` subcommands. The limit remains baseline plus two optional refinements per pose. No last-attempt default selection is imposed.

To send feedback, activate the desired batch/pass, then upload the one ZIP from `upload/`. To look at another batch, activate it; the previous selected snapshot remains intact. Multiple Blender jobs can render **different** batch/pass runs concurrently while their snapshot outputs remain isolated. Only one activation updates the shared exchange view at a time; the activation command holds `tracking/exchange-activation.lock` for this purpose.

## Non-linear audit example

1. Batch 0002 Pass 1 starts locally, but does not change global exchange views.
2. Remote assistant prepares Batch 0003 Pass 1; independent package identities and plan file.
3. Batch 0003 Pass 1 finishes first. Finalize its snapshot, activate 0003/01, upload its one feedback ZIP.
4. Remote assistant audits 0003/01 and prepares 0003/02, even while 0002/01 is still rendering.
5. Batch 0002 later finishes. Finalize its own snapshot, activate 0002/01, upload its ZIP.
6. The registry records both; no pass completion or quality permission gate exists.

## Migration honesty and transaction safety

`migrate_registry.py` scans actual stored `batches/*.json` and snapshots with `batch-summary.json`. It creates only observed batch/pass/run entries. It **never** assumes missing Pass 1 evidence exists, fabricates acceptance, or rewrites Blender scenes. It uses an online SQLite backup before initial schema changes and `BEGIN IMMEDIATE` for transactional updates. A duplicate snapshot is an idempotent re-index, not a second run. Multiple registry writers share SQLite locks rather than maintaining separate databases.

If a historical snapshot has conflicting batch IDs or pose lists, the migrator reports the conflict and continues with other entries. Inspect those records manually; do not silently reassign their identities.

## Cold-start and remote feedback

On a fresh session, open the received ZIP's `START-HERE.md`, `manifest.json`, `registry/registry.json`, `SUMMARY.md`, and `batch-summary.json`, then inspect the actual pose images/measurements. Different feedback ZIPs may contain registry snapshots taken at different times. The **installed local SQLite registry** is canonical for current state; never merge two JSON exports by last upload date. The local agent can regenerate an up-to-date JSON view using `python scripts/export_registry.py` and include it in the next feedback.

## Boundaries and limitations

- Infra 0002 is metadata infrastructure, **not** a job scheduler, background service or Blender queue.
- It cannot make a pose correct or improve geometric measurement accuracy on its own.
- `run_calibrated_batch.py` and bare `local_refinement.py` without `--session-snapshot` are legacy sequential commands and may use global latest/active context. They must not be used for overlapping registered jobs.
- Registry `next` is advisory. It does not automatically execute anything or prohibit moving to another family.
- Saved pose revisions remain under `poses/`; selected local attempts need explicit promotion if they are to become authoritative.
- A process crash may leave `tracking/exchange-activation.lock`; inspect for an active activation process before removing a stale lock manually. Never auto-remove it while another process may be writing.
