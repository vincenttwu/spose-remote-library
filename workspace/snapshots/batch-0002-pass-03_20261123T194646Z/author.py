"""Author all 4 batch-0002 (UADG) Pass 03 data-only packages into workspace/incoming/ + workspace/batches/BATCH-0002-PASS-03.json.

Applies the proven USDG Pass 04 (8.70/10) pelvis-cupping & standing-knee calibration to UADG:
- Front pelvis (B) lowered slightly below rear pelvis (A) via relaxed deeper standing knee bend
  (b_z=0.935m, B grounded knees ~132 deg; a_z=1.02m, A grounded knees ~146-147 deg; A_pel_z > B_pel_z by ~7.5cm).
- Rear pelvis (A) brought forward (a_y=0.25m) and more upright (a_pitch=38-39 deg vs Pass 02's 50-52 deg)
  so A's front pelvis directly cups B's lower-set hips with zero chest-into-buttocks clipping and zero air gap.
- Rear arms (A) naturally extended (~150-156 deg) with tucked elbows (x=0.28m vs Pass 02's 0.54-0.56m wings)
  and zero fingertip bleed-through (deltoid offset 0.132, 0.08, 0.068).
- Deeper B hip hinge (84-86 deg, chest=-16 deg) with gentle lumbar arch, neck_assist_enabled=true, and
  clean downward edge-bracing forearms (z=0.72-0.75m).
- Preserves and polishes all 4 asymmetric leg geometries:
  * FELV: B.L foot flat & less abducted on ~0.62m table plane (clears A.L forearm & keeps sole level).
  * FASS: A.L palm cleanly cradles underneath B.L popliteal crease/upper calf (no lateral shin clip).
  * RELV: B bilateral relaxed grounded stance, A.L elevated flat at knee height (~0.52m) with clean thigh clearance.
  * DUAL: B.L & A.L elevated feet locked dead-level on the exact same horizontal sofa plane (z=0.48 / 0.484m).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

WS_ROOT = Path(__file__).resolve().parents[1]
WS_SCRIPTS = WS_ROOT / "scripts"
if str(WS_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(WS_SCRIPTS))

from ws_common import (
    BATCHES_DIR,
    INCOMING_DIR,
    build_pose_package_zip,
    read_v00_catalog,
    utc_now_stamp,
    workspace_rel,
    write_json_workspace,
)

POSE_ORDER = [
    "UADG-FELV-V00",
    "UADG-FASS-V00",
    "UADG-RELV-V00",
    "UADG-DUAL-V00",
]

EDGE_DIR = [0.0, -0.98, -0.20]
EDGE_NORM_L = [-0.24, 0.20, -0.95]
EDGE_NORM_R = [0.24, 0.20, -0.95]


def front_edge_hands(x: float = 0.20, y: float = -0.70, z: float = 0.72) -> list[dict]:
    return [
        {
            "actor": "B",
            "bone": "hand_ik.L",
            "space": "POSE_WORLD_HAND_FRAME",
            "value": [x, y, z],
            "direction_world": EDGE_DIR,
            "normal_world": EDGE_NORM_L,
        },
        {
            "actor": "B",
            "bone": "hand_ik.R",
            "space": "POSE_WORLD_HAND_FRAME",
            "value": [-x, y, z],
            "direction_world": EDGE_DIR,
            "normal_world": EDGE_NORM_R,
        },
    ]


def rear_shoulder_hand(side: str, offset: tuple[float, float, float] = (0.132, 0.08, 0.068)) -> dict:
    sign = 1 if side == "L" else -1
    ox, oy, oz = offset
    return {
        "actor": "A",
        "bone": f"hand_ik.{side}",
        "space": "POSE_RELATIVE_BONE_HEAD_HAND",
        "value": [ox * sign, oy, oz],
        "target_actor": "B",
        "target_bone": f"DEF-upper_arm.{side}",
        "direction_world": [-0.34 * sign, -0.86, -0.38],
        "normal_world": [-0.82 * sign, 0.20, -0.54],
    }


def make_contacts(
    note: str,
    left_target_bone: str = "DEF-upper_arm.L",
    left_id: str = "left_rear_palm_to_front_outer_shoulder",
) -> dict:
    return {
        "schema_version": 1,
        "anchors": [
            {"id": "pelvis_proximity", "actor": "A", "bone": "hips", "target_actor": "B", "target_bone": "hips", "tolerance_m": 0.45},
            {"id": left_id, "actor": "A", "bone": "hand_ik.L", "target_actor": "B", "target_bone": left_target_bone, "tolerance_m": 0.24},
            {"id": "right_rear_palm_to_front_outer_shoulder", "actor": "A", "bone": "hand_ik.R", "target_actor": "B", "target_bone": "DEF-upper_arm.R", "tolerance_m": 0.24},
        ],
        "note": note,
    }


def make_pose_specs() -> dict[str, dict]:
    specs: dict[str, dict] = {}

    # 1. UADG-FELV-V00 — Lower-set B pelvis cupped by upright-leaning A, B.L flat on ~0.62m table plane, extended tucked A arms
    specs["UADG-FELV-V00"] = {
        "expected_support": {
            "A": "both feet flat on floor (relaxed knees ~147 deg); upright-leaning pelvis directly cupping above B's lower-set hips; extended tucked arms on B outer deltoids",
            "B": "right foot flat on floor (relaxed bent knee ~132 deg lowering front pelvis below rear); left foot flat on ~0.62m table plane; hands braced flat on ~0.72m edge",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "UADG-FELV-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-03",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "A", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "B", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.0, 0.935], "pitch_x_deg": 86},
                {"actor": "B", "bone": "foot_ik.R", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [-0.14, 0.02, 0.091], "pitch_x_deg": 0, "yaw_z_deg": -6},
                {"actor": "B", "bone": "thigh_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.16, -0.60, 0.50]},
                # B.L foot flat on ~0.62m table plane with modest abduction so sole reads dead-flat in front view
                {"actor": "B", "bone": "foot_ik.L", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.36, -0.44, 0.62], "pitch_x_deg": 0, "yaw_z_deg": 18},
                {"actor": "B", "bone": "thigh_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.58, -0.58, 0.84]},
                *front_edge_hands(x=0.20, y=-0.70, z=0.72),
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.25, -0.46, 0.86]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.25, -0.46, 0.86]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -30},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -28},
                # A pelvis directly cupping slightly above B's lower-set hips, upright lean (38 deg), extended tucked arms
                {"actor": "A", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.25, 1.02], "pitch_x_deg": 38},
                {"actor": "A", "bone": "foot_ik.L", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.22, 0.29, 0.095], "pitch_x_deg": 0, "yaw_z_deg": 10},
                {"actor": "A", "bone": "foot_ik.R", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [-0.22, 0.29, 0.095], "pitch_x_deg": 0, "yaw_z_deg": -10},
                {"actor": "A", "bone": "thigh_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.25, -0.22, 0.55]},
                {"actor": "A", "bone": "thigh_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.25, -0.22, 0.55]},
                {"actor": "A", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.30, -0.10, 1.04]},
                {"actor": "A", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.28, -0.10, 1.02]},
                {"actor": "A", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -24},
                {"actor": "A", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -24},
                rear_shoulder_hand("L"),
                rear_shoulder_hand("R"),
            ],
            "styling_controls": [
                {"actor": "B", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -16},
                {"actor": "A", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -8},
            ],
            "head_aim": {"actor": "B", "target_elevation_deg": 4, "max_delta_deg": 50, "neck_assist_enabled": True, "reference": "RIG001_forward_-Y_world_rest_to_pose_delta", "objective": "face_forward_naturally"},
            "floor_calibration": [
                {"actor": "B", "region": "feet", "side": "R", "adjust_bone": "foot_ik.R", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "A", "region": "feet", "side": "L", "adjust_bone": "foot_ik.L", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "A", "region": "feet", "side": "R", "adjust_bone": "foot_ik.R", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
            ],
            "pelvic_alignment": {"actor": "A", "target_actor": "B", "region": "pelvis", "target_distance_m": 0.075, "max_forward_shift_m": 0.015, "iterations": 3},
            "support_assertions": [
                {"actor": "B", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "A", "region": "feet", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "A", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
            ],
            "posture_assertions": [
                {"actor": "A", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.85, "max_hip_z_m": 1.28},
                {"actor": "B", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.78, "max_hip_z_m": 1.24},
            ],
        },
        "contacts": make_contacts("UADG-FELV-V00 Pass 03: lower-set B pelvis cupped by upright A, extended tucked A arms, zero fingertip clip, level elevated B.L foot."),
    }

    # 2. UADG-FASS-V00 — Lower-set B pelvis cupped by A, A.L cleanly cradles under B.L popliteal crease/upper calf, A.R extended on B.R deltoid
    specs["UADG-FASS-V00"] = {
        "expected_support": {
            "A": "both feet flat on floor (relaxed knees ~147 deg); pelvis cupping above B's lower-set hips; LEFT palm cradles smoothly under B's lifted knee/calf; RIGHT extended tucked arm on B.R outer deltoid",
            "B": "right foot flat on floor (relaxed bent knee ~132 deg); left leg raised forward/outward & cradled by A.L palm; hands braced flat on ~0.72m edge",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "UADG-FASS-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-03",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "A", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "B", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.0, 0.935], "pitch_x_deg": 84},
                {"actor": "B", "bone": "foot_ik.R", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [-0.14, 0.02, 0.091], "pitch_x_deg": 0, "yaw_z_deg": -6},
                {"actor": "B", "bone": "thigh_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.16, -0.60, 0.50]},
                {"actor": "B", "bone": "foot_ik.L", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.35, -0.18, 0.66], "pitch_x_deg": 10, "yaw_z_deg": 20},
                {"actor": "B", "bone": "thigh_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.52, -0.46, 0.96]},
                *front_edge_hands(x=0.20, y=-0.70, z=0.72),
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.25, -0.46, 0.86]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.25, -0.46, 0.86]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -30},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -28},
                {"actor": "A", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.25, 1.02], "pitch_x_deg": 39},
                {"actor": "A", "bone": "foot_ik.L", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.22, 0.30, 0.095], "pitch_x_deg": 0, "yaw_z_deg": 12},
                {"actor": "A", "bone": "foot_ik.R", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [-0.22, 0.29, 0.095], "pitch_x_deg": 0, "yaw_z_deg": -10},
                {"actor": "A", "bone": "thigh_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.25, -0.20, 0.55]},
                {"actor": "A", "bone": "thigh_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.25, -0.22, 0.55]},
                {"actor": "A", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.40, 0.02, 0.86]},
                {"actor": "A", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.28, -0.10, 1.02]},
                {"actor": "A", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -24},
                {"actor": "A", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -24},
                # A.L hand shifted slightly posterior/downward under popliteal crease / upper calf (no lateral shin clip!)
                {
                    "actor": "A",
                    "bone": "hand_ik.L",
                    "space": "POSE_RELATIVE_BONE_HEAD_HAND",
                    "value": [0.03, 0.085, -0.08],
                    "target_actor": "B",
                    "target_bone": "DEF-shin.L",
                    "direction_world": [-0.30, -0.92, 0.25],
                    "normal_world": [-0.15, 0.30, 0.94],
                },
                rear_shoulder_hand("R"),
            ],
            "styling_controls": [
                {"actor": "B", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -16},
                {"actor": "A", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -8},
            ],
            "head_aim": {"actor": "B", "target_elevation_deg": 4, "max_delta_deg": 50, "neck_assist_enabled": True, "reference": "RIG001_forward_-Y_world_rest_to_pose_delta", "objective": "face_forward_naturally"},
            "floor_calibration": [
                {"actor": "B", "region": "feet", "side": "R", "adjust_bone": "foot_ik.R", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "A", "region": "feet", "side": "L", "adjust_bone": "foot_ik.L", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "A", "region": "feet", "side": "R", "adjust_bone": "foot_ik.R", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
            ],
            "pelvic_alignment": {"actor": "A", "target_actor": "B", "region": "pelvis", "target_distance_m": 0.075, "max_forward_shift_m": 0.015, "iterations": 3},
            "support_assertions": [
                {"actor": "B", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "A", "region": "feet", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "A", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
            ],
            "posture_assertions": [
                {"actor": "A", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.85, "max_hip_z_m": 1.28},
                {"actor": "B", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.78, "max_hip_z_m": 1.24},
            ],
        },
        "contacts": make_contacts(
            "UADG-FASS-V00 Pass 03: lower-set B pelvis cupped by A, clean popliteal palm cradle under B.L knee, zero right-hand fingertip clip.",
            left_target_bone="DEF-shin.L",
            left_id="left_rear_hand_supporting_front_raised_leg",
        ),
    }

    # 3. UADG-RELV-V00 — B bilateral lower-set pelvis (~132 deg knees), A.L flat elevated (~0.52m), A pelvis cupping above B hips
    specs["UADG-RELV-V00"] = {
        "expected_support": {
            "A": "right foot flat on floor (relaxed knee ~146 deg); left foot flat on knee-height (~0.52m) support; pelvis cupping above B's lower-set hips; extended tucked arms on B outer deltoids",
            "B": "both feet flat on floor (relaxed bent knees ~132 deg lowering front pelvis below rear); ~86 deg hinge w/ lumbar arch; hands braced flat on ~0.72m edge",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "UADG-RELV-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-03",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "A", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "B", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.0, 0.935], "pitch_x_deg": 86},
                {"actor": "B", "bone": "foot_ik.L", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.15, 0.02, 0.091], "pitch_x_deg": 0, "yaw_z_deg": 6},
                {"actor": "B", "bone": "foot_ik.R", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [-0.15, 0.02, 0.091], "pitch_x_deg": 0, "yaw_z_deg": -6},
                {"actor": "B", "bone": "thigh_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.18, -0.60, 0.50]},
                {"actor": "B", "bone": "thigh_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.18, -0.60, 0.50]},
                *front_edge_hands(x=0.20, y=-0.70, z=0.72),
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.25, -0.46, 0.86]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.25, -0.46, 0.86]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -30},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -28},
                {"actor": "A", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.25, 1.02], "pitch_x_deg": 38},
                {"actor": "A", "bone": "foot_ik.R", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [-0.20, 0.30, 0.095], "pitch_x_deg": 0, "yaw_z_deg": -10},
                {"actor": "A", "bone": "thigh_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.24, -0.20, 0.55]},
                {"actor": "A", "bone": "foot_ik.L", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.38, 0.14, 0.52], "pitch_x_deg": 0, "yaw_z_deg": 18},
                {"actor": "A", "bone": "thigh_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.72, -0.18, 0.90]},
                {"actor": "A", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.28, -0.10, 1.02]},
                {"actor": "A", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.28, -0.10, 1.02]},
                {"actor": "A", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -24},
                {"actor": "A", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -24},
                rear_shoulder_hand("L"),
                rear_shoulder_hand("R"),
            ],
            "styling_controls": [
                {"actor": "B", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -16},
                {"actor": "A", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -8},
            ],
            "head_aim": {"actor": "B", "target_elevation_deg": 4, "max_delta_deg": 50, "neck_assist_enabled": True, "reference": "RIG001_forward_-Y_world_rest_to_pose_delta", "objective": "face_forward_naturally"},
            "floor_calibration": [
                {"actor": "B", "region": "feet", "side": "L", "adjust_bone": "foot_ik.L", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "B", "region": "feet", "side": "R", "adjust_bone": "foot_ik.R", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "A", "region": "feet", "side": "R", "adjust_bone": "foot_ik.R", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
            ],
            "pelvic_alignment": {"actor": "A", "target_actor": "B", "region": "pelvis", "target_distance_m": 0.075, "max_forward_shift_m": 0.015, "iterations": 3},
            "support_assertions": [
                {"actor": "B", "region": "feet", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "B", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "A", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
            ],
            "posture_assertions": [
                {"actor": "A", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.85, "max_hip_z_m": 1.28},
                {"actor": "B", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.78, "max_hip_z_m": 1.24},
            ],
        },
        "contacts": make_contacts("UADG-RELV-V00 Pass 03: lower-set B pelvis cupped by upright A, relaxed grounded knees, extended tucked A arms, zero fingertip clip."),
    }

    # 4. UADG-DUAL-V00 — Exact matched sofa-height plane (B.L z=0.48, A.L z=0.484), lower-set B pelvis cupped by upright A, clean elbow/knee clearance
    specs["UADG-DUAL-V00"] = {
        "expected_support": {
            "A": "right foot flat on floor (relaxed knee ~146 deg); left foot flat on shared sofa plane aligned with B.L; pelvis cupping above B's lower-set hips; extended tucked arms on B outer deltoids",
            "B": "right foot flat on floor (relaxed bent knee ~132 deg); left foot flat on shared sofa plane; hands braced flat on ~0.75m edge clear of knee",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "UADG-DUAL-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-03",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "A", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "B", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.0, 0.935], "pitch_x_deg": 86},
                {"actor": "B", "bone": "foot_ik.R", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [-0.15, 0.02, 0.091], "pitch_x_deg": 0, "yaw_z_deg": -6},
                {"actor": "B", "bone": "thigh_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.18, -0.60, 0.50]},
                # B.L & A.L flat on EXACT SAME horizontal sofa plane (sole z ~ 0.39m)
                {"actor": "B", "bone": "foot_ik.L", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.36, -0.28, 0.48], "pitch_x_deg": 0, "yaw_z_deg": 14},
                {"actor": "B", "bone": "thigh_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.56, -0.58, 0.80]},
                *front_edge_hands(x=0.20, y=-0.70, z=0.75),
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.25, -0.46, 0.92]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.25, -0.46, 0.92]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -30},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -28},
                {"actor": "A", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.25, 1.02], "pitch_x_deg": 38},
                {"actor": "A", "bone": "foot_ik.R", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [-0.20, 0.30, 0.095], "pitch_x_deg": 0, "yaw_z_deg": -10},
                {"actor": "A", "bone": "thigh_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.24, -0.20, 0.55]},
                {"actor": "A", "bone": "foot_ik.L", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.40, 0.18, 0.484], "pitch_x_deg": 0, "yaw_z_deg": 14},
                {"actor": "A", "bone": "thigh_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.74, -0.10, 0.88]},
                {"actor": "A", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.28, -0.10, 1.02]},
                {"actor": "A", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.28, -0.10, 1.02]},
                {"actor": "A", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -24},
                {"actor": "A", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -24},
                rear_shoulder_hand("L"),
                rear_shoulder_hand("R"),
            ],
            "styling_controls": [
                {"actor": "B", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -16},
                {"actor": "A", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -8},
            ],
            "head_aim": {"actor": "B", "target_elevation_deg": 4, "max_delta_deg": 50, "neck_assist_enabled": True, "reference": "RIG001_forward_-Y_world_rest_to_pose_delta", "objective": "face_forward_naturally"},
            "floor_calibration": [
                {"actor": "B", "region": "feet", "side": "R", "adjust_bone": "foot_ik.R", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "A", "region": "feet", "side": "R", "adjust_bone": "foot_ik.R", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
            ],
            "pelvic_alignment": {"actor": "A", "target_actor": "B", "region": "pelvis", "target_distance_m": 0.075, "max_forward_shift_m": 0.015, "iterations": 3},
            "support_assertions": [
                {"actor": "B", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "A", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
            ],
            "posture_assertions": [
                {"actor": "A", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.85, "max_hip_z_m": 1.28},
                {"actor": "B", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.78, "max_hip_z_m": 1.24},
            ],
        },
        "contacts": make_contacts("UADG-DUAL-V00 Pass 03: lower-set B pelvis cupped by upright A, matched shared sofa foot plane, extended tucked A arms."),
    }

    return specs


def main() -> None:
    auth, rows = read_v00_catalog()
    by_id = {r["pose_id"]: r for r in rows}
    specs = make_pose_specs()
    ts = utc_now_stamp()

    plan_poses = []
    created = []
    for pose_id in POSE_ORDER:
        row = by_id[pose_id]
        sp = specs[pose_id]
        pose_json = {
            "schema_version": 1,
            "pose_id": pose_id,
            "status": "proposal",
            "batch_id": "WORKSPACE-BATCH-0002-PASS-03",
            "source_checkpoint": auth["source_checkpoint"],
            "source_id": auth["source_id"],
            "actor_mapping": {"ACTOR_1": "A", "ACTOR_2": "B"},
            "pose_name": row["pose_name"],
            "source_gate": row["generation_gate"],
            "source_complexity_pose": row.get("complexity_pose", ""),
            "specification": row["specification"],
            "approach": "Workspace batch-0002 (UADG) Pass 03 calibrated with USDG Pass 04 pelvis-cupping, lower front pelvis, relaxed knees, extended tucked A arms, and FASS cradle polish.",
            "expected_support": sp["expected_support"],
            "pass_label": "pass-03",
            "workspace_experimental": True,
        }
        zpath = build_pose_package_zip(
            dest_dir=INCOMING_DIR,
            pose_id=pose_id,
            pose_json=pose_json,
            rig_targets=sp["rig_targets"],
            contacts=sp["contacts"],
            timestamp_utc=ts,
        )
        plan_poses.append({"pose_id": pose_id, "package": zpath.name})
        created.append(workspace_rel(zpath))

    plan = {
        "schema_version": 2,
        "kind": "spose_workspace_batch_plan",
        "batch_label": "batch-0002",
        "pass_label": "pass-03",
        "family": "UADG",
        "note": "Calibrated UADG Pass 03: lower-set front pelvis cupped by upright rear partner, relaxed standing knees, extended tucked A arms, zero fingertip clip, and FASS cradle polish.",
        "local_calibration": {"enabled": True, "max_refinement_attempts": 2},
        "poses": plan_poses,
    }
    plan_path = write_json_workspace(BATCHES_DIR / "BATCH-0002-PASS-03.json", plan)
    print(json.dumps({"ok": True, "plan": workspace_rel(plan_path), "packages": created}, indent=2))


if __name__ == "__main__":
    main()
