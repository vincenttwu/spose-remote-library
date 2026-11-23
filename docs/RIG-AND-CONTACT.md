# Rig, scene coordinates and contact quality

## Identity and coordinate system

- Pair: `CPL01/v001`; two independent Rigify mannequins.
- Actor A = source `[ACTOR_1]` at 1.85 m; actor B = source `[ACTOR_2]` at 1.77 m.
- Blender world units: meters; +Z upward, -Y forward, left/right from each character's perspective.
- Objects are named `CPL01_A_ROOT`, `CPL01_A_RIG`, `CPL01_A_BODY` and corresponding B objects.
- Use `tooling/rig-maps/RIG001-v001.json` to confirm bone names, mode semantics and original test limitations. A map file is a **contract**, not a substitute for inspecting the evaluated rig on the user's machine.
- BP001/CPL01/VP001 are preserved draft assets; do not deform or rescale meshes to make bad IK targets look acceptable.

## Main mapped controls

| Function | Mapped control examples | Common risk |
|---|---|---|
| Pair root translation/rotation | `CPL01_A_ROOT`, `CPL01_B_ROOT` | Body alignment changes more than desired contact location |
| Pelvis, torso, chest | `hips`, `torso`, `chest` | Local rotation interpreted as world axis; accumulated spine offsets |
| Head/neck | `head`, `neck` | Unrealistic cervical bend when targeting contact |
| Hands | `hand_ik.L`, `hand_ik.R` | Palm orientation wrong despite wrist control reaching target |
| Elbow guides | `upper_arm_ik_target.L/R` | Elbow flips or pole crossing |
| Feet | `foot_ik.L`, `foot_ik.R` | Ground penetration/floating foot |
| Knee guides | `thigh_ik_target.L/R` | Knee articulation instability |
| IK/FK mode | Parent custom properties from rig map | Property may be left in a mode inconsistent with target controls |

The current JSON importer can set four supported control spaces. It does **not** expose all rig custom slider operations or an automatic inverse-kinematics solve from prose. Extend the implementation deliberately after local Blender tests; document newly enabled controls and update package schemas before using them broadly.

## Contact hierarchy

1. **Environmental support:** feet/knees/forearms on floor or surfaces; evaluate actual support contact after rig deformation.
2. **Global relative pose:** root transforms and pelvic/torso orientation of actors A and B; set relative alignment before fine hand IK.
3. **Local hand/body contact:** target contact region, palm/hand orientation, elbow path and bone constraints; use evaluated mesh surfaces rather than just bone-head distance.
4. **Proximity quality:** avoid floating-gap artifacts and severe interpenetrations; check contact across front/side/three-quarter views.
5. **Visual readability:** body-part occlusion, camera framing, and color-region QA support diagnosis but are not substitutes for contact checks.

A body-to-body nearest-vertex distance approaching zero **does not prove** intended contact. It can mean a hand passes through a torso. The current contact validator computes unsigned sampled nearest-surface statistics and bone-head-to-bone-head proxies. It cannot supply signed collision depth, stable balance, or a contact mechanics simulation.

## Local diagnostics to request after first Blender attempt

- Blender version, loaded template path and exact rig bone names/IK mode.
- Root A/B matrices, pelvis world coordinates and forward vectors.
- For every contact: target body part, intended side, actual wrist/palm position and measured surface separation, elbow pole directions, bone/mesh interpenetrations.
- Screenshots of front/side/three-quarter and region QA.
- Front/rear independent floor support heights and floor penetration.
- Build log and `validation.json`; note which observations are provisional or untested.

## Script boundaries

- `scripts/blender_build.py`: applies explicit controls only.
- `scripts/render_previews.py`: renders static named cameras, optional region mode.
- `scripts/validate_pose.py`: produces proximity proxies, not a collision solver.
- `scripts/import_pose.py`: checks integrity, orchestrates Blender, versions outputs and tracking.

Do not infer that a saved `scene.blend` or a technical status of `draft` means the contact fits. The first pilot is specifically intended to calibrate this gap before large-scale V00 generation.

## Pass-03 additional evaluated-mesh contact diagnostics
Contact now uses VP001 `pelvis` and `hands` material patches plus side filtering; `palm_to_hip_surface` moves the A `hand_ik.L/R` controls with bounded translation and reports unsigned residuals. Side-specific lateral hip filtering avoids thigh/whole-mesh snapping. `forearms` support uses VP001 `forearms` material narrowed near `DEF-forearm.L/R` bone segments. `head_side` uses `head_neck` material close to the head bone and **does not identify an exact cheek**. No material diagnostic proves non-interpenetration or physical contact force. See `docs/PASS-03-CALIBRATION.md`.


## Pass-04 measurement correction

Pass-03 nearly-zero closest palm vertex did NOT predict visually convincing contact. Pass-04 uses adaptive DEF-hand-centered palm patches, pelvis lateral surface bands, p10–p90 nearest-surface distance distributions and within-15mm/30mm coverage. The engine samples head pitch directions and reports RIG001-rest-based world elevation; both remain approximate and require visual inspection. See `docs/CALIBRATION-REFERENCE.md` and the persistent local rig probe results.
