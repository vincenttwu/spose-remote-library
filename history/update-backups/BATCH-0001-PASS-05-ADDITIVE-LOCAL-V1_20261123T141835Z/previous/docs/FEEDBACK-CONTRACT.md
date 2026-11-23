# Feedback exchange contract — one upload, full context

## Purpose

The user must be able to finish a complete five-pose pass and upload **one** ZIP. That single file must contain all rendered evidence, machine diagnostics, exact pose inputs and enough source/rig/docs context for a cold-start remote assistant. The user may additionally select individual original PNGs from `upload/` for targeted discussion without repackaging or navigating deeply nested revision folders.

## Filenames

- Pose bundle from remote assistant: `spose-remote-bundle-batch-0001-pass-02_<YYYYMMDDTHHMMSSZ>.zip`.
- Feedback from local: `spose-remote-feedback-batch-0001-pass-02_<YYYYMMDDTHHMMSSZ>.zip`.
- Tooling-only upgrade: `spose-remote-bundle-infra-0001_<YYYYMMDDTHHMMSSZ>.zip` (does not count as Pass 03).

No second context ZIP is routinely needed. `context/` is embedded under the feedback ZIP. Old nested-feedback files remain valid historical artifacts but are not the new standard.

## Local flat artifacts

- `review/`: at most current batch's 20 original PNGs plus `SUMMARY.md` and `manifest.json`, no subfolders.
- `upload/`: same original PNGs and **exactly one** feedback ZIP, plus `SUMMARY.md` and `manifest.json`; no `current/` or `feedback/` subfolder.
- `snapshots/`: persistent history; the ZIP used to create `upload/` stays preserved under the selected run folder. Recovery regenerates disposable folders without Blender.

Image basename: `{POSE_ID}_front.png`, `{POSE_ID}_side.png`, `{POSE_ID}_three-quarter.png`, `{POSE_ID}_qa-regions.png`. Absent views must be recorded, never silently replaced by earlier results.

## Lossless compression policy

- Default compact ZIP stores **lossless WebP**, encoded from existing PNGs, verifying exact RGBA pixel equality on decoding. For fully opaque RGBA, RGB encoding is allowed only because RGBA reconstruction is exact.
- The original PNG is never overwritten or deleted; the PNG remains in `poses/`, `review/` and `upload/`.
- `Pillow` and WebP encoder support are optional; if absent, the combined ZIP falls back to the original PNG bytes with an explicit warning, and the five-pose batch still completes.
- Lossy JPEG, lossy WebP, resizing, resampling, altered camera configuration and alpha-dropping that changes RGBA pixels are prohibited for default feedback.
- No per-pose nested ZIPs; a single outer ZIP with `poses/<POSE_ID>/` members reduces complexity. ZIP compression itself adds little to existing PNG/WebP, so savings chiefly come from lossless pixel codec selection.

## Full evidence

Each pose directory includes original `pose.json`, `validation.json`, `checksums.json`, `blender-result.json`, `build.log`, all JSON inputs and available images. Top-level summary always contains all five attempted result rows, including failed runs without images. Embedded context includes derived V00 source rows, complete ID index, rig maps, scripts, docs and ROADMAP snapshot. It omits heavy `.blend`, authoritative SQLite and full raw catalog; local owner retains those.

`manifest.json` SHA-256 inventory allows verification of payload integrity. A separate file checksum/hash for original PNG is recorded for each WebP conversion. `scripts/verify_feedback.py` checks integrity and returns warnings for incomplete poses/views; it never blocks the next batch based on geometry.

## Reproducibility and interpretation

`reused_existing_package` must be displayed as reuse, not a new pass. A batch with five reused revision references is not five newly calibrated poses. Remote evaluator should inspect all images and source requirements and give per-pose quality scores with an explanation of uncertainty; machine validation is not a human quality score. See `docs/REVIEW-AND-SCORING.md` for the proposed rubric.


## Additive local attempt evidence (schema extension within combined v2 ZIP)

`manifest.json.local_refinement` records whether local attempts were included, selected attempt indices for each pose, per-pose attempt counts, and compact image count. Inside the **same** feedback ZIP, `local/SELECTIONS.json` provides the complete selection/evidence manifest and `local/local-evidence/<POSE_ID>/attempt-XX/` contains proposal edits, result JSON, optional scene-calibration JSON, and selected `rig-targets.json`. Local candidate images are lossless WebP. The selected candidate receives four views; any nonselected refinement provides side and three-quarter. The baseline is already included under `poses/<POSE_ID>/images`; when a local candidate is selected, the baseline includes only two diagnostic views to avoid unnecessary duplication. Full PNGs for the **selected** current batch remain directly in flat `review/` and `upload/`.

No `.blend` or nested per-pose ZIPs are uploaded. Original candidate `.blend` and full-size PNGs stay local. `local/` can be cleared once `finalize` has copied all selected parameters, trial measurements and evidence into `snapshots/`. Old feedback ZIPs remain valid and verify normally without the optional local section.
