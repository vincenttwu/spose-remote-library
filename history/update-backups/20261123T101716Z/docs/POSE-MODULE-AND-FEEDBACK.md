# Pose-module and feedback contract

## Goals

Each candidate should be a **small, portable ZIP of declarative controls**, not a copy of 20–60 MB of mannequin assets. All modifications occur on the user's full remote Blender library and create a fresh versioned `rNNN` pose revision. Candidate ZIPs are data-only, are source-and-pair pinned, and cannot execute arbitrary imported scripts.

## Pose input ZIP

Naming: `{POSE_ID}_{YYYYMMDDTHHMMSSZ}.zip`, for example `DOGG-DOGG-V00_20261123T091500Z.zip`. The ZIP is flat; required files: `manifest.json`, `pose.json`, `rig-targets.json`, `contacts.json`; optional: `render-config.json` and `validation-plan.json`.

`manifest.json` fields: schema version 1, package_type `spose_pose_module`, exact pose ID and UTC filename timestamp, dependencies (`source_id`, `source_checkpoint`, `source_row_sha256`, `pair_id`, `pair_version`, `template_sha256`, `rig_map_id`, `rig_map_version`), SHA-256 for every other JSON member. The format does **not** provide cryptographic signatures.

`pose.json`: metadata, pose ID, status proposal, authoring hypothesis, expected support geometry, notes and risks. `rig-targets.json`: an ordered `controls` array; explicit actor A/B, bone or root role, supported coordinate-space string, numeric triple. `contacts.json`: `anchors` array with declared source and target actor/bone, tolerance and desired contact intent. `render-config.json` may set PNG resolution and `validation-plan.json` may provide a human QA checklist. Fields outside the validated schema may be recorded as notes but are not automatically enacted.

## Rig target examples (illustrative only)

```json
{
  "schema_version": 1,
  "controls": [
    {"actor": "A", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0.0, 0.0, 0.0]},
    {"actor": "B", "bone": "torso", "space": "POSE_LOCAL_ROTATION_DEG", "value": [10.0, 0.0, 0.0]},
    {"actor": "B", "bone": "hand_ik.L", "space": "POSE_WORLD_HEAD_M", "value": [0.2, -0.7, 0.15]}
  ]
}
```

These numbers are *not* a working SPOSE pose; they illustrate syntax. The current builder supports `OBJECT_WORLD_LOCATION_M`, `OBJECT_WORLD_ROTATION_DEG`, `POSE_LOCAL_ROTATION_DEG`, and `POSE_WORLD_HEAD_M`. Bone local rotations are not world angles; Blender constraints can alter evaluated results. Only mapped Rigify bone names should be used.

## Contact hypotheses are not success proofs

The current script measures sampled minimum unsigned surface distance and bone-head anchor distances. It does **not** compute full signed penetration depth, stable bodyweight, pressure, or validated anatomical closeness. A low distance may mean hands are inside the chest mesh, not resting on its surface. Every contact needs actual image review and, where possible, evaluated local mesh inspection.

Annotate intended hand/foot/pelvis contact zones in human notes. When receiving Blender feedback, compare intended and actual contact zones. Record explicit failures (floating support, misplaced IK target, inverted palm, clipping, wrong camera visibility) and propose targeted corrections rather than shifting entire actors blindly.

## Full-library import and output

```powershell
python scripts/import_pose.py incoming/<POSE_ID>_<UTC>.zip --dry-run
python scripts/import_pose.py incoming/<POSE_ID>_<UTC>.zip --blender "C:\path\to\blender.exe"
```

The importer loads shared pair, applies controls, renders front/side/three-quarter and optional region QA, records proxy metrics and logs; then writes `poses/<POSE_ID>/CPL01/v001/rNNN/`. Optional `--save-blend` creates a scene only when needed. Failed builds remain auditable. Every imported module is a *candidate* until explicit review.

## Feedback ZIP

```powershell
python scripts/export_feedback.py DOGG-DOGG-V00 --revision 1
```

Expected evidence: `pose.json`, `validation.json`, `checksums.json`, `blender-result.json`, `build.log`, and `previews/*.png`. Upload feedback to the next session if you need visual diagnosis. The portable *library context handoff* intentionally excludes renders; these two ZIP types complement each other.

## Revision discipline

- Never overwrite the old candidate package or existing `r001`; issue a new UTC-stamped pose input ZIP and let importer create `r002`.
- Keep source and pair hashes pinned; new source/template requires re-authoring or explicit migration, not a hash patch.
- If the previous pose was accepted, a later failed experiment does not automatically revoke it.
- `validated` and `accepted` are separate states; accepting a pose requires manual review. Character/appearance profile approval remains independent.
- V01–V10 work is deferred until all 276 V00 bases are accepted and the user separately unlocks the new phase.
