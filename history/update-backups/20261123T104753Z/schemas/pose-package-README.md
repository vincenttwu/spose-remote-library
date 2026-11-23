# SPOSE Pose ZIP Contract — geometry v2 required

Files at ZIP root: `manifest.json`, `pose.json`, `rig-targets.json`, `contacts.json`, optional `render-config.json`, `validation-plan.json`. Package outer filename `{POSE_ID}_{YYYYMMDDTHHMMSSZ}.zip`. Source and pair/template dependency hashes must match current full library. No scripts or `.blend` inside the pose ZIP.

`rig-targets.json` mandatory `schema_version:1`, `engine:"rigify_floor_v2"`, `geometry_contract_version:2`, `controls` list, `floor_calibration`, `support_assertions`, `posture_assertions` for A and B. Allowed spaces: `OBJECT_WORLD_LOCATION_M`, `OBJECT_WORLD_ROTATION_DEG`, `POSE_WORLD_HEAD_M`, `POSE_WORLD_HEAD_ROT_X_DEG` (`pitch_x_deg`), `POSE_WORLD_HAND_FRAME` (`direction_world`,`normal_world`), `POSE_RELATIVE_BONE_HEAD_HAND` (`target_actor`,`target_bone`, orientation), `POSE_LOCAL_REST_AXIS_ROT_X_DEG` (`angle_deg`), bounded `POSE_LOCAL_ROTATION_DEG`. See `docs/GEOMETRY-ENGINE-V2.md` and five current starter candidate ZIPs for examples.

Offline dry-run verifies declarative grammar; the actual Blender geometry and support checks run locally. Legacy V1 batch input intentionally fails. Human review must not accept blocked geometry.
