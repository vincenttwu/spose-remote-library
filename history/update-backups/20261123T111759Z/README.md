# SPOSE — standalone Blender library batch update 0.9.2

This is a **flat-root upgrade ZIP** for an existing standalone SPOSE remote library. Extract elsewhere, run `python install-update.py --library "<LIBRARY>"` and then the same command with `--apply`. The package updates scripts/documentation, stages **five** timestamped DOGG V00 modules and installs `batches/BATCH-001.json`. It does not include or overwrite `.blend`, full catalog, SQLite, roadmap, or any prior pose revision.

## The policy change

**No pose approval, geometry score, source REVIEW/EXCLUDE value, or previous result prevents the next pose/batch.** The operational default is run **all five**, save all previews/measurements, register stability separately, and move on. `ROADMAP` is an inventory of built/attempted vs accepted, not an approval gate. V00 first remains the *preferred schedule*, not permission logic for variations.

**Only integrity/safety checks remain:** data-only ZIP member allowlist, JSON identity/schema, source and template fingerprints, path traversal protection, independent-library identity, and non-destructive revision/install behavior.

Read `GUIDE.md` (local agent), `WORKFLOW.md` (process), `SKILL.md` (cold-start agent), and `docs/STATUS-AND-BATCH-SEMANTICS.md` (state definitions). Numerical V2 adjustments are unverified until local Blender runs all five.
