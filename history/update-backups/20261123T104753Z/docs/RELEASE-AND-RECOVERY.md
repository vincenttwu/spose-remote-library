# Release, backup and recovery checklist

## Full remote release

A new **full** `spose-remote-library-YYYYMMDDTHHMMSSZ.zip` should contain exactly one `remote/` top-level directory. It is a complete snapshot: BP001/CPL01 `.blend` assets, full source CSV, history, scripts, pose metadata/output and independent tracker. Before delivering, verify catalog SHA, base count, checker, roadmap consistency, member hashes, ZIP integrity, and that Blender testing status is stated accurately. Keep the previous full ZIP until the new version opens locally.

## Portable handoff release

`spose-remote-handoff-YYYYMMDDTHHMMSSZ.zip` also uses one `remote/` root, but it is **context-only**. Create via `python scripts/package-library-for-remote.py`; it checks source/pair fingerprints and derived roadmap, then builds `handoff/HANDOFF-MANIFEST.json`. The packager includes source rows only for 276 V00s (full source text), all pose IDs+hashes, scripts/docs, and latest lightweight pose JSON. It excludes `.blend`, full CSV, SQLite and image previews.

Never restore the local library from a context handoff. It intentionally omits required binary/data contents.

## Update/revision protocol

1. Work against a copy of the current full remote library.
2. Preserve old `rNNN` pose revisions and history. No in-place overwrite of user-approved poses.
3. Test Python contracts offline. Blender-specific tests must be run on the owner's machine before claiming rig compatibility.
4. Regenerate roadmap; check identity against the catalog and tracker.
5. Update `CONTINUATION.md`, `SKILL.md`, `WORKFLOW.md`, ROADMAP and relevant `docs/` when process decisions change.
6. Record limitations in CHANGELOG. Update `RELEASE-MANIFEST.json` with current hashes and a new release stamp.
7. Create full ZIP and separately verify all member checksums and exactly one `remote/` root.
8. Create portable handoff from the **same full checkpoint** and verify its manifest; send both or provide full once and handoff for later sessions.

## Recovery after failed import

The importer first stages a candidate inside the target pose's directory and only commits a new rNNN after builder execution. An interrupted process may leave a `.pose-stage-*` directory; preserve it for diagnosis. Compare logs and tracked state before retrying. Do not silently delete a failing stage or reassign it a successful status. A new package timestamp is preferred for a corrected attempt.

## Recovery after tracking/roadmap inconsistency

SQLite `tracking/progress.sqlite` owns job and review history. `tracking/progress.csv`, `events.jsonl`, `ROADMAP.json`, `ROADMAP.md` are regenerate-able derived snapshots. If a tracker job exists but a view is stale, run `python scripts/update_roadmap.py` and `update_tracking.export_snapshots()` in a controlled Python invocation. Do not reconcile by editing checkboxes.

## Source/template migration

If BP001/CPL01, rig map or source CSV must change, assign a new version and document hashes. Old input packages may then fail the dependency check intentionally. Avoid modifying a SHA fingerprint to bypass a mismatch. Old accepted V00 revisions may become `stale_source` if a source row changes. Review applicability and migrate explicitly, rather than counting old acceptance against new geometry.

## Security practices

Use a dedicated working copy, preserve a trusted full-library backup, and treat inbound ZIP content as untrusted. The pose importer allows only specific JSON names and denies path traversal, code execution, symlinks and oversized payloads. Portable handoff excludes binary/large files by allowlist. Checksums detect corruption but are not authenticity signatures. Inspect unexpected external paths or absolute filenames before passing them to Blender.
