# Cold-start instructions: standalone library, full vs context-only

When user uploads a ZIP, inspect its top-level entries first. **New releases do not have a wrapper `remote/`**. A **full** library includes `project.json`, full catalog CSV, pair `.blend` and `tracking/progress.sqlite`. A **portable context** includes root `project.json`, `CONTINUATION.md`, `ROADMAP.md`, scripts, rig-maps and source subset/pose hashes, but excludes big binaries and SQLite. Never overlay a context-only ZIP onto the full library.

Read `CONTINUATION.md`, `SKILL.md`, `WORKFLOW.md`, `ROADMAP.json`, `docs/GEOMETRY-ENGINE-V2.md`, then relevant source V00 rows. Inspect `tracking/progress.csv` for latest local run (SQLite authoritative at owner machine). Ask for actual feedback ZIP if reviewing contact quality; source/spec text alone cannot establish visual contact.

General context: all 276 V00 bases must be reviewed before variations. Three first DOGG poses had visibly incorrect geometry under v1; engine v2 introduced rootless packaging, world-space torso positioning, IK initialization, material-region floor calibration, and posture hard gates. This does not establish Blender validation in the assistant runtime. Start with `DOGG-DOGG-V00` alone; user runs Blender and returns feedback.

Authoring from handoff only: `python scripts/check_handoff.py`, then draft `pose.json`, `rig-targets.json`, `contacts.json` etc, package with `python scripts/package_pose_from_handoff.py POSE_ID /path/to/draft --output out/`. Handoff includes full V00 specification, pose dependencies and hash fingerprints, but cannot reconstruct a Blender scene.

For local upgrades, a self-contained **flat-root batch ZIP** contains `install-update.py`, `UPDATE-MANIFEST.json`, `scripts/`, `docs/`, `pose-packages/`. Extract separately and run installer with `--library FULL_ROOT` then `--apply`. Installer backs up scripts/docs and copies pose inputs to `incoming`, without touching binary rigs or existing revisions.

## When a local agent receives an upgrade batch ZIP

Read `GUIDE.md` at that batch ZIP's root. It is the *executable local-agent checklist* for safe installation and staged Blender calibration. `install-update.py` must be run with `--library <actual standalone library root>` first as a dry run and only then with `--apply`; never extract over the library. The upgrade ZIP uses a flat root (`scripts/`, `docs/`, `pose-packages/`) and is not the entire runnable library. After installation, compare `CURRENT-INSTALL.json`, `ROADMAP.md` and the build diagnostics. Return a small feedback ZIP rather than the entire library, and mark no pose accepted without user review.
