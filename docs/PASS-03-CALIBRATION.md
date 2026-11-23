# Batch 0001 Pass 03 — executable calibration and diagnostics

**Status:** candidate implementation; no Blender 5.2 runtime validation was possible in this environment. This document describes exact modifications; measurements are only proven after local execution.

## Evidence and scope

Basis: `spose-remote-feedback-batch-0001-pass-02_20261123T115958Z.zip`, current revisions DOGG r003, CLSD r002, DOWN r002, FCDN r001, FROG r001. Pass-02 merely reused old packages; this Pass-03 release includes five new timestamped packages. Source SRC003/v001, pair CPL01/v001, rig RIG001/v001 are **unchanged**.

## Five variants and intended support topologies

| Pose | Rear A | Front B | Pass-03 adjustments |
|---|---|---|---|
| DOGG-DOGG-V00 | kneeling | palms + knees | Slightly higher tabletop torso, distributed chest/neck/head styling, palm-to-lateral-hip contact |
| DOGG-CLSD-V00 | kneeling | palms + narrow knees | Same principle, preserve narrow-knee corridor |
| DOGG-DOWN-V00 | standing | standing forward fold, palms + feet | Lower/fold torso, bring palms nearer shoulders, increased floor-stage budget, mild raised gaze relative to chest |
| DOGG-FCDN-V00 | kneeling | bent-knee deep fold, **forearms + knees** | Torso/head lower, local-axis side-of-head turn, forearm support calibration; no head-up/lumbar overlay |
| DOGG-FROG-V00 | kneeling | low wide **palms + feet** | Head/chest lifted mildly; B knee floor check removed |

## Changes to the engine

1. `scripts/rigify_floor_engine.py`: `region_points` recognizes evaluated VP001 `forearms`, and approximate `head_side` from `head_neck` material around the DEF head bone. `palm_to_hip_surface` targets lateral mesh points on B pelvis by side and the wrist-near patch of A hand mesh. It works iteratively, caps each hand IK translation at 0.21 m and each step at 0.055 m, and reports residuals. Old wrist/hip bone-head proxies remain unchanged. No physics, pressure, collision-depth proof, or guaranteed finger curl.
2. `scripts/pose_common.py`: accepts new declarative styling controls, FCDN forearm supports and FROG `low_wide_hands_feet` posture classification. Data-only schema; pose ZIPs carry JSON only and preserve dependency/source hash checks.
3. `scripts/blender_build.py`: initial non-relative controls → initial floor calibration → bounded chest/neck/head styling → optional support recheck → pelvic approach → original hand frames → mesh-surface palm targeting → diagnostics → four renders. Geometry warnings do not stop rendering.
4. `scripts/validate_pose.py`: FCDN low-forearm fold knees are checked like knees; FROG low-wide pose does **not** inherit quadruped knee-contact warnings. The legacy field `hard_gate_pass` remains diagnostics metadata and controls nothing.

## Measurement caveats

- **Surface gap goal**: target 0–15 mm palm-to-correct-side-lateral-hip, no excessive penetration. Actual mesh proximity is unsigned. `palm_patch_p25_distance_m` helps detect a single fingertip point falsely reading as contact.
- **Head**: the raised-head/lordosis profile is approximately 5–12° mild trunk and head adjustment, not verified visual orientation. FCDN uses an approximate side-of-head patch; no safe neck weight-bearing is asserted.
- **DOWN**: previous palm floor deviation was 0.418 m even though floor stage exhausted its -0.22m budget. Pass 03 both changes torso and hands, and raises calibration budget. This remains the main geometry risk until Blender validation.
- **FCDN forearms**: material region and rig deformation permit a diagnostic, not proof of proper forearm loading. Stage may fail while a usable draft is saved.
- **FROG**: B knees deliberately not grounded; knee height in outputs is still observable but not an error under `low_wide_hands_feet`.

## Local QA and return

Run **all five** and return one combined compressed feedback ZIP from `upload/`; 20 PNGs remain flat in `review/` and `upload/`. The local agent should report new revision count, per-pose supports, surface gap on both hands, front head/hip heights, FCDN forearm/head-side readings and unresolved issues. Visual ratings /10 are for user review; they are not acceptance gates.

**Do not overwrite** previous revisions, source data, library binaries, or SQLite tracking; do not mark accepted automatically.
