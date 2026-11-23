> **INFRA 0002: non-linear registry active.** The old Batch 0001 Pass 05 headers below are preserved historical information, not a global work queue. Batch/pass operations now use `scripts/registry.py`, `scripts/run_registered_batch.py`, and `scripts/activate_batch.py`; read `docs/REGISTRY-OPERATIONS.md`.

> **ACTIVE: Batch 0001 Pass 05.** Read release `APPLY.md`, `LOCAL-WORKS.md` and installed `docs/PASS-05-CALIBRATION.md`; five new modules seeded from Pass04 selected local Attempt02 controls. Optional 0–2 guided local refinements per pose. Existing older pass instructions below are historical. All quality metrics are advisory.

# GUIDE.md — local commands, checks, recovery

This guide is for the installed standalone SPOSE library and agents maintaining it. The update ZIP is *not* the library. It does not contain `.blend` assets or the full SQLite tracker. Work from the actual library root; verify `project.json` reports `project_id=SPOSE-REMOTE-LIBRARY`.

## 1. Install infrastructure update (no new pose pass)

Extract `spose-remote-bundle-infra-0001_<UTC>.zip` to a **temporary folder outside the library**. With a Python interpreter on the machine:

```powershell
cd "<EXTRACTED_INFRA_BUNDLE>"
python install-update.py --library "<LOCAL_SPOSE_LIBRARY>"
python install-update.py --library "<LOCAL_SPOSE_LIBRARY>" --apply
```

Preflight prints changed/identical files; apply backs up overwritten files under `history/update-backups/<RELEASE>_<UTC>/` and records the precise receipt. Only explicitly inventoried docs/scripts are changed. The source, pair assets, SQLite, old revisions and installed pose packages stay intact.

This bundle does **not** automatically execute Blender, alter pose geometry, or count as Pass 03. Do not copy the ZIP's `updates/scripts/` into multiple alternate locations; the installer maps them into `<LIBRARY>/scripts/`.

## 2. Verify tooling after installation

```powershell
cd "<LOCAL_SPOSE_LIBRARY>"
python scripts/check_remote.py
python scripts/check_documentation.py
python scripts/update_continuation.py
python scripts/run_pose_batch.py --plan batches/BATCH-001.json --dry-run
```

`check_remote.py` and dry-run may report genuine missing dependencies; these are **integrity checks**, never pose-quality gates. `check_documentation.py` is advisory by default. See `docs/MAINTENANCE.md` for optional `--strict` and image library installation.

## 3. Refresh *existing* Pass 02 evidence without Blender

The infrastructure update is specifically designed to work with already-rendered Batch 0001 Pass 02 results. Once installed, run:

```powershell
python scripts/refresh_exchange.py
```

It selects the latest valid `snapshots/batch-*-pass-*` run, regenerates `CONTINUATION.md` from live state, creates a compressed single feedback ZIP in that persistent snapshot, and refreshes two flat temporary folders:

```text
review/
  DOGG-DOGG-V00_front.png
  DOGG-DOGG-V00_side.png
  DOGG-DOGG-V00_three-quarter.png
  DOGG-DOGG-V00_qa-regions.png
  ... other four pose IDs
  SUMMARY.md
  manifest.json
upload/
  same individual PNGs
  SUMMARY.md
  manifest.json
  spose-remote-feedback-batch-0001-pass-02_<UTC>.zip
```

This does **not** create r004, r003, or any other pose revision. The images represent the old recorded geometry until a genuinely new geometry package is installed. To select a specific historical run, add `--snapshot "snapshots/<RUN>"`.

## 4. Compress/verify evidence

For compact WebP feedback, Pillow is optional but recommended (install in the *Python used for export*):

```powershell
python -m pip install Pillow
python scripts/refresh_exchange.py --image-format webp
python scripts/verify_feedback.py "upload/<FEEDBACK_ZIP_NAME>"
```

If Pillow is unavailable, the exporter includes **unchanged PNGs** in the single ZIP with an explicit warning and proceeds. Never silently convert to lossy JPEG or change the authoritative PNGs. Individual lossless conversion test:

```powershell
python scripts/compress_images.py "review/DOGG-DOGG-V00_front.png" --output "<TEMP_DIR>/test.webp"
```

The converter decodes and compares RGBA pixel bytes; a mismatch raises an error.

## 5. Later: run a truly new five-pose batch

Once five **newly authored**, timestamped pose modules and a matching plan are staged in `incoming/`:

```powershell
python scripts/run_pose_batch.py --plan batches/BATCH-001.json --dry-run
python scripts/run_pose_batch.py --plan batches/BATCH-001.json --blender "<BLENDER_EXE>"
```

Use your real Blender 5.2.2 LTS executable. The runner attempts all five even if one produces poor posture, warning or fails. If a module is identical to a prior import, its result explicitly says `reused_existing_package` and it **does not count as a new calibration revision**. `--rerun` exists for deliberately repeating an identical module, but normally a real new geometry pass requires a newly authored package.

Afterward the runner refreshes `review/` and `upload/` automatically. Upload **only the one ZIP** from `upload/`, unless additional individual PNGs are requested to discuss visual problems. Do not separately upload a handoff ZIP; it is already embedded in the combined feedback ZIP when the library's portable context packer is healthy.

## 6. Recovery and rollback

- If `review/` or `upload/` was deleted: `python scripts/refresh_exchange.py` (no Blender).
- If a batch fails after some poses: inspect snapshot `batch-summary.json` and logs; record partial results; never throw away successful revisions.
- If documentation became stale: `python scripts/update_continuation.py` then `python scripts/check_documentation.py`.
- If the ZIP is corrupt, source hashes do not match, or wrong library selected: resolve **integrity** issue before installing. Do not disable integrity checks to force an update.
- For an infrastructure rollback, locate the receipt printed by the installer, then from extracted update folder:

