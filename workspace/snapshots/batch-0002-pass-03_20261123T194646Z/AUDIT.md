# Visual QA Audit — `batch-0002` (`UADG`) Pass 03

- **Batch / Pass:** `batch-0002` (`UADG`, Backward Family #2) / `pass-03`
- **Snapshot:** `snapshots/batch-0002-pass-03_20261123T194646Z`
- **Revisions:** `poses/UADG-*/CPL01/v001/r003` (`reused_existing_package: false` on all 4, `scene_blend_saved: true` on all 4)
- **Build & Render Engine:** Blender `5.2.2 LTS` (`4/4` rendered, `exit_code: 0`, `16/16` previews, **`0` automated JSON issues** across all 4 poses)
- **Audit Protocol:** Strict fresh-context two-phase blind visual audit over `batch-summary.json`, all 4 `r003/inputs/pose.json` & `r003/blender-result.json`, and all 16 PNGs in `workspace/review/` before comparing against Pass 02 `AUDIT.md`.
- **Overall Locked Blind Score:** **8.78 / 10** (`8.8 / 10` rounded; **+2.4** vs Pass 02's `6.4 / 10`; **+4.3** vs Pass 01's `4.5 / 10`)
- **Total Defects:** **0 P0 / 0 P1 / 9 P2**
- **Verdict:** **4/4 READY FOR USER REVIEW & PROMOTION** — all 4 poses score `8.5–8.9 / 10` with zero P0/P1 defects and zero automated issues.

---

## 1. Per-Pose Score Progression (Pass 01 → Pass 02 → Pass 03)

| Pose ID | Pass 01 | Pass 02 | Pass 03 (Blind) | Delta vs P02 | P0 / P1 / P2 | Visual Summary |
|---|---:|---:|---:|---:|:---:|---|
| `UADG-FELV-V00` | 4.0 | 6.0 | **8.8 / 10** | **+2.8** | 0 / 0 / 2 | Clean lower-set B pelvis cupping, tucked extended A arms with zero bleed-through, flat elevated B.L foot, clean wrist-to-knee clearance |
| `UADG-FASS-V00` | 3.0 | 5.5 | **8.5 / 10** | **+3.0** | 0 / 0 / 3 | Genuine under-knee A.L palm cradle with zero lateral shin clipping and clear suspended B.L foot; minor P2 tight knee-capsule wrap |
| `UADG-RELV-V00` | 6.0 | 7.0 | **8.9 / 10** | **+1.9** | 0 / 0 / 2 | Effortless bilateral grounded B stance, knee-height flat elevated A.L foot with generous thigh clearance, crisp pelvis cupping & tucked arms |
| `UADG-DUAL-V00` | 5.0 | 7.0 | **8.9 / 10** | **+1.9** | 0 / 0 / 2 | Dead-coplanar flat horizontal A.L & B.L elevated feet on shared sofa plane, clear B elbow-to-knee triangle, clean thigh separation & tucked arms |
| **Mean** | **4.50** | **6.40** | **8.78 / 10** | **+2.38** | **0 / 0 / 9** | **4/4 promotion-ready (`8.5–8.9 / 10`), zero P0/P1, zero automated issues** |

---

## 2. Pass 02 Defect Resolution Matrix

- **Systemic P1 (A crouched knees `130–135°` & wide torso V-gap / pelvis misalignment):** **RESOLVED** — A grounded knees opened to `145.9°–147.2°` (`A hip_z ~1.17m`), B pelvis lowered (`~0.93m`, grounded knees `~131°`) for tight `3.4–3.7 cm` rear-over-front pelvis cupping & tucked extended A arms.
- **P1 (`FELV`, `FASS.R`, `RELV` A fingertip bleed-through on B upper arms):** **RESOLVED** — zero fingertip-to-deltoid bleed-through across all 16 PNGs.
- **P1 (`FASS.L` lateral shin clipping & fingers jutting past knee):** **RESOLVED (to minor P2)** — lateral shin clipping eliminated; palm cleanly cups underneath B's raised knee/popliteal crease.
- **P2 (`FELV`, `DUAL` elevated B.L foot roll):** **RESOLVED** — flat horizontal soles in `side` (dead-coplanar with A.L in `DUAL`) and natural grounded reading in `front`.

---

## 3. Per-Pose Diagnostics Summary

- **`UADG-FELV-V00` (`8.8`):** Grounded feet `0.0040m`; `A knees 147.0° / 147.0°`, `B_kR 131.2°`, `B_kL 86.2° @ 1.045m`; `closest_pelvis 0.0370m`; `mesh_min 0.0086m`, `4 <1cm`; `0` issues.
- **`UADG-FASS-V00` (`8.5`):** Grounded feet `0.0040m`; `A knees 147.2° / 146.9°`, `B_kR 131.0°`, `B_kL 56.5° @ 1.099m`; `closest_pelvis 0.0341m`; `left_rear_hand_supporting_front_raised_leg 0.1205m`; `mesh_min 0.0030m`, `61 <1cm` (active palm cradle); `B gaze -6.0° (achieved: true)`; `0` issues.
- **`UADG-RELV-V00` (`8.9`):** Grounded feet `0.0040m`; `A_kR 145.9°`, `A_kL 74.9° @ 0.966m`, `B knees 131.5° / 131.5°`; `closest_pelvis 0.0370m`; `mesh_min 0.0086m`, `4 <1cm`; `0` issues.
- **`UADG-DUAL-V00` (`8.9`):** Grounded feet `0.0040m`; `A_kR 145.9°`, `A_kL 80.3° @ 0.932m`, `B_kR 131.5°`, `B_kL 83.7° @ 0.934m`; `closest_pelvis 0.0370m`; `mesh_min 0.0068m`, `5 <1cm`; `0` issues.
