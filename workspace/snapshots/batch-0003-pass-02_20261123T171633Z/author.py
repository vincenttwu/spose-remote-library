"""Author all 5 USDG V00 Pass 02 calibrated data-only pose packages inside workspace/.

Addresses all P0/P1/P2 findings from USDG Pass 01 blind QA (6.3/10):
- ALL 5 (P0): eliminate A-pelvis-to-B-buttocks clipping (+3.5cm Y spacing + bounded
  pelvic_alignment target 0.085m) and tuck A's wide-flaring elbows slightly inward.
- LOW (P0): keep B hips high (~0.95m, soft knees ~152 deg) + deeper fold (pitch=126 deg)
  so chest & head drop cleanly below hips; raise A knees out of crouch (129 -> ~150 deg).
- EDGE (P0): deepen B hip hinge (pitch=96 deg) with gentle lumbar lordosis so hips sit
  clearly above chest; soften B elbows (~150-160 deg) on ~0.80m horizontal edge.
- PULL (P1): lower B rearward arm path (~18cm lower, past outer hip line) to remove forced
  horizontal shoulder hyperextension and waist grazing.
- SURF (P1): elevate B hips slightly above chest with gentle lumbar arch while keeping
  coplanar chest + elbow + forearm tabletop contact; smooth B neck angle.
- WALL (P2): add natural slight elbow bend (~162-168 deg) while preserving level arms &
  vertical flat palms against virtual wall.
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

    # 1. USDG-EDGE-V00 — Deeper B hip hinge (hips clearly above chest!), gentle lumbar lordosis, soft B elbows, zero pelvis clip
    specs["USDG-EDGE-V00"] = {
        "expected_support": {
            "A": "both feet flat on floor (soft knees ~150 deg); close torso alignment without pelvis clipping; tucked elbows; palms at B outer shoulders",
            "B": "both feet flat on floor (soft knees ~155 deg); hips clearly higher than chest with gentle lumbar arch; soft-elbow palm brace on ~0.80m horizontal edge",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "USDG-EDGE-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-02",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "A", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                # Deeper hip hinge (pitch=96) so trunk angles gently down with hips higher than chest!
                {"actor": "B", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.0, 1.00], "pitch_x_deg": 96},
                *standing_feet("B", x=0.16, y=0.02, z=0.091, yaw=6, knee_x=0.18, knee_y=-0.52, knee_z=0.56),
                # Soft-elbow palm brace on ~0.80m waist-height horizontal edge
                {"actor": "B", "bone": "hand_ik.L", "space": "POSE_WORLD_HAND_FRAME", "value": [0.21, -0.60, 0.80], "direction_world": HORIZ_DIR, "normal_world": HORIZ_NORM_L},
                {"actor": "B", "bone": "hand_ik.R", "space": "POSE_WORLD_HAND_FRAME", "value": [-0.21, -0.60, 0.80], "direction_world": HORIZ_DIR, "normal_world": HORIZ_NORM_R},
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.34, -0.44, 0.94]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.34, -0.44, 0.94]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -30},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -30},
                # A shifted +0.05m rearward to eliminate pelvis-to-buttocks clipping while leaning closely over B's back
                {"actor": "A", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.35, 1.03], "pitch_x_deg": 62},
                *standing_feet("A", x=0.22, y=0.39, z=0.095, yaw=10, knee_x=0.26, knee_y=-0.08, knee_z=0.58),
                {"actor": "A", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.44, -0.06, 1.14]},
                {"actor": "A", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.44, -0.06, 1.14]},
                {"actor": "A", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -34},
                {"actor": "A", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -38},
                *rear_shoulder_hands(),
            ],
            "styling_controls": [
                {"actor": "B", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -18},
                {"actor": "A", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -12},
            ],
            "head_aim": {"actor": "B", "target_elevation_deg": 2, "max_delta_deg": 45, "reference": "RIG001_forward_-Y_world_rest_to_pose_delta", "objective": "face_forward_naturally"},
            "floor_calibration": standard_floor_calibration(),
            "pelvic_alignment": {"actor": "A", "target_actor": "B", "region": "pelvis", "target_distance_m": 0.085, "max_forward_shift_m": 0.03, "iterations": 5},
            "support_assertions": standard_support_assertions(),
            "posture_assertions": [
                {"actor": "A", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.85, "max_hip_z_m": 1.28},
                {"actor": "B", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.82, "max_hip_z_m": 1.24},
            ],
        },
        "contacts": make_contacts("USDG-EDGE-V00 Pass 02: deeper B hinge (hips > chest), soft B elbows, zero pelvis clip, tucked A elbows."),
    }

    # 2. USDG-SURF-V00 — Elevated B hips above chest + gentle lumbar arch + coplanar chest/forearm tabletop + smooth neck + zero pelvis clip
    specs["USDG-SURF-V00"] = {
        "expected_support": {
            "A": "both feet flat on floor (soft knees ~150 deg); close torso alignment without pelvis clipping; tucked elbows; palms at B outer shoulders",
            "B": "both feet flat on floor (soft knees ~155 deg); hips clearly higher than chest with gentle lumbar arch; chest & horizontal forearms coplanar on ~0.83m tabletop",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "USDG-SURF-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-02",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "A", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                # Slightly higher hips + deeper pitch (104) + lumbar extension (-18) -> hips clearly higher than tabletop chest!
                {"actor": "B", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.0, 1.01], "pitch_x_deg": 104},
                *standing_feet("B", x=0.16, y=0.02, z=0.091, yaw=6, knee_x=0.18, knee_y=-0.52, knee_z=0.56),
                {"actor": "B", "bone": "hand_ik.L", "space": "POSE_WORLD_HAND_FRAME", "value": [0.18, -0.78, 0.83], "direction_world": [0.0, -0.98, -0.20], "normal_world": [-0.30, 0.20, -0.93]},
                {"actor": "B", "bone": "hand_ik.R", "space": "POSE_WORLD_HAND_FRAME", "value": [-0.18, -0.78, 0.83], "direction_world": [0.0, -0.98, -0.20], "normal_world": [0.30, 0.20, -0.93]},
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.34, -0.48, 0.81]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.34, -0.48, 0.81]},
                # Distribute neck+head extension smoothly (no -60 deg single-joint kink!)
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -36},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -28},
                {"actor": "A", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.36, 1.03], "pitch_x_deg": 66},
                *standing_feet("A", x=0.22, y=0.40, z=0.095, yaw=10, knee_x=0.26, knee_y=-0.06, knee_z=0.58),
                {"actor": "A", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.44, -0.06, 1.10]},
                {"actor": "A", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.44, -0.06, 1.10]},
                {"actor": "A", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -34},
                {"actor": "A", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -38},
                *rear_shoulder_hands(),
            ],
            "styling_controls": [
                {"actor": "B", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -18},
                {"actor": "A", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -12},
            ],
            "head_aim": {"actor": "B", "target_elevation_deg": -2, "max_delta_deg": 35, "reference": "RIG001_forward_-Y_world_rest_to_pose_delta", "objective": "smooth_neck_clear_of_tabletop"},
            "floor_calibration": standard_floor_calibration(),
            "pelvic_alignment": {"actor": "A", "target_actor": "B", "region": "pelvis", "target_distance_m": 0.085, "max_forward_shift_m": 0.03, "iterations": 5},
            "support_assertions": standard_support_assertions(),
            "posture_assertions": [
                {"actor": "A", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.85, "max_hip_z_m": 1.28},
                {"actor": "B", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.82, "max_hip_z_m": 1.24},
            ],
        },
        "contacts": make_contacts("USDG-SURF-V00 Pass 02: zero pelvis clip, hips elevated above tabletop chest with lumbar arch, smooth B neck."),
    }

    # 3. USDG-WALL-V00 — Keep vertical wall read, soften B's locked elbows (~165 deg), eliminate pelvis clip, tuck A elbows
    specs["USDG-WALL-V00"] = {
        "expected_support": {
            "A": "both feet flat on floor (soft knees ~150 deg); closer torso alignment without pelvis clipping; tucked elbows; palms at B outer shoulders",
            "B": "both feet flat on floor (soft knees ~152 deg); level arms with slight soft elbow bend pressing vertical flat palms against wall (y=-0.74m)",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "USDG-WALL-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-02",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "A", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "B", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.0, 0.99], "pitch_x_deg": 68},
                *standing_feet("B", x=0.16, y=0.02, z=0.091, yaw=6, knee_x=0.18, knee_y=-0.52, knee_z=0.56),
                # Pull hands 6cm closer to y=-0.74m so elbows gain a natural soft weight-bearing bend (~164 deg)!
                {"actor": "B", "bone": "hand_ik.L", "space": "POSE_WORLD_HAND_FRAME", "value": [0.22, -0.74, 1.15], "direction_world": [0.0, 0.0, 1.0], "normal_world": [0.0, -1.0, 0.0]},
                {"actor": "B", "bone": "hand_ik.R", "space": "POSE_WORLD_HAND_FRAME", "value": [-0.22, -0.74, 1.15], "direction_world": [0.0, 0.0, 1.0], "normal_world": [0.0, -1.0, 0.0]},
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.36, -0.52, 1.04]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.36, -0.52, 1.04]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -24},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -28},
                {"actor": "A", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.35, 1.03], "pitch_x_deg": 56},
                *standing_feet("A", x=0.22, y=0.39, z=0.095, yaw=10, knee_x=0.26, knee_y=-0.08, knee_z=0.58),
                {"actor": "A", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.44, -0.02, 1.24]},
                {"actor": "A", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.44, -0.02, 1.24]},
                {"actor": "A", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -32},
                {"actor": "A", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -36},
                *rear_shoulder_hands(),
            ],
            "styling_controls": [
                {"actor": "B", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -14},
                {"actor": "A", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -12},
            ],
            "head_aim": {"actor": "B", "target_elevation_deg": 6, "max_delta_deg": 55, "reference": "RIG001_forward_-Y_world_rest_to_pose_delta", "objective": "face_wall_naturally"},
            "floor_calibration": standard_floor_calibration(),
            "pelvic_alignment": {"actor": "A", "target_actor": "B", "region": "pelvis", "target_distance_m": 0.085, "max_forward_shift_m": 0.03, "iterations": 5},
            "support_assertions": standard_support_assertions(),
            "posture_assertions": [
                {"actor": "A", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.85, "max_hip_z_m": 1.28},
                {"actor": "B", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.82, "max_hip_z_m": 1.24},
            ],
        },
        "contacts": make_contacts("USDG-WALL-V00 Pass 02: zero pelvis clip, softer B elbows on vertical wall, tucked A elbows."),
    }

    # 4. USDG-LOW-V00 — High B hips (~0.95m, soft knees ~152 deg) + deep hip fold (pitch=128 deg) so chest & head drop cleanly below hips; A standing tall (~150 deg)!
    specs["USDG-LOW-V00"] = {
        "expected_support": {
            "A": "both feet flat on floor (standing with soft knees ~148-154 deg, NOT crouching); deep hip hinge over B; zero pelvis clip; palms at B outer shoulders",
            "B": "both feet flat on floor (standing with soft knees ~152 deg); high hips (~0.95m) with deep forward hip fold (chest & head substantially below hips); palms on knee-height ~0.50m plane",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "USDG-LOW-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-02",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "A", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                # Keep B hips high (torso_z=1.00) while folding deeply at hips (pitch=128) -> chest & head drop >18cm below hips!
                {"actor": "B", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.0, 1.00], "pitch_x_deg": 128},
                *standing_feet("B", x=0.17, y=0.02, z=0.091, yaw=6, knee_x=0.19, knee_y=-0.52, knee_z=0.56),
                {"actor": "B", "bone": "hand_ik.L", "space": "POSE_WORLD_HAND_FRAME", "value": [0.21, -0.64, 0.50], "direction_world": HORIZ_DIR, "normal_world": HORIZ_NORM_L},
                {"actor": "B", "bone": "hand_ik.R", "space": "POSE_WORLD_HAND_FRAME", "value": [-0.21, -0.64, 0.50], "direction_world": HORIZ_DIR, "normal_world": HORIZ_NORM_R},
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.30, -0.50, 0.70]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.30, -0.50, 0.70]},
                # Smooth neck+head angle without sharp pinch
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -32},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -26},
                # Raise A torso to 1.02m so A stands cleanly (knees ~150 deg instead of 129 deg crouch!) and hinges forward over B
                {"actor": "A", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.36, 1.02], "pitch_x_deg": 76},
                *standing_feet("A", x=0.23, y=0.40, z=0.095, yaw=10, knee_x=0.26, knee_y=-0.06, knee_z=0.58),
                {"actor": "A", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.46, -0.10, 0.98]},
                {"actor": "A", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.46, -0.10, 0.98]},
                {"actor": "A", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -36},
                {"actor": "A", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -40},
                *rear_shoulder_hands(),
            ],
            "styling_controls": [
                {"actor": "B", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -12},
                {"actor": "A", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -12},
            ],
            "head_aim": {"actor": "B", "target_elevation_deg": -16, "max_delta_deg": 35, "reference": "RIG001_forward_-Y_world_rest_to_pose_delta", "objective": "deep_fold_smooth_neck"},
            "floor_calibration": standard_floor_calibration(),
            "pelvic_alignment": {"actor": "A", "target_actor": "B", "region": "pelvis", "target_distance_m": 0.085, "max_forward_shift_m": 0.03, "iterations": 5},
            "support_assertions": standard_support_assertions(),
            "posture_assertions": [
                {"actor": "A", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.82, "max_hip_z_m": 1.26},
                {"actor": "B", "kind": "forward_fold_standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.80, "max_hip_z_m": 1.22, "min_head_drop_below_hip_m": 0.10},
            ],
        },
        "contacts": make_contacts("USDG-LOW-V00 Pass 02: high B hips + deep forward fold, A standing soft knees (no crouch), zero pelvis clip."),
    }

    # 5. USDG-PULL-V00 — Lower B's rearward arm path cleanly past outer hips (no forced shoulder hyperextension!), zero pelvis clip
    specs["USDG-PULL-V00"] = {
        "expected_support": {
            "A": "both feet flat on floor (soft knees ~150 deg); closer torso alignment without pelvis clipping; tucked elbows; palms at B outer shoulders",
            "B": "both feet flat on floor (independent weight bearing, NO front support); BOTH arms angle naturally down-back past outer hips onto A's lower outer flanks/hips",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "USDG-PULL-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-02",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "A", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "B", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.0, 0.99], "pitch_x_deg": 68},
                *standing_feet("B", x=0.17, y=0.02, z=0.091, yaw=6, knee_x=0.19, knee_y=-0.52, knee_z=0.56),
                # Drop B's elbows DOWN & slightly wider outside hips so B's arms drop naturally past outer hip line (zero forced shoulder hyperextension!)
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.42, -0.26, 0.80]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.42, -0.26, 0.80]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -24},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -28},
                {"actor": "A", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.35, 1.03], "pitch_x_deg": 56},
                *standing_feet("A", x=0.22, y=0.39, z=0.095, yaw=10, knee_x=0.26, knee_y=-0.08, knee_z=0.58),
                {"actor": "A", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.46, -0.04, 1.24]},
                {"actor": "A", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.46, -0.04, 1.24]},
                {"actor": "A", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -32},
                {"actor": "A", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -36},
                # B hands drop ~18cm lower past B's outer hips onto A's outer lower flanks/hips!
                {
                    "actor": "B",
                    "bone": "hand_ik.L",
                    "space": "POSE_RELATIVE_BONE_HEAD_HAND",
                    "value": [0.22, -0.02, -0.18],
                    "target_actor": "A",
                    "target_bone": "hips",
                    "direction_world": [-0.15, 0.92, -0.36],
                    "normal_world": [-0.94, -0.22, -0.24],
                },
                {
                    "actor": "B",
                    "bone": "hand_ik.R",
                    "space": "POSE_RELATIVE_BONE_HEAD_HAND",
                    "value": [-0.22, -0.02, -0.18],
                    "target_actor": "A",
                    "target_bone": "hips",
                    "direction_world": [0.15, 0.92, -0.36],
                    "normal_world": [0.94, -0.22, -0.24],
                },
                *rear_shoulder_hands(offset=(0.118, 0.08, 0.05)),
            ],
            "styling_controls": [
                {"actor": "B", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -14},
                {"actor": "A", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -12},
            ],
            "head_aim": {"actor": "B", "target_elevation_deg": 6, "max_delta_deg": 55, "reference": "RIG001_forward_-Y_world_rest_to_pose_delta", "objective": "face_forward_naturally"},
            "floor_calibration": standard_floor_calibration(),
            "pelvic_alignment": {"actor": "A", "target_actor": "B", "region": "pelvis", "target_distance_m": 0.085, "max_forward_shift_m": 0.03, "iterations": 5},
            "support_assertions": standard_support_assertions(),
            "posture_assertions": [
                {"actor": "A", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.85, "max_hip_z_m": 1.28},
                {"actor": "B", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.82, "max_hip_z_m": 1.24},
            ],
        },
        "contacts": make_contacts(
            "USDG-PULL-V00 Pass 02: lowered B rearward arm path cleanly past outer hips (zero hyperextension), zero pelvis clip.",
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
            "batch_id": "WORKSPACE-USDG-V00-PASS02",
            "source_checkpoint": auth["source_checkpoint"],
            "source_id": auth["source_id"],
            "actor_mapping": {"ACTOR_1": "A", "ACTOR_2": "B"},
            "pose_name": row["pose_name"],
            "source_gate": row["generation_gate"],
            "source_complexity_pose": row.get("complexity_pose", ""),
            "specification": row["specification"],
            "approach": "Workspace experimental Pass 02 calibrated from USDG Pass 01 blind QA (6.3/10).",
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
        "batch_label": "workspace-usdg",
        "pass_label": "pass-02",
        "family": "USDG",
        "note": "Calibrated USDG Pass 02 in workspace/ addressing all Pass 01 blind QA findings.",
        "local_calibration": {"enabled": True, "max_refinement_attempts": 2},
        "poses": plan_poses,
    }
    plan_path = write_json_workspace(PASS_DIR / "plan.json", plan)
    print(json.dumps({"ok": True, "plan": workspace_rel(plan_path), "packages": created}, indent=2))


if __name__ == "__main__":
    main()
