# Pose modules and combined batch feedback

## Incoming pose modules (unchanged core contract)

One flat data-only pose ZIP is named `{POSE_ID}_{YYYYMMDDTHHMMSSZ}.zip` and contains `manifest.json`, `pose.json`, `rig-targets.json`, `contacts.json`, and usually `validation-plan.json`/`render-config.json`. All non-manifest JSON member hashes appear in the manifest. No scripts, `.blend` or executable code belong in a pose ZIP. Source/pair/template identifiers remain pinned for reproducibility; source editorial PASS/REVIEW/EXCLUDE has **no permission effect**. The installed importer renders each module, recording a fresh revision under `poses/` with previews, inputs and diagnostics.

`scripts/run_pose_batch.py` reads a JSON batch plan and attempts **all five** poses in sequence. Failures/warnings in one do not skip the others. Human acceptance is optional; correctly built drafts remain usable and can be revisited later. New pass labels alone do not create new geometry: if package identity was already imported, record `reused_existing_package` and `new_revision_created=false` rather than claiming a new result.

## Combined feedback (infra 0001 schema 2)

Earlier Batch 0001 releases nested **five per-pose feedback ZIPs inside another ZIP**. This is now superseded as the *default* exchange, without deleting historical files. The new combined feedback archive is **one flat ZIP** named `spose-remote-feedback-batch-0001-pass-02_<timestamp>.zip`. It includes:

- `START-HERE.md`, `SUMMARY.md`, `batch-summary.json`, `manifest.json` with SHA-256 inventory.
- `poses/<POSE_ID>/` for each of the five with `inputs/*.json`, pose/validation/checksum/Blender result/log files and images.
- Exact-pixel **lossless WebP images** under `poses/<POSE_ID>/images/` if Pillow/WebP support is available; otherwise original PNG bytes with explicit warnings.
- `context/` containing portable read-only library context — all V00 rows, full pose ID index, rig map, docs, scripts, ROADMAP and current continuation snapshot.

Original PNGs remain in the authoritative revisions and are copied as `POSE_ID_<VIEW>.png` directly inside both `review/` and `upload/`. The feedback ZIP is also directly inside `upload/` alongside the PNGs. Both folders are ephemeral and regenerable using `scripts/refresh_exchange.py`; history stays in `snapshots/`.

See `docs/FEEDBACK-CONTRACT.md` for exact member names and verification, and `docs/SCHEMAS.md` for the schema version. A poor geometry result still never blocks another pose or another batch.
