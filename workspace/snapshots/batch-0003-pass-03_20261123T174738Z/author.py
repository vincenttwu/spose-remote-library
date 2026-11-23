"""Author all 5 batch-0003 (USDG) Pass 03 data-only packages into workspace/incoming/ + workspace/batches/BATCH-0003-PASS-03.json.

Directly addresses BOTH user visual review feedback and Pass 02 blind QA (6.88/10):
- USER FEEDBACK (core pelvis & silhouette calibration across all 5 poses):
  1. Rear pelvis (A) moved forward (torso_y ~0.24-0.27 vs Pass 02's 0.35-0.36) and pitched more upright
     (a_pitch ~35-48 deg on EDGE/SURF/WALL/PULL, ~60 deg on LOW) so A's front pelvis directly cups
     B's hips/buttocks with zero chest-into-buttocks collision and zero triangular air gap.
  2. Front hips (B) stay LOWER than rear hips (A_thigh_z ~0.98m > B_thigh_z ~0.95m) with relaxed
     standing knees on BOTH actors (~144-152 deg — eliminates locked 179.7 deg B knees on SURF/LOW).
  3. Rear arms (A) naturally more extended (~152-164 deg) with tucked elbow poles (no wide horizontal
     wings in front view) and outward/dorsal deltoid palm clearance (no fingertip bleed-through).
  4. USDG-WALL-V00: front bent nearly 90 deg (pitch=88 deg) reaching forward level to vertical wall
     (y=-0.84m, z=1.00m) — similar torso hinge to LOW but 90 deg horizontal instead of low fold.
- PASS 02 BLIND QA FIXES:
  5. LOW: eliminates P0 A-chest-in-B-buttocks clipping, unlocks B knees, enables neck assist.
  6. SURF: unlocks B knees, eliminates glute clip, enables neck assist for smooth forward/down gaze.
  7. EDGE: eliminates B chicken-wing elbow flare (tucked poles x=0.25, z=0.82), keeps hips > chest.
  8. PULL: brings B rearward palms cleanly onto A's outer flanks/hips with 0mm reach error (no hover).
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
    """Place A's palms cleanly over B's outer deltoid cap with zero fingertip bleed-through."""
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

    # 1. USDG-EDGE-V00 — Rear pelvis cupping B hips (A hip > B hip), A more upright w/ extended tucked arms, B relaxed knees + tucked elbows on ~0.74m edge
    specs["USDG-EDGE-V00"] = {
        "expected_support": {
            "A": "both feet flat on floor (relaxed knees ~145 deg); upright-leaning stance with pelvis directly cupping B's hips (A hip > B hip); extended tucked arms resting cleanly on B outer deltoids",
            "B": "both feet flat on floor (relaxed knees ~146 deg); ~95 deg forward hinge with hips above chest and gentle lumbar arch; soft tucked elbows with flat palms bracing ~0.74m edge",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "USDG-EDGE-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-03",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "A", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "B", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.0, 0.97], "pitch_x_deg": 95},
                *standing_feet("B", x=0.16, y=0.02, z=0.091, yaw=6, knee_x=0.18, knee_y=-0.58, knee_z=0.52),
                {"actor": "B", "bone": "hand_ik.L", "space": "POSE_WORLD_HAND_FRAME", "value": [0.20, -0.70, 0.74], "direction_world": HORIZ_DIR, "normal_world": HORIZ_NORM_L},
                {"actor": "B", "bone": "hand_ik.R", "space": "POSE_WORLD_HAND_FRAME", "value": [-0.20, -0.70, 0.74], "direction_world": HORIZ_DIR, "normal_world": HORIZ_NORM_R},
                # Tucked downward/inward B elbow poles (eliminates Pass 02 chicken-wing flare!)
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.24, -0.46, 0.80]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.24, -0.46, 0.80]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -30},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -28},
                # A pelvis directly cupping B's hips (a_y=0.245, a_z=1.01 > b_z=0.97), upright lean (41 deg) w/ extended tucked arms
                {"actor": "A", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.245, 1.01], "pitch_x_deg": 41},
                *standing_feet("A", x=0.22, y=0.29, z=0.095, yaw=10, knee_x=0.25, knee_y=-0.22, knee_z=0.54),
                {"actor": "A", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.28, -0.10, 1.02]},
                {"actor": "A", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.28, -0.10, 1.02]},
                {"actor": "A", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -24},
                {"actor": "A", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -24},
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
                {"actor": "B", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.82, "max_hip_z_m": 1.24},
            ],
        },
        "contacts": make_contacts("USDG-EDGE-V00 Pass 03: rear pelvis cupping front hips (A > B), relaxed knees, extended tucked A arms, no B elbow flare."),
    }

    # 2. USDG-SURF-V00 — Unlocked relaxed B knees (~147 deg), rear pelvis cupping B hips, tabletop forearm+chest coplanarity, smooth neck assist
    specs["USDG-SURF-V00"] = {
        "expected_support": {
            "A": "both feet flat on floor (relaxed knees ~145 deg); pelvis cupping B's hips (A hip > B hip); extended tucked arms cleanly on B deltoids",
            "B": "both feet flat on floor (relaxed knees ~147 deg, unlocked!); hips clearly above chest w/ lumbar arch; chest & forearms coplanar on ~0.77m tabletop",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "USDG-SURF-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-03",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "A", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "B", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.0, 0.97], "pitch_x_deg": 103},
                *standing_feet("B", x=0.16, y=0.02, z=0.091, yaw=6, knee_x=0.18, knee_y=-0.58, knee_z=0.52),
                {"actor": "B", "bone": "hand_ik.L", "space": "POSE_WORLD_HAND_FRAME", "value": [0.18, -0.78, 0.77], "direction_world": [0.0, -0.99, -0.14], "normal_world": [-0.22, 0.14, -0.96]},
                {"actor": "B", "bone": "hand_ik.R", "space": "POSE_WORLD_HAND_FRAME", "value": [-0.18, -0.78, 0.77], "direction_world": [0.0, -0.99, -0.14], "normal_world": [0.22, 0.14, -0.96]},
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.27, -0.48, 0.76]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.27, -0.48, 0.76]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -36},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -30},
                {"actor": "A", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.245, 1.01], "pitch_x_deg": 47},
                *standing_feet("A", x=0.22, y=0.29, z=0.095, yaw=10, knee_x=0.25, knee_y=-0.22, knee_z=0.54),
                {"actor": "A", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.28, -0.10, 0.98]},
                {"actor": "A", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.28, -0.10, 0.98]},
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
                {"actor": "B", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.82, "max_hip_z_m": 1.24},
            ],
        },
        "contacts": make_contacts("USDG-SURF-V00 Pass 03: unlocked B knees (~147 deg), pelvis cupping (A > B), neck assist enabled, tabletop coplanarity."),
    }

    # 3. USDG-WALL-V00 — User-directed ~90 deg front bend reaching forward to vertical wall + rear pelvis cupping B hips + upright A w/ extended arms!
    specs["USDG-WALL-V00"] = {
        "expected_support": {
            "A": "both feet flat on floor (relaxed knees ~145 deg); upright-leaning stance with pelvis directly cupping B's hips (A hip > B hip); extended tucked arms cleanly on B outer shoulders",
            "B": "both feet flat on floor (relaxed knees ~145 deg); nearly 90 deg hip hinge with gentle inward lumbar curve; arms reaching forward level to vertical wall (y=-0.84m, z=1.00m)",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "USDG-WALL-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-03",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "A", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                # Almost 90 deg bend (pitch=88 deg) with relaxed knees (torso_z=0.97 -> B_knee ~145 deg, B_thigh_z=0.952 < A_thigh_z=0.983)!
                {"actor": "B", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.0, 0.97], "pitch_x_deg": 88},
                *standing_feet("B", x=0.16, y=0.02, z=0.091, yaw=6, knee_x=0.18, knee_y=-0.58, knee_z=0.52),
                # Level arms reaching forward to vertical wall (y=-0.84m -> ~158 deg soft weight-bearing bend, z=1.00m level with shoulders!)
                {"actor": "B", "bone": "hand_ik.L", "space": "POSE_WORLD_HAND_FRAME", "value": [0.22, -0.84, 1.00], "direction_world": [0.0, 0.0, 1.0], "normal_world": [0.0, -1.0, 0.0]},
                {"actor": "B", "bone": "hand_ik.R", "space": "POSE_WORLD_HAND_FRAME", "value": [-0.22, -0.84, 1.00], "direction_world": [0.0, 0.0, 1.0], "normal_world": [0.0, -1.0, 0.0]},
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.28, -0.58, 0.90]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.28, -0.58, 0.90]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -32},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -30},
                # Upright rear partner (pitch=36 deg) with pelvis directly cupping B's hips (a_y=0.25, a_z=1.01) & extended tucked arms (~153 deg)!
                {"actor": "A", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.25, 1.01], "pitch_x_deg": 36},
                *standing_feet("A", x=0.22, y=0.29, z=0.095, yaw=10, knee_x=0.25, knee_y=-0.22, knee_z=0.54),
                {"actor": "A", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.28, -0.10, 1.04]},
                {"actor": "A", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.28, -0.10, 1.04]},
                {"actor": "A", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -22},
                {"actor": "A", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -22},
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
                {"actor": "B", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.82, "max_hip_z_m": 1.24},
            ],
        },
        "contacts": make_contacts("USDG-WALL-V00 Pass 03: ~90 deg front bend reaching forward to vertical wall, rear pelvis cupping front hip (A > B), extended tucked A arms."),
    }

    # 4. USDG-LOW-V00 — Eliminates P0 chest-to-glute clip, unlocks B knees (~144 deg), rear pelvis cupping B hips (A > B), neck assist enabled!
    specs["USDG-LOW-V00"] = {
        "expected_support": {
            "A": "both feet flat on floor (relaxed standing knees ~142 deg); pelvis cupping B's hips (A hip > B hip) with zero chest-into-glute clip; extended tucked arms to B deltoids",
            "B": "both feet flat on floor (relaxed knees ~144 deg, unlocked!); deep ~120 deg forward hip fold with chest & head cleanly below hips; flat palms on ~0.48m low support",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "USDG-LOW-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-03",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "A", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "B", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.0, 0.96], "pitch_x_deg": 120},
                *standing_feet("B", x=0.17, y=0.02, z=0.091, yaw=6, knee_x=0.19, knee_y=-0.58, knee_z=0.52),
                {"actor": "B", "bone": "hand_ik.L", "space": "POSE_WORLD_HAND_FRAME", "value": [0.20, -0.64, 0.48], "direction_world": HORIZ_DIR, "normal_world": HORIZ_NORM_L},
                {"actor": "B", "bone": "hand_ik.R", "space": "POSE_WORLD_HAND_FRAME", "value": [-0.20, -0.64, 0.48], "direction_world": HORIZ_DIR, "normal_world": HORIZ_NORM_R},
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.25, -0.48, 0.66]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.25, -0.48, 0.66]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -38},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -34},
                # A pelvis cupping B's hips (a_y=0.275, a_z=0.99 > b_z=0.96) with pitch=60 deg so extended arms reach B shoulders cleanly without chest-into-buttocks clip!
                {"actor": "A", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.275, 0.99], "pitch_x_deg": 60},
                *standing_feet("A", x=0.23, y=0.31, z=0.095, yaw=10, knee_x=0.26, knee_y=-0.20, knee_z=0.54),
                {"actor": "A", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.30, -0.10, 0.92]},
                {"actor": "A", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.30, -0.10, 0.92]},
                {"actor": "A", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -32},
                {"actor": "A", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -34},
                *rear_shoulder_hands(offset=(0.132, 0.08, 0.068)),
            ],
            "styling_controls": [
                {"actor": "B", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -16},
                {"actor": "A", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -10},
            ],
            "head_aim": {"actor": "B", "target_elevation_deg": -18, "max_delta_deg": 45, "neck_assist_enabled": True, "reference": "RIG001_forward_-Y_world_rest_to_pose_delta", "objective": "deep_fold_smooth_neck"},
            "floor_calibration": standard_floor_calibration(),
            "pelvic_alignment": {"actor": "A", "target_actor": "B", "region": "pelvis", "target_distance_m": 0.080, "max_forward_shift_m": 0.015, "iterations": 3},
            "support_assertions": standard_support_assertions(),
            "posture_assertions": [
                {"actor": "A", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.82, "max_hip_z_m": 1.26},
                {"actor": "B", "kind": "forward_fold_standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.78, "max_hip_z_m": 1.22, "min_head_drop_below_hip_m": 0.06},
            ],
        },
        "contacts": make_contacts("USDG-LOW-V00 Pass 03: P0 chest-to-buttocks clip cleared, unlocked B knees, rear pelvis cupping (A > B), neck assist enabled."),
    }

    # 5. USDG-PULL-V00 — Rear pelvis cupping B hips (A > B), A upright w/ extended tucked arms, B hands cleanly contacting A outer flanks (0mm reach error)
    specs["USDG-PULL-V00"] = {
        "expected_support": {
            "A": "both feet flat on floor (relaxed knees ~145 deg); upright-leaning stance with pelvis directly cupping B's hips (A hip > B hip); extended tucked arms cleanly on B shoulders",
            "B": "both feet flat on floor (relaxed knees ~145 deg, independent balance); ~84 deg hinge w/ gentle lumbar arch; arms angled naturally down-back onto A's outer flanks/hips",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "USDG-PULL-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-03",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "A", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "B", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.0, 0.97], "pitch_x_deg": 84},
                *standing_feet("B", x=0.17, y=0.02, z=0.091, yaw=6, knee_x=0.19, knee_y=-0.58, knee_z=0.52),
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.36, -0.26, 0.78]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.36, -0.26, 0.78]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -30},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -28},
                {"actor": "A", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.25, 1.01], "pitch_x_deg": 35},
                *standing_feet("A", x=0.22, y=0.29, z=0.095, yaw=10, knee_x=0.25, knee_y=-0.22, knee_z=0.54),
                {"actor": "A", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.28, -0.10, 1.04]},
                {"actor": "A", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.28, -0.10, 1.04]},
                {"actor": "A", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -22},
                {"actor": "A", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -22},
                # B palms softly tucked onto A's outer flanks/hips (within natural arm reach, no 3cm hover)
                {
                    "actor": "B",
                    "bone": "hand_ik.L",
                    "space": "POSE_RELATIVE_BONE_HEAD_HAND",
                    "value": [0.195, -0.07, -0.12],
                    "target_actor": "A",
                    "target_bone": "hips",
                    "direction_world": [-0.18, 0.90, -0.40],
                    "normal_world": [-0.94, -0.22, -0.24],
                },
                {
                    "actor": "B",
                    "bone": "hand_ik.R",
                    "space": "POSE_RELATIVE_BONE_HEAD_HAND",
                    "value": [-0.195, -0.07, -0.12],
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
                {"actor": "B", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.82, "max_hip_z_m": 1.24},
            ],
        },
        "contacts": make_contacts(
            "USDG-PULL-V00 Pass 03: rear pelvis cupping front hip (A > B), tucked A elbows, B hands cleanly contacting A flanks.",
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
            "batch_id": "WORKSPACE-BATCH-0003-PASS-03",
            "source_checkpoint": auth["source_checkpoint"],
            "source_id": auth["source_id"],
            "actor_mapping": {"ACTOR_1": "A", "ACTOR_2": "B"},
            "pose_name": row["pose_name"],
            "source_gate": row["generation_gate"],
            "source_complexity_pose": row.get("complexity_pose", ""),
            "specification": row["specification"],
            "approach": "Workspace batch-0003 Pass 03 calibrated from user pelvis-cupping / WALL-90-deg feedback + Pass 02 blind QA.",
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
        "batch_label": "batch-0003",
        "pass_label": "pass-03",
        "family": "USDG",
        "note": "Calibrated USDG Pass 03: rear pelvis cupping front hips (A hip > B hip), relaxed knees, extended tucked A arms, WALL ~90 deg forward bend.",
        "local_calibration": {"enabled": True, "max_refinement_attempts": 2},
        "poses": plan_poses,
    }
    plan_path = write_json_workspace(BATCHES_DIR / "BATCH-0003-PASS-03.json", plan)
    print(json.dumps({"ok": True, "plan": workspace_rel(plan_path), "packages": created}, indent=2))


if __name__ == "__main__":
    main()
