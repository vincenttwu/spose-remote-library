# WORKFLOW.md — five-pose, two-pass remote production workflow

## Standard cycle (without approval gates)

**Pass 01:** select five source V00 candidates; author five *distinct data-only* pose modules and one batch plan; send one ZIP bundle. Local agent installs, builds **all five**, records geometry diagnostics and exports one feedback ZIP. Remote assistant evaluates all five side-by-side and issues a numerical visual/source rating.

**Pass 02 (normal completion target):** based on *actual* Pass 01 renders, adjust target coordinates/calibration and create five newly identified module packages. Apply the class-appropriate change to each posture (e.g. quadruped, folded standing, low-prone, frog-wide); do not force every silhouette to match a single calibration pose. Send one Pass 02 ZIP and evaluate all five again. Confirm new revision IDs **and** changed control hashes to distinguish real improvement from merely repacking old results.

**Pass 03 (optional):** only if the user judges the results sufficiently unsatisfactory. User may move on to the next five even when this batch remains `needs_work`. Tooling updates are independent of pose passes.

## State and status model

- `attempted`: execution was recorded (including technical errors).
- `built`: usable render/revision exists; may be a `draft` and may have serious warnings.
- `needs_work`: geometry/stability annotation, **not** a block.
- `accepted`: optional human designation, **not** required.
- `reused_existing_package`: same pose-package identity was recognized and no new revision created. **Never count as a successful geometry Pass N**.
- `failed`: technical build did not complete; preserve logs and continue other poses.
- `generation_gate=REVIEW/EXCLUDE`, `hard_gate_pass`, and `geometry_reference_pass`: reference/classification metadata only. A true source or file-integrity error may prevent importing *that item*, but all other items continue.

A V00-built ROADMAP checkbox means built, not visually validated. V00-first is a planning order, never permission logic. See existing `docs/TRACKING-AND-ROADMAP.md` and `docs/STATUS-AND-BATCH-SEMANTICS.md`.

## Local execution (entire batch)

```powershell
cd "<LOCAL_SPOSE_LIBRARY>"
python scripts/run_pose_batch.py --plan batches/BATCH-001.json --dry-run
python scripts/run_pose_batch.py --plan batches/BATCH-001.json --blender "<BLENDER_EXE>"
python scripts/verify_feedback.py "upload/<FEEDBACK_ZIP>"
```

The batch runner continues after any individual pose error. The summary includes rows for all five, new/reused identity, revision, diagnostics and render count. The local agent does not manually approve each pose and does not create five separate outbound uploads.

## Folder lifecycle

| Top-level location | Role | Lifetime |
|---|---|---|
| `batches/` | Batch plans, labels, package references | Long-lived |
| `incoming/` | Staged data-only module ZIPs | Keep until safe to clear |
| `poses/` | Authoritative versioned results | Permanent |
| `snapshots/` | Per-run `batch-summary.json`, optional metadata and outbound feedback history | Permanent |
| `review/` | Flat original pose-prefixed PNGs, `SUMMARY.md`, `manifest.json` | Disposable, regenerable |
| `upload/` | Same PNGs and **one** return ZIP | Disposable, regenerable |

When refreshing `review/` and `upload/`, only the **latest selected batch/pass** should be present; do not mix images from earlier passes. Preserve persistent snapshots and pose revisions. Recover both disposable folders with `python scripts/refresh_exchange.py --snapshot "snapshots/<RUN>"` without rerendering.

## One-feedback handoff

Naming: `spose-remote-feedback-batch-0001-pass-02_<YYYYMMDDTHHMMSSZ>.zip`. Includes `manifest.json` + member SHA-256, `SUMMARY.md`, `batch-summary.json`, `poses/<ID>/{images/*.webp,inputs/*.json,validation.json,build.log,...}` and `context/` containing full portable docs/scripts/rig/source references (no heavy .blend/SQLite). Images are exact-pixel lossless WebP when Pillow/WebP are available, otherwise byte-identical PNG fallback. **No five nested feedback ZIPs.**

Locally the PNG originals remain in `poses/`, `review/`, and `upload/`. Upload individual prefixed PNGs if deeper human visual discussion is needed. ZIP contents and image fidelity are checked by scripts; visual/source ratings remain a human/assistant task.

## Decision after every feedback

Provide a batch score (qualitative /10) and individual scores; state data quality and whether this pass actually produced new revisions. Summarize improvements/regressions and top three fix categories. Offer **move on** or **another pass** as a user choice, never as a gate. Do not claim hardware/Blender geometry testing when only offline ZIP tests were run.


## Active geometry pass: Batch 0001 / Pass 03
The Pass-02 feedback contained five **reused** revisions. This new Pass-03 package has five new module identities and should create five new revisions when run. Record `new_revision_count=5` as a factual check, not a stop gate. Do not mislabel reused or failed revisions. Geometry defects remain `needs_work` metadata; all five items are attempted regardless. The local operator returns only `upload/spose-remote-feedback-batch-0001-pass-03_<UTC>.zip`, optionally individual PNGs on request.
