"""Author all 4 UADG V00 Pass 02 calibrated data-only pose packages inside workspace/.

Addresses all P0/P1 visual QA findings from UADG Pass 01 AUDIT.md (4.5/10):
- FASS (P0): raises B's lifted left knee/shin cleanly off A's legs & brings A's torso forward
  so A's left arm reaches easily and cradles directly underneath B's lifted knee/upper calf.
- FELV (P0): moves B's elevated left foot forward & abducted onto ~0.68m table plane so
  B's knee drops below ~0.94m, completely clearing A's left forearm/wrist.
- DUAL (P0): locks both A's & B's elevated left feet to the exact same sofa-height plane
  (z=0.50m, flat sole, aligned X band) and raises B's left elbow cleanly clear of B's knee.
- ALL 4 (P1): raises standing torsos (B=0.97m, A=0.98m) so grounded knees are softly flexed
  (~150-160 deg, not crouched), hinges A forward closer to B (pitch=50 deg) with clean head
  clearance, and positions B's hands as weight-bearing horizontal edge braces (z=0.84m).
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

# Flat horizontal waist-edge palm brace for Actor B (palms resting flat on horizontal virtual table edge)
EDGE_DIR = [0.0, -0.96, -0.28]
EDGE_NORM_L = [-0.36, 0.28, -0.89]
EDGE_NORM_R = [0.36, 0.28, -0.89]


def front_edge_hands(x: float = 0.21, y: float = -0.66, z: float = 0.84) -> list[dict]:
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


def rear_shoulder_hand(side: str, offset: tuple[float, float, float] = (0.105, 0.08, 0.025)) -> dict:
    sign = 1 if side == "L" else -1
    ox, oy, oz = offset
    return {
        "actor": "A",
        "bone": f"hand_ik.{side}",
        "space": "POSE_RELATIVE_BONE_HEAD_HAND",
        "value": [ox * sign, oy, oz],
        "target_actor": "B",
        "target_bone": f"DEF-upper_arm.{side}",
        "direction_world": [-0.45 * sign, -0.82, -0.35],
        "normal_world": [-0.82 * sign, 0.22, -0.53],
    }


def make_contacts(note: str, left_target_bone: str = "DEF-upper_arm.L", left_id: str = "left_rear_palm_to_front_outer_shoulder") -> dict:
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

    # 1. UADG-FELV-V00 — B left foot forward & abducted on ~0.68m table plane (knee drops below ~0.94m, zero wrist clip!)
    specs["UADG-FELV-V00"] = {
        "expected_support": {
            "A": "both feet flat on floor with softly flexed knees (~150 deg); torso hinged closely; both palms at B outer shoulders",
            "B": "right foot flat on floor (softly flexed knee); left foot forward/outward on ~0.68m table plane; hands braced flat on ~0.84m edge",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "UADG-FELV-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-02",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "A", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "B", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.0, 0.97], "pitch_x_deg": 74},
                # B right foot grounded with softly flexed knee
                {"actor": "B", "bone": "foot_ik.R", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [-0.14, 0.02, 0.091], "pitch_x_deg": 0, "yaw_z_deg": -6},
                {"actor": "B", "bone": "thigh_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.16, -0.52, 0.54]},
                # B left foot forward & abducted onto ~0.68m table plane (opens knee to ~95 deg, keeps knee well below A's left arm!)
                {"actor": "B", "bone": "foot_ik.L", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.42, -0.46, 0.68], "pitch_x_deg": 0, "yaw_z_deg": 24},
                {"actor": "B", "bone": "thigh_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.68, -0.60, 0.86]},
                # B downward load-bearing edge brace
                *front_edge_hands(x=0.21, y=-0.66, z=0.84),
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.30, -0.44, 1.04]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.30, -0.44, 1.04]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -26},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -30},
                # A standing closely behind with softly flexed knees & forward torso alignment
                {"actor": "A", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.30, 0.98], "pitch_x_deg": 50},
                {"actor": "A", "bone": "foot_ik.L", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.22, 0.34, 0.095], "pitch_x_deg": 0, "yaw_z_deg": 10},
                {"actor": "A", "bone": "foot_ik.R", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [-0.22, 0.34, 0.095], "pitch_x_deg": 0, "yaw_z_deg": -10},
                {"actor": "A", "bone": "thigh_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.26, -0.14, 0.56]},
                {"actor": "A", "bone": "thigh_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.26, -0.14, 0.56]},
                # A left elbow slightly lifted to guarantee generous clearance over B's elevated left knee
                {"actor": "A", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.56, -0.04, 1.24]},
                {"actor": "A", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.54, -0.04, 1.20]},
                {"actor": "A", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -30},
                {"actor": "A", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -34},
                rear_shoulder_hand("L"),
                rear_shoulder_hand("R"),
            ],
            "styling_controls": [
                {"actor": "B", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -12},
                {"actor": "A", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -12},
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
                {"actor": "A", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.80, "max_hip_z_m": 1.25},
                {"actor": "B", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.78, "max_hip_z_m": 1.22},
            ],
        },
        "contacts": make_contacts("UADG-FELV-V00 Pass 02: cleared B knee / A wrist collision, softened grounded knees, closer A torso, edge-braced B palms."),
    }

    # 2. UADG-FASS-V00 — True rear-assisted leg cradle (A.L hand cradles directly under B.L raised knee/shin; B.L foot cleanly clear of A!)
    specs["UADG-FASS-V00"] = {
        "expected_support": {
            "A": "both feet flat on floor (softly flexed knees); LEFT hand cradles directly underneath B's raised left knee/calf; RIGHT hand cups B's right outer shoulder",
            "B": "right foot flat on floor (softly flexed knee); left leg raised forward/outward & supported by A's left hand; hands braced on ~0.84m edge",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "UADG-FASS-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-02",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "A", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "B", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.0, 0.97], "pitch_x_deg": 72},
                # B right foot grounded with softly flexed knee
                {"actor": "B", "bone": "foot_ik.R", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [-0.14, 0.02, 0.091], "pitch_x_deg": 0, "yaw_z_deg": -6},
                {"actor": "B", "bone": "thigh_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.16, -0.52, 0.54]},
                # B left leg raised HIGHER & FORWARD/OUTWARD so foot clears A's legs by >30cm and knee sits cleanly in A's arm reach (~0.95m)!
                {"actor": "B", "bone": "foot_ik.L", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.36, -0.18, 0.72], "pitch_x_deg": 12, "yaw_z_deg": 24},
                {"actor": "B", "bone": "thigh_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.54, -0.46, 1.00]},
                *front_edge_hands(x=0.21, y=-0.66, z=0.84),
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.30, -0.44, 1.04]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.30, -0.44, 1.04]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -26},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -30},
                # A hinged forward closely (pitch=52 deg) so A's left shoulder drops forward into effortless cradling reach!
                {"actor": "A", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.30, 0.97], "pitch_x_deg": 52},
                {"actor": "A", "bone": "foot_ik.L", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.22, 0.35, 0.095], "pitch_x_deg": 0, "yaw_z_deg": 12},
                {"actor": "A", "bone": "foot_ik.R", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [-0.22, 0.34, 0.095], "pitch_x_deg": 0, "yaw_z_deg": -10},
                {"actor": "A", "bone": "thigh_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.26, -0.10, 0.56]},
                {"actor": "A", "bone": "thigh_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.26, -0.14, 0.56]},
                # A left elbow drops cleanly outside-under to scoop underneath B's raised knee/calf
                {"actor": "A", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.54, 0.02, 0.88]},
                {"actor": "A", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.54, -0.04, 1.20]},
                {"actor": "A", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -30},
                {"actor": "A", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -34},
                # A LEFT hand cradles DIRECTLY underneath B's raised left knee/upper shin (DEF-shin.L), palm facing UP!
                {
                    "actor": "A",
                    "bone": "hand_ik.L",
                    "space": "POSE_RELATIVE_BONE_HEAD_HAND",
                    "value": [0.02, 0.04, -0.065],
                    "target_actor": "B",
                    "target_bone": "DEF-shin.L",
                    "direction_world": [-0.30, -0.92, 0.25],
                    "normal_world": [-0.15, 0.30, 0.94],
                },
                # A RIGHT hand cups B's right outer shoulder
                rear_shoulder_hand("R"),
            ],
            "styling_controls": [
                {"actor": "B", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -12},
                {"actor": "A", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -12},
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
                {"actor": "A", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.80, "max_hip_z_m": 1.25},
                {"actor": "B", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.78, "max_hip_z_m": 1.22},
            ],
        },
        "contacts": make_contacts(
            "UADG-FASS-V00 Pass 02: A left palm directly cradles B raised left knee/shin; B foot cleanly clears A knees; A right hand cups B right outer shoulder.",
            left_target_bone="DEF-shin.L",
            left_id="left_rear_hand_supporting_front_raised_leg",
        ),
    }

    # 3. UADG-RELV-V00 — B both feet grounded (soft knees), A.L elevated at knee height (~0.52m), closer A lean & hip clearance
    specs["UADG-RELV-V00"] = {
        "expected_support": {
            "A": "right foot flat on floor (softly flexed knee); left foot elevated at knee height (~0.52m); closer torso lean; palms at B outer shoulders",
            "B": "both feet flat on floor (softly flexed knees ~155 deg); hands braced flat on waist-height edge (~0.84m)",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "UADG-RELV-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-02",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "A", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "B", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.0, 0.97], "pitch_x_deg": 74},
                {"actor": "B", "bone": "foot_ik.L", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.15, 0.02, 0.091], "pitch_x_deg": 0, "yaw_z_deg": 6},
                {"actor": "B", "bone": "foot_ik.R", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [-0.15, 0.02, 0.091], "pitch_x_deg": 0, "yaw_z_deg": -6},
                {"actor": "B", "bone": "thigh_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.18, -0.52, 0.54]},
                {"actor": "B", "bone": "thigh_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.18, -0.52, 0.54]},
                *front_edge_hands(x=0.21, y=-0.66, z=0.84),
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.30, -0.44, 1.04]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.30, -0.44, 1.04]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -26},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -30},
                # A standing closely behind: right foot grounded, left foot elevated at knee height (~0.52m) with clean thigh clearance
                {"actor": "A", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.31, 0.99], "pitch_x_deg": 50},
                {"actor": "A", "bone": "foot_ik.R", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [-0.20, 0.36, 0.095], "pitch_x_deg": 0, "yaw_z_deg": -10},
                {"actor": "A", "bone": "thigh_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.24, -0.10, 0.56]},
                {"actor": "A", "bone": "foot_ik.L", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.40, 0.18, 0.52], "pitch_x_deg": 0, "yaw_z_deg": 20},
                {"actor": "A", "bone": "thigh_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.74, -0.14, 0.90]},
                {"actor": "A", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.54, -0.04, 1.22]},
                {"actor": "A", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.54, -0.04, 1.22]},
                {"actor": "A", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -30},
                {"actor": "A", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -34},
                rear_shoulder_hand("L"),
                rear_shoulder_hand("R"),
            ],
            "styling_controls": [
                {"actor": "B", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -12},
                {"actor": "A", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -12},
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
                "target_distance_m": 0.065,
                "max_forward_shift_m": 0.10,
                "iterations": 6,
            },
            "support_assertions": [
                {"actor": "B", "region": "feet", "side": "L", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "B", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "A", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
            ],
            "posture_assertions": [
                {"actor": "A", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.80, "max_hip_z_m": 1.25},
                {"actor": "B", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.78, "max_hip_z_m": 1.22},
            ],
        },
        "contacts": make_contacts("UADG-RELV-V00 Pass 02: softer grounded knees, closer A torso alignment, wider thigh clearance, edge-braced B palms."),
    }

    # 4. UADG-DUAL-V00 — Exact matched sofa-height plane (both A.L & B.L flat at z=0.50m along same X band) + clear B elbow/knee
    specs["UADG-DUAL-V00"] = {
        "expected_support": {
            "A": "right foot flat on floor (softly flexed knee); left foot flat on shared ~0.41m-sole sofa platform aligned with B.L; palms at B outer shoulders",
            "B": "right foot flat on floor (softly flexed knee); left foot flat on shared ~0.41m-sole sofa platform; hands braced on ~0.86m edge clear of knee",
        },
        "rig_targets": {
            "schema_version": 1,
            "geometry_contract_version": 2,
            "engine": "rigify_floor_v2",
            "pose_id": "UADG-DUAL-V00",
            "control_order": "root_then_torso_then_ik_then_contacts",
            "pass_label": "workspace-pass-02",
            "calibration_is_advisory": True,
            "controls": [
                {"actor": "B", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "A", "object_role": "root", "space": "OBJECT_WORLD_LOCATION_M", "value": [0, 0, 0]},
                {"actor": "B", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.0, 0.96], "pitch_x_deg": 74},
                # B right foot flat on floor (softly flexed knee)
                {"actor": "B", "bone": "foot_ik.R", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [-0.15, 0.02, 0.091], "pitch_x_deg": 0, "yaw_z_deg": -6},
                {"actor": "B", "bone": "thigh_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.18, -0.52, 0.54]},
                # B left foot flat on shared sofa platform (x=0.36, z=0.50 -> sole z~0.41m, flat 0 deg pitch, knee cleanly clear of elbow!)
                {"actor": "B", "bone": "foot_ik.L", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.36, -0.26, 0.50], "pitch_x_deg": 0, "yaw_z_deg": 16},
                {"actor": "B", "bone": "thigh_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.58, -0.56, 0.84]},
                # B hands slightly higher on ~0.86m edge with elevated elbows so B.L elbow clears B.L knee by >15cm!
                *front_edge_hands(x=0.20, y=-0.68, z=0.86),
                {"actor": "B", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.28, -0.46, 1.12]},
                {"actor": "B", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.28, -0.46, 1.12]},
                {"actor": "B", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -26},
                {"actor": "B", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -30},
                # A right foot flat on floor; A left foot on EXACT SAME sofa plane (x=0.40, z=0.504 -> sole z~0.41m!)
                {"actor": "A", "bone": "torso", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.0, 0.31, 0.98], "pitch_x_deg": 50},
                {"actor": "A", "bone": "foot_ik.R", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [-0.20, 0.36, 0.095], "pitch_x_deg": 0, "yaw_z_deg": -10},
                {"actor": "A", "bone": "thigh_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.24, -0.10, 0.56]},
                {"actor": "A", "bone": "foot_ik.L", "space": "POSE_WORLD_HEAD_ROT_X_DEG", "value": [0.40, 0.22, 0.504], "pitch_x_deg": 0, "yaw_z_deg": 16},
                {"actor": "A", "bone": "thigh_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.76, -0.06, 0.88]},
                {"actor": "A", "bone": "upper_arm_ik_target.L", "space": "POSE_WORLD_HEAD_M", "value": [0.54, -0.04, 1.22]},
                {"actor": "A", "bone": "upper_arm_ik_target.R", "space": "POSE_WORLD_HEAD_M", "value": [-0.54, -0.04, 1.22]},
                {"actor": "A", "bone": "neck", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -30},
                {"actor": "A", "bone": "head", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -34},
                rear_shoulder_hand("L"),
                rear_shoulder_hand("R"),
            ],
            "styling_controls": [
                {"actor": "B", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -12},
                {"actor": "A", "bone": "chest", "space": "POSE_LOCAL_REST_AXIS_ROT_X_DEG", "value": [0, 0, 0], "angle_deg": -12},
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
                "target_distance_m": 0.065,
                "max_forward_shift_m": 0.10,
                "iterations": 6,
            },
            "support_assertions": [
                {"actor": "B", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
                {"actor": "A", "region": "feet", "side": "R", "target_z_m": 0.004, "tolerance_m": 0.028},
            ],
            "posture_assertions": [
                {"actor": "A", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.80, "max_hip_z_m": 1.25},
                {"actor": "B", "kind": "standing", "min_knee_joint_z_m": 0.35, "min_hip_z_m": 0.78, "max_hip_z_m": 1.22},
            ],
        },
        "contacts": make_contacts("UADG-DUAL-V00 Pass 02: matched shared sofa foot plane (sole ~0.41m), cleared B elbow/knee, softer grounded knees, closer A lean."),
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
            "batch_id": "WORKSPACE-UADG-V00-PASS02",
            "source_checkpoint": auth["source_checkpoint"],
            "source_id": auth["source_id"],
            "actor_mapping": {"ACTOR_1": "A", "ACTOR_2": "B"},
            "pose_name": row["pose_name"],
            "source_gate": row["generation_gate"],
            "source_complexity_pose": row.get("complexity_pose", ""),
            "specification": row["specification"],
            "approach": "Workspace experimental Pass 02 calibrated from UADG Pass 01 blind QA (4.5/10).",
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
        "batch_label": "workspace-uadg",
        "pass_label": "pass-02",
        "family": "UADG",
        "note": "Calibrated UADG Pass 02 in workspace/ addressing all Pass 01 blind QA findings.",
        "local_calibration": {"enabled": True, "max_refinement_attempts": 2},
        "poses": plan_poses,
    }
    plan_path = write_json_workspace(PASS_DIR / "plan.json", plan)
    print(json.dumps({"ok": True, "plan": workspace_rel(plan_path), "packages": created}, indent=2))


if __name__ == "__main__":
    main()
