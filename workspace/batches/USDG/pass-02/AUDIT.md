# Visual QA Audit — `USDG` Pass 02

- **Family:** `USDG` (Upright Standing Doggy — Backward Family #3)
- **Pass:** `pass-02`
- **Build & Render Engine:** Blender `5.2.2 LTS` (`5/5` rendered, `exit_code: 0`, `0` automated JSON issues across all 5 poses)
- **Audit Protocol:** Independent fresh-context two-phase blind visual audit over `pass-summary.json`, all 5 `inputs/pose.json` & `blender-result.json`, and all 20 preview PNGs (`front`, `side`, `three-quarter`, `qa-regions`) before comparing against `pass-01/AUDIT.md`. Note: automated `issue_count: 0` did not flag `1` P0 and `14` P1 visual/anatomical defects identified by visual inspection.
- **Overall Blind Visual Score:** **6.88 / 10** (**+0.58** vs Pass 01's `6.30 / 10`)
- **Verdict:** **NEEDS PASS 03** (`PULL` 8.0 and `WALL` 7.9 are near promotion-ready, while `LOW` 5.4 [1 P0], `SURF` 6.3, and `EDGE` 6.8 need targeted fixes for torso-to-glute clipping, locked `179.7°` B knees, A-fingertip deltoid clipping, and elbow pole tucking).

---

## 1. Per-Pose Score Comparison (Pass 01 → Pass 02)

| Pose ID | Pass 01 | Pass 02 (Blind) | Delta | P0 / P1 / P2 | Visual Summary |
|---|---:|---:|---:|:---:|---|
| `USDG-EDGE-V00` | 6.0 | **6.8 / 10** | **+0.8** | 0 / 3 / 3 | Deeper hinge & grounded feet, but B has wide "chicken-wing" elbows + flat back, and A clips into B's deltoids & upper buttocks |
| `USDG-SURF-V00` | 6.5 | **6.3 / 10** | **-0.2** | 0 / 4 / 2 | Clean coplanar chest + forearm tabletop (~0.83m), but regressed to locked `179.7°` B knees, A-abdomen-into-B-glute clip, & A-fingertip deltoid clip |
| `USDG-WALL-V00` | 7.5 | **7.9 / 10** | **+0.4** | 0 / 2 / 3 | Strong vertical-palm wall brace, soft knees (`151°`), gentle lumbar arch & level gaze; mild A-lower-chest-to-B-glute overlap & wide A elbows |
| `USDG-LOW-V00` | 5.5 | **5.4 / 10** | **-0.1** | **1** / 3 / 2 | True standing deep fold (A no longer crouches), but **P0 A-chest-buried-in-B-buttocks clip**, locked `179.7°` B knees, `-67°` head drop & A-finger clip |
| `USDG-PULL-V00` | 6.0 | **8.0 / 10** | **+2.0** | 0 / 2 / 2 | Major Pass 02 win: natural hands-back arm path, cleanest mesh separation (`20 <1cm`), soft knees & lumbar curve; wide A elbows & slightly hovering flat B hands |
| **Mean** | **6.30** | **6.88 / 10** | **+0.58** | **1 / 14 / 12** | **PULL (+2.0) & WALL (+0.4) strong; LOW & SURF regressed via locked knees & torso/finger clipping** |

---

## 2. Per-Pose Visual Findings & Diagnostics

### `USDG-EDGE-V00` — **6.8 / 10** (`+0.8`) | `0 P0, 3 P1, 3 P2`
- **Diagnostics:** Feet grounded (`0.004m`); A knees `152.0°`, B knees `162.3°`; A `hip_z 1.108m`, B `hip_z 0.957m`, B `head_z 1.077m`; B gaze `-21.0°` (req `+2.0°`, `achieved: false`); `pelvis_proximity 0.382m`, `closest_pelvis_distance_m 0.0899m`; `mesh_sample min 0.00149m`, `p01 0.00669m`, `samples_under_1cm 213`.
- **Defects:**
  - **P1:** A fingertips clip into B's outer deltoids (`three-quarter`, `front`, new regression).
  - **P1:** A lower torso/abdomen overlaps B's upper buttocks (`side`, `three-quarter`, `213 <1cm`, persisted).
  - **P1:** B's elbows flare ~90° laterally ("chicken-wing") and back stays flat/horizontal instead of sloping down from high hips with subtle lumbar arch.
  - **P2:** B's palms/fingertips angle slightly upward off edge plane; B knees (`162.3°`) slightly stiff; A elbows flare in `front`.

### `USDG-SURF-V00` — **6.3 / 10** (`-0.2`) | `0 P0, 4 P1, 2 P2`
- **Diagnostics:** Feet grounded (`0.004m`); A knees `152.6°`, **B knees `179.7°` (locked)**; A `hip_z 1.094m`, B `hip_z 0.941m`, B `head_z 1.020m`; B gaze `-41.0°` (req `-2.0°`, `achieved: false`); `closest_pelvis_distance_m 0.0850m` (`rear_forward_shift +0.0114m`); `mesh_sample min 0.00194m`, `samples_under_1cm 226`.
- **Strengths:** Clean coplanar chest, forearms, and palms along horizontal ~0.83m tabletop plane.
- **Defects:**
  - **P1:** B's knees completely locked straight (`179.7°`, new regression).
  - **P1:** A lower torso/abdomen clips B's upper buttocks (`226 <1cm`, worsened by `+1.14cm` forward shift).
  - **P1:** A fingertips clip into B's outer deltoids (`three-quarter`, `front`, new regression).
  - **P1:** Flat horizontal back lacking hip-over-chest slope/lumbar arch + bowed B elbows.
  - **P2:** B head drops to `-41°` (`neck_assist_enabled: false`); moderate A elbow flare in `front`.

### `USDG-WALL-V00` — **7.9 / 10** (`+0.4`) | `0 P0, 2 P1, 3 P2`
- **Diagnostics:** Feet grounded (`0.004m`); A knees `151.7°`, B knees `151.1°`; A `hip_z 1.128m`, B `hip_z 1.045m`, B `head_z 1.295m`; B gaze `+1.25°` (`achieved: true`); `closest_pelvis_distance_m 0.0798m`; `mesh_sample min 0.00145m`, `samples_under_1cm 191`.
- **Strengths:** Crisp vertical-wall palm brace with softened elbows, soft `151°` knees on both actors, gentle lumbar arch, and natural level gaze (`+1.25°`).
- **Defects:**
  - **P1:** A lower chest/ribcage clips slightly into B's upper buttocks (`side`, `191 <1cm`, persisted).
  - **P1:** A elbows flare wide horizontally in `front`.
  - **P2:** Very slight fingertip graze on B's outer deltoid; slight outward bow in B's elbows; minor pelvic height offset.

### `USDG-LOW-V00` — **5.4 / 10** (`-0.1`) | `1 P0, 3 P1, 2 P2`
- **Diagnostics:** Feet grounded (`0.004m`); A knees `149.6°` (fixed crouch!), **B knees `179.7°` (locked)**; A `hip_z 1.048m`, B `hip_z 0.860m`, B `head_z 0.758m`; B gaze **`-67.0°`** (req `-16.0°`, `achieved: false`); `closest_pelvis_distance_m 0.0852m` (`rear_forward_shift +0.0107m`); `mesh_sample min 0.00167m`, `samples_under_1cm 167`.
- **Strengths:** Cleared `FORWARD_FOLD_NOT_ESTABLISHED` (`head_z < hip_z`), restored standing A posture (`149.6°`), and positioned B's palms cleanly near knee height (~0.50m).
- **Defects:**
  - **P0:** Severe interpenetration — A's lower chest/abdomen buries directly into B's upper buttocks/pelvis (`front` hard flat clip seam, `side` & `three-quarter` gluteal crest inside A's lower ribcage).
  - **P1:** B's knees completely locked straight (`179.7°`).
  - **P1:** B's head drops straight down (`-67°`) with a noticeably rounded upper-back hump.
  - **P1:** A fingertips clip into B's outer deltoids (`three-quarter`, `front`).
  - **P2:** B's fingers angle slightly up off ~0.50m plane with bowed elbows; A elbows flare in `front`.

### `USDG-PULL-V00` — **8.0 / 10** (`+2.0`) | `0 P0, 2 P1, 2 P2`
- **Diagnostics:** Feet grounded (`0.004m`); A knees `151.7°`, B knees `151.6°`; A `hip_z 1.128m`, B `hip_z 1.045m`, B `head_z 1.295m`; B gaze `+1.25°` (`achieved: true`); `closest_pelvis_distance_m 0.0798m`; `front_hand_to_rear_flank 0.285m`; `mesh_sample min 0.00444m`, `p01 0.01572m`, **`samples_under_1cm 20`** (cleanest in batch).
- **Strengths:** Natural hands-back arm path outside B's hips without shoulder strain, balanced soft `152°` knees, gentle lumbar arch, level gaze, and zero gross clipping.
- **Defects:**
  - **P1:** A elbows flare wide horizontally in `front`.
  - **P1:** B's hands stay rigid/flat and hover ~2–3cm off A's outer upper thighs rather than softly contacting A's flanks/hips.
  - **P2:** Minor seam graze between A's lower chest edge and B's upper buttocks (`min 4.4mm`); tiny deltoid fingertip graze in `front`.

---

## 3. Prioritized Pass 03 Fix Plan

1. **[P0 — `LOW`, `SURF`, `EDGE`, `WALL`] Eliminate A-torso-into-B-buttocks clipping:** Shift A rearward (`+0.03–0.05m` in `LOW`/`SURF`/`EDGE`, `+0.02–0.03m` in `WALL`), reduce A's excessive pitch over B's hips in `LOW`, and raise `pelvic_alignment` `target_distance_m` to `≥ 0.105m` (or disable forward shift when already close) so A's lower chest/abdomen clears B's upper buttocks cleanly in all views.
2. **[P1 — `LOW`, `SURF`, `EDGE`] Unlock B's `179.7°` knees:** Lower B's `torso_z` slightly (`~0.97–0.985m` in `SURF`/`LOW`/`EDGE`) and push knee poles forward so B stands on softly flexed `150–156°` knees instead of hyperextending at `179.7°`.
3. **[P1 — `EDGE`, `SURF`, `LOW`] Clear A-fingertip deltoid clipping:** Offset A's hand IK targets slightly outward/dorsally and tune palm orientation to match B's steeper pitched shoulders so fingers rest on top without piercing deltoid mesh.
4. **[P1 — `LOW`, `SURF`] Lift B's dropped head (`-67°` / `-41°`) & soften upper-back hump:** Enable `neck_assist_enabled: true` / increase cervical + upper-thoracic extension so B looks gently forward/down (`~-20°` in `LOW`, `~-10°` in `SURF`) with a smoother spine curve.
5. **[P1 — `EDGE`, `SURF`] Fix B's chicken-wing elbow flare & hip-over-chest slope:** Pull B's elbow poles downward and inward, flatten B's wrists onto the virtual edge, and add gentle hip-over-chest slope/lumbar lordosis.
6. **[P1/P2 — All 5 poses, esp. `WALL` & `PULL`] Tuck A's wide horizontal elbows + refine B's hands in `PULL`:** Lower A's `upper_arm_ik_target` `z` and pull inward so `front.png` reads as natural tucked elbows; in `PULL`, curve/tuck B's hands `~2cm` closer toward A's outer hips/thighs without clipping.
