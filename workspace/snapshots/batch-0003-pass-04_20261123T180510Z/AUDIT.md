# Visual QA Audit — `batch-0003` (`USDG`) Pass 04

- **Batch / Pass:** `batch-0003` (`USDG`, Backward Family #3) / `pass-04`
- **Snapshot:** `snapshots/batch-0003-pass-04_20261123T180510Z`
- **Revisions:** `poses/USDG-*/CPL01/v001/r004` (`reused_existing_package: false` on all 5, `scene_blend_saved: true` on all 5)
- **Build & Render Engine:** Blender `5.2.2 LTS` (`5/5` rendered, `exit_code: 0`, `20/20` previews, **`0` automated JSON issues** across all 5 poses)
- **Audit Protocol:** Strict fresh-context two-phase blind visual audit over `batch-summary.json`, all 5 `r004/inputs/pose.json` & `r004/blender-result.json`, and all 20 PNGs in `workspace/review/` before comparing against Pass 03 `AUDIT.md`.
- **Overall Locked Blind Score:** **8.70 / 10** (**+0.46** vs Pass 03's `8.24 / 10`; **+1.82** vs Pass 02's `6.88 / 10`; **+2.40** vs Pass 01's `6.30 / 10`)
- **Total Defects:** **0 P0 / 0 P1 / 9 P2** (down from Pass 03's `0 P0 / 1 P1 / 10 P2`)
- **Verdict:** **5/5 READY FOR USER REVIEW & PROMOTION** — all 5 poses score `8.5–8.9 / 10` with zero P0/P1 defects and zero automated issues.

---

## 1. Per-Pose Score Progression (Pass 01 → Pass 02 → Pass 03 → Pass 04)

| Pose ID | Pass 01 | Pass 02 | Pass 03 | Pass 04 (Blind) | Delta vs P03 | P0 / P1 / P2 | Visual Summary |
|---|---:|---:|---:|---:|---:|:---:|---|
| `USDG-EDGE-V00` | 6.0 | 6.8 | 8.3 | **8.7 / 10** | **+0.4** | 0 / 0 / 2 | Clean lower-set B pelvis (`132.8°` knees) cupped by A (`147.0°`), proper downward forearm slope to edge, zero clipping |
| `USDG-SURF-V00` | 6.5 | 6.3 | 8.6 | **8.6 / 10** | **0.0** | 0 / 0 / 2 | Crisp coplanar chest & horizontal forearms on tabletop, lower-set B pelvis (`133.7°`), clean lumbar arch & cupping |
| `USDG-WALL-V00` | 7.5 | 7.9 | 8.9 | **8.9 / 10** | **0.0** | 0 / 0 / 1 | Standout ~90° hinge with level arms, unmistakable vertical-wall palms, `-8°` gaze, clean lower-set B pelvis (`132.0°`) |
| `USDG-LOW-V00` | 5.5 | 5.4 | 6.7 | **8.5 / 10** | **+1.8** | 0 / 0 / 2 | Deep standing fold established (`head 7.5cm < hip`, `0` issues), relaxed knees (`A 142.3° / B 137.2°`), P1 chest clip cleared |
| `USDG-PULL-V00` | 6.0 | 8.0 | 8.7 | **8.8 / 10** | **+0.1** | 0 / 0 / 2 | Unstrained hands-back path onto A outer hips, lower-set B pelvis (`132.0°`), clean cupping, `-6°` gaze (`achieved: true`) |
| **Mean** | **6.30** | **6.88** | **8.24** | **8.70 / 10** | **+0.46** | **0 / 0 / 9** | **5/5 promotion-ready (`8.5–8.9 / 10`), zero P0/P1, zero automated issues** |

---

## 2. Targeted Pass 04 Verification

- **Front pelvis visibly slightly lower than rear pelvis via deeper relaxed B knee bend:** Verified across all 5 poses (`B` knees `132.0°–137.2°`, `A` knees `142.3°–147.0°`; `closest_pelvis_distance_m`: `0.0182m–0.0341m`).
- **`USDG-LOW-V00` Pass 03 P1 chest clip & `FORWARD_FOLD_NOT_ESTABLISHED`:** Both resolved (`issues: []`, `B head_z 0.728m` vs `B hip_z 0.803m`, `7.5 cm` drop; `closest_pelvis_distance_m 0.0249m`, zero polygon poke-through).
- **Floor & contact cleanliness:** All 20 feet grounded (`0.0040m`), zero fingertip-to-deltoid bleed-through, zero thigh/knee collisions, clear 5-way silhouette differentiation.

---

## 3. Per-Pose Diagnostics Summary

- **`USDG-EDGE-V00` (`8.7`):** Knees `A 147.0° / B 132.8°`; `A hip 1.154m > B hip 0.896m`; `closest_pelvis 0.0246m`; `mesh_min 0.0063m`, `7 <1cm`; `0` issues. P2: mild front-view outward B elbow bow & tiny ~1 cm lateral palm-heel gap.
- **`USDG-SURF-V00` (`8.6`):** Knees `A 147.0° / B 133.7°`; `A hip 1.140m > B hip 0.869m`; `closest_pelvis 0.0182m`; `mesh_min 0.0087m`, `5 <1cm`; `0` issues. P2: minor front-view lateral wrist gap & snug `1.8cm` pelvic clearance.
- **`USDG-WALL-V00` (`8.9`):** Knees `A 146.9° / B 132.0°`; `A hip 1.165m > B hip 0.920m`; `closest_pelvis 0.0336m`; `mesh_min 0.0040m`, `47 <1cm`; `0` issues. P2: tiny ~1 cm front-view outer palm-heel gap.
- **`USDG-LOW-V00` (`8.5`):** Knees `A 142.3° / B 137.2°`; `A hip 1.076m > B hip 0.803m`; `B head 0.728m` (`7.5 cm` drop); `closest_pelvis 0.0249m`; `mesh_min 0.0018m`, `52 <1cm`; `0` issues. P2: hairline surface kiss between A lower-chest rim & B upper-glute crest (no poke-through), mild frontal wrist gap & open B fingers.
- **`USDG-PULL-V00` (`8.8`):** Knees `A 146.9° / B 132.0°`; `A hip 1.168m > B hip 0.934m`; `closest_pelvis 0.0341m`; `front_hand_to_rear_flank 0.250m`; `mesh_min 0.0080m`, `4 <1cm`; `0` issues. P2: stiff open B fingers on lower hip/thigh border & tiny frontal palm-heel gap.
