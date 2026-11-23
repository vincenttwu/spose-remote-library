# Pose package JSON contract v1

A generated pose package is named `POSE-ID_YYYYMMDDTHHMMSSZ.zip` and contains **JSON only**, no directory prefix. All required names: `manifest.json`, `pose.json`, `rig-targets.json`, `contacts.json`. Optional: `render-config.json`, `validation-plan.json`. No scripts, meshes, credentials, absolute paths, external files or embedded `.blend`.

## Dependency fields

`manifest.json`:

```json
{
  "schema_version": 1, "package_type": "spose_pose_module",
  "pose_id": "DOGG-DOGG-V00", "package_timestamp_utc": "20261123T091500Z",
  "dependencies": {
    "source_id": "SRC003", "source_checkpoint": "20261122T013728Z",
    "source_row_sha256": "<sha256(specification UTF-8)>",
    "pair_id": "CPL01", "pair_version": "v001",
    "template_sha256": "<sha256 pairs/CPL01/v001/template.blend>",
    "rig_map_id": "RIG001", "rig_map_version": "v001"
  },
  "payload_sha256": {"pose.json": "...", "rig-targets.json": "...", "contacts.json": "..."}
}
```

Use `scripts/check_remote.py` to check the installed source, and the package manifest generator/validator in `scripts/` to obtain exact hashes. All ZIP members are checksummed; `manifest.json` itself is outside the hash map (manifest is not digitally signed).

`pose.json` (minimum): `{"schema_version":1,"pose_id":"DOGG-DOGG-V00","status":"proposal"}`.

`rig-targets.json` (example values are **illustrative, not a finished pose**):

```json
{
  "schema_version": 1,
  "controls": [
    {"actor":"A", "object_role":"root", "space":"OBJECT_WORLD_LOCATION_M", "value":[0,0,0]},
    {"actor":"B", "bone":"torso", "space":"POSE_LOCAL_ROTATION_DEG", "value":[15,0,0]},
    {"actor":"B", "bone":"hand_ik.L", "space":"POSE_WORLD_HEAD_M", "value":[0.2,-0.8,0.12]}
  ]
}
```

Other accepted spaces: `OBJECT_WORLD_ROTATION_DEG` and `POSE_WORLD_HEAD_M` (IK/pole controls), with all values as 3-number lists. Bone names must exist in rig. `contacts.json`: `{"schema_version":1,"anchors":[]}`. Optional anchor pairs can specify `id`, `actor`, `bone`, `target_actor`, `target_bone`, `tolerance_m`; they are measured using bone-head proxies and require visual confirmation.

`render-config.json`: `{"resolution":[960,800]}`; QA regions render uses available VP001 controls. `validation-plan.json` may contain user-facing acceptance notes; this is not automatically interpreted as passing evidence.

## Execution and outputs

```powershell
python scripts/import_pose.py incoming/DOGG-DOGG-V00_20261123T091500Z.zip --dry-run
python scripts/import_pose.py incoming/DOGG-DOGG-V00_20261123T091500Z.zip --blender "C:\path\to\blender.exe"
python scripts/export_feedback.py DOGG-DOGG-V00
```

Default output: `poses/POSE-ID/CPL01/v001/r001/` holding inputs, metadata, PNGs, validation, logs, checksums. Use `--save-blend` if you need a full Blender scene. No build is auto-accepted. User should review images and contact fit and return feedback ZIP for next revision.

The pose module must already contain **explicit rig transforms**. These scripts do not infer a physically correct pose from the SPOSE specification text automatically.

## Portable context-only authoring and roadmap (0.8.0)

From a compact handoff rather than the full library, use `python scripts/package_pose_from_handoff.py POSE_ID draft-folder --output outgoing/`. The handoff contains `source/pose-dependencies.json` with the registered source row and pair template hashes needed to create importable data-only ZIPs. **No scene is built or validated by this offline script.** The receiving full remote independently checks dependency hashes before Blender execution.

Run `python scripts/check_handoff.py` to verify the context members and V00 hashes after extraction. The full `remote/` uses `scripts/check_remote.py` instead. Neither check automatically marks any V00 accepted.

`ROADMAP.md` and `ROADMAP.json` are generated from `source/` and `tracking/progress.sqlite`. The current global V00-first phase requires all 276 base IDs across 28 families to be explicitly accepted before any V01–V10 work, regardless of individual family completion. See `docs/TRACKING-AND-ROADMAP.md`.
