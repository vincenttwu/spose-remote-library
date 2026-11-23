# Tracking and roadmap contract

## Why two files?

- `ROADMAP.md` is a **readable project-plan table and checkbox list**: one line per V00 base, grouped by family. This supports quick human scheduling and visual progress review.
- `ROADMAP.json` is a **machine-readable derived snapshot** with source identity, all V00 rows, per-family counts, latest attempts, accepted revision references and locked variations state.

**Neither is the authority for acceptance.** SQLite `tracking/progress.sqlite` holds revision jobs and human review events. The pinned catalog determines the expected 276 V00 IDs. Running `python scripts/update_roadmap.py` joins the two and regenerates both. No duplicate manual state should be kept in those files.

## State machine

| State in roadmap | Meaning | Changes the acceptance count? |
|---|---|---|
| `not_started` | Source row exists; no remote job for that V00 ID | No |
| `in_progress` | Latest job queued/working | No |
| `draft` | Imported build candidate, awaiting review | No |
| `validated` | Explicit human/technical review stage, still not final acceptance | No |
| `accepted` | At least one explicitly accepted revision for current row SHA and checkpoint | **Yes** |
| `blocked` | Last attempt rejected or blocked | No |
| `failed` | Blender/import execution failed | No |
| `excluded` | Latest tracker job status excluded (not source gate alone) | No |
| `stale_source` | Tracking job exists, but none matches current source checkpoint and row SHA | No |

A source `generation_gate` of `PASS`/`REVIEW`/`EXCLUDE` is a separate risk filter. A `PASS` source row does not cause a tracker `accepted` state.

If an older revision is accepted and a newer draft fails, the base remains `accepted` in the roadmap while `latest_revision`/`latest_status` still shows the new attempt. This is intentional and prevents accidental loss of a previously reviewed baseline.

## Family and global milestones

- Family `not_started`: no V00 base has a remote attempt.
- Family `in_progress`: any attempt exists but not all base poses accepted.
- Family `v00_complete`: every expected V00 base for that family has an accepted source-matching revision.
- Global V00-first milestone complete: all 276 accepted. Other 2,760 variation records remain deferred until the user separately authorizes a new production phase.
- The machine field `variation_phase_enabled` in the current roadmap is a readiness indicator only when 276/276 accepted. It is **not authorization to execute variations**. The full importer still enforces V00-only scope.

## Regeneration and verification

```powershell
python scripts/update_roadmap.py
python scripts/update_roadmap.py --check
```

The default command regenerates. `--check` recomputes the expected JSON and Markdown from source and SQLite, compares bytes and returns an error if stale. This is useful before packaging an assistant handoff. Both outputs are deterministic given the same source and tracker.

`update_tracking.export_snapshots()` regenerates the roadmap after importer writes and after `review_pose.py` decisions. If snapshot generation fails after a committed tracker update, run `update_roadmap.py` again; the SQLite job remains authoritative.

## Manual review instructions (user-only)

The importer creates a `draft` after running Blender; **it never auto-accepts**. After actually reviewing the rendered previews and contact QA, the user may run:

```powershell
python scripts/review_pose.py DOGG-DOGG-V00 --revision 1 --decision accepted --reviewer user --note "Viewed front/side/three-quarter and verified contact" --confirm-reviewed
```

Use `--decision blocked` with a specific reason when a pose is incorrect; use `validated` when it has been inspected but is not yet approved. If the source `generation_gate` is `REVIEW`, acceptance additionally requires `--acknowledge-source-review`. The script will reject an unexecuted build or one without standard previews.

`review_pose.py` writes an event into SQLite, updates the revision state and refreshes derived views. It cannot guarantee that the human correctly assessed the pose; the flag documents user attestation.

## Integrity checks and handoffs

- All roadmap V00 rows derive from source; compare counts against `source/dataset.json`.
- The derived JSON contains the SHA-256 of each source V00 `specification` and current source checkpoint.
- A future session that only has a small handoff can inspect progress but cannot write authoritative SQLite. If progress happened after the snapshot, the user must create an updated handoff.
- Never manually check a box and claim the tracker advanced; never update the full library by extracting the portable handoff over it.
