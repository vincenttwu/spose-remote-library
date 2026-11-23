# Workspace Visual QA Audit — `USDG` Pass 01

- **Scope:** Experimental backward-roadmap batch #3 (`USDG-EDGE-V00`, `USDG-SURF-V00`, `USDG-WALL-V00`, `USDG-LOW-V00`, `USDG-PULL-V00`)
- **Blender build:** Blender `5.2.2 LTS` (`5/5` rendered, exit code `0`, `4` views each)
- **Audit method:** Fresh-context blind QA auditor inspecting all 20 Pass 01 PNGs against `inputs/pose.json` CSV specs and `blender-result.json`
- **Batch visual benchmark:** **6.3 / 10** — strongest Pass 01 starting score across all workspace families (`UFDG` 4.7, `UADG` 4.5); **targeted Pass 02 calibration recommended**

---

## Summary Table

| Pose ID | JSON Issues | Blind Score | Verdict | Primary Visual Findings |
|---|---:|---:|---|---|
| `USDG-EDGE-V00` | 0 | **6.0 / 10** | Needs Pass 02 | Clean grounded soft-knee stance (`147°/152°`), clean A shoulder palms & head clearance; **B chest sits above hips** (needs deeper hinge + mild lumbar curve); A-to-B pelvis clip; stiff B elbows |
| `USDG-SURF-V00` | 0 | **6.5 / 10** | Needs Pass 02 | **Strong horizontal chest + elbow + forearm tabletop alignment (~0.85m)** clearly distinct from `EDGE`; **A-pelvis-to-B-buttocks clipping (`209` `<1cm`)**; B hips level with upper back; pinched `-60°` neck kink |
| `USDG-WALL-V00` | 0 | **7.5 / 10** | Best in Batch | **Unmistakable vertical wall brace:** dead-level arms, coplanar vertical palms with fingers UP, subtle inward lumbar curve, clean A shoulder palms & head clearance; **A-to-B pelvis clip (`190` `<1cm`)**; rigid locked B elbows |
| `USDG-LOW-V00` | 1 (`FORWARD_FOLD_NOT_ESTABLISHED`) | **5.5 / 10** | Needs Pass 02 | Both remain standing with palms near knee height (~0.53m), clean A shoulder palms & head clearance; **B hips dropped too low (`0.871m`) instead of folding deeper through high hips**; A crouches (`129°`); pelvis clip |
| `USDG-PULL-V00` | 0 | **6.0 / 10** | Needs Pass 02 | Correct hands-back topology with clean A-over-B arm separation and zero shoulder bleed-through; **B arms run too high/horizontal (forced shoulder extension, forearm grazing waist)** instead of dropping past outer hip line; pelvis clip |
| **Overall** | **1** | **6.3 / 10** | **Run Pass 02** | Grounded feet, zero A-shoulder bleed-through, clean head clearance, and 5 distinct silhouettes all established on Pass 01 |

---

## Prioritized Concrete Fixes for `USDG` Pass 02

1. **[P0 — All 5 poses] Eliminate A-pelvis-to-B-buttocks clipping:** Back off `pelvic_alignment` (`target_distance_m: 0.09` / shift A rearward ~`+0.03–0.04m`) so A's lower abdomen clears B's buttocks cleanly in `side` view while keeping upper torsos aligned.
2. **[P0 — `USDG-LOW-V00`] High hips + deeper forward fold:** Keep B's hips up (`~0.96m`, knees `~150°`), fold deeper through the hips (`pitch ~120°`) so chest & head drop well below hips (`FORWARD_FOLD_NOT_ESTABLISHED` cleared), keep palms on `~0.50m` plane, and raise A's knees from `129°` into `148°+` standing range.
3. **[P0 — `USDG-EDGE-V00`] Deepen B's hip hinge & soften elbows:** Increase B's torso pitch (`~88–92°`) with gentle lumbar lordosis so hips sit clearly higher than chest, and add soft elbow bend (`~150–160°`) on the `~0.82m` edge.
4. **[P1 — `USDG-PULL-V00`] Lower B's rearward arm path past outer hips:** Drop B's elbows/upper arms lower (`~15–25°` downward, slightly wider laterally) so forearms pass cleanly below/outside B's hips without forced shoulder hyperextension, then flex softly onto A's outer flanks.
5. **[P1 — `USDG-SURF-V00`] Elevate B's hips above chest & smooth neck:** Raise B's hips slightly with mild lumbar contour while preserving coplanar chest + forearm tabletop contact, and distribute head lift across neck + head.
6. **[P2 — Batch polish]:** Tuck A's wide-flaring elbows slightly inward across all 5 poses, add a slight soft bend (`~165°`) to B's elbows in `WALL`, and smooth B's neck pitch in `SURF` & `LOW`.
