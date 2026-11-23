# Geometry Engine v2 — Rigify mannequin calibration and limits

## Why v2 exists

First Batch 001 erroneously used `POSE_LOCAL_ROTATION_DEG` on `torso`, uninitialized IK and uncalibrated foot/hand positions, producing standing figures for kneeling poses. V2 ports *procedures* from `tooling/scripts/build_pilot_underarm_pose.py`, not a historically approved final pose. Rigify map is `tooling/rig-maps/RIG001-v001.json`, with both actors independent and 406 mapped bones each. The reference Blender environment is 5.2.2 LTS.

## Source geometry is authoritative

`DOGG-DOGG-V00`: A kneeling, B quadruped, B palms and knees floor, A hands hip contact. `DOGG-CLSD-V00`: same support topology, B knees closer. `DOGG-DOWN-V00`: A standing, B forward-fold standing with palms and feet floor. **Do not treat all five as kneeling.** Dataset actor mapping is A=ACTOR_1 (rear) and B=ACTOR_2 (front). Forward anatomical direction is -Y; historical pair code defines L as positive X.

## Engine data grammar

`rig-targets.json` top level: `schema_version:1`, `geometry_contract_version:2`, `engine:"rigify_floor_v2"`, `controls` (nonempty), `floor_calibration`, `support_assertions`, `posture_assertions`. Each control has `actor: A|B`, `bone` unless object root, `space`, `value` 3 finite bounded numbers.

- `OBJECT_WORLD_LOCATION_M`, `OBJECT_WORLD_ROTATION_DEG` — root controls (not reference surface compensation).
- `POSE_WORLD_HEAD_ROT_X_DEG` — set a bone control at world head XYZ **and** world X pitch using `pitch_x_deg`, optional `yaw_z_deg`. Especially mandatory for torso and feet; uses historical `Matrix.Rotation @ bone.bone.matrix_local` convention.
- `POSE_WORLD_HEAD_M` — move hand/foot/pole IK world head with rotation preserved; should not be used as a substitute for torso pitch.
- `POSE_WORLD_HAND_FRAME` — palm IK at world target; `direction_world` and `normal_world` define palm orientation with the historic mirrored rest-normal estimate.
- `POSE_RELATIVE_BONE_HEAD_HAND` — same palm frame but `value` is offset XYZ from target participant's evaluated `target_bone` world head. Applied only after floor stages, usually A hands to B hips.
- `POSE_LOCAL_REST_AXIS_ROT_X_DEG` — neck/head local rotation around converted world X rest axis; requires `angle_deg`.
- `POSE_LOCAL_ROTATION_DEG` — retained only for bounded local details, never torso posture strategy.

Rig init per actor and side: `upper_arm_parent.L/R[IK_FK]=0`, `thigh_parent.L/R[IK_FK]=0`, both `IK_Stretch=0`, `pole_vector=True`; all IK constraints `use_stretch=False`. `point()` works in armature pose space via the inverse rig world matrix. The engine calls depsgraph updates after every target. **The library's shared pair must not be resized or overwritten.**

## Physical support calibration

The floor is Z=0 (actual visible plane may be at Z=-0.003). The engine samples **evaluated, skinned BODY mesh** and material `region` properties. `hands` and `feet` use each regional material; `knees` use thigh/calf material vertices within 0.135 m of `DEF-shin.L/R` head (an approximation). This prevents a distant grounded heel from being mistaken for a grounded knee.

Calibration is ordered: (1) **each left/right knee patch** by shifting `torso` control Z (then check both sides again), (2) front palms by shifting hand IK Z, (3) foot/sole regions by shifting foot IK Z. Each adjustment is bounded by `max_total_shift_m` (max .40, usually .22-.24), iterates to correct region min Z toward 0.004 m, and records before/after. Root-floor offsets are not used to disguise unresolved knee or foot placements.

An automatically measured support needs an explicit assertion. For a kneeling actor, joint `DEF-shin` head Z must be low and knee angle must show bending (rather than standing); side and front renders are also essential. For standing forward fold, the head should be materially lower than hips and both hands/feet should have measured floor contact. Aggregate mesh points below -0.022 m produce a floor penetration issue.

## Limitations and honest output language

The engine **is not a constrained IK optimization solver**, not guaranteed to avoid rig singularities, and cannot certify self-collision, exact joint range, comfort, force balance, pelvis interface or anatomically precise contact. Hip-head proximity is a rough proxy, not a surface-normal contact proof. A pose may pass simple hard gates and still look bad; human review is mandatory. Some v2 guessed coordinates may fail outright on this rig, in which case the `blocked` output and Blender logs are the intended feedback mechanism.

## What to inspect in a failed feedback ZIP

1. `blender-result.json` -> `checks.floor_calibration`, `checks.posture_heights`, `checks.geometry`, `issues`.
2. `validation.json` -> hard gate pass, issues, actual executed Blender version.
3. `build.log` if no preview.
4. Side image for knee/hip height, rear/front spacing, floating palms, foot mesh below plane.
5. Front image for knee corridor and asymmetric pole failures.
6. `inputs/rig-targets.json` for explicit vectors and order.

Adjust one mechanistic source of error at a time; create a new UTC pose ZIP. Avoid global translations that solve feet while losing pelvic contact. If the same failure repeats in multiple poses, repair `rigify_floor_engine.py` and ship an updater before producing more pose guesses.
