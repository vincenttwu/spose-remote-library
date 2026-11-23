"""Author all 5 UFDG V00 Pass 03 surgically calibrated data-only pose packages inside workspace/.

Addresses the ONLY two remaining systemic defects from Pass 02 blind QA (6.7/10):
1. Actor A face-into-B-back clearance (all 5 poses, especially QUAD):
   - Lifts A's neck (-32 deg), head (-36 deg), and thoracic chest (-10 to -12 deg)
   - Relaxes A's forward torso pitch by 6-12 deg and eases pelvic_alignment to 0.080-0.085m
2. Actor B flat floor palms (all 5 poses):
   - Measured in live Blender 5.2: direction_world=[0, -0.906, -0.423] (-25 deg) with
     side-mirrored normal_world=[-+0.410, +0.386, -0.827] flattens thumb, index, middle,
     and pinky tips together within 6-13mm of the floor instead of balancing on thumb-tips.
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

# Live-measured flat floor palm frame for Actor B (thumb, index, middle, pinky planar on floor)
FLAT_FLOOR_DIR = [0.0, -0.906, -0.423]
FLAT_FLOOR_NORM_L = [-0.410, 0.386, -0.827]
FLAT_FLOOR_NORM_R = [0.410, 0.386, -0.827]


def front_floor_hands(x: float, y: float, z: float) -> list[dict]:
    return [
        {
            "actor": "B",
            "bone": "hand_ik.L",
            "space": "POSE_WORLD_HAND_FRAME",
            "value": [x, y, z],
            "direction_world": FLAT_FLOOR_DIR,
            "normal_world": FLAT_FLOOR_NORM_L,
        },
        {
            "actor": "B",
            "bone": "hand_ik.R",
            "space": "POSE_WORLD_HAND_FRAME",
            "value": [-x, y, z],
            "direction_world": FLAT_FLOOR_DIR,
            "normal_world": FLAT_FLOOR_NORM_R,
        },
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
    hand_offset: tuple[float, float, float] = (0.105, 0.10, 0.045),
    neck_angle: float = -32.0,
    head_angle: float = -36.0,
) -> list[dict]:
    """Actor A deep wide-footed frog squat + lifted head clearance + inward-turned outer-shoulder palms."""
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
        {"actor": "A", "bone": "thigh_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [knee_x, knee_y, knee_z]},
        {"actor": "A", "bone": "thigh_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-knee_x, knee_y, knee_z]},
        {"actor": "A", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [elbow_x, elbow_y, elbow_z]},
        {"actor": "A", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-elbow_x, elbow_y, elbow_z]},
        {"actor": "A", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": neck_angle},
        {"actor": "A", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": head_angle},
        {
            "actor": "A",
            "bone": "hand_ik.L",
            "space": "POSE_RELATIVE_BONE_HEAD_HAND",
            "value": [ox, oy, oz],
            "target_actor": "B",
            "target_bone": "DEF-upper_arm.L",
            "direction_world": [-0.45, -0.80, -0.39],
            "normal_world": [-0.80, 0.25, -0.54],
        },
        {
            "actor": "A",
            "bone": "hand_ik.R",
            "space": "POSE_RELATIVE_BONE_HEAD_HAND",
            "value": [-ox, oy, oz],
            "target_actor": "B",
            "target_bone": "DEF-upper_arm.R",
            "direction_world": [0.45, -0.80, -0.39],
            "normal_world": [0.80, 0.25, -0.54],
        },
    ]


def front_kneeling_legs(
    foot_x: float,
    foot_y: float,
    foot_yaw: float,
    knee_x: float,
    knee_y: float,
    knee_z: float = 0.07,
    foot_z: float = 0.082,
) -> list[dict]:
    return [
        {
            "actor": "B",
            "bone": "foot_ik.L",
            "space": "POSE_WORLD_HEAD_ROT_X_DEG",
            "value": [foot_x, foot_y, foot_z],
            "pitch_x_deg": 135,
            "yaw_z_deg": foot_yaw,
        },
        {
            "actor": "B",
            "bone": "foot_ik.R",
            "space": "POSE_WORLD_HEAD_ROT_X_DEG",
            "value": [-foot_x, foot_y, foot_z],
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
                "tolerance_m": 0.22,
            },
            {
                "id": "right_rear_palm_to_front_outer_shoulder",
                "actor": "A",
                "bone": "hand_ik.R",
                "target_actor": "B",
                "target_bone": "DEF-upper_arm.R",
                "tolerance_m": 0.22,
            },
        ],
        "note": note,
    }


def make_pose_specs() -> dict[str, dict]:
    specs: dict[str, dict] = {}

    # 1. UFDG-FWCH-V00
    specs["UFDG-FWCH-V00"] = {
        "expected_support": {
            "A": "both feet grounded wide in deep frog squat (never kneeling)",
            "B": "both knees/shins hip-width on floor; long forward palms flat on floor; low chest with elevated pelvis",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "UFDG-FWCH-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-03",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {
                    "actor": "B",
                    "bone": "torso",
                    "space": "POSE_WORLD_HEAD_ROT_X_DEG",
                    "value": [0.0, 0.0, 0.45],
                    "pitch_x_deg": 124,
                },
                *front_kneeling_legs(foot_x=0.14, foot_y=0.40, foot_yaw=2, knee_x=0.15, knee_y=-0.76, knee_z=0.06),
                *front_floor_hands(x=0.20, y=-0.84, z=0.022),
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.26, -0.60, 0.14]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.26, -0.60, 0.14]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -26},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -34},
                *rear_frog_squat_controls(
                    torso_y=0.43,
                    torso_z=0.42,
                    torso_pitch=73,
                    foot_x=0.38,
                    foot_y=0.42,
                    foot_yaw=26,
                    knee_x=0.96,
                    knee_y=-0.02,
                    knee_z=0.30,
                    elbow_x=0.56,
                    elbow_y=-0.16,
                    elbow_z=0.36,
                    hand_offset=(0.105, 0.10, 0.045),
                    neck_angle=-32.0,
                    head_angle=-36.0,
                ),
            ],
            "styling_controls": [
                {"actor": "B", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -4},
                {"actor": "A", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -10},
            ],
            "head_aim": {
                "actor": "B",
                "target_elevation_deg": -10,
                "max_delta_deg": 55,
                "reference": "RIG001_forward_-Y_world_rest_to_pose_delta",
                "objective": "keep_head_clear_of_floor",
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
                {"actor": "B", "region": "hands", "side": "L", "adjust_bone": "hand_ik.L", "target_z_m": 0.004, "tolerance_m": 0.020, "max_total_shift_m": 0.10, "iterations": 5},
                {"actor": "B", "region": "hands", "side": "R", "adjust_bone": "hand_ik.R", "target_z_m": 0.004, "tolerance_m": 0.020, "max_total_shift_m": 0.10, "iterations": 5},
            ],
            "pelvic_alignment": {
                "actor": "A",
                "target_actor": "B",
                "region": "pelvis",
                "target_distance_m": 0.085,
                "max_forward_shift_m": 0.08,
                "iterations": 6,
            },
            "support_assertions": [
                {"actor": "B", "region": "knees", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.030},
                {"actor": "B", "region": "knees", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.030},
                {"actor": "B", "region": "hands", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.024},
                {"actor": "B", "region": "hands", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.024},
                {"actor": "B", "region": "feet", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "B", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "A", "region": "feet", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "A", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
            ],
            "posture_assertions": [
                {"actor": "A", "kind": "low_wide_hands_feet", "min_hip_z_m": 0.25, "max_hip_z_m": 0.56},
                {"actor": "B", "kind": "quadruped", "max_knee_joint_z_m": 0.23, "max_knee_angle_deg": 148, "min_hip_z_m": 0.30, "max_hip_z_m": 0.65, "min_head_z_m": 0.14},
            ],
        },
        "contacts": make_contacts("UFDG-FWCH-V00 Pass 03: cleared A head above B back; flattened B floor palms."),
    }

    # 2. UFDG-WCHD-V00
    specs["UFDG-WCHD-V00"] = {
        "expected_support": {
            "A": "both feet grounded wide in deep frog squat (never kneeling)",
            "B": "both knees/lower shins clearly wider than hip-width on floor; chest lowered between thighs; long forward palms flat on floor; head clear of floor",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "UFDG-WCHD-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-03",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {
                    "actor": "B",
                    "bone": "torso",
                    "space": "POSE_WORLD_HEAD_ROT_X_DEG",
                    "value": [0.0, -0.02, 0.44],
                    "pitch_x_deg": 118,
                },
                *front_kneeling_legs(foot_x=0.23, foot_y=0.35, foot_yaw=16, knee_x=0.44, knee_y=-0.56, knee_z=0.07),
                *front_floor_hands(x=0.20, y=-0.84, z=0.022),
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.24, -0.60, 0.14]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.24, -0.60, 0.14]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -28},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -36},
                *rear_frog_squat_controls(
                    torso_y=0.41,
                    torso_z=0.39,
                    torso_pitch=75,
                    foot_x=0.44,
                    foot_y=0.43,
                    foot_yaw=28,
                    knee_x=1.00,
                    knee_y=-0.02,
                    knee_z=0.28,
                    elbow_x=0.56,
                    elbow_y=-0.18,
                    elbow_z=0.32,
                    hand_offset=(0.115, 0.10, 0.055),
                    neck_angle=-32.0,
                    head_angle=-36.0,
                ),
            ],
            "styling_controls": [
                {"actor": "B", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -6},
                {"actor": "A", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -10},
            ],
            "head_aim": {
                "actor": "B",
                "target_elevation_deg": -8,
                "max_delta_deg": 55,
                "reference": "RIG001_forward_-Y_world_rest_to_pose_delta",
                "objective": "keep_face_well_clear_of_floor",
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
                {"actor": "B", "region": "hands", "side": "L", "adjust_bone": "hand_ik.L", "target_z_m": 0.004, "tolerance_m": 0.020, "max_total_shift_m": 0.10, "iterations": 5},
                {"actor": "B", "region": "hands", "side": "R", "adjust_bone": "hand_ik.R", "target_z_m": 0.004, "tolerance_m": 0.020, "max_total_shift_m": 0.10, "iterations": 5},
            ],
            "pelvic_alignment": {
                "actor": "A",
                "target_actor": "B",
                "region": "pelvis",
                "target_distance_m": 0.085,
                "max_forward_shift_m": 0.08,
                "iterations": 6,
            },
            "support_assertions": [
                {"actor": "B", "region": "knees", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.030},
                {"actor": "B", "region": "knees", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.030},
                {"actor": "B", "region": "hands", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.024},
                {"actor": "B", "region": "hands", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.024},
                {"actor": "B", "region": "feet", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "B", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "A", "region": "feet", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "A", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
            ],
            "posture_assertions": [
                {"actor": "A", "kind": "low_wide_hands_feet", "min_hip_z_m": 0.24, "max_hip_z_m": 0.56},
                {"actor": "B", "kind": "quadruped", "max_knee_joint_z_m": 0.23, "max_knee_angle_deg": 148, "min_hip_z_m": 0.26, "max_hip_z_m": 0.62, "min_head_z_m": 0.14},
            ],
        },
        "contacts": make_contacts("UFDG-WCHD-V00 Pass 03: cleared A head above B back; flattened B floor palms."),
    }

    # 3. UFDG-ELBW-V00
    specs["UFDG-ELBW-V00"] = {
        "expected_support": {
            "A": "both feet grounded wide in deep frog squat (never kneeling)",
            "B": "both knees and BOTH elbows/forearms resting flat on floor; palms flat; head clearly above floor",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "UFDG-ELBW-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-03",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {
                    "actor": "B",
                    "bone": "torso",
                    "space": "POSE_WORLD_HEAD_ROT_X_DEG",
                    "value": [0.0, 0.0, 0.45],
                    "pitch_x_deg": 126,
                },
                *front_kneeling_legs(foot_x=0.15, foot_y=0.38, foot_yaw=3, knee_x=0.16, knee_y=-0.68, knee_z=0.07, foot_z=0.088),
                *front_floor_hands(x=0.16, y=-0.70, z=0.026),
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.22, -0.34, 0.01]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.22, -0.34, 0.01]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -28},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -36},
                *rear_frog_squat_controls(
                    torso_y=0.43,
                    torso_z=0.42,
                    torso_pitch=73,
                    foot_x=0.38,
                    foot_y=0.42,
                    foot_yaw=26,
                    knee_x=0.96,
                    knee_y=-0.02,
                    knee_z=0.30,
                    elbow_x=0.56,
                    elbow_y=-0.16,
                    elbow_z=0.36,
                    hand_offset=(0.105, 0.10, 0.045),
                    neck_angle=-32.0,
                    head_angle=-36.0,
                ),
            ],
            "styling_controls": [
                {"actor": "B", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -4},
                {"actor": "A", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -10},
            ],
            "head_aim": {
                "actor": "B",
                "target_elevation_deg": -4,
                "max_delta_deg": 60,
                "reference": "RIG001_forward_-Y_world_rest_to_pose_delta",
                "objective": "keep_head_free_above_floor_during_forearm_support",
            },
            "floor_calibration": [
                {"actor": "B", "region": "knees", "side": "L", "adjust_bone": "torso", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "B", "region": "knees", "side": "R", "adjust_bone": "torso", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "B", "region": "hands", "side": "L", "adjust_bone": "hand_ik.L", "target_z_m": 0.004, "tolerance_m": 0.024, "max_total_shift_m": 0.14, "iterations": 6},
                {"actor": "B", "region": "hands", "side": "R", "adjust_bone": "hand_ik.R", "target_z_m": 0.004, "tolerance_m": 0.024, "max_total_shift_m": 0.14, "iterations": 6},
                {"actor": "B", "region": "forearms", "side": "L", "adjust_bone": "hand_ik.L", "target_z_m": 0.004, "tolerance_m": 0.024, "max_total_shift_m": 0.05, "iterations": 4},
                {"actor": "B", "region": "forearms", "side": "R", "adjust_bone": "hand_ik.R", "target_z_m": 0.004, "tolerance_m": 0.024, "max_total_shift_m": 0.05, "iterations": 4},
                {"actor": "B", "region": "feet", "side": "L", "adjust_bone": "foot_ik.L", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "B", "region": "feet", "side": "R", "adjust_bone": "foot_ik.R", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "A", "region": "feet", "side": "L", "adjust_bone": "foot_ik.L", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "A", "region": "feet", "side": "R", "adjust_bone": "foot_ik.R", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
            ],
            "final_support_calibration": [
                {"actor": "B", "region": "hands", "side": "L", "adjust_bone": "hand_ik.L", "target_z_m": 0.004, "tolerance_m": 0.020, "max_total_shift_m": 0.06, "iterations": 4},
                {"actor": "B", "region": "hands", "side": "R", "adjust_bone": "hand_ik.R", "target_z_m": 0.004, "tolerance_m": 0.020, "max_total_shift_m": 0.06, "iterations": 4},
            ],
            "pelvic_alignment": {
                "actor": "A",
                "target_actor": "B",
                "region": "pelvis",
                "target_distance_m": 0.080,
                "max_forward_shift_m": 0.08,
                "iterations": 6,
            },
            "support_assertions": [
                {"actor": "B", "region": "knees", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.030},
                {"actor": "B", "region": "knees", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.030},
                {"actor": "B", "region": "forearms", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "B", "region": "forearms", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "B", "region": "hands", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.026},
                {"actor": "B", "region": "hands", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.026},
                {"actor": "B", "region": "feet", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "B", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "A", "region": "feet", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "A", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
            ],
            "posture_assertions": [
                {"actor": "A", "kind": "low_wide_hands_feet", "min_hip_z_m": 0.24, "max_hip_z_m": 0.56},
                {"actor": "B", "kind": "low_forearm_fold", "max_knee_joint_z_m": 0.23, "max_knee_angle_deg": 148, "min_hip_z_m": 0.30, "max_hip_z_m": 0.66, "min_head_z_m": 0.16},
            ],
        },
        "contacts": make_contacts("UFDG-ELBW-V00 Pass 03: cleared A head above B back; flattened B floor palms with grounded elbows."),
    }

    # 4. UFDG-QUAD-V00 — Critical P0 fix: lift A head & chest cleanly above B's thoracic back while preserving deep squat!
    specs["UFDG-QUAD-V00"] = {
        "expected_support": {
            "A": "both feet grounded wide in deep frog squat (never kneeling)",
            "B": "both knees and both palms flat on floor in conventional four-point quadruped stance; higher chest than FWCH/ELBW",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "UFDG-QUAD-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-03",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {
                    "actor": "B",
                    "bone": "torso",
                    "space": "POSE_WORLD_HEAD_ROT_X_DEG",
                    "value": [0.0, 0.0, 0.55],
                    "pitch_x_deg": 94,
                },
                *front_kneeling_legs(foot_x=0.15, foot_y=0.38, foot_yaw=3, knee_x=0.16, knee_y=-0.62, knee_z=0.07),
                *front_floor_hands(x=0.19, y=-0.49, z=0.015),
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.24, -0.22, 0.25]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.24, -0.22, 0.25]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -28},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -34},
                # Deep rear squat (hip_z ~ 0.50m) with reduced torso pitch (60 deg) + thoracic/neck/head lift so A clears B's upper back!
                *rear_frog_squat_controls(
                    torso_y=0.42,
                    torso_z=0.47,
                    torso_pitch=58,
                    foot_x=0.38,
                    foot_y=0.42,
                    foot_yaw=26,
                    knee_x=0.96,
                    knee_y=-0.04,
                    knee_z=0.34,
                    elbow_x=0.54,
                    elbow_y=-0.10,
                    elbow_z=0.52,
                    hand_offset=(0.10, 0.10, 0.04),
                    neck_angle=-34.0,
                    head_angle=-38.0,
                ),
            ],
            "styling_controls": [
                {"actor": "B", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -14},
                {"actor": "A", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -14},
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
                {"actor": "B", "region": "hands", "side": "L", "adjust_bone": "hand_ik.L", "target_z_m": 0.004, "tolerance_m": 0.020, "max_total_shift_m": 0.12, "iterations": 6},
                {"actor": "B", "region": "hands", "side": "R", "adjust_bone": "hand_ik.R", "target_z_m": 0.004, "tolerance_m": 0.020, "max_total_shift_m": 0.12, "iterations": 6},
            ],
            "pelvic_alignment": {
                "actor": "A",
                "target_actor": "B",
                "region": "pelvis",
                "target_distance_m": 0.085,
                "max_forward_shift_m": 0.07,
                "iterations": 6,
            },
            "support_assertions": [
                {"actor": "B", "region": "knees", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.030},
                {"actor": "B", "region": "knees", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.030},
                {"actor": "B", "region": "hands", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.020},
                {"actor": "B", "region": "hands", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.020},
                {"actor": "B", "region": "feet", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "B", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "A", "region": "feet", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "A", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
            ],
            "posture_assertions": [
                {"actor": "A", "kind": "low_wide_hands_feet", "min_hip_z_m": 0.28, "max_hip_z_m": 0.60},
                {"actor": "B", "kind": "quadruped", "max_knee_joint_z_m": 0.23, "max_knee_angle_deg": 148, "min_hip_z_m": 0.42, "max_hip_z_m": 0.78, "min_head_z_m": 0.34, "max_shoulder_to_hand_xy_m": 0.62},
            ],
        },
        "contacts": make_contacts("UFDG-QUAD-V00 Pass 03: fixed A face-to-back clip while keeping deep squat; flattened B palms."),
    }

    # 5. UFDG-FFRG-V00
    specs["UFDG-FFRG-V00"] = {
        "expected_support": {
            "A": "both feet grounded wide in deep frog squat (never kneeling)",
            "B": "both feet planted wide on floor with knees bent outward OFF floor; both palms flat on floor",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "UFDG-FFRG-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-03",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {
                    "actor": "B",
                    "bone": "torso",
                    "space": "POSE_WORLD_HEAD_ROT_X_DEG",
                    "value": [0.0, 0.0, 0.44],
                    "pitch_x_deg": 106,
                },
                {
                    "actor": "B",
                    "bone": "foot_ik.L",
                    "space": "POSE_WORLD_HEAD_ROT_X_DEG",
                    "value": [0.34, 0.06, 0.088],
                    "pitch_x_deg": 0,
                    "yaw_z_deg": 28,
                },
                {
                    "actor": "B",
                    "bone": "foot_ik.R",
                    "space": "POSE_WORLD_HEAD_ROT_X_DEG",
                    "value": [-0.34, 0.06, 0.088],
                    "pitch_x_deg": 0,
                    "yaw_z_deg": -28,
                },
                {"actor": "B", "bone": "thigh_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.68, -0.26, 0.16]},
                {"actor": "B", "bone": "thigh_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.68, -0.26, 0.16]},
                *front_floor_hands(x=0.22, y=-0.58, z=0.018),
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.28, -0.32, 0.22]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.28, -0.32, 0.22]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -24},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -30},
                *rear_frog_squat_controls(
                    torso_y=0.43,
                    torso_z=0.43,
                    torso_pitch=67,
                    foot_x=0.44,
                    foot_y=0.46,
                    foot_yaw=28,
                    knee_x=1.00,
                    knee_y=0.04,
                    knee_z=0.30,
                    elbow_x=0.66,
                    elbow_y=-0.06,
                    elbow_z=0.62,
                    hand_offset=(0.105, 0.10, 0.045),
                    neck_angle=-32.0,
                    head_angle=-36.0,
                ),
            ],
            "styling_controls": [
                {"actor": "B", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -10},
                {"actor": "A", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -10},
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
                {"actor": "B", "region": "hands", "side": "L", "adjust_bone": "hand_ik.L", "target_z_m": 0.004, "tolerance_m": 0.020, "max_total_shift_m": 0.10, "iterations": 5},
                {"actor": "B", "region": "hands", "side": "R", "adjust_bone": "hand_ik.R", "target_z_m": 0.004, "tolerance_m": 0.020, "max_total_shift_m": 0.10, "iterations": 5},
            ],
            "pelvic_alignment": {
                "actor": "A",
                "target_actor": "B",
                "region": "pelvis",
                "target_distance_m": 0.080,
                "max_forward_shift_m": 0.08,
                "iterations": 6,
            },
            "support_assertions": [
                {"actor": "B", "region": "feet", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "B", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "B", "region": "hands", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.024},
                {"actor": "B", "region": "hands", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.024},
                {"actor": "A", "region": "feet", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "A", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
            ],
            "posture_assertions": [
                {"actor": "A", "kind": "low_wide_hands_feet", "min_hip_z_m": 0.25, "max_hip_z_m": 0.56},
                {"actor": "B", "kind": "low_wide_hands_feet", "min_hip_z_m": 0.26, "max_hip_z_m": 0.65, "min_head_z_m": 0.20},
            ],
        },
        "contacts": make_contacts("UFDG-FFRG-V00 Pass 03: cleared A head above B back; flattened B floor palms; kept knee clearance."),
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
            "batch_id": "WORKSPACE-UFDG-V00-PASS03",
            "source_checkpoint": auth["source_checkpoint"],
            "source_id": auth["source_id"],
            "actor_mapping": {"ACTOR_1": "A", "ACTOR_2": "B"},
            "pose_name": row["pose_name"],
            "source_gate": row["generation_gate"],
            "source_complexity_pose": row.get("complexity_pose", ""),
            "specification": row["specification"],
            "approach": "Workspace experimental Pass 03 surgical polish from Pass 02 blind QA (6.7/10): A head clearance + B flat floor palms.",
            "expected_support": sp["expected_support"],
            "pass_label": "pass-03",
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
        "pass_label": "pass-03",
        "family": "UFDG",
        "note": "Surgical Pass 03 polish in workspace/ resolving Pass 02 blind QA items.",
        "local_calibration": {"enabled": True, "max_refinement_attempts": 2},
        "poses": plan_poses,
    }
    plan_path = write_json_workspace(PASS_DIR / "plan.json", plan)
    print(json.dumps({"ok": True, "plan": workspace_rel(plan_path), "packages": created}, indent=2))


if __name__ == "__main__":
    main()
