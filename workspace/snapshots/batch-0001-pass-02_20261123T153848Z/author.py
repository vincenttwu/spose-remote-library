"""Author all 5 UFDG V00 Pass 02 calibrated data-only pose packages inside workspace/.

Addresses all P0/P1 visual QA findings from Pass 01 AUDIT.md:
- ELBW: true elbow + forearm floor contact (lowered shoulder height, horizontal forearm)
- WCHD: eliminate A hand-through-B-arm clipping & B face floor dip; long forward B arms
- FFRG: route A forearms cleanly over/outside B's raised knees; deepen A squat
- FWCH: lower B chest with longer forward reach; eliminate A-torso/B-buttock clip
- QUAD: dramatically deepen A rear frog squat; ground B palms flat at z~0.004m
- ALL 5: pitch B floor palms flat; place & angle A palms inward onto B's outer deltoids
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

# Flat floor palm frame for Actor B (pitches fingers downward ~20 deg so whole palm+fingers rest flat on floor)
FLAT_FLOOR_DIR = [0.0, -0.94, -0.34]
FLAT_FLOOR_NORM = [0.0, 0.34, -0.94]


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
    hand_dir_x: float = 0.45,
    hand_dir_y: float = -0.80,
    hand_dir_z: float = -0.39,
    hand_norm_x: float = 0.80,
    hand_norm_y: float = 0.25,
    hand_norm_z: float = -0.54,
    neck_angle: float = -10.0,
    head_angle: float = -12.0,
) -> list[dict]:
    """Actor A deep wide-footed frog squat + inward-turned palms on B's outer shoulders."""
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
        # Wide outward-opened deep-flexion knees
        {"actor": "A", "bone": "thigh_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [knee_x, knee_y, knee_z]},
        {"actor": "A", "bone": "thigh_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-knee_x, knee_y, knee_z]},
        # Rear elbows routed outside front upper arms
        {"actor": "A", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [elbow_x, elbow_y, elbow_z]},
        {"actor": "A", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-elbow_x, elbow_y, elbow_z]},
        {"actor": "A", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": neck_angle},
        {"actor": "A", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": head_angle},
        # Wrist behind/outside B's deltoid, fingers angling inward around B's outer shoulder, palm turned inward
        {
            "actor": "A",
            "bone": "hand_ik.L",
            "space": "POSE_RELATIVE_BONE_HEAD_HAND",
            "value": [ox, oy, oz],
            "target_actor": "B",
            "target_bone": "DEF-upper_arm.L",
            "direction_world": [-hand_dir_x, hand_dir_y, hand_dir_z],
            "normal_world": [-hand_norm_x, hand_norm_y, hand_norm_z],
        },
        {
            "actor": "A",
            "bone": "hand_ik.R",
            "space": "POSE_RELATIVE_BONE_HEAD_HAND",
            "value": [-ox, oy, oz],
            "target_actor": "B",
            "target_bone": "DEF-upper_arm.R",
            "direction_world": [hand_dir_x, hand_dir_y, hand_dir_z],
            "normal_world": [hand_norm_x, hand_norm_y, hand_norm_z],
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

    # 1. UFDG-FWCH-V00 — Lower B chest with long forward reach, flat palms; deepen A squat, clear B buttocks
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
            "pass_label": "workspace-pass-02",
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
                {
                    "actor": "B",
                    "bone": "hand_ik.L",
                    "space": "POSE_WORLD_HAND_FRAME",
                    "value": [0.20, -0.84, 0.022],
                    "direction_world": FLAT_FLOOR_DIR,
                    "normal_world": FLAT_FLOOR_NORM,
                },
                {
                    "actor": "B",
                    "bone": "hand_ik.R",
                    "space": "POSE_WORLD_HAND_FRAME",
                    "value": [-0.20, -0.84, 0.022],
                    "direction_world": FLAT_FLOOR_DIR,
                    "normal_world": FLAT_FLOOR_NORM,
                },
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.26, -0.60, 0.14]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.26, -0.60, 0.14]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -26},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -34},
                *rear_frog_squat_controls(
                    torso_y=0.42,
                    torso_z=0.41,
                    torso_pitch=82,
                    foot_x=0.38,
                    foot_y=0.42,
                    foot_yaw=26,
                    knee_x=0.96,
                    knee_y=-0.02,
                    knee_z=0.30,
                    elbow_x=0.56,
                    elbow_y=-0.16,
                    elbow_z=0.34,
                    hand_offset=(0.105, 0.10, 0.045),
                ),
            ],
            "styling_controls": [
                {"actor": "B", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -4},
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
                {"actor": "B", "region": "hands", "side": "L", "adjust_bone": "hand_ik.L", "target_z_m": 0.004, "tolerance_m": 0.024, "max_total_shift_m": 0.10, "iterations": 5},
                {"actor": "B", "region": "hands", "side": "R", "adjust_bone": "hand_ik.R", "target_z_m": 0.004, "tolerance_m": 0.024, "max_total_shift_m": 0.10, "iterations": 5},
            ],
            "pelvic_alignment": {
                "actor": "A",
                "target_actor": "B",
                "region": "pelvis",
                "target_distance_m": 0.075,
                "max_forward_shift_m": 0.10,
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
                {"actor": "A", "kind": "low_wide_hands_feet", "min_hip_z_m": 0.25, "max_hip_z_m": 0.56},
                {"actor": "B", "kind": "quadruped", "max_knee_joint_z_m": 0.23, "max_knee_angle_deg": 148, "min_hip_z_m": 0.30, "max_hip_z_m": 0.65, "min_head_z_m": 0.14},
            ],
        },
        "contacts": make_contacts("UFDG-FWCH-V00 Pass 02: deeper A squat, lower B chest, flat floor palms, inward shoulder palms."),
    }

    # 2. UFDG-WCHD-V00 — Raise B pelvis & head clear of floor, straight long forward arms, zero A-hand-to-B-arm clipping
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
            "pass_label": "workspace-pass-02",
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
                # Clearly wider than hip-width knees, externally rotated thighs, without collapsing pelvis to 0.21m
                *front_kneeling_legs(foot_x=0.23, foot_y=0.35, foot_yaw=16, knee_x=0.44, knee_y=-0.56, knee_z=0.07),
                # Long forward arms along floor (straight elbows, no lateral splay!)
                {
                    "actor": "B",
                    "bone": "hand_ik.L",
                    "space": "POSE_WORLD_HAND_FRAME",
                    "value": [0.20, -0.84, 0.022],
                    "direction_world": FLAT_FLOOR_DIR,
                    "normal_world": FLAT_FLOOR_NORM,
                },
                {
                    "actor": "B",
                    "bone": "hand_ik.R",
                    "space": "POSE_WORLD_HAND_FRAME",
                    "value": [-0.20, -0.84, 0.022],
                    "direction_world": FLAT_FLOOR_DIR,
                    "normal_world": FLAT_FLOOR_NORM,
                },
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.24, -0.60, 0.14]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.24, -0.60, 0.14]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -28},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -36},
                # Deep rear frog squat closely over B; hands cleanly outside B's deltoids (oz=+0.055, ox=0.115)
                *rear_frog_squat_controls(
                    torso_y=0.40,
                    torso_z=0.38,
                    torso_pitch=84,
                    foot_x=0.44,
                    foot_y=0.43,
                    foot_yaw=28,
                    knee_x=1.00,
                    knee_y=-0.02,
                    knee_z=0.28,
                    elbow_x=0.56,
                    elbow_y=-0.18,
                    elbow_z=0.30,
                    hand_offset=(0.115, 0.10, 0.055),
                ),
            ],
            "styling_controls": [
                {"actor": "B", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -6},
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
                {"actor": "B", "region": "hands", "side": "L", "adjust_bone": "hand_ik.L", "target_z_m": 0.004, "tolerance_m": 0.024, "max_total_shift_m": 0.10, "iterations": 5},
                {"actor": "B", "region": "hands", "side": "R", "adjust_bone": "hand_ik.R", "target_z_m": 0.004, "tolerance_m": 0.024, "max_total_shift_m": 0.10, "iterations": 5},
            ],
            "pelvic_alignment": {
                "actor": "A",
                "target_actor": "B",
                "region": "pelvis",
                "target_distance_m": 0.075,
                "max_forward_shift_m": 0.10,
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
                {"actor": "A", "kind": "low_wide_hands_feet", "min_hip_z_m": 0.24, "max_hip_z_m": 0.56},
                {"actor": "B", "kind": "quadruped", "max_knee_joint_z_m": 0.23, "max_knee_angle_deg": 148, "min_hip_z_m": 0.26, "max_hip_z_m": 0.62, "min_head_z_m": 0.14},
            ],
        },
        "contacts": make_contacts("UFDG-WCHD-V00 Pass 02: fixed A-hand/B-arm impaling, raised B face clear of floor, straight long forward arms."),
    }

    # 3. UFDG-ELBW-V00 — True grounded elbows + horizontal forearms on floor, zero toe/wrist floor penetration
    specs["UFDG-ELBW-V00"] = {
        "expected_support": {
            "A": "both feet grounded wide in deep frog squat (never kneeling)",
            "B": "both knees and BOTH elbows/forearms resting flat on floor; head clearly above floor",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "UFDG-ELBW-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-02",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                # Pitched steeper forward so B's shoulders drop to ~0.27m — allowing elbows to rest squarely on the floor!
                {
                    "actor": "B",
                    "bone": "torso",
                    "space": "POSE_WORLD_HEAD_ROT_X_DEG",
                    "value": [0.0, 0.0, 0.45],
                    "pitch_x_deg": 126,
                },
                *front_kneeling_legs(foot_x=0.15, foot_y=0.38, foot_yaw=3, knee_x=0.16, knee_y=-0.68, knee_z=0.07, foot_z=0.088),
                # Horizontal forearms resting flat along the floor from elbow (y~-0.42, z~0.04) to wrist (y~-0.70, z~0.025)
                {
                    "actor": "B",
                    "bone": "hand_ik.L",
                    "space": "POSE_WORLD_HAND_FRAME",
                    "value": [0.16, -0.70, 0.026],
                    "direction_world": FLAT_FLOOR_DIR,
                    "normal_world": FLAT_FLOOR_NORM,
                },
                {
                    "actor": "B",
                    "bone": "hand_ik.R",
                    "space": "POSE_WORLD_HAND_FRAME",
                    "value": [-0.16, -0.70, 0.026],
                    "direction_world": FLAT_FLOOR_DIR,
                    "normal_world": FLAT_FLOOR_NORM,
                },
                # Elbow pole targets placed low & behind wrists so elbows bend DOWN directly onto floor
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.22, -0.34, 0.01]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.22, -0.34, 0.01]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -28},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -36},
                *rear_frog_squat_controls(
                    torso_y=0.42,
                    torso_z=0.41,
                    torso_pitch=82,
                    foot_x=0.38,
                    foot_y=0.42,
                    foot_yaw=26,
                    knee_x=0.96,
                    knee_y=-0.02,
                    knee_z=0.30,
                    elbow_x=0.56,
                    elbow_y=-0.16,
                    elbow_z=0.34,
                    hand_offset=(0.105, 0.10, 0.045),
                ),
            ],
            "styling_controls": [
                {"actor": "B", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -4},
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
                {"actor": "B", "region": "hands", "side": "L", "adjust_bone": "hand_ik.L", "target_z_m": 0.004, "tolerance_m": 0.024, "max_total_shift_m": 0.06, "iterations": 4},
                {"actor": "B", "region": "hands", "side": "R", "adjust_bone": "hand_ik.R", "target_z_m": 0.004, "tolerance_m": 0.024, "max_total_shift_m": 0.06, "iterations": 4},
            ],
            "pelvic_alignment": {
                "actor": "A",
                "target_actor": "B",
                "region": "pelvis",
                "target_distance_m": 0.065,
                "max_forward_shift_m": 0.10,
                "iterations": 6,
            },
            "support_assertions": [
                {"actor": "B", "region": "knees", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.030},
                {"actor": "B", "region": "knees", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.030},
                {"actor": "B", "region": "forearms", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "B", "region": "forearms", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "B", "region": "hands", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "B", "region": "hands", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
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
        "contacts": make_contacts("UFDG-ELBW-V00 Pass 02: lowered B shoulders for true grounded elbows/forearms, deeper A squat."),
    }

    # 4. UFDG-QUAD-V00 — Dramatically deeper A frog squat, grounded flat B palms, relaxed B elbow poles, cupped A palms
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
            "pass_label": "workspace-pass-02",
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
                {
                    "actor": "B",
                    "bone": "hand_ik.L",
                    "space": "POSE_WORLD_HAND_FRAME",
                    "value": [0.19, -0.49, 0.015],
                    "direction_world": FLAT_FLOOR_DIR,
                    "normal_world": FLAT_FLOOR_NORM,
                },
                {
                    "actor": "B",
                    "bone": "hand_ik.R",
                    "space": "POSE_WORLD_HAND_FRAME",
                    "value": [-0.19, -0.49, 0.015],
                    "direction_world": FLAT_FLOOR_DIR,
                    "normal_world": FLAT_FLOOR_NORM,
                },
                # Natural rear-facing elbow poles (reduces upper-arm twist banding)
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.24, -0.22, 0.25]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.24, -0.22, 0.25]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -28},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -34},
                # Much deeper rear frog squat (torso_z 0.58->0.44, pitch 58->72) to drop hip_z near knee height!
                *rear_frog_squat_controls(
                    torso_y=0.40,
                    torso_z=0.44,
                    torso_pitch=72,
                    foot_x=0.38,
                    foot_y=0.41,
                    foot_yaw=26,
                    knee_x=0.96,
                    knee_y=-0.04,
                    knee_z=0.34,
                    elbow_x=0.54,
                    elbow_y=-0.10,
                    elbow_z=0.48,
                    hand_offset=(0.10, 0.10, 0.04),
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
                {"actor": "B", "region": "hands", "side": "L", "adjust_bone": "hand_ik.L", "target_z_m": 0.004, "tolerance_m": 0.020, "max_total_shift_m": 0.12, "iterations": 6},
                {"actor": "B", "region": "hands", "side": "R", "adjust_bone": "hand_ik.R", "target_z_m": 0.004, "tolerance_m": 0.020, "max_total_shift_m": 0.12, "iterations": 6},
            ],
            "pelvic_alignment": {
                "actor": "A",
                "target_actor": "B",
                "region": "pelvis",
                "target_distance_m": 0.06,
                "max_forward_shift_m": 0.10,
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
                {"actor": "A", "kind": "low_wide_hands_feet", "min_hip_z_m": 0.28, "max_hip_z_m": 0.58},
                {"actor": "B", "kind": "quadruped", "max_knee_joint_z_m": 0.23, "max_knee_angle_deg": 148, "min_hip_z_m": 0.42, "max_hip_z_m": 0.78, "min_head_z_m": 0.34, "max_shoulder_to_hand_xy_m": 0.62},
            ],
        },
        "contacts": make_contacts("UFDG-QUAD-V00 Pass 02: deeper A squat, flat grounded B palms, cupped A shoulder palms."),
    }

    # 5. UFDG-FFRG-V00 — Route A forearms cleanly OVER/OUTSIDE B's raised knees, deepen A squat, flat B palms
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
            "pass_label": "workspace-pass-02",
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
                # Front wide flat-footed frog stance; knees opened wide & cleanly off floor (~0.34m) without blocking A's arms
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
                {
                    "actor": "B",
                    "bone": "hand_ik.L",
                    "space": "POSE_WORLD_HAND_FRAME",
                    "value": [0.22, -0.58, 0.018],
                    "direction_world": FLAT_FLOOR_DIR,
                    "normal_world": FLAT_FLOOR_NORM,
                },
                {
                    "actor": "B",
                    "bone": "hand_ik.R",
                    "space": "POSE_WORLD_HAND_FRAME",
                    "value": [-0.22, -0.58, 0.018],
                    "direction_world": FLAT_FLOOR_DIR,
                    "normal_world": FLAT_FLOOR_NORM,
                },
                # Relaxed elbow poles to remove upper-arm twist banding
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.28, -0.32, 0.22]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.28, -0.32, 0.22]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -24},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -30},
                # Deep rear frog squat with A's elbows lifted & routed cleanly OVER/OUTSIDE B's knees!
                *rear_frog_squat_controls(
                    torso_y=0.42,
                    torso_z=0.42,
                    torso_pitch=76,
                    foot_x=0.44,
                    foot_y=0.46,
                    foot_yaw=28,
                    knee_x=1.00,
                    knee_y=0.04,
                    knee_z=0.30,
                    elbow_x=0.66,
                    elbow_y=-0.06,
                    elbow_z=0.60,
                    hand_offset=(0.105, 0.10, 0.045),
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
                {"actor": "B", "region": "hands", "side": "L", "adjust_bone": "hand_ik.L", "target_z_m": 0.004, "tolerance_m": 0.022, "max_total_shift_m": 0.10, "iterations": 5},
                {"actor": "B", "region": "hands", "side": "R", "adjust_bone": "hand_ik.R", "target_z_m": 0.004, "tolerance_m": 0.022, "max_total_shift_m": 0.10, "iterations": 5},
            ],
            "pelvic_alignment": {
                "actor": "A",
                "target_actor": "B",
                "region": "pelvis",
                "target_distance_m": 0.06,
                "max_forward_shift_m": 0.10,
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
        "contacts": make_contacts("UFDG-FFRG-V00 Pass 02: cleared A forearm/B knee collision, deepened A squat, flat B palms."),
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
            "batch_id": "WORKSPACE-UFDG-V00-PASS02",
            "source_checkpoint": auth["source_checkpoint"],
            "source_id": auth["source_id"],
            "actor_mapping": {"ACTOR_1": "A", "ACTOR_2": "B"},
            "pose_name": row["pose_name"],
            "source_gate": row["generation_gate"],
            "source_complexity_pose": row.get("complexity_pose", ""),
            "specification": row["specification"],
            "approach": "Workspace experimental Pass 02 calibrated from Pass 01 blind visual QA audit (4.7/10).",
            "expected_support": sp["expected_support"],
            "pass_label": "pass-02",
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
        "pass_label": "pass-02",
        "family": "UFDG",
        "note": "Calibrated Pass 02 in workspace/ addressing Pass 01 blind QA findings.",
        "local_calibration": {"enabled": True, "max_refinement_attempts": 2},
        "poses": plan_poses,
    }
    plan_path = write_json_workspace(PASS_DIR / "plan.json", plan)
    print(json.dumps({"ok": True, "plan": workspace_rel(plan_path), "packages": created}, indent=2))


if __name__ == "__main__":
    main()
