# Workspace Visual QA Audit — `UADG` Pass 01

- **Scope:** Experimental backward-roadmap batch #2 (`UADG-FELV-V00`, `UADG-FASS-V00`, `UADG-RELV-V00`, `UADG-DUAL-V00`)
- **Blender build:** Blender `5.2.2 LTS` (`4/4` rendered, exit code `0`, `4` views each, `0` JSON issues across all 4 poses)
- **Audit method:** Fresh-context blind QA auditor inspecting all 16 PNGs against `inputs/pose.json` CSV specs and `blender-result.json`
- **Batch visual benchmark:** **4.5 / 10** — **Pass 02 rework required** (advisory; no quality gates)

> **Diagnostic honesty note:** All 4 poses reported `0` JSON issues, yet direct visual inspection revealed 3 critical contact/collision/plane failures (`FASS`, `FELV`, `DUAL`) plus 4 systemic baseline issues.

---

## Summary Table

| Pose ID | JSON Issues | Blind Score | Verdict | Primary Visual Findings |
|---|---:|---:|---|---|
| `UADG-FELV-V00` | 0 | **4.0 / 10** | Fail (P0) | Grounded feet flat & clean head clearance, **but B's elevated left knee spikes to `1.185 m` directly through A's left wrist/forearm**; elevated foot tucked under chest instead of forward/outward on table plane |
| `UADG-FASS-V00` | 0 | **3.0 / 10** | Fail (P0) | Correct asymmetric rear arm assignment (left arm lowered, right on shoulder), **but A's left hand completely misses B's lifted leg** (hovers high beside B's hip) and **B's lifted left heel jams into A's left knee** |
| `UADG-RELV-V00` | 0 | **6.0 / 10** | Strongest (Needs Pass 02) | Cleanest topology & leg clearance; A's elevated left foot sits cleanly at knee height; needs closer upper-torso alignment, softer standing knee flexion (`121°` → `150°+`), and edge-braced B palms |
| `UADG-DUAL-V00` | 0 | **5.0 / 10** | Fail (P0) | Dual asymmetric silhouette reads cleanly laterally, **but A's and B's elevated left feet are ~6–8 cm off in height** (not one shared sofa plane) and **B's left elbow grazes/clips B's own elevated left knee** |
| **Overall** | **0** | **4.5 / 10** | **Run Pass 02** | Solid grounding and head clearance; clear P0/P1 fixes identified for Pass 02 |

---

## Systemic Cross-Batch Issues

1. **B's forward hands float downward instead of bracing a horizontal waist-height edge:** Wrists angle down ~20–30° into air instead of flat/dorsiflexed palms resting on a horizontal virtual edge (~0.80–0.82 m).
2. **A is too upright and detached from B:** Wide V-gap between A's chest and B's back (`A hip_z ≈ 1.10 m` vs `B hip_z ≈ 0.94 m`); upper torsos need closer alignment.
3. **Grounded knees are overly bent (`118°–125°`):** Reads as a crouch rather than softly flexed standing knees (`~150°–165°`).
4. **A's shoulder hands sit high/rearward:** Need slightly more lateral/forward placement wrapping inward onto B's outer deltoids.

---

## Prioritized Fixes for `UADG` Pass 02

1. **P0 — `UADG-FASS-V00` real leg-cradle contact & foot clearance:** Hinge A further forward and slightly lower; lift B's left knee/thigh higher and forward (foot clear of A's left knee by `≥10 cm`); place A's left cupped palm/forearm directly underneath B's lifted knee/upper calf.
2. **P0 — `UADG-FELV-V00` eliminate knee-through-wrist collision:** Move B's elevated left foot forward & slightly abducted (~20–25°) on a believable ~0.70–0.74 m table plane so B's knee drops below `~0.98 m` and clears A's left arm completely.
3. **P0 — `UADG-DUAL-V00` match shared sofa plane & clear B elbow/knee:** Lock both A's and B's elevated left foot soles to the **exact same world Z (~0.45 m)** and horizontal orientation along one shared sofa X-band; abduct B's left knee slightly and raise/extend B's left elbow cleanly clear of B's knee; relieve A-thigh / B-glute crowding.
4. **P1 — Systemic standing-hinge polish (all 4 poses):** Straighten grounded knees to `~150°–162°`, hinge A closer to B (`pitch ~48°–54°`, lower A torso slightly to match B pelvis height while keeping clean head clearance), orient B's edge-bracing palms flat on the virtual ~0.82 m edge, and seat A's shoulder hands slightly further forward/lateral around B's outer deltoids.