```powershell
python install-update.py --library "<LOCAL_SPOSE_LIBRARY>" --rollback "<LIBRARY>/history/update-backups/<RELEASE>_<UTC>/INSTALL-RECEIPT.json"
```

Rollback refuses to overwrite targets edited since installation. Existing pose revisions, template, source and SQLite are unaffected either way. See `docs/MAINTENANCE.md` and `docs/COLD-START.md`.


## Pass 03: exact local execution
1. Extract the one Pass-03 release ZIP somewhere **outside** the live library.
2. Read release `APPLY.md`, then `LOCAL-WORKS.md` and `docs/PASS-03-CALIBRATION.md`.
3. From the extracted release root, run `python install-update.py --library "<LIBRARY>"`; review changes, then run `python install-update.py --library "<LIBRARY>" --apply`.
4. From the existing standalone library, run `python scripts/check_remote.py` and `python scripts/run_pose_batch.py --plan batches/BATCH-001.json --dry-run`. Ensure five new timestamped packages verify.
5. Run `python scripts/run_pose_batch.py --plan batches/BATCH-001.json --blender "<BLENDER_EXE>"`. No `--rerun` normally; these are new packages. Run all five even if one has warnings.
6. Verify `review/` has 20 flat PNGs if all render successfully and `upload/` has one compact feedback ZIP plus PNG copies; preserve `snapshots/`. If export fails but poses built, use `python scripts/refresh_exchange.py` without rerendering.
7. Inspect `batch-summary.json` for `new_revision_count`, `reused_revision_count`, and failures. These are recording fields, not quality gates.
8. Return only `upload/spose-remote-feedback-batch-0001-pass-03_<UTC>.zip` by default. Do not generate a separate handoff ZIP.


## Active update: Batch 0001 / Pass 04 — measured geometry and calibration

This update supersedes the previous Pass-03 *active-pass instructions* but preserves all prior architecture and safety guidance. The user requested a fourth geometry pass because Pass 03 rendered worse overall despite misleading tiny nearest-vertex contact gaps. Use `APPLY.md` and `LOCAL-WORKS.md` from the incoming Pass-04 release as the exact procedure.

The local agent shall run all five poses and inspect their measured new revisions **without approval gates**, then collect independent neutral-rig and saved-scene measurements using `scripts/run_calibrated_batch.py --blender "<BLENDER_EXE>" --plan batches/BATCH-001.json`. This command builds with `--save-blend`, runs `scripts/collect_calibration.py`, refreshes `review/` and `upload/`, and verifies a **single** compact feedback ZIP containing `calibration/` members.

The head-aim solver measures rotation sign using RIG001 -Y reference. Palm contact uses **distribution/coverage of a bounded patch**; zero minimum distance is not proof of a correct grip. The calibration JSON is versioned under `tooling/calibration/CPL01-v001/` and remains descriptive. Never modify Blender template, catalog or tracker manually. `docs/CALIBRATION-REFERENCE.md` provides schema, confidence limits, recovery and cold-start instructions.


## Additive local agent flow — optional, not a quality gate

The earlier instructions above remain relevant for simple batch-only runs. **For the currently active Pass 04**, prefer `APPLY.md` and `docs/LOCAL-COLLABORATION.md`: run five baseline builds and rig/scene probes with `scripts/run_calibrated_batch.py --blender "<BLENDER_EXE>" --plan batches/BATCH-001.json`. Then inspect `local/ACTIVE.json`, edit generated proposal files with bounded explicit target changes, and call `scripts/local_refinement.py run --pose <POSE_ID> --attempt 1|2 --blender "<EXE>"` for the chosen poses. Run `scripts/local_refinement.py select --pose <POSE_ID> --attempt 0|1|2 --reason "<observed justification>"`, then `scripts/run_calibrated_batch.py --phase finalize`. The single feedback ZIP in `upload/` contains original baseline and any local trial evidence. To turn this off add `--local-calibration off` to the baseline command. No local trial creates a tracked pose revision or automatic approval. `local/` is disposable **after** finalization.

## Active Pass 05 commands (supersede old pass commands)

After installation and checks, run from library root:

```powershell
python scripts/run_calibrated_batch.py --blender "<BLENDER_EXE>" --plan batches/BATCH-001.json
# edit bounded proposal JSONs in local/ only if improvements are plausible
python scripts/local_refinement.py run --pose DOGG-DOWN-V00 --attempt 1 --blender "<BLENDER_EXE>"
python scripts/local_refinement.py select --pose DOGG-DOWN-V00 --attempt 0 --reason "Baseline chosen; trial regressed measured support"
python scripts/run_calibrated_batch.py --phase finalize --plan batches/BATCH-001.json
```

All five are required in the batch plan, but no specific pose is required to pass quality checks to continue. For each pose, select 00/01/02 by evidence rather than always choosing 02. `upload/` contains the one feedback ZIP and flat selected images.


## Infra 0002 command overrides for overlapping work

For registered non-linear runs, the old unqualified `run_calibrated_batch.py` and `refresh_exchange.py` commands in historical sections below are **not** the default. Use `python scripts/registry.py status`, then `python scripts/run_registered_batch.py --phase baseline --plan batches/BATCH-002.json --blender "<EXE>"`, then `python scripts/run_registered_batch.py --phase finalize --snapshot "snapshots/<RUN>"`, then `python scripts/activate_batch.py --batch 0002 --pass 01`. Every local refinement command must include `--session-snapshot "snapshots/<RUN>"` **before** the subcommand. See the full tested procedure in `docs/REGISTRY-OPERATIONS.md`.
