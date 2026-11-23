# Pose module and batch feedback

One flat data-only pose ZIP is named `{POSE_ID}_{YYYYMMDDTHHMMSSZ}.zip` and contains `manifest.json`, `pose.json`, `rig-targets.json`, `contacts.json` and optional render/validation JSON. All non-manifest JSON member hashes appear in manifest. No scripts, `.blend` or executable code belong in a pose ZIP. Source/pair/template identifiers remain pinned for reproducibility; source editorial PASS/REVIEW/EXCLUDE has no permission effect.

The installed local importer renders each module and creates a fresh revision path. `scripts/run_pose_batch.py` reads a JSON batch plan and runs **all five** in sequence. Failure/warnings in one do not skip another. It saves a combined ZIP with one summary table plus per-pose feedback ZIPs. Human acceptance is optional; every correctly built draft remains usable and can be revised later.
