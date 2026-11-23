"""Author all 5 USDG V00 Pass 01 data-only pose packages inside workspace/.

Standing hinge family (carries forward UADG Pass 02 calibration lessons:
softly flexed standing knees ~150-160 deg, close A torso alignment with clean
head clearance, and clean outer-shoulder palm clearance with zero fingertip bleed):
- USDG-EDGE-V00: Waist-height horizontal edge palm brace (~0.80m)
- USDG-SURF-V00: Broad waist-height tabletop supporting B's chest + horizontal forearms (~0.84m)
- USDG-WALL-V00: Vertical wall brace with B arms level/parallel to floor (y=-0.80m, z=1.16m)
- USDG-LOW-V00:  Deep standing forward fold bracing a low knee-height surface (~0.50m)
- USDG-PULL-V00: Hands-back standing hinge — B arms reach rearward past outer hips to A's flanks;
                 A arms reach forward outside/over to hold B's outer shoulders/upper arms
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
    "USDG-EDGE-V00",
    "USDG-SURF-V00",
    "USDG-WALL-V00",
    "USDG-LOW-V00",
    "USDG-PULL-V00",
]

# Flat horizontal edge/surface palm frame for Actor B
HORIZ_DIR = [0.0, -0.96, -0.28]
HORIZ_NORM_L = [-0.32, 0.28, -0.90]
HORIZ_NORM_R = [0.32, 0.28, -0.90]


def standing_feet(actor: str, x: float, y: float, z: float, yaw: float, knee_x: float, knee_y: float, knee_z: float) -> list[dict]:
    return [
        {"actor": actor, "bone": "foot_ik.L", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [x, y, z], "pitch_x_deg": 0, "yaw_z_deg": yaw},
        {"actor": actor, "bone": "foot_ik.R", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [-x, y, z], "pitch_x_deg": 0, "yaw_z_deg": -yaw},
        {"actor": actor, "bone": "thigh_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [knee_x, knee_y, knee_z]},
        {"actor": actor, "bone": "thigh_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-knee_x, knee_y, knee_z]},
    ]


def rear_shoulder_hands(offset: tuple[float, float, float] = (0.118, 0.08, 0.045)) -> list[dict]:
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
                "direction_world": [-0.42 * sign, -0.84, -0.34],
                "normal_world": [-0.82 * sign, 0.22, -0.53],
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

    # 1. USDG-EDGE-V00 — Edge-supported standing hinge (~0.80m horizontal edge)
    specs["USDG-EDGE-V00"] = {
        "expected_support": {
            "A": "both feet flat on floor (softly flexed knees ~155 deg); close forward torso lean; palms at B outer shoulders",
            "B": "both feet flat on floor (softly flexed knees ~155 deg); palms bracing waist-height horizontal edge (~0.82m), elbows soft",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "USDG-EDGE-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-01",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "A", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "B", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.0, 0.99], "pitch_x_deg": 76},
                *standing_feet("B", x=0.16, y=0.02, z=0.091, yaw=6, knee_x=0.18, knee_y=-0.52, knee_z=0.56),
                {"actor": "B", "bone": "hand_ik.L", "space": "POSE_WORLD_HAND_FRAME", "value": [0.21, -0.68, 0.82], "direction_world": HORIZ_DIR, "normal_world": HORIZ_NORM_L},
                {"actor": "B", "bone": "hand_ik.R", "space": "POSE_WORLD_HAND_FRAME", "value": [-0.21, -0.68, 0.82], "direction_world": HORIZ_DIR, "normal_world": HORIZ_NORM_R},
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.30, -0.46, 1.02]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.30, -0.46, 1.02]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -26},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -30},
                {"actor": "A", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.30, 1.02], "pitch_x_deg": 56},
                *standing_feet("A", x=0.22, y=0.34, z=0.095, yaw=10, knee_x=0.26, knee_y=-0.12, knee_z=0.58),
                {"actor": "A", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.54, -0.04, 1.20]},
                {"actor": "A", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.54, -0.04, 1.20]},
                {"actor": "A", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -32},
                {"actor": "A", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -36},
                *rear_shoulder_hands(),
            ],
            "styling_controls": [
                {"actor": "B", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -12},
                {"actor": "A", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -12},
            ],
            "head_aim": {"actor": "B", "target_elevation_deg": 6, "max_delta_deg": 60, "reference": "RIG001_forward_-Y_world_rest_to_pose_delta", "objective": "face_forward_naturally"},
            "floor_calibration": standard_floor_calibration(),
            "pelvic_alignment": {"actor": "A", "target_actor": "B", "region": "pelvis", "target_distance_m": 0.06, "max_forward_shift_m": 0.10, "iterations": 6},
            "support_assertions": standard_support_assertions(),
            "posture_assertions": [
                {"actor": "A", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.85, "max_hip_z_m": 1.28},
                {"actor": "B", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.80, "max_hip_z_m": 1.24},
            ],
        },
        "contacts": make_contacts("USDG-EDGE-V00 Pass 01: waist-height horizontal edge palm brace; soft standing knees; aligned upper torsos."),
    }

    # 2. USDG-SURF-V00 — Torso-supported standing hinge (chest + horizontal forearms on broad ~0.85m tabletop)
    specs["USDG-SURF-V00"] = {
        "expected_support": {
            "A": "both feet flat on floor (softly flexed knees); close forward torso lean; palms at B outer shoulders",
            "B": "both feet flat on floor (softly flexed knees); chest, upper torso, and BOTH elbows/forearms resting horizontally on broad ~0.85m tabletop; hips elevated above chest",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "USDG-SURF-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-01",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "A", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                # Deeper fold (pitch=94) so B's chest drops onto ~0.86m tabletop while hips remain higher (~1.00m)!
                {"actor": "B", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.0, 0.99], "pitch_x_deg": 94},
                *standing_feet("B", x=0.16, y=0.02, z=0.091, yaw=6, knee_x=0.18, knee_y=-0.52, knee_z=0.56),
                # Forearms & hands resting flat along the ~0.86m tabletop plane (elbows at z=0.86, wrists at z=0.86)
                {"actor": "B", "bone": "hand_ik.L", "space": "POSE_WORLD_HAND_FRAME", "value": [0.18, -0.78, 0.86], "direction_world": [0.0, -0.98, -0.20], "normal_world": [-0.30, 0.20, -0.93]},
                {"actor": "B", "bone": "hand_ik.R", "space": "POSE_WORLD_HAND_FRAME", "value": [-0.18, -0.78, 0.86], "direction_world": [0.0, -0.98, -0.20], "normal_world": [0.30, 0.20, -0.93]},
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.34, -0.48, 0.84]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.34, -0.48, 0.84]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -28},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -34},
                {"actor": "A", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.30, 1.01], "pitch_x_deg": 66},
                *standing_feet("A", x=0.22, y=0.34, z=0.095, yaw=10, knee_x=0.26, knee_y=-0.12, knee_z=0.58),
                {"actor": "A", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.54, -0.06, 1.12]},
                {"actor": "A", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.54, -0.06, 1.12]},
                {"actor": "A", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -34},
                {"actor": "A", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -38},
                *rear_shoulder_hands(),
            ],
            "styling_controls": [
                {"actor": "B", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -10},
                {"actor": "A", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -12},
            ],
            "head_aim": {"actor": "B", "target_elevation_deg": 4, "max_delta_deg": 60, "reference": "RIG001_forward_-Y_world_rest_to_pose_delta", "objective": "face_forward_clear_of_tabletop"},
            "floor_calibration": standard_floor_calibration(),
            "pelvic_alignment": {"actor": "A", "target_actor": "B", "region": "pelvis", "target_distance_m": 0.065, "max_forward_shift_m": 0.10, "iterations": 6},
            "support_assertions": standard_support_assertions(),
            "posture_assertions": [
                {"actor": "A", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.85, "max_hip_z_m": 1.28},
                {"actor": "B", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.80, "max_hip_z_m": 1.24},
            ],
        },
        "contacts": make_contacts("USDG-SURF-V00 Pass 01: chest & horizontal forearms on broad ~0.86m tabletop; hips elevated above chest."),
    }

    # 3. USDG-WALL-V00 — Wall-supported standing hinge (arms level/parallel to floor bracing vertical wall at y=-0.80m)
    specs["USDG-WALL-V00"] = {
        "expected_support": {
            "A": "both feet flat on floor (softly flexed knees); close forward torso lean; palms at B outer shoulders",
            "B": "both feet flat on floor (softly flexed knees); arms level/parallel to floor bracing both palms flat against vertical wall (y=-0.80m, fingers up)",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "USDG-WALL-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-01",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "A", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "B", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.0, 0.99], "pitch_x_deg": 66},
                *standing_feet("B", x=0.16, y=0.02, z=0.091, yaw=6, knee_x=0.18, knee_y=-0.52, knee_z=0.56),
                # Level arms parallel to floor (z=1.18m) pressing palms flat against vertical wall at y=-0.80m (fingers UP +Z, palm normal -Y!)
                {"actor": "B", "bone": "hand_ik.L", "space": "POSE_WORLD_HAND_FRAME", "value": [0.22, -0.80, 1.18], "direction_world": [0.0, 0.0, 1.0], "normal_world": [0.0, -1.0, 0.0]},
                {"actor": "B", "bone": "hand_ik.R", "space": "POSE_WORLD_HAND_FRAME", "value": [-0.22, -0.80, 1.18], "direction_world": [0.0, 0.0, 1.0], "normal_world": [0.0, -1.0, 0.0]},
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.34, -0.54, 1.12]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.34, -0.54, 1.12]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -24},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -28},
                {"actor": "A", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.30, 1.02], "pitch_x_deg": 50},
                *standing_feet("A", x=0.22, y=0.34, z=0.095, yaw=10, knee_x=0.26, knee_y=-0.12, knee_z=0.58),
                {"actor": "A", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.54, -0.02, 1.26]},
                {"actor": "A", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.54, -0.02, 1.26]},
                {"actor": "A", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -30},
                {"actor": "A", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -34},
                *rear_shoulder_hands(),
            ],
            "styling_controls": [
                {"actor": "B", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -12},
                {"actor": "A", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -12},
            ],
            "head_aim": {"actor": "B", "target_elevation_deg": 6, "max_delta_deg": 60, "reference": "RIG001_forward_-Y_world_rest_to_pose_delta", "objective": "face_wall_naturally"},
            "floor_calibration": standard_floor_calibration(),
            "pelvic_alignment": {"actor": "A", "target_actor": "B", "region": "pelvis", "target_distance_m": 0.06, "max_forward_shift_m": 0.10, "iterations": 6},
            "support_assertions": standard_support_assertions(),
            "posture_assertions": [
                {"actor": "A", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.85, "max_hip_z_m": 1.28},
                {"actor": "B", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.80, "max_hip_z_m": 1.24},
            ],
        },
        "contacts": make_contacts("USDG-WALL-V00 Pass 01: arms level/parallel to floor bracing vertical wall at y=-0.80m."),
    }

    # 4. USDG-LOW-V00 — Low-surface standing hinge (deep fold bracing knee-height ~0.50m surface; both remain standing)
    specs["USDG-LOW-V00"] = {
        "expected_support": {
            "A": "both feet flat on floor (standing, knees flexed slightly to follow lowered hip height); palms at B outer shoulders",
            "B": "both feet flat on floor (standing, softly flexed knees, never kneeling); deeper hip hinge with chest substantially below hips; palms braced on knee-height surface (~0.50m)",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "USDG-LOW-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-01",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "A", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                # Deeper standing forward fold (pitch=110) so chest is substantially below hips while staying standing!
                {"actor": "B", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.0, 0.96], "pitch_x_deg": 110},
                *standing_feet("B", x=0.17, y=0.02, z=0.091, yaw=6, knee_x=0.19, knee_y=-0.52, knee_z=0.54),
                {"actor": "B", "bone": "hand_ik.L", "space": "POSE_WORLD_HAND_FRAME", "value": [0.21, -0.66, 0.50], "direction_world": HORIZ_DIR, "normal_world": HORIZ_NORM_L},
                {"actor": "B", "bone": "hand_ik.R", "space": "POSE_WORLD_HAND_FRAME", "value": [-0.21, -0.66, 0.50], "direction_world": HORIZ_DIR, "normal_world": HORIZ_NORM_R},
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.30, -0.50, 0.72]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.30, -0.50, 0.72]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -28},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -34},
                {"actor": "A", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.30, 0.96], "pitch_x_deg": 70},
                *standing_feet("A", x=0.24, y=0.34, z=0.095, yaw=12, knee_x=0.28, knee_y=-0.12, knee_z=0.54),
                {"actor": "A", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.54, -0.08, 1.00]},
                {"actor": "A", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.54, -0.08, 1.00]},
                {"actor": "A", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -34},
                {"actor": "A", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -38},
                *rear_shoulder_hands(),
            ],
            "styling_controls": [
                {"actor": "B", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -8},
                {"actor": "A", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -12},
            ],
            "head_aim": {"actor": "B", "target_elevation_deg": -8, "max_delta_deg": 60, "reference": "RIG001_forward_-Y_world_rest_to_pose_delta", "objective": "face_forward_low_fold"},
            "floor_calibration": standard_floor_calibration(),
            "pelvic_alignment": {"actor": "A", "target_actor": "B", "region": "pelvis", "target_distance_m": 0.065, "max_forward_shift_m": 0.10, "iterations": 6},
            "support_assertions": standard_support_assertions(),
            "posture_assertions": [
                {"actor": "A", "kind": "standing", "min_knee_joint_z_m": 0.32, "min_hip_z_m": 0.78, "max_hip_z_m": 1.24},
                {"actor": "B", "kind": "forward_fold_standing", "min_knee_joint_z_m": 0.32, "min_hip_z_m": 0.74, "max_hip_z_m": 1.20, "min_head_drop_below_hip_m": 0.08},
            ],
        },
        "contacts": make_contacts("USDG-LOW-V00 Pass 01: deep standing fold bracing knee-height ~0.50m surface; both remain standing."),
    }

    # 5. USDG-PULL-V00 — Rear-assisted hands-back standing hinge (NO front support; B arms reach rearward past hips to A's flanks!)
    specs["USDG-PULL-V00"] = {
        "expected_support": {
            "A": "both feet flat on floor (softly flexed knees); upper-arm/shoulder receiving hold on B's outer shoulders (routed cleanly above B's rearward arms)",
            "B": "both feet flat on floor (independently bearing weight, NO front hand/wall support); BOTH arms directed rearward past outer hip line to A's outer flanks/back",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "USDG-PULL-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-01",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "A", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "B", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.0, 0.99], "pitch_x_deg": 66},
                *standing_feet("B", x=0.17, y=0.02, z=0.091, yaw=6, knee_x=0.19, knee_y=-0.52, knee_z=0.56),
                # B elbows routed cleanly OUTSIDE B's hips so B's arms travel rearward to A's outer flanks with ZERO hip clipping!
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.40, -0.22, 0.96]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.40, -0.22, 0.96]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -24},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -28},
                {"actor": "A", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.30, 1.02], "pitch_x_deg": 50},
                *standing_feet("A", x=0.22, y=0.34, z=0.095, yaw=10, knee_x=0.26, knee_y=-0.12, knee_z=0.58),
                # A elbows higher/wider so A's arms pass cleanly ABOVE B's rearward arms!
                {"actor": "A", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.56, -0.04, 1.30]},
                {"actor": "A", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.56, -0.04, 1.30]},
                {"actor": "A", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -30},
                {"actor": "A", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -34},
                # B hands reach rearward past outer hip line onto A's outer flanks/hips (palms facing inward onto A's flanks!)
                {
                    "actor": "B",
                    "bone": "hand_ik.L",
                    "space": "POSE_RELATIVE_BONE_HEAD_HAND",
                    "value": [0.22, -0.02, -0.02],
                    "target_actor": "A",
                    "target_bone": "hips",
                    "direction_world": [-0.15, 0.96, 0.22],
                    "normal_world": [-0.96, -0.18, 0.20],
                },
                {
                    "actor": "B",
                    "bone": "hand_ik.R",
                    "space": "POSE_RELATIVE_BONE_HEAD_HAND",
                    "value": [-0.22, -0.02, -0.02],
                    "target_actor": "A",
                    "target_bone": "hips",
                    "direction_world": [0.15, 0.96, 0.22],
                    "normal_world": [0.96, -0.18, 0.20],
                },
                *rear_shoulder_hands(offset=(0.118, 0.08, 0.05)),
            ],
            "styling_controls": [
                {"actor": "B", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -12},
                {"actor": "A", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -12},
            ],
            "head_aim": {"actor": "B", "target_elevation_deg": 6, "max_delta_deg": 60, "reference": "RIG001_forward_-Y_world_rest_to_pose_delta", "objective": "face_forward_naturally"},
            "floor_calibration": standard_floor_calibration(),
            "pelvic_alignment": {"actor": "A", "target_actor": "B", "region": "pelvis", "target_distance_m": 0.06, "max_forward_shift_m": 0.10, "iterations": 6},
            "support_assertions": standard_support_assertions(),
            "posture_assertions": [
                {"actor": "A", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.85, "max_hip_z_m": 1.28},
                {"actor": "B", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.80, "max_hip_z_m": 1.24},
            ],
        },
        "contacts": make_contacts(
            "USDG-PULL-V00 Pass 01: hands-back standing hinge — B arms reach rearward past hips to A flanks; A holds B outer shoulders.",
            extra_anchors=[
                {"id": "front_left_hand_to_rear_flank", "actor": "B", "bone": "hand_ik.L", "target_actor": "A", "target_bone": "hips", "tolerance_m": 0.30},
                {"id": "front_right_hand_to_rear_flank", "actor": "B", "bone": "hand_ik.R", "target_actor": "A", "target_bone": "hips", "tolerance_m": 0.30},
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
            "batch_id": "WORKSPACE-USDG-V00-PASS01",
            "source_checkpoint": auth["source_checkpoint"],
            "source_id": auth["source_id"],
            "actor_mapping": {"ACTOR_1": "A", "ACTOR_2": "B"},
            "pose_name": row["pose_name"],
            "source_gate": row["generation_gate"],
            "source_complexity_pose": row.get("complexity_pose", ""),
            "specification": row["specification"],
            "approach": "Workspace experimental Pass 01 authoring for USDG standing hinge family, seeded with UADG standing calibration lessons.",
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
        "batch_label": "workspace-usdg",
        "pass_label": "pass-01",
        "family": "USDG",
        "note": "Experimental backward-roadmap batch #3 (USDG, 5 poses) in workspace/.",
        "local_calibration": {"enabled": True, "max_refinement_attempts": 2},
        "poses": plan_poses,
    }
    plan_path = write_json_workspace(PASS_DIR / "plan.json", plan)
    print(json.dumps({"ok": True, "plan": workspace_rel(plan_path), "packages": created}, indent=2))


if __name__ == "__main__":
    main()
