"""Author all 5 UFDG V00 Pass 01 data-only pose packages inside workspace/.

Every generated ZIP is validated immediately against the pinned top-level
catalog and pair template hashes via scripts/pose_common.py::load_package().
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

WS_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
if str(WS_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(WS_SCRIPTS))

from ws_common import (
    build_pose_package_zip,
    read_v00_catalog,
    utc_now_stamp,
    workspace_rel,
    write_json_workspace,
)

PASS_DIR = Path(__file__).resolve().parent
PKG_DIR = PASS_DIR / "packages"
POSE_ORDER = [
    "UFDG-FWCH-V00",
    "UFDG-WCHD-V00",
    "UFDG-ELBW-V00",
    "UFDG-QUAD-V00",
    "UFDG-FFRG-V00",
]


def rear_frog_squat_controls(
    torso_y: float,
    torso_z: float,
    torso_pitch: float,
    foot_x: float,
    foot_y: float,
    foot_yaw: float,
    knee_x: float,
    knee_y: float,
    knee_z: float,
    elbow_x: float,
    elbow_y: float,
    elbow_z: float,
    hand_offset: tuple[float, float, float],
    neck_angle: float = -12.0,
    head_angle: float = -14.0,
) -> list[dict]:
    """Build Actor A (rear partner) deep wide-footed frog squat + outer-shoulder reach."""
    ox, oy, oz = hand_offset
    return [
        {"actor": "A", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
        {
            "actor": "A",
            "bone": "torso",
            "space": "POSE_WORLD_HEAD_ROT_X_DEG",
            "value": [0.0, torso_y, torso_z],
            "pitch_x_deg": torso_pitch,
        },
        # Wide flat grounded feet (never kneeling)
        {
            "actor": "A",
            "bone": "foot_ik.L",
            "space": "POSE_WORLD_HEAD_ROT_X_DEG",
            "value": [foot_x, foot_y, 0.09],
            "pitch_x_deg": 0,
            "yaw_z_deg": foot_yaw,
        },
        {
            "actor": "A",
            "bone": "foot_ik.R",
            "space": "POSE_WORLD_HEAD_ROT_X_DEG",
            "value": [-foot_x, foot_y, 0.09],
            "pitch_x_deg": 0,
            "yaw_z_deg": -foot_yaw,
        },
        # Wide outward-opened knees
        {"actor": "A", "bone": "thigh_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [knee_x, knee_y, knee_z]},
        {"actor": "A", "bone": "thigh_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-knee_x, knee_y, knee_z]},
        # Rear elbows routed outside front upper arms
        {"actor": "A", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [elbow_x, elbow_y, elbow_z]},
        {"actor": "A", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-elbow_x, elbow_y, elbow_z]},
        # Neutral forward-down gaze
        {"actor": "A", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": neck_angle},
        {"actor": "A", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": head_angle},
        # V00 custom baseline: rear palms settle at B's outer shoulders and turn inward
        {
            "actor": "A",
            "bone": "hand_ik.L",
            "space": "POSE_RELATIVE_BONE_HEAD_HAND",
            "value": [ox, oy, oz],
            "target_actor": "B",
            "target_bone": "DEF-upper_arm.L",
            "direction_world": [0.0, -0.95, -0.30],
            "normal_world": [-0.85, 0.0, -0.52],
        },
        {
            "actor": "A",
            "bone": "hand_ik.R",
            "space": "POSE_RELATIVE_BONE_HEAD_HAND",
            "value": [-ox, oy, oz],
            "target_actor": "B",
            "target_bone": "DEF-upper_arm.R",
            "direction_world": [0.0, -0.95, -0.30],
            "normal_world": [0.85, 0.0, -0.52],
        },
    ]


def front_kneeling_legs(
    foot_x: float,
    foot_y: float,
    foot_yaw: float,
    knee_x: float,
    knee_y: float,
    knee_z: float = 0.07,
) -> list[dict]:
    return [
        {
            "actor": "B",
            "bone": "foot_ik.L",
            "space": "POSE_WORLD_HEAD_ROT_X_DEG",
            "value": [foot_x, foot_y, 0.078],
            "pitch_x_deg": 135,
            "yaw_z_deg": foot_yaw,
        },
        {
            "actor": "B",
            "bone": "foot_ik.R",
            "space": "POSE_WORLD_HEAD_ROT_X_DEG",
            "value": [-foot_x, foot_y, 0.078],
            "pitch_x_deg": 135,
            "yaw_z_deg": -foot_yaw,
        },
        {"actor": "B", "bone": "thigh_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [knee_x, knee_y, knee_z]},
        {"actor": "B", "bone": "thigh_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-knee_x, knee_y, knee_z]},
    ]


def make_contacts(note: str) -> dict:
    return {
        "schema_version": 1,
        "anchors": [
            {
                "id": "pelvis_proximity",
                "actor": "A",
                "bone": "hips",
                "target_actor": "B",
                "target_bone": "hips",
                "tolerance_m": 0.45,
            },
            {
                "id": "left_rear_palm_to_front_outer_shoulder",
                "actor": "A",
                "bone": "hand_ik.L",
                "target_actor": "B",
                "target_bone": "DEF-upper_arm.L",
                "tolerance_m": 0.16,
            },
            {
                "id": "right_rear_palm_to_front_outer_shoulder",
                "actor": "A",
                "bone": "hand_ik.R",
                "target_actor": "B",
                "target_bone": "DEF-upper_arm.R",
                "tolerance_m": 0.16,
            },
        ],
        "note": note,
    }


def make_pose_specs() -> dict[str, dict]:
    specs: dict[str, dict] = {}

    # 1. UFDG-FWCH-V00 — Forward child-like floor hinge
    specs["UFDG-FWCH-V00"] = {
        "expected_support": {
            "A": "both feet grounded wide in deep frog squat (never kneeling)",
            "B": "both knees/shins hip-width on floor; both palms reaching long forward on floor; chest low",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "UFDG-FWCH-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-01",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {
                    "actor": "B",
                    "bone": "torso",
                    "space": "POSE_WORLD_HEAD_ROT_X_DEG",
                    "value": [0.0, 0.0, 0.46],
                    "pitch_x_deg": 118,
                },
                *front_kneeling_legs(foot_x=0.14, foot_y=0.40, foot_yaw=2, knee_x=0.15, knee_y=-0.75, knee_z=0.06),
                {
                    "actor": "B",
                    "bone": "hand_ik.L",
                    "space": "POSE_WORLD_HAND_FRAME",
                    "value": [0.22, -0.78, 0.03],
                    "direction_world": [0, -1, 0],
                    "normal_world": [0, 0, -1],
                },
                {
                    "actor": "B",
                    "bone": "hand_ik.R",
                    "space": "POSE_WORLD_HAND_FRAME",
                    "value": [-0.22, -0.78, 0.03],
                    "direction_world": [0, -1, 0],
                    "normal_world": [0, 0, -1],
                },
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.36, -0.62, 0.14]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.36, -0.62, 0.14]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -20},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -28},
                *rear_frog_squat_controls(
                    torso_y=0.38,
                    torso_z=0.49,
                    torso_pitch=74,
                    foot_x=0.36,
                    foot_y=0.42,
                    foot_yaw=25,
                    knee_x=0.92,
                    knee_y=-0.04,
                    knee_z=0.22,
                    elbow_x=0.56,
                    elbow_y=-0.16,
                    elbow_z=0.36,
                    hand_offset=(0.085, 0.02, 0.02),
                ),
            ],
            "styling_controls": [
                {"actor": "B", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -8},
            ],
            "floor_calibration": [
                {"actor": "B", "region": "knees", "side": "L", "adjust_bone": "torso", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "B", "region": "knees", "side": "R", "adjust_bone": "torso", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "B", "region": "hands", "side": "L", "adjust_bone": "hand_ik.L", "target_z_m": 0.004, "tolerance_m": 0.024, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "B", "region": "hands", "side": "R", "adjust_bone": "hand_ik.R", "target_z_m": 0.004, "tolerance_m": 0.024, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "B", "region": "feet", "side": "L", "adjust_bone": "foot_ik.L", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "B", "region": "feet", "side": "R", "adjust_bone": "foot_ik.R", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "A", "region": "feet", "side": "L", "adjust_bone": "foot_ik.L", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "A", "region": "feet", "side": "R", "adjust_bone": "foot_ik.R", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
            ],
            "final_support_calibration": [
                {"actor": "B", "region": "hands", "side": "L", "adjust_bone": "hand_ik.L", "target_z_m": 0.004, "tolerance_m": 0.024, "max_total_shift_m": 0.08, "iterations": 4},
                {"actor": "B", "region": "hands", "side": "R", "adjust_bone": "hand_ik.R", "target_z_m": 0.004, "tolerance_m": 0.024, "max_total_shift_m": 0.08, "iterations": 4},
            ],
            "pelvic_alignment": {
                "actor": "A",
                "target_actor": "B",
                "region": "pelvis",
                "target_distance_m": 0.04,
                "max_forward_shift_m": 0.12,
                "iterations": 6,
            },
            "support_assertions": [
                {"actor": "B", "region": "knees", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.030},
                {"actor": "B", "region": "knees", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.030},
                {"actor": "B", "region": "hands", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.026},
                {"actor": "B", "region": "hands", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.026},
                {"actor": "B", "region": "feet", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "B", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "A", "region": "feet", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "A", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
            ],
            "posture_assertions": [
                {"actor": "A", "kind": "low_wide_hands_feet", "min_hip_z_m": 0.25, "max_hip_z_m": 0.68},
                {"actor": "B", "kind": "quadruped", "max_knee_joint_z_m": 0.23, "max_knee_angle_deg": 148, "min_hip_z_m": 0.34, "max_hip_z_m": 0.68},
            ],
        },
        "contacts": make_contacts("UFDG-FWCH-V00 Pass 01: rear deep frog squat, palms at B outer shoulders."),
    }

    # 2. UFDG-WCHD-V00 — Wide child-like floor hinge
    specs["UFDG-WCHD-V00"] = {
        "expected_support": {
            "A": "both feet grounded wide in deep frog squat (never kneeling)",
            "B": "both knees/lower shins clearly wider than hip-width on floor; chest lowered between thighs; palms long forward on floor",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "UFDG-WCHD-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-01",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {
                    "actor": "B",
                    "bone": "torso",
                    "space": "POSE_WORLD_HEAD_ROT_X_DEG",
                    "value": [0.0, -0.02, 0.43],
                    "pitch_x_deg": 120,
                },
                # Clearly wide knees & externally rotated thighs
                *front_kneeling_legs(foot_x=0.24, foot_y=0.36, foot_yaw=18, knee_x=0.58, knee_y=-0.50, knee_z=0.08),
                {
                    "actor": "B",
                    "bone": "hand_ik.L",
                    "space": "POSE_WORLD_HAND_FRAME",
                    "value": [0.24, -0.78, 0.03],
                    "direction_world": [0, -1, 0],
                    "normal_world": [0, 0, -1],
                },
                {
                    "actor": "B",
                    "bone": "hand_ik.R",
                    "space": "POSE_WORLD_HAND_FRAME",
                    "value": [-0.24, -0.78, 0.03],
                    "direction_world": [0, -1, 0],
                    "normal_world": [0, 0, -1],
                },
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.38, -0.62, 0.14]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.38, -0.62, 0.14]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -20},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -28},
                *rear_frog_squat_controls(
                    torso_y=0.36,
                    torso_z=0.47,
                    torso_pitch=76,
                    foot_x=0.42,
                    foot_y=0.44,
                    foot_yaw=28,
                    knee_x=0.98,
                    knee_y=-0.02,
                    knee_z=0.22,
                    elbow_x=0.56,
                    elbow_y=-0.18,
                    elbow_z=0.34,
                    hand_offset=(0.085, 0.02, 0.02),
                ),
            ],
            "styling_controls": [
                {"actor": "B", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -8},
            ],
            "floor_calibration": [
                {"actor": "B", "region": "knees", "side": "L", "adjust_bone": "torso", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "B", "region": "knees", "side": "R", "adjust_bone": "torso", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "B", "region": "hands", "side": "L", "adjust_bone": "hand_ik.L", "target_z_m": 0.004, "tolerance_m": 0.024, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "B", "region": "hands", "side": "R", "adjust_bone": "hand_ik.R", "target_z_m": 0.004, "tolerance_m": 0.024, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "B", "region": "feet", "side": "L", "adjust_bone": "foot_ik.L", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "B", "region": "feet", "side": "R", "adjust_bone": "foot_ik.R", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "A", "region": "feet", "side": "L", "adjust_bone": "foot_ik.L", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "A", "region": "feet", "side": "R", "adjust_bone": "foot_ik.R", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
            ],
            "final_support_calibration": [
                {"actor": "B", "region": "hands", "side": "L", "adjust_bone": "hand_ik.L", "target_z_m": 0.004, "tolerance_m": 0.024, "max_total_shift_m": 0.08, "iterations": 4},
                {"actor": "B", "region": "hands", "side": "R", "adjust_bone": "hand_ik.R", "target_z_m": 0.004, "tolerance_m": 0.024, "max_total_shift_m": 0.08, "iterations": 4},
            ],
            "pelvic_alignment": {
                "actor": "A",
                "target_actor": "B",
                "region": "pelvis",
                "target_distance_m": 0.04,
                "max_forward_shift_m": 0.12,
                "iterations": 6,
            },
            "support_assertions": [
                {"actor": "B", "region": "knees", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.030},
                {"actor": "B", "region": "knees", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.030},
                {"actor": "B", "region": "hands", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.026},
                {"actor": "B", "region": "hands", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.026},
                {"actor": "B", "region": "feet", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "B", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "A", "region": "feet", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "A", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
            ],
            "posture_assertions": [
                {"actor": "A", "kind": "low_wide_hands_feet", "min_hip_z_m": 0.25, "max_hip_z_m": 0.68},
                {"actor": "B", "kind": "quadruped", "max_knee_joint_z_m": 0.23, "max_knee_angle_deg": 148, "min_hip_z_m": 0.30, "max_hip_z_m": 0.65},
            ],
        },
        "contacts": make_contacts("UFDG-WCHD-V00 Pass 01: wide child-like front, rear deep frog squat, palms at B outer shoulders."),
    }

    # 3. UFDG-ELBW-V00 — Forearm-supported low hinge
    specs["UFDG-ELBW-V00"] = {
        "expected_support": {
            "A": "both feet grounded wide in deep frog squat (never kneeling)",
            "B": "both knees and both elbows/forearms grounded on floor; head free of floor contact",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "UFDG-ELBW-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-01",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {
                    "actor": "B",
                    "bone": "torso",
                    "space": "POSE_WORLD_HEAD_ROT_X_DEG",
                    "value": [0.0, 0.0, 0.50],
                    "pitch_x_deg": 112,
                },
                *front_kneeling_legs(foot_x=0.16, foot_y=0.38, foot_yaw=3, knee_x=0.18, knee_y=-0.68, knee_z=0.07),
                # Shortened forearm/elbow support on floor
                {
                    "actor": "B",
                    "bone": "hand_ik.L",
                    "space": "POSE_WORLD_HAND_FRAME",
                    "value": [0.19, -0.60, 0.032],
                    "direction_world": [0, -1, -0.05],
                    "normal_world": [0, 0, -1],
                },
                {
                    "actor": "B",
                    "bone": "hand_ik.R",
                    "space": "POSE_WORLD_HAND_FRAME",
                    "value": [-0.19, -0.60, 0.032],
                    "direction_world": [0, -1, -0.05],
                    "normal_world": [0, 0, -1],
                },
                # Low elbow pole targets so elbows & forearms rest flat on floor
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.27, -0.44, 0.055]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.27, -0.44, 0.055]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -24},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -30},
                *rear_frog_squat_controls(
                    torso_y=0.38,
                    torso_z=0.52,
                    torso_pitch=68,
                    foot_x=0.36,
                    foot_y=0.42,
                    foot_yaw=25,
                    knee_x=0.92,
                    knee_y=-0.04,
                    knee_z=0.22,
                    elbow_x=0.56,
                    elbow_y=-0.14,
                    elbow_z=0.40,
                    hand_offset=(0.085, 0.02, 0.02),
                ),
            ],
            "styling_controls": [
                {"actor": "B", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -10},
            ],
            "head_aim": {
                "actor": "B",
                "target_elevation_deg": -5,
                "max_delta_deg": 55,
                "reference": "RIG001_forward_-Y_world_rest_to_pose_delta",
                "objective": "keep_head_clear_of_floor",
            },
            "floor_calibration": [
                {"actor": "B", "region": "knees", "side": "L", "adjust_bone": "torso", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "B", "region": "knees", "side": "R", "adjust_bone": "torso", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "B", "region": "forearms", "side": "L", "adjust_bone": "hand_ik.L", "target_z_m": 0.004, "tolerance_m": 0.024, "max_total_shift_m": 0.16, "iterations": 6},
                {"actor": "B", "region": "forearms", "side": "R", "adjust_bone": "hand_ik.R", "target_z_m": 0.004, "tolerance_m": 0.024, "max_total_shift_m": 0.16, "iterations": 6},
                {"actor": "B", "region": "feet", "side": "L", "adjust_bone": "foot_ik.L", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "B", "region": "feet", "side": "R", "adjust_bone": "foot_ik.R", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "A", "region": "feet", "side": "L", "adjust_bone": "foot_ik.L", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "A", "region": "feet", "side": "R", "adjust_bone": "foot_ik.R", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
            ],
            "final_support_calibration": [
                {"actor": "B", "region": "forearms", "side": "L", "adjust_bone": "hand_ik.L", "target_z_m": 0.004, "tolerance_m": 0.024, "max_total_shift_m": 0.08, "iterations": 4},
                {"actor": "B", "region": "forearms", "side": "R", "adjust_bone": "hand_ik.R", "target_z_m": 0.004, "tolerance_m": 0.024, "max_total_shift_m": 0.08, "iterations": 4},
            ],
            "pelvic_alignment": {
                "actor": "A",
                "target_actor": "B",
                "region": "pelvis",
                "target_distance_m": 0.04,
                "max_forward_shift_m": 0.12,
                "iterations": 6,
            },
            "support_assertions": [
                {"actor": "B", "region": "knees", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.030},
                {"actor": "B", "region": "knees", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.030},
                {"actor": "B", "region": "forearms", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "B", "region": "forearms", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "B", "region": "feet", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "B", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "A", "region": "feet", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "A", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
            ],
            "posture_assertions": [
                {"actor": "A", "kind": "low_wide_hands_feet", "min_hip_z_m": 0.25, "max_hip_z_m": 0.70},
                {"actor": "B", "kind": "low_forearm_fold", "max_knee_joint_z_m": 0.23, "max_knee_angle_deg": 148, "min_hip_z_m": 0.36, "max_hip_z_m": 0.70, "min_head_z_m": 0.18},
            ],
        },
        "contacts": make_contacts("UFDG-ELBW-V00 Pass 01: forearm-supported front, rear deep frog squat, palms at B outer shoulders."),
    }

    # 4. UFDG-QUAD-V00 — Standard quadruped with rear frog squat
    specs["UFDG-QUAD-V00"] = {
        "expected_support": {
            "A": "both feet grounded wide in deep frog squat (never kneeling)",
            "B": "both knees and both palms on floor in conventional four-point quadruped stance; higher chest than FWCH/ELBW",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "UFDG-QUAD-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-01",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {
                    "actor": "B",
                    "bone": "torso",
                    "space": "POSE_WORLD_HEAD_ROT_X_DEG",
                    "value": [0.0, 0.0, 0.56],
                    "pitch_x_deg": 94,
                },
                *front_kneeling_legs(foot_x=0.15, foot_y=0.38, foot_yaw=3, knee_x=0.16, knee_y=-0.62, knee_z=0.07),
                {
                    "actor": "B",
                    "bone": "hand_ik.L",
                    "space": "POSE_WORLD_HAND_FRAME",
                    "value": [0.19, -0.49, 0.02],
                    "direction_world": [0, -1, 0],
                    "normal_world": [0, 0, -1],
                },
                {
                    "actor": "B",
                    "bone": "hand_ik.R",
                    "space": "POSE_WORLD_HAND_FRAME",
                    "value": [-0.19, -0.49, 0.02],
                    "direction_world": [0, -1, 0],
                    "normal_world": [0, 0, -1],
                },
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.34, -0.35, 0.28]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.34, -0.35, 0.28]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -28},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -34},
                *rear_frog_squat_controls(
                    torso_y=0.40,
                    torso_z=0.58,
                    torso_pitch=58,
                    foot_x=0.37,
                    foot_y=0.44,
                    foot_yaw=25,
                    knee_x=0.92,
                    knee_y=-0.02,
                    knee_z=0.25,
                    elbow_x=0.56,
                    elbow_y=-0.12,
                    elbow_z=0.50,
                    hand_offset=(0.085, 0.02, 0.02),
                ),
            ],
            "styling_controls": [
                {"actor": "B", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -14},
            ],
            "head_aim": {
                "actor": "B",
                "target_elevation_deg": 8,
                "max_delta_deg": 65,
                "reference": "RIG001_forward_-Y_world_rest_to_pose_delta",
                "objective": "face_forward_slightly_up",
            },
            "floor_calibration": [
                {"actor": "B", "region": "knees", "side": "L", "adjust_bone": "torso", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "B", "region": "knees", "side": "R", "adjust_bone": "torso", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "B", "region": "hands", "side": "L", "adjust_bone": "hand_ik.L", "target_z_m": 0.004, "tolerance_m": 0.024, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "B", "region": "hands", "side": "R", "adjust_bone": "hand_ik.R", "target_z_m": 0.004, "tolerance_m": 0.024, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "B", "region": "feet", "side": "L", "adjust_bone": "foot_ik.L", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "B", "region": "feet", "side": "R", "adjust_bone": "foot_ik.R", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "A", "region": "feet", "side": "L", "adjust_bone": "foot_ik.L", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "A", "region": "feet", "side": "R", "adjust_bone": "foot_ik.R", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
            ],
            "final_support_calibration": [
                {"actor": "B", "region": "hands", "side": "L", "adjust_bone": "hand_ik.L", "target_z_m": 0.004, "tolerance_m": 0.024, "max_total_shift_m": 0.08, "iterations": 4},
                {"actor": "B", "region": "hands", "side": "R", "adjust_bone": "hand_ik.R", "target_z_m": 0.004, "tolerance_m": 0.024, "max_total_shift_m": 0.08, "iterations": 4},
            ],
            "pelvic_alignment": {
                "actor": "A",
                "target_actor": "B",
                "region": "pelvis",
                "target_distance_m": 0.04,
                "max_forward_shift_m": 0.12,
                "iterations": 6,
            },
            "support_assertions": [
                {"actor": "B", "region": "knees", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.030},
                {"actor": "B", "region": "knees", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.030},
                {"actor": "B", "region": "hands", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.026},
                {"actor": "B", "region": "hands", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.026},
                {"actor": "B", "region": "feet", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "B", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "A", "region": "feet", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "A", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
            ],
            "posture_assertions": [
                {"actor": "A", "kind": "low_wide_hands_feet", "min_hip_z_m": 0.30, "max_hip_z_m": 0.74},
                {"actor": "B", "kind": "quadruped", "max_knee_joint_z_m": 0.23, "max_knee_angle_deg": 148, "min_hip_z_m": 0.44, "max_hip_z_m": 0.78, "min_head_z_m": 0.34, "max_shoulder_to_hand_xy_m": 0.62},
            ],
        },
        "contacts": make_contacts("UFDG-QUAD-V00 Pass 01: conventional front quadruped, rear deep frog squat, palms at B outer shoulders."),
    }

    # 5. UFDG-FFRG-V00 — Front frog with rear frog squat (BOTH actors on feet, NOT knees!)
    specs["UFDG-FFRG-V00"] = {
        "expected_support": {
            "A": "both feet grounded wide in deep frog squat (never kneeling)",
            "B": "both feet planted wide on floor with knees opened outward off floor; both palms on floor stabilizing lowered torso",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "UFDG-FFRG-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-01",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {
                    "actor": "B",
                    "bone": "torso",
                    "space": "POSE_WORLD_HEAD_ROT_X_DEG",
                    "value": [0.0, 0.0, 0.46],
                    "pitch_x_deg": 106,
                },
                # Front wide flat-footed frog stance (knees off floor!)
                {
                    "actor": "B",
                    "bone": "foot_ik.L",
                    "space": "POSE_WORLD_HEAD_ROT_X_DEG",
                    "value": [0.34, 0.06, 0.088],
                    "pitch_x_deg": 0,
                    "yaw_z_deg": 26,
                },
                {
                    "actor": "B",
                    "bone": "foot_ik.R",
                    "space": "POSE_WORLD_HEAD_ROT_X_DEG",
                    "value": [-0.34, 0.06, 0.088],
                    "pitch_x_deg": 0,
                    "yaw_z_deg": -26,
                },
                {"actor": "B", "bone": "thigh_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.76, -0.26, 0.28]},
                {"actor": "B", "bone": "thigh_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.76, -0.26, 0.28]},
                {
                    "actor": "B",
                    "bone": "hand_ik.L",
                    "space": "POSE_WORLD_HAND_FRAME",
                    "value": [0.24, -0.58, 0.025],
                    "direction_world": [0, -1, 0],
                    "normal_world": [0, 0, -1],
                },
                {
                    "actor": "B",
                    "bone": "hand_ik.R",
                    "space": "POSE_WORLD_HAND_FRAME",
                    "value": [-0.24, -0.58, 0.025],
                    "direction_world": [0, -1, 0],
                    "normal_world": [0, 0, -1],
                },
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.38, -0.44, 0.20]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.38, -0.44, 0.20]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -24},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -30},
                *rear_frog_squat_controls(
                    torso_y=0.40,
                    torso_z=0.50,
                    torso_pitch=70,
                    foot_x=0.42,
                    foot_y=0.46,
                    foot_yaw=28,
                    knee_x=0.98,
                    knee_y=0.04,
                    knee_z=0.26,
                    elbow_x=0.58,
                    elbow_y=-0.12,
                    elbow_z=0.40,
                    hand_offset=(0.085, 0.02, 0.02),
                ),
            ],
            "styling_controls": [
                {"actor": "B", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -10},
            ],
            "head_aim": {
                "actor": "B",
                "target_elevation_deg": 2,
                "max_delta_deg": 60,
                "reference": "RIG001_forward_-Y_world_rest_to_pose_delta",
                "objective": "face_forward_clear_of_floor",
            },
            "floor_calibration": [
                {"actor": "B", "region": "feet", "side": "L", "adjust_bone": "foot_ik.L", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "B", "region": "feet", "side": "R", "adjust_bone": "foot_ik.R", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "B", "region": "hands", "side": "L", "adjust_bone": "hand_ik.L", "target_z_m": 0.004, "tolerance_m": 0.024, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "B", "region": "hands", "side": "R", "adjust_bone": "hand_ik.R", "target_z_m": 0.004, "tolerance_m": 0.024, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "A", "region": "feet", "side": "L", "adjust_bone": "foot_ik.L", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "A", "region": "feet", "side": "R", "adjust_bone": "foot_ik.R", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
            ],
            "final_support_calibration": [
                {"actor": "B", "region": "hands", "side": "L", "adjust_bone": "hand_ik.L", "target_z_m": 0.004, "tolerance_m": 0.024, "max_total_shift_m": 0.08, "iterations": 4},
                {"actor": "B", "region": "hands", "side": "R", "adjust_bone": "hand_ik.R", "target_z_m": 0.004, "tolerance_m": 0.024, "max_total_shift_m": 0.08, "iterations": 4},
            ],
            "pelvic_alignment": {
                "actor": "A",
                "target_actor": "B",
                "region": "pelvis",
                "target_distance_m": 0.04,
                "max_forward_shift_m": 0.12,
                "iterations": 6,
            },
            "support_assertions": [
                {"actor": "B", "region": "feet", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "B", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "B", "region": "hands", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.026},
                {"actor": "B", "region": "hands", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.026},
                {"actor": "A", "region": "feet", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "A", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
            ],
            "posture_assertions": [
                {"actor": "A", "kind": "low_wide_hands_feet", "min_hip_z_m": 0.26, "max_hip_z_m": 0.70},
                {"actor": "B", "kind": "low_wide_hands_feet", "min_hip_z_m": 0.28, "max_hip_z_m": 0.70, "min_head_z_m": 0.22},
            ],
        },
        "contacts": make_contacts("UFDG-FFRG-V00 Pass 01: double frog squat (both actors feet-grounded), palms at B outer shoulders."),
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
            "batch_id": "WORKSPACE-UFDG-V00-PASS01",
            "source_checkpoint": auth["source_checkpoint"],
            "source_id": auth["source_id"],
            "actor_mapping": {"ACTOR_1": "A", "ACTOR_2": "B"},
            "pose_name": row["pose_name"],
            "source_gate": row["generation_gate"],
            "source_complexity_pose": row.get("complexity_pose", ""),
            "specification": row["specification"],
            "approach": "Workspace experimental Pass 01 authoring using rigify_floor_v2; rear deep wide-footed frog squat with outer-shoulder palm placement.",
            "expected_support": sp["expected_support"],
            "pass_label": "pass-01",
            "workspace_experimental": True,
        }
        zpath = build_pose_package_zip(
            dest_dir=PKG_DIR,
            pose_id=pose_id,
            pose_json=pose_json,
            rig_targets=sp["rig_targets"],
            contacts=sp["contacts"],
            timestamp_utc=ts,
        )
        plan_poses.append({"pose_id": pose_id, "package": zpath.name})
        created.append(workspace_rel(zpath))

    plan = {
        "schema_version": 1,
        "kind": "spose_workspace_batch_plan",
        "batch_label": "workspace-ufdg",
        "pass_label": "pass-01",
        "family": "UFDG",
        "note": "Experimental backward-roadmap batch in workspace/. Assign official batch_label on explicit promotion.",
        "local_calibration": {"enabled": True, "max_refinement_attempts": 2},
        "poses": plan_poses,
    }
    plan_path = write_json_workspace(PASS_DIR / "plan.json", plan)
    print(json.dumps({"ok": True, "plan": workspace_rel(plan_path), "packages": created}, indent=2))


if __name__ == "__main__":
    main()
