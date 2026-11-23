# Troubleshooting SPOSE Remote

## Source mismatch on import

**Symptom:** `Package dependency mismatch for source_row_sha256` or catalog SHA error.

**Likely cause:** A package was authored against an older source or incomplete handoff. In the full library, run `python scripts/check_remote.py`; inspect `source/dataset.json` and current CSV SHA. Regenerate portable handoff, re-create pose input ZIP from latest source, and preserve rejected artifacts for audit. **Do not change a checksum string merely to force acceptance.**

## Pair/template mismatch

**Symptom:** template SHA or pair-version mismatch.

The target library's `pairs/CPL01/v001/template.blend` differs from what the package pins. Verify actual file identity. If the rig changed deliberately, version the pair, update docs/source registration and regenerate the handoff. Never make the module overwrite the shared rig.

## ZIP invalid / wrong root

- Pose package `{POSE_ID}_{UTC}.zip`: flat JSON-only root, `manifest.json` plus required payloads. No `remote/` prefix.
- Full remote library or context handoff ZIP: exactly one top-level `remote/` root.
- The small handoff is **not** an importable pose ZIP and cannot be installed over full remote. See `docs/HANDOFF-DESIGN.md`.

## Blender not found

`import_pose.py` requires an executable Blender path in `--blender` or `SPOSE_BLENDER`. Run `--dry-run` to validate package data independently, but the pose cannot be rendered without Blender. Blender version in source tests was 5.2.2 LTS; newer versions need local compatibility tests.

## Blender build fails or rig bone missing

Inspect `poses/<ID>/.../rNNN/build.log` or retained `.pose-stage-*` folder. Confirm `CPL01_A_RIG/B_RIG` are present in loaded scene and bone names exist. Cross-check `RIG001-v001.json`; the rig builder currently supports only mapped control spaces and explicit numeric triples. Keep stage files for forensics; author a new package revision, don't overwrite an older result.

## Contact proxy looks good but image is wrong

Expected limitation. Proxy distance is unsigned and nearest-surface sampled; overlapping meshes can appear numerically close. Inspect front/side/three-quarter images, wrists/palms, elbow poles, chest, pelvis and floor load path. Distinguish (1) whole-character alignment error from (2) limb-local contact error. Update root/IK targets cautiously in a new revision and export feedback; never auto-accept.

## Previews missing / QA regions absent

The builder requires cameras `CAM_Front`, `CAM_Side`, `CAM_ThreeQuarter` for standard renders. `qa-regions.png` additionally requires region-mode appearance control. Missing QA renders are an issue; do not claim full appearance testing. Check scene camera names, VP001 controls, lights, Blender log and template fallback.

## ROADMAP.md checkboxes not updating

1. Verify the job/review is in `tracking/progress.sqlite`; a mere pose ZIP draft in `incoming/` has no tracker job.
2. Run `python scripts/update_roadmap.py` and then `--check`.
3. If the row remains unchecked, inspect whether the job is merely `draft`, blocked, failed, or stale with respect to current `source_row_sha256`.
4. To mark accepted, user must inspect images and run `scripts/review_pose.py` with a specific revision and `--confirm-reviewed`.
5. Never edit the generated Markdown checkbox or JSON status directly.

## A whole family is done—can I do V01 now?

**Not yet.** The current global plan requires all 276 V00 across 28 families accepted first. After global completion, the user must separately authorize V01–V10; importer currently rejects non-V00.

## Portable handoff seems incomplete

That is intentional: it excludes `.blend`, full catalog, SQLite and images. It includes all 276 V00 source rows, IDs+hashes for all records, dependencies, rig map and docs. To **run Blender** or update true tracking you need the full library. To **see visual errors**, additionally provide the relevant feedback ZIP. To **synchronize progress**, regenerate handoff on user's machine after local updates.

## Historical pilot confusion

`history/local-pilots/UFDG-FWCH-V00` is an excluded local draft, not an accepted remote V00. `UFDG-FWCH-V01` is a local contact-review draft. Neither belongs to the new independent remote active tracker or the V00 acceptance totals. Treat history as diagnostic evidence only.

## Unexpected local/provenance absolute paths

Files may mention the creator's Windows paths as original provenance. Remote runtime should resolve assets relative to `remote/`, not those paths. Do not modify the read-only original source to conceal provenance.

## What to send for help

For context/continued authoring: a **new** `spose-remote-handoff-<UTC>.zip`. For visual contact correction: the **pose feedback ZIP**. For a pair-template or rig structural change: the **full remote library** (or explicit changed asset and updated metadata). No need to upload 60 MB of Blender assets for routine prompt/pose JSON design when rig versions are unchanged.
