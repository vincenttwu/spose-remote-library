# Changelog — standalone remote library

## 0.9.0-remote — 2026-11-23, Batch 001 geometry rebuild

- Removed mandatory outer `remote/` archive wrapper from **update bundles** and **future portable context handoffs**; library's own folder name does not matter.
- Added `scripts/rigify_floor_engine.py`: historical Rigify IK initialization, hand palm frames, world torso placement, leg pole targets, evaluated mesh floor region calibration.
- Rewrote Blender builder to require geometry-contract v2; accepts only v2 input, runs geometry hard gate, still renders blocked candidates for analysis.
- Rewrote `scripts/validate_pose.py`: hard gates for grounded knee/hands/feet, knee angle/height, forward fold and sampled below-floor mesh.
- Adapted importer and review workflow: blocked geometry cannot be validated or accepted; old V1 input packages are refused.
- Adaptive camera framing, based on evaluated body mesh bounds.
- Added flat-root, one-command safe update installer with backup, file hashes and no source/tracker/old revision edits.
- Rebuilt DOGG-DOGG-V00, DOGG-CLSD-V00 and DOGG-DOWN-V00 as **unverified** V2 candidates. No Blender runtime run or accepted pose claimed.
- Rewrote all essential skill/workflow/continuation docs for fresh-session usage and actual local feedback loop.

- Added root `GUIDE.md` for local agents receiving only a batch ZIP, and `scripts/check_batch_001.py` for post-install offline contract checks.
- Added per-side kneeling support assertions; both knees must be supported rather than the minimum of an aggregate knee patch.
- Fixed palm-frame matrix application to avoid multiplying the rest orientation twice.
- Installer now surgically switches only `project.json.portable_handoff.archive_root` to `flat`, creates `CURRENT-INSTALL.json` as an incremental install receipt, and preserves the historical `RELEASE-MANIFEST.json` snapshot.

- Expanded current Batch 001 scope to five DOGG-family V00s by adding `DOGG-FCDN-V00` and `DOGG-FROG-V00`; still no move to the next family.
