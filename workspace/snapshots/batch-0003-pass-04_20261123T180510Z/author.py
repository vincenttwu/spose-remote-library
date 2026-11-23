"""Author all 5 batch-0003 (USDG) Pass 04 data-only packages into workspace/incoming/ + workspace/batches/BATCH-0003-PASS-04.json.

Applies user's precise Pass 03 polish request across all 5 poses while preserving Pass 03's clean geometry:
- Front pelvis (B) lowered ~3.5cm via slightly deeper relaxed knee bend (b_z: 0.97 -> 0.935m,
  B knees ~133-137 deg) while rear pelvis (A) rises ~1cm (a_z: 1.01 -> 1.02m, A knees ~146-148 deg),
  so front pelvis sits cleanly ~6-7cm LOWER than rear pelvis while A's front pelvis directly cups B's hips.
- Preserves Pass 03's extended tucked A arms (0mm reach error), clean deltoid palm placement,
  ~90 deg WALL reach, coplanar SURF tabletop, and clean PULL flank contact.
- Also clears USDG-LOW-V00's remaining P1 A-lower-chest-to-B-buttocks clip and FORWARD_FOLD_NOT_ESTABLISHED
  diagnostic, and raises B's elbows slightly on USDG-EDGE-V00 for level/downward edge loading.
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
    "USDG-EDGE-V00",
    "USDG-SURF-V00",
    "USDG-WALL-V00",
    "USDG-LOW-V00",
    "USDG-PULL-V00",
]

HORIZ_DIR = [0.0, -0.98, -0.20]
HORIZ_NORM_L = [-0.24, 0.20, -0.95]
HORIZ_NORM_R = [0.24, 0.20, -0.95]


def standing_feet(
    actor: str,
    x: float,
    y: float,
    z: float,
    yaw: float,
    knee_x: float,
    knee_y: float,
    knee_z: float,
) -> list[dict]:
    return [
        {"actor": actor, "bone": "foot_ik.L", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [x, y, z], "pitch_x_deg": 0, "yaw_z_deg": yaw},
        {"actor": actor, "bone": "foot_ik.R", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [-x, y, z], "pitch_x_deg": 0, "yaw_z_deg": -yaw},
        {"actor": actor, "bone": "thigh_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [knee_x, knee_y, knee_z]},
        {"actor": actor, "bone": "thigh_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-knee_x, knee_y, knee_z]},
    ]


def rear_shoulder_hands(offset: tuple[float, float, float] = (0.132, 0.08, 0.068)) -> list[dict]:
    ox, oy, oz = offset
    out = []
    for side, sign in (("L", 1), ("R", -1)):
        out.append(
            {
                "actor": "A",
                "bone": f"hand_ik.{side}",
                "space": "POSE_RELATIVE_BONE_HEAD_HAND",
                "value": [ox * sign, oy, oz],
                "target_actor": "B",
                "target_bone": f"DEF-upper_arm.{side}",
                "direction_world": [-0.34 * sign, -0.86, -0.38],
                "normal_world": [-0.82 * sign, 0.20, -0.54],
            }
        )
    return out


def standard_floor_calibration() -> list[dict]:
    return [
        {"actor": "B", "region": "feet", "side": "L", "adjust_bone": "foot_ik.L", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
        {"actor": "B", "region": "feet", "side": "R", "adjust_bone": "foot_ik.R", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
        {"actor": "A", "region": "feet", "side": "L", "adjust_bone": "foot_ik.L", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
        {"actor": "A", "region": "feet", "side": "R", "adjust_bone": "foot_ik.R", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
    ]


def standard_support_assertions() -> list[dict]:
    return [
        {"actor": "B", "region": "feet", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.028},
        {"actor": "B", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
        {"actor": "A", "region": "feet", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.028},
        {"actor": "A", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
    ]


def make_contacts(note: str, extra_anchors: list[dict] | None = None) -> dict:
    anchors = [
        {"id": "pelvis_proximity", "actor": "A", "bone": "hips", "target_actor": "B", "target_bone": "hips", "tolerance_m": 0.45},
        {"id": "left_rear_palm_to_front_outer_shoulder", "actor": "A", "bone": "hand_ik.L", "target_actor": "B", "target_bone": "DEF-upper_arm.L", "tolerance_m": 0.24},
        {"id": "right_rear_palm_to_front_outer_shoulder", "actor": "A", "bone": "hand_ik.R", "target_actor": "B", "target_bone": "DEF-upper_arm.R", "tolerance_m": 0.24},
    ]
    if extra_anchors:
        anchors.extend(extra_anchors)
    return {"schema_version": 1, "anchors": anchors, "note": note}


def make_pose_specs() -> dict[str, dict]:
    specs: dict[str, dict] = {}

    # 1. USDG-EDGE-V00 — B pelvis slightly lower via ~134 deg bent knees, A cupping higher (~147 deg knees), level/downward edge forearms
    specs["USDG-EDGE-V00"] = {
        "expected_support": {
            "A": "both feet flat on floor (relaxed knees ~147 deg); pelvis cupping slightly above B's lower-set hips; extended tucked arms on B outer deltoids",
            "B": "both feet flat on floor (slightly deeper knee bend ~134 deg lowering front pelvis below rear); ~95 deg hinge w/ lumbar arch; palms bracing ~0.71m edge",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "USDG-EDGE-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-04",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "A", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "B", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.0, 0.935], "pitch_x_deg": 95},
                *standing_feet("B", x=0.16, y=0.02, z=0.091, yaw=6, knee_x=0.18, knee_y=-0.60, knee_z=0.50),
                {"actor": "B", "bone": "hand_ik.L", "space": "POSE_WORLD_HAND_FRAME", "value": [0.20, -0.70, 0.71], "direction_world": HORIZ_DIR, "normal_world": HORIZ_NORM_L},
                {"actor": "B", "bone": "hand_ik.R", "space": "POSE_WORLD_HAND_FRAME", "value": [-0.20, -0.70, 0.71], "direction_world": HORIZ_DIR, "normal_world": HORIZ_NORM_R},
                # Raised B elbow pole slightly so forearms angle level/downward onto the edge (fixes Pass 03 P2 upward slope)
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.24, -0.46, 0.85]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.24, -0.46, 0.85]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -30},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -28},
                {"actor": "A", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.245, 1.02], "pitch_x_deg": 44},
                *standing_feet("A", x=0.22, y=0.29, z=0.095, yaw=10, knee_x=0.25, knee_y=-0.22, knee_z=0.55),
                {"actor": "A", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.28, -0.10, 0.99]},
                {"actor": "A", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.28, -0.10, 0.99]},
                {"actor": "A", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -26},
                {"actor": "A", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -26},
                *rear_shoulder_hands(offset=(0.132, 0.08, 0.068)),
            ],
            "styling_controls": [
                {"actor": "B", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -17},
                {"actor": "A", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -8},
            ],
            "head_aim": {"actor": "B", "target_elevation_deg": 0, "max_delta_deg": 45, "neck_assist_enabled": True, "reference": "RIG001_forward_-Y_world_rest_to_pose_delta", "objective": "face_forward_naturally"},
            "floor_calibration": standard_floor_calibration(),
            "pelvic_alignment": {"actor": "A", "target_actor": "B", "region": "pelvis", "target_distance_m": 0.075, "max_forward_shift_m": 0.015, "iterations": 3},
            "support_assertions": standard_support_assertions(),
            "posture_assertions": [
                {"actor": "A", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.85, "max_hip_z_m": 1.28},
                {"actor": "B", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.78, "max_hip_z_m": 1.24},
            ],
        },
        "contacts": make_contacts("USDG-EDGE-V00 Pass 04: front pelvis lowered below rear via deeper B knee bend (~134 deg), rear cupping above, level edge forearms."),
    }

    # 2. USDG-SURF-V00 — B pelvis lower via ~135 deg knee bend, coplanar tabletop at z=0.735m, A cupping higher (~147 deg knees)
    specs["USDG-SURF-V00"] = {
        "expected_support": {
            "A": "both feet flat on floor (relaxed knees ~147 deg); pelvis cupping cleanly above B's lower-set hips; extended tucked arms on B outer deltoids",
            "B": "both feet flat on floor (slightly deeper knee bend ~135 deg lowering front pelvis below rear); chest & forearms coplanar on ~0.735m tabletop",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "USDG-SURF-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-04",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "A", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "B", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.0, 0.935], "pitch_x_deg": 103},
                *standing_feet("B", x=0.16, y=0.02, z=0.091, yaw=6, knee_x=0.18, knee_y=-0.60, knee_z=0.50),
                {"actor": "B", "bone": "hand_ik.L", "space": "POSE_WORLD_HAND_FRAME", "value": [0.18, -0.78, 0.735], "direction_world": [0.0, -0.99, -0.14], "normal_world": [-0.22, 0.14, -0.96]},
                {"actor": "B", "bone": "hand_ik.R", "space": "POSE_WORLD_HAND_FRAME", "value": [-0.18, -0.78, 0.735], "direction_world": [0.0, -0.99, -0.14], "normal_world": [0.22, 0.14, -0.96]},
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.27, -0.48, 0.73]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.27, -0.48, 0.73]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -36},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -30},
                {"actor": "A", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.245, 1.02], "pitch_x_deg": 49},
                *standing_feet("A", x=0.22, y=0.29, z=0.095, yaw=10, knee_x=0.25, knee_y=-0.22, knee_z=0.55),
                {"actor": "A", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.28, -0.10, 0.96]},
                {"actor": "A", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.28, -0.10, 0.96]},
                {"actor": "A", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -28},
                {"actor": "A", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -28},
                *rear_shoulder_hands(offset=(0.132, 0.08, 0.068)),
            ],
            "styling_controls": [
                {"actor": "B", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -17},
                {"actor": "A", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -8},
            ],
            "head_aim": {"actor": "B", "target_elevation_deg": -8, "max_delta_deg": 45, "neck_assist_enabled": True, "reference": "RIG001_forward_-Y_world_rest_to_pose_delta", "objective": "smooth_neck_clear_of_tabletop"},
            "floor_calibration": standard_floor_calibration(),
            "pelvic_alignment": {"actor": "A", "target_actor": "B", "region": "pelvis", "target_distance_m": 0.075, "max_forward_shift_m": 0.015, "iterations": 3},
            "support_assertions": standard_support_assertions(),
            "posture_assertions": [
                {"actor": "A", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.85, "max_hip_z_m": 1.28},
                {"actor": "B", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.78, "max_hip_z_m": 1.24},
            ],
        },
        "contacts": make_contacts("USDG-SURF-V00 Pass 04: front pelvis lowered below rear via deeper B knee bend (~135 deg), coplanar tabletop, clean cupping."),
    }

    # 3. USDG-WALL-V00 — Preserves standout ~90 deg vertical-wall silhouette while dropping B pelvis slightly below A via deeper B knee bend (~133 deg)
    specs["USDG-WALL-V00"] = {
        "expected_support": {
            "A": "both feet flat on floor (relaxed knees ~147 deg); pelvis cupping cleanly above B's lower-set hips; extended tucked arms on B outer deltoids",
            "B": "both feet flat on floor (slightly deeper knee bend ~133 deg lowering front pelvis below rear); ~90 deg hinge reaching forward level onto vertical wall (y=-0.85m, z=0.965m)",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "USDG-WALL-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-04",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "A", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "B", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.0, 0.935], "pitch_x_deg": 88},
                *standing_feet("B", x=0.16, y=0.02, z=0.091, yaw=6, knee_x=0.18, knee_y=-0.60, knee_z=0.50),
                {"actor": "B", "bone": "hand_ik.L", "space": "POSE_WORLD_HAND_FRAME", "value": [0.22, -0.85, 0.965], "direction_world": [0.0, 0.0, 1.0], "normal_world": [0.0, -1.0, 0.0]},
                {"actor": "B", "bone": "hand_ik.R", "space": "POSE_WORLD_HAND_FRAME", "value": [-0.22, -0.85, 0.965], "direction_world": [0.0, 0.0, 1.0], "normal_world": [0.0, -1.0, 0.0]},
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.28, -0.58, 0.90]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.28, -0.58, 0.90]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -32},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -30},
                {"actor": "A", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.25, 1.02], "pitch_x_deg": 40},
                *standing_feet("A", x=0.22, y=0.29, z=0.095, yaw=10, knee_x=0.25, knee_y=-0.22, knee_z=0.55),
                {"actor": "A", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.28, -0.10, 1.01]},
                {"actor": "A", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.28, -0.10, 1.01]},
                {"actor": "A", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -24},
                {"actor": "A", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -24},
                *rear_shoulder_hands(offset=(0.132, 0.08, 0.068)),
            ],
            "styling_controls": [
                {"actor": "B", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -16},
                {"actor": "A", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -8},
            ],
            "head_aim": {"actor": "B", "target_elevation_deg": 4, "max_delta_deg": 50, "neck_assist_enabled": True, "reference": "RIG001_forward_-Y_world_rest_to_pose_delta", "objective": "face_wall_naturally"},
            "floor_calibration": standard_floor_calibration(),
            "pelvic_alignment": {"actor": "A", "target_actor": "B", "region": "pelvis", "target_distance_m": 0.075, "max_forward_shift_m": 0.015, "iterations": 3},
            "support_assertions": standard_support_assertions(),
            "posture_assertions": [
                {"actor": "A", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.85, "max_hip_z_m": 1.28},
                {"actor": "B", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.78, "max_hip_z_m": 1.24},
            ],
        },
        "contacts": make_contacts("USDG-WALL-V00 Pass 04: ~90 deg vertical wall reach with front pelvis slightly lower than rear via deeper B knee bend (~133 deg)."),
    }

    # 4. USDG-LOW-V00 — B pelvis lowered via ~136 deg knee bend + deeper 125 deg fold (clears FORWARD_FOLD_NOT_ESTABLISHED!), A higher w/ zero chest-to-buttocks clip!
    specs["USDG-LOW-V00"] = {
        "expected_support": {
            "A": "both feet flat on floor (relaxed standing knees ~142 deg); pelvis cupping above B's lower-set hips with zero chest-into-buttocks clip; extended tucked arms on B deltoids",
            "B": "both feet flat on floor (relaxed bent knees ~136 deg lowering front pelvis below rear); deep ~125 deg forward fold (head >7cm below hip); palms on ~0.45m low support",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "USDG-LOW-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-04",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "A", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "B", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.0, 0.935], "pitch_x_deg": 125},
                *standing_feet("B", x=0.17, y=0.02, z=0.091, yaw=6, knee_x=0.19, knee_y=-0.60, knee_z=0.50),
                {"actor": "B", "bone": "hand_ik.L", "space": "POSE_WORLD_HAND_FRAME", "value": [0.20, -0.64, 0.45], "direction_world": HORIZ_DIR, "normal_world": HORIZ_NORM_L},
                {"actor": "B", "bone": "hand_ik.R", "space": "POSE_WORLD_HAND_FRAME", "value": [-0.20, -0.64, 0.45], "direction_world": HORIZ_DIR, "normal_world": HORIZ_NORM_R},
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.24, -0.48, 0.63]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.24, -0.48, 0.63]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -32},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -26},
                # A pelvis slightly higher (a_z=1.005 > b_z=0.935) and slightly further back (a_y=0.285) with pitch=64 deg -> zero chest-to-buttocks clip & clean reach!
                {"actor": "A", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.285, 1.005], "pitch_x_deg": 64},
                *standing_feet("A", x=0.23, y=0.32, z=0.095, yaw=10, knee_x=0.26, knee_y=-0.20, knee_z=0.55),
                {"actor": "A", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.29, -0.10, 0.90]},
                {"actor": "A", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.29, -0.10, 0.90]},
                {"actor": "A", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -34},
                {"actor": "A", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -34},
                *rear_shoulder_hands(offset=(0.132, 0.10, 0.072)),
            ],
            "styling_controls": [
                {"actor": "B", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -14},
                {"actor": "A", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -10},
            ],
            "head_aim": {"actor": "B", "target_elevation_deg": -26, "max_delta_deg": 40, "neck_assist_enabled": True, "reference": "RIG001_forward_-Y_world_rest_to_pose_delta", "objective": "deep_fold_smooth_neck"},
            "floor_calibration": standard_floor_calibration(),
            "pelvic_alignment": {"actor": "A", "target_actor": "B", "region": "pelvis", "target_distance_m": 0.080, "max_forward_shift_m": 0.010, "iterations": 3},
            "support_assertions": standard_support_assertions(),
            "posture_assertions": [
                {"actor": "A", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.82, "max_hip_z_m": 1.26},
                {"actor": "B", "kind": "forward_fold_standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.76, "max_hip_z_m": 1.22, "min_head_drop_below_hip_m": 0.06},
            ],
        },
        "contacts": make_contacts("USDG-LOW-V00 Pass 04: front pelvis lowered below rear, clears P1 chest-to-buttocks clip and FORWARD_FOLD_NOT_ESTABLISHED."),
    }

    # 5. USDG-PULL-V00 — Front pelvis lowered below rear via deeper B knee bend (~133 deg), clean cupping, B hands on A outer hips
    specs["USDG-PULL-V00"] = {
        "expected_support": {
            "A": "both feet flat on floor (relaxed knees ~147 deg); pelvis cupping cleanly above B's lower-set hips; extended tucked arms on B outer deltoids",
            "B": "both feet flat on floor (slightly deeper knee bend ~133 deg lowering front pelvis below rear); ~84 deg hinge; arms down-back contacting A outer hips",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "USDG-PULL-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-04",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "A", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "B", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.0, 0.935], "pitch_x_deg": 84},
                *standing_feet("B", x=0.17, y=0.02, z=0.091, yaw=6, knee_x=0.19, knee_y=-0.60, knee_z=0.50),
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.36, -0.26, 0.74]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.36, -0.26, 0.74]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -30},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -28},
                {"actor": "A", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.25, 1.02], "pitch_x_deg": 39},
                *standing_feet("A", x=0.22, y=0.29, z=0.095, yaw=10, knee_x=0.25, knee_y=-0.22, knee_z=0.55),
                {"actor": "A", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.28, -0.10, 1.01]},
                {"actor": "A", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.28, -0.10, 1.01]},
                {"actor": "A", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -24},
                {"actor": "A", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -24},
                {
                    "actor": "B",
                    "bone": "hand_ik.L",
                    "space": "POSE_RELATIVE_BONE_HEAD_HAND",
                    "value": [0.195, -0.07, -0.14],
                    "target_actor": "A",
                    "target_bone": "hips",
                    "direction_world": [-0.18, 0.90, -0.40],
                    "normal_world": [-0.94, -0.22, -0.24],
                },
                {
                    "actor": "B",
                    "bone": "hand_ik.R",
                    "space": "POSE_RELATIVE_BONE_HEAD_HAND",
                    "value": [-0.195, -0.07, -0.14],
                    "target_actor": "A",
                    "target_bone": "hips",
                    "direction_world": [0.18, 0.90, -0.40],
                    "normal_world": [0.94, -0.22, -0.24],
                },
                *rear_shoulder_hands(offset=(0.132, 0.08, 0.068)),
            ],
            "styling_controls": [
                {"actor": "B", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -15},
                {"actor": "A", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -8},
            ],
            "head_aim": {"actor": "B", "target_elevation_deg": 4, "max_delta_deg": 50, "neck_assist_enabled": True, "reference": "RIG001_forward_-Y_world_rest_to_pose_delta", "objective": "face_forward_naturally"},
            "floor_calibration": standard_floor_calibration(),
            "pelvic_alignment": {"actor": "A", "target_actor": "B", "region": "pelvis", "target_distance_m": 0.075, "max_forward_shift_m": 0.015, "iterations": 3},
            "support_assertions": standard_support_assertions(),
            "posture_assertions": [
                {"actor": "A", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.85, "max_hip_z_m": 1.28},
                {"actor": "B", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.78, "max_hip_z_m": 1.24},
            ],
        },
        "contacts": make_contacts(
            "USDG-PULL-V00 Pass 04: front pelvis lowered below rear via deeper B knee bend (~133 deg), clean cupping, B hands on A flanks.",
            extra_anchors=[
                {"id": "front_left_hand_to_rear_flank", "actor": "B", "bone": "hand_ik.L", "target_actor": "A", "target_bone": "hips", "tolerance_m": 0.34},
                {"id": "front_right_hand_to_rear_flank", "actor": "B", "bone": "hand_ik.R", "target_actor": "A", "target_bone": "hips", "tolerance_m": 0.34},
            ],
        ),
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
            "batch_id": "WORKSPACE-BATCH-0003-PASS-04",
            "source_checkpoint": auth["source_checkpoint"],
            "source_id": auth["source_id"],
            "actor_mapping": {"ACTOR_1": "A", "ACTOR_2": "B"},
            "pose_name": row["pose_name"],
            "source_gate": row["generation_gate"],
            "source_complexity_pose": row.get("complexity_pose", ""),
            "specification": row["specification"],
            "approach": "Workspace batch-0003 Pass 04: lower front pelvis slightly below rear via relaxed deeper B knee bend (~133-137 deg) + LOW chest-clearance & fold fix.",
            "expected_support": sp["expected_support"],
            "pass_label": "pass-04",
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
        "batch_label": "batch-0003",
        "pass_label": "pass-04",
        "family": "USDG",
        "note": "Calibrated USDG Pass 04: front pelvis slightly lower than rear via deeper relaxed B knee bend across all 5 poses + LOW chest-clearance & fold fix.",
        "local_calibration": {"enabled": True, "max_refinement_attempts": 2},
        "poses": plan_poses,
    }
    plan_path = write_json_workspace(BATCHES_DIR / "BATCH-0003-PASS-04.json", plan)
    print(json.dumps({"ok": True, "plan": workspace_rel(plan_path), "packages": created}, indent=2))


if __name__ == "__main__":
    main()
