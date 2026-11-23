# Visual QA Audit — `batch-0003` (`USDG`) Pass 03

- **Batch / Pass:** `batch-0003` (`USDG`, Backward Family #3) / `pass-03`
- **Snapshot:** `snapshots/batch-0003-pass-03_20261123T174738Z`
- **Revisions:** `poses/USDG-*/CPL01/v001/r003` (`reused_existing_package: false` on all 5)
- **Build & Render Engine:** Blender `5.2.2 LTS` (`5/5` rendered, `exit_code: 0`, `20/20` previews, `1` automated JSON issue on `USDG-LOW-V00`: `FORWARD_FOLD_NOT_ESTABLISHED`)
- **Audit Protocol:** Strict fresh-context two-phase blind visual audit over `batch-summary.json`, all 5 `r003/inputs/pose.json` & `r003/blender-result.json`, and all 20 PNGs in `workspace/review/` before comparing against `batch-0003-pass-02` `AUDIT.md`.
- **Overall Blind Visual Score:** **8.24 / 10** (**+1.36** vs Pass 02's `6.88 / 10`; **+1.94** vs Pass 01's `6.30 / 10`)
- **Defects:** **0 P0 / 1 P1 / 10 P2** (down from Pass 02's `1 P0 / 14 P1 / 12 P2`)
- **Verdict:** **4/5 READY FOR REVIEW & PROMOTION (`WALL` 8.9, `PULL` 8.7, `SURF` 8.6, `EDGE` 8.3)**; optional targeted Pass 04 polish only if desired for `USDG-LOW-V00` (`6.7`, 1 P1 A-lower-chest-to-B-buttocks clip + fold flag).

---

## 1. Per-Pose Score Progression (Pass 01 → Pass 02 → Pass 03)

| Pose ID | Pass 01 | Pass 02 | Pass 03 (Blind) | Delta vs Pass 02 | P0 / P1 / P2 | Visual Summary |
|---|---:|---:|---:|---:|:---:|---|
| `USDG-EDGE-V00` | 6.0 | 6.8 | **8.3 / 10** | **+1.5** | 0 / 0 / 2 | Clean pelvis cupping, soft knees (`143°/145°`), tucked A elbows & clean shoulder palms; minor upward forearm slope from low B elbows |
| `USDG-SURF-V00` | 6.5 | 6.3 | **8.6 / 10** | **+2.3** | 0 / 0 / 2 | Crisp coplanar chest/forearms, unlocked `146.7°` B knees, clear hip-over-chest lumbar arch & tight pelvis cupping; slightly stiff forward B forearms |
| `USDG-WALL-V00` | 7.5 | 7.9 | **8.9 / 10** | **+1.0** | 0 / 0 / 2 | Standout ~90° hinge with level arms, unmistakable vertical-wall flat palms, `-8°` gaze, clean cupping & tucked A arms; slight B elbow sag |
| `USDG-LOW-V00` | 5.5 | 5.4 | **6.7 / 10** | **+1.3** | 0 / **1** / 2 | Deep standing fold with unlocked `145.9°` B knees & clean shoulder palms, but **P1 A-lower-chest clips B's upper buttocks**, A knees `136.9°`, & fold flag |
| `USDG-PULL-V00` | 6.0 | 8.0 | **8.7 / 10** | **+0.7** | 0 / 0 / 2 | Natural unstrained hands-back path onto A's outer hips, tucked A arms, clean cupping, `-6°` gaze & zero clipping; slightly stiff B fingers |
| **Mean** | **6.30** | **6.88** | **8.24 / 10** | **+1.36** | **0 / 1 / 10** | **Decisive batch-wide jump (+1.36); 4/5 promotion-ready (`8.3–8.9`), only `LOW` retains 1 P1** |

---

## 2. User-Requested Fix & Pass 02 Resolution Summary

- **Pelvis cupping & height alignment (`A hip > B hip`, no wide air gap):** Fully resolved on `EDGE`, `SURF`, `WALL`, and `PULL` (`samples_under_1cm` plunged from `213/226/191/167/20` → `5/15/60/15/5`; `A hip_z > B hip_z` on all 5). `LOW` improved from P0 to a smaller P1 lower-chest edge graze against B's upper buttocks.
- **`USDG-WALL-V00` ~90° front bend reaching forward to vertical wall:** Fully resolved (`8.9 / 10`, standout pose of the batch).
- **Relaxed standing knees (unlock `179.7°` B knees):** Resolved on all 5 front actors (`144.3°–146.7°`) and 4/5 rear actors (`143.0°–143.1°`); `LOW` rear knees `136.9°` (mildly deep).
- **Extended tucked rear arms & clean deltoid palms:** Fully resolved across all 5 poses — zero A horizontal wing flare and zero fingertip bleed-through in any view.

---

## 3. Detailed Per-Pose Diagnostics

### `USDG-EDGE-V00` — **8.3 / 10** (`+1.5`) | `0 P0, 0 P1, 2 P2`
- Feet grounded (`0.0040m`); knees `A 143.0°`, `B 145.4°`; `A hip_z 1.153m > B hip_z 0.931m`; B gaze `-22.0°`; `closest_pelvis_distance_m 0.0057m`; `mesh_sample min 0.0059m`, `samples_under_1cm 5`; `0` issues.
- **P2:** B elbows hang ~8–10cm lower than wrists causing a mild upward forearm slope toward the edge; back sits nearly level (~90°).

### `USDG-SURF-V00` — **8.6 / 10** (`+2.3`) | `0 P0, 0 P1, 2 P2`
- Feet grounded (`0.0040m`); knees `A 143.0°`, `B 146.7°`; `A hip_z 1.136m > B hip_z 0.904m`; B gaze `-28.0°`; `closest_pelvis_distance_m 0.0015m`; `mesh_sample min 0.0053m`, `samples_under_1cm 15`; `0` issues.
- **P2:** B forearms/fingers extend forward somewhat stiffly; gaze `-28.0°` slightly below target `-8°`.

### `USDG-WALL-V00` — **8.9 / 10** (`+1.0`) | `0 P0, 0 P1, 2 P2`
- Feet grounded (`0.0040m`); knees `A 143.0°`, `B 144.4°`; `A hip_z 1.166m > B hip_z 0.955m`; B gaze `-8.0°`; `closest_pelvis_distance_m 0.0167m`; `mesh_sample min 0.0029m`, `samples_under_1cm 60`; `0` issues.
- **P2:** Slight ~3–4cm elbow sag below shoulder-wrist line; fingers pressed tightly together.

### `USDG-LOW-V00` — **6.7 / 10** (`+1.3`) | `0 P0, 1 P1, 2 P2`
- Feet grounded (`0.0040m`); knees `A 136.9°`, `B 145.9°`; `A hip_z 1.075m > B hip_z 0.841m`, `B head_z 0.816m`; B gaze `-41.0°`; `closest_pelvis_distance_m 0.0032m`; `mesh_sample min 0.0047m`, `samples_under_1cm 15`; `1` issue (`FORWARD_FOLD_NOT_ESTABLISHED`: `head 0.816m hip 0.841m`, 2.5cm drop vs 6cm threshold).
- **P1:** A's lower chest edge clips into the upper crest of B's buttocks (`front`, `side`, `three-quarter`), paired with slightly squatty A knees (`136.9°`).
- **P2:** Automated fold margin short by 3.5cm (`head_z 0.816m` vs `hip_z 0.841m`); mild outward bow in B elbows in `front`.

### `USDG-PULL-V00` — **8.7 / 10** (`+0.7`) | `0 P0, 0 P1, 2 P2`
- Feet grounded (`0.0040m`); knees `A 143.1°`, `B 144.3°`; `A hip_z 1.168m > B hip_z 0.969m`; B gaze `-6.0°` (`achieved: true`); `closest_pelvis_distance_m 0.0169m`; `front_hand_to_rear_flank 0.239m`; `mesh_sample min 0.0083m`, `samples_under_1cm 5`; `0` issues.
- **P2:** B rear-reaching fingers slightly rigid/flat along A's outer pelvis/thigh seam; minor finger rigidity on A.

---

## 4. Optional Targeted Polish (if user requests Pass 04 for `USDG-LOW-V00`)
1. Shift A `~2–3cm` rearward, reduce A torso pitch `~6–8°`, and raise A knees `136.9° → ~143°` to clear the remaining P1 A-lower-chest-to-B-buttocks clip.
2. Drop B's chest/head `~3.5cm` lower (or lift B pelvis `~1.5cm` keeping ~145° knees) to clear `FORWARD_FOLD_NOT_ESTABLISHED`.
3. Optionally raise B's elbow poles in `USDG-EDGE-V00` slightly so forearms angle level/downward onto the waist-height edge.
