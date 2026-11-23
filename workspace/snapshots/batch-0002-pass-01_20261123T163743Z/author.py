"""Author all 4 UADG V00 Pass 01 data-only pose packages inside workspace/.

Poses (Asymmetric Standing Hinge family):
- UADG-FELV-V00: B right foot grounded, B left leg elevated to table height (~0.74m),
  B hands on forward edge (~0.80m); A both feet grounded, both palms at B outer shoulders.
- UADG-FASS-V00: B right foot grounded, B left leg lifted & cradled by A's left arm/hand;
  A both feet grounded, A right hand cups B's right outer shoulder.
- UADG-RELV-V00: B both feet grounded, hands on waist-height edge; A right foot grounded,
  A left foot elevated to knee height (~0.50m), both palms at B outer shoulders.
- UADG-DUAL-V00: Both A and B place left foot on shared sofa-height platform (~0.45m)
  and right foot on floor; A both palms at B outer shoulders.
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
    "UADG-FELV-V00",
    "UADG-FASS-V00",
    "UADG-RELV-V00",
    "UADG-DUAL-V00",
]

# Virtual table/edge palm orientation for Actor B (flat downward-facing palms on support edge)
EDGE_DIR = [0.0, -0.94, -0.34]
EDGE_NORM_L = [-0.30, 0.34, -0.89]
EDGE_NORM_R = [0.30, 0.34, -0.89]


def front_edge_hands(x: float, y: float, z: float) -> list[dict]:
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


def rear_shoulder_hand(side: str, offset: tuple[float, float, float] = (0.105, 0.10, 0.04)) -> dict:
    sign = 1 if side == "L" else -1
    ox, oy, oz = offset
    return {
        "actor": "A",
        "bone": f"hand_ik.{side}",
        "space": "POSE_RELATIVE_BONE_HEAD_HAND",
        "value": [ox * sign, oy, oz],
        "target_actor": "B",
        "target_bone": f"DEF-upper_arm.{side}",
        "direction_world": [-0.45 * sign, -0.80, -0.39],
        "normal_world": [-0.80 * sign, 0.25, -0.54],
    }


def make_shoulder_contacts(note: str, left_target_bone: str = "DEF-upper_arm.L", left_id: str = "left_rear_palm_to_front_outer_shoulder") -> dict:
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
                "id": left_id,
                "actor": "A",
                "bone": "hand_ik.L",
                "target_actor": "B",
                "target_bone": left_target_bone,
                "tolerance_m": 0.24,
            },
            {
                "id": "right_rear_palm_to_front_outer_shoulder",
                "actor": "A",
                "bone": "hand_ik.R",
                "target_actor": "B",
                "target_bone": "DEF-upper_arm.R",
                "tolerance_m": 0.24,
            },
        ],
        "note": note,
    }


def make_pose_specs() -> dict[str, dict]:
    specs: dict[str, dict] = {}

    # 1. UADG-FELV-V00 — Asymmetric front-leg elevated hinge (B.L foot on table-height ~0.74m, B.R on floor)
    specs["UADG-FELV-V00"] = {
        "expected_support": {
            "A": "both feet grounded on floor, knees softly flexed; both palms at B outer shoulders",
            "B": "right foot grounded on floor; left foot elevated to table-height support (~0.74m); both hands on forward support edge (~0.80m)",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "UADG-FELV-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-01",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "A", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                # B standing forward hinge with mild lumbar contour
                {"actor": "B", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.0, 0.90], "pitch_x_deg": 72},
                # B right foot grounded on floor
                {"actor": "B", "bone": "foot_ik.R", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [-0.14, 0.02, 0.091], "pitch_x_deg": 0, "yaw_z_deg": -6},
                {"actor": "B", "bone": "thigh_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.16, -0.52, 0.50]},
                # B left foot elevated onto table-height support surface (~0.74m)
                {"actor": "B", "bone": "foot_ik.L", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.26, -0.34, 0.74], "pitch_x_deg": 0, "yaw_z_deg": 18},
                {"actor": "B", "bone": "thigh_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.46, -0.58, 1.00]},
                # B hands on forward support edge (~0.80m)
                *front_edge_hands(x=0.22, y=-0.74, z=0.80),
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.34, -0.44, 0.96]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.34, -0.44, 0.96]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -24},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -28},
                # A close standing behind, both feet grounded, softly flexed knees
                {"actor": "A", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.34, 0.94], "pitch_x_deg": 38},
                {"actor": "A", "bone": "foot_ik.L", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.22, 0.36, 0.095], "pitch_x_deg": 0, "yaw_z_deg": 10},
                {"actor": "A", "bone": "foot_ik.R", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [-0.22, 0.36, 0.095], "pitch_x_deg": 0, "yaw_z_deg": -10},
                {"actor": "A", "bone": "thigh_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.28, -0.14, 0.52]},
                {"actor": "A", "bone": "thigh_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.28, -0.14, 0.52]},
                {"actor": "A", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.54, -0.02, 1.18]},
                {"actor": "A", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.54, -0.02, 1.18]},
                {"actor": "A", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -26},
                {"actor": "A", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -30},
                rear_shoulder_hand("L"),
                rear_shoulder_hand("R"),
            ],
            "styling_controls": [
                {"actor": "B", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -12},
                {"actor": "A", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -10},
            ],
            "head_aim": {
                "actor": "B",
                "target_elevation_deg": 6,
                "max_delta_deg": 60,
                "reference": "RIG001_forward_-Y_world_rest_to_pose_delta",
                "objective": "face_forward_naturally",
            },
            "floor_calibration": [
                {"actor": "B", "region": "feet", "side": "R", "adjust_bone": "foot_ik.R", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "A", "region": "feet", "side": "L", "adjust_bone": "foot_ik.L", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "A", "region": "feet", "side": "R", "adjust_bone": "foot_ik.R", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
            ],
            "pelvic_alignment": {
                "actor": "A",
                "target_actor": "B",
                "region": "pelvis",
                "target_distance_m": 0.055,
                "max_forward_shift_m": 0.12,
                "iterations": 6,
            },
            "support_assertions": [
                {"actor": "B", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "A", "region": "feet", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "A", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
            ],
            "posture_assertions": [
                {"actor": "A", "kind": "standing", "min_knee_joint_z_m": 0.30, "min_hip_z_m": 0.72, "max_hip_z_m": 1.25},
                {"actor": "B", "kind": "standing", "min_knee_joint_z_m": 0.30, "min_hip_z_m": 0.70, "max_hip_z_m": 1.20},
            ],
        },
        "contacts": make_shoulder_contacts("UADG-FELV-V00 Pass 01: B left foot elevated to ~0.74m virtual table, right foot grounded; A standing behind with outer-shoulder palms."),
    }

    # 2. UADG-FASS-V00 — Rear-assisted front-leg hinge (A.L arm supports B.L lifted leg; A.R hand cups B.R outer shoulder!)
    specs["UADG-FASS-V00"] = {
        "expected_support": {
            "A": "both feet grounded on floor; LEFT hand/forearm cradles B's lifted left leg; RIGHT hand cups B's right outer shoulder",
            "B": "right foot grounded on floor; left leg lifted & externally supported by A's left arm; hands brace forward virtual edge (~0.82m)",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "UADG-FASS-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-01",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "A", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "B", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.0, 0.90], "pitch_x_deg": 70},
                # B right foot grounded on floor
                {"actor": "B", "bone": "foot_ik.R", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [-0.14, 0.02, 0.091], "pitch_x_deg": 0, "yaw_z_deg": -6},
                {"actor": "B", "bone": "thigh_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.16, -0.52, 0.50]},
                # B left leg lifted outward/upward, knee bent so A's left arm cradles under the knee/upper shin
                {"actor": "B", "bone": "foot_ik.L", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.30, 0.10, 0.54], "pitch_x_deg": 32, "yaw_z_deg": 20},
                {"actor": "B", "bone": "thigh_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.46, -0.45, 0.84]},
                # B hands on forward edge (~0.82m)
                *front_edge_hands(x=0.22, y=-0.72, z=0.82),
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.34, -0.42, 0.98]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.34, -0.42, 0.98]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -24},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -28},
                # A standing behind, both feet grounded
                {"actor": "A", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.34, 0.94], "pitch_x_deg": 34},
                {"actor": "A", "bone": "foot_ik.L", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.22, 0.38, 0.095], "pitch_x_deg": 0, "yaw_z_deg": 12},
                {"actor": "A", "bone": "foot_ik.R", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [-0.22, 0.36, 0.095], "pitch_x_deg": 0, "yaw_z_deg": -10},
                {"actor": "A", "bone": "thigh_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.28, -0.10, 0.52]},
                {"actor": "A", "bone": "thigh_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.28, -0.14, 0.52]},
                # A left elbow drops cleanly outside-down to scoop underneath B's raised left knee/calf
                {"actor": "A", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.54, 0.24, 0.86]},
                {"actor": "A", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.54, -0.02, 1.18]},
                {"actor": "A", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -24},
                {"actor": "A", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -28},
                # A LEFT hand dedicated to supporting B's lifted left leg under knee/upper shin (palm facing UP!)
                {
                    "actor": "A",
                    "bone": "hand_ik.L",
                    "space": "POSE_RELATIVE_BONE_HEAD_HAND",
                    "value": [0.02, 0.05, -0.075],
                    "target_actor": "B",
                    "target_bone": "DEF-shin.L",
                    "direction_world": [-0.25, -0.90, 0.35],
                    "normal_world": [-0.15, 0.38, 0.91],
                },
                # A RIGHT hand reaches forward to cup B's right outer shoulder
                rear_shoulder_hand("R"),
            ],
            "styling_controls": [
                {"actor": "B", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -12},
                {"actor": "A", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -10},
            ],
            "head_aim": {
                "actor": "B",
                "target_elevation_deg": 6,
                "max_delta_deg": 60,
                "reference": "RIG001_forward_-Y_world_rest_to_pose_delta",
                "objective": "face_forward_naturally",
            },
            "floor_calibration": [
                {"actor": "B", "region": "feet", "side": "R", "adjust_bone": "foot_ik.R", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "A", "region": "feet", "side": "L", "adjust_bone": "foot_ik.L", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "A", "region": "feet", "side": "R", "adjust_bone": "foot_ik.R", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
            ],
            "pelvic_alignment": {
                "actor": "A",
                "target_actor": "B",
                "region": "pelvis",
                "target_distance_m": 0.055,
                "max_forward_shift_m": 0.12,
                "iterations": 6,
            },
            "support_assertions": [
                {"actor": "B", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "A", "region": "feet", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "A", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
            ],
            "posture_assertions": [
                {"actor": "A", "kind": "standing", "min_knee_joint_z_m": 0.30, "min_hip_z_m": 0.72, "max_hip_z_m": 1.25},
                {"actor": "B", "kind": "standing", "min_knee_joint_z_m": 0.30, "min_hip_z_m": 0.70, "max_hip_z_m": 1.20},
            ],
        },
        "contacts": make_shoulder_contacts(
            "UADG-FASS-V00 Pass 01: A left arm supports B lifted left leg under knee/shin; A right hand cups B right outer shoulder.",
            left_target_bone="DEF-shin.L",
            left_id="left_rear_hand_supporting_front_raised_leg",
        ),
    }

    # 3. UADG-RELV-V00 — Rear elevated-leg hinge (B both feet grounded; A.L foot elevated at knee height ~0.50m, A.R on floor)
    specs["UADG-RELV-V00"] = {
        "expected_support": {
            "A": "right foot grounded on floor; left foot elevated to knee-height surface (~0.50m); both palms at B outer shoulders",
            "B": "both feet grounded on floor, knees softly flexed; both hands bracing waist-height edge (~0.82m)",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "UADG-RELV-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-01",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "A", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "B", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.0, 0.90], "pitch_x_deg": 72},
                # B both feet grounded on floor
                {"actor": "B", "bone": "foot_ik.L", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.15, 0.02, 0.091], "pitch_x_deg": 0, "yaw_z_deg": 6},
                {"actor": "B", "bone": "foot_ik.R", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [-0.15, 0.02, 0.091], "pitch_x_deg": 0, "yaw_z_deg": -6},
                {"actor": "B", "bone": "thigh_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.18, -0.52, 0.50]},
                {"actor": "B", "bone": "thigh_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.18, -0.52, 0.50]},
                # B hands on waist-height edge (~0.82m)
                *front_edge_hands(x=0.22, y=-0.74, z=0.82),
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.34, -0.44, 0.98]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.34, -0.44, 0.98]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -24},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -28},
                # A asymmetric split stance: right foot on floor, left foot elevated at knee height (~0.50m)
                {"actor": "A", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.34, 0.95], "pitch_x_deg": 38},
                {"actor": "A", "bone": "foot_ik.R", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [-0.20, 0.40, 0.095], "pitch_x_deg": 0, "yaw_z_deg": -10},
                {"actor": "A", "bone": "thigh_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.26, -0.10, 0.52]},
                {"actor": "A", "bone": "foot_ik.L", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.36, 0.16, 0.50], "pitch_x_deg": 0, "yaw_z_deg": 20},
                {"actor": "A", "bone": "thigh_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.64, -0.22, 0.88]},
                {"actor": "A", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.54, -0.02, 1.20]},
                {"actor": "A", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.54, -0.02, 1.20]},
                {"actor": "A", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -26},
                {"actor": "A", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -30},
                rear_shoulder_hand("L"),
                rear_shoulder_hand("R"),
            ],
            "styling_controls": [
                {"actor": "B", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -12},
                {"actor": "A", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -10},
            ],
            "head_aim": {
                "actor": "B",
                "target_elevation_deg": 6,
                "max_delta_deg": 60,
                "reference": "RIG001_forward_-Y_world_rest_to_pose_delta",
                "objective": "face_forward_naturally",
            },
            "floor_calibration": [
                {"actor": "B", "region": "feet", "side": "L", "adjust_bone": "foot_ik.L", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "B", "region": "feet", "side": "R", "adjust_bone": "foot_ik.R", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "A", "region": "feet", "side": "R", "adjust_bone": "foot_ik.R", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
            ],
            "pelvic_alignment": {
                "actor": "A",
                "target_actor": "B",
                "region": "pelvis",
                "target_distance_m": 0.055,
                "max_forward_shift_m": 0.12,
                "iterations": 6,
            },
            "support_assertions": [
                {"actor": "B", "region": "feet", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "B", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "A", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
            ],
            "posture_assertions": [
                {"actor": "A", "kind": "standing", "min_knee_joint_z_m": 0.30, "min_hip_z_m": 0.72, "max_hip_z_m": 1.25},
                {"actor": "B", "kind": "standing", "min_knee_joint_z_m": 0.30, "min_hip_z_m": 0.70, "max_hip_z_m": 1.20},
            ],
        },
        "contacts": make_shoulder_contacts("UADG-RELV-V00 Pass 01: B both feet grounded; A left foot elevated to ~0.50m knee-height support, right foot grounded."),
    }

    # 4. UADG-DUAL-V00 — Dual-platform asymmetric hinge (BOTH A.L and B.L on shared ~0.46m sofa-height platform; both R feet on floor)
    specs["UADG-DUAL-V00"] = {
        "expected_support": {
            "A": "right foot grounded on floor; left foot on shared sofa-height platform (~0.46m); both palms at B outer shoulders",
            "B": "right foot grounded on floor; left foot on shared sofa-height platform (~0.46m); hands on forward virtual edge (~0.80m)",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "UADG-DUAL-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-01",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "A", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "B", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.0, 0.89], "pitch_x_deg": 72},
                # B right foot on floor, left foot on shared ~0.46m sofa-height platform
                {"actor": "B", "bone": "foot_ik.R", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [-0.15, 0.02, 0.091], "pitch_x_deg": 0, "yaw_z_deg": -6},
                {"actor": "B", "bone": "thigh_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.18, -0.52, 0.50]},
                {"actor": "B", "bone": "foot_ik.L", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.28, -0.20, 0.46], "pitch_x_deg": 0, "yaw_z_deg": 18},
                {"actor": "B", "bone": "thigh_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.46, -0.54, 0.82]},
                *front_edge_hands(x=0.22, y=-0.72, z=0.80),
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.34, -0.44, 0.96]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.34, -0.44, 0.96]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -24},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -28},
                # A right foot on floor, left foot on same shared ~0.46m platform behind/outside B.L
                {"actor": "A", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.34, 0.94], "pitch_x_deg": 38},
                {"actor": "A", "bone": "foot_ik.R", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [-0.20, 0.40, 0.095], "pitch_x_deg": 0, "yaw_z_deg": -10},
                {"actor": "A", "bone": "thigh_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.26, -0.10, 0.52]},
                {"actor": "A", "bone": "foot_ik.L", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.40, 0.22, 0.46], "pitch_x_deg": 0, "yaw_z_deg": 22},
                {"actor": "A", "bone": "thigh_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.70, -0.14, 0.84]},
                {"actor": "A", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.54, -0.02, 1.18]},
                {"actor": "A", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.54, -0.02, 1.18]},
                {"actor": "A", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -26},
                {"actor": "A", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -30},
                rear_shoulder_hand("L"),
                rear_shoulder_hand("R"),
            ],
            "styling_controls": [
                {"actor": "B", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -12},
                {"actor": "A", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -10},
            ],
            "head_aim": {
                "actor": "B",
                "target_elevation_deg": 6,
                "max_delta_deg": 60,
                "reference": "RIG001_forward_-Y_world_rest_to_pose_delta",
                "objective": "face_forward_naturally",
            },
            "floor_calibration": [
                {"actor": "B", "region": "feet", "side": "R", "adjust_bone": "foot_ik.R", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
                {"actor": "A", "region": "feet", "side": "R", "adjust_bone": "foot_ik.R", "target_z_m": 0.004, "tolerance_m": 0.025, "max_total_shift_m": 0.22, "iterations": 6},
            ],
            "pelvic_alignment": {
                "actor": "A",
                "target_actor": "B",
                "region": "pelvis",
                "target_distance_m": 0.055,
                "max_forward_shift_m": 0.12,
                "iterations": 6,
            },
            "support_assertions": [
                {"actor": "B", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "A", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
            ],
            "posture_assertions": [
                {"actor": "A", "kind": "standing", "min_knee_joint_z_m": 0.30, "min_hip_z_m": 0.72, "max_hip_z_m": 1.25},
                {"actor": "B", "kind": "standing", "min_knee_joint_z_m": 0.30, "min_hip_z_m": 0.70, "max_hip_z_m": 1.20},
            ],
        },
        "contacts": make_shoulder_contacts("UADG-DUAL-V00 Pass 01: both A and B left feet on shared ~0.46m sofa-height platform, right feet grounded."),
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
            "batch_id": "WORKSPACE-UADG-V00-PASS01",
            "source_checkpoint": auth["source_checkpoint"],
            "source_id": auth["source_id"],
            "actor_mapping": {"ACTOR_1": "A", "ACTOR_2": "B"},
            "pose_name": row["pose_name"],
            "source_gate": row["generation_gate"],
            "source_complexity_pose": row.get("complexity_pose", ""),
            "specification": row["specification"],
            "approach": "Workspace experimental Pass 01 authoring for asymmetric standing hinge family (UADG); elevated virtual support planes without template furniture props.",
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
        "batch_label": "workspace-uadg",
        "pass_label": "pass-01",
        "family": "UADG",
        "note": "Experimental backward-roadmap batch #2 (UADG, 4 poses) in workspace/.",
        "local_calibration": {"enabled": True, "max_refinement_attempts": 2},
        "poses": plan_poses,
    }
    plan_path = write_json_workspace(PASS_DIR / "plan.json", plan)
    print(json.dumps({"ok": True, "plan": workspace_rel(plan_path), "packages": created}, indent=2))


if __name__ == "__main__":
    main()
