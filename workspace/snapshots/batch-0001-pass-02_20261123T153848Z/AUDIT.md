# Workspace Visual QA Audit — `UFDG` Pass 02

- **Scope:** Experimental backward-roadmap Pass 02 (`UFDG-FWCH-V00`, `UFDG-WCHD-V00`, `UFDG-ELBW-V00`, `UFDG-QUAD-V00`, `UFDG-FFRG-V00`)
- **Blender build:** Blender `5.2.2 LTS` (`5/5` rendered, exit code `0`, `4` views each, **`0` JSON issues across all 5 poses**)
- **Audit method:** Fresh-context blind QA auditor (inspected all 20 Pass 02 PNGs + `pose.json` + `blender-result.json` strictly before reading `pass-01/AUDIT.md`)
- **Batch visual score:** **6.7 / 10** (`+2.0` vs Pass 01's `4.7 / 10`) — **Targeted Pass 03 recommended before promotion**

> **Diagnostic honesty note:** All 5 poses report `0` JSON issues and `hard_gate_pass: true`, yet direct visual inspection confirmed two systemic issues across all 5 poses: (1) B's palms/fingers hover on drooping thumb-tips, and (2) A's nose/chin clips into B's upper back (severe in `QUAD`, mild-to-moderate in the other 4).

---

## Summary Table (Pass 01 → Pass 02)

| Pose ID | JSON Issues | Pass 01 | Pass 02 | Delta | Verdict | Visual Findings |
|---|---:|---:|---:|---:|---|---|
| `UFDG-FWCH-V00` | 0 | 5.5 | **6.8 / 10** | **+1.3** | Needs Pass 03 | Deep rear frog squat (`hip_z=0.416 m` vs `knee_z=0.420 m`), clean outer-shoulder hands, grounded hip-width knees & lowered chest; **B palms hover on thumb-tips**; **A nose/chin clips B upper back** |
| `UFDG-WCHD-V00` | 0 | 3.0 | **6.8 / 10** | **+3.8** | Needs Pass 03 | All Pass 01 P0s solved: clearly wide knees, low chest, long straight arms, face clear (`head_z=0.202 m`), zero A-hand-to-B-arm clip; **B palms hover on thumb-tips**; **A nose/chin clips B upper back** |
| `UFDG-ELBW-V00` | 0 | 3.5 | **7.5 / 10** | **+4.0** | Best in Batch | Pass 01 P0 fully solved: **both elbows AND full forearms rest genuinely flat on floor**, zero floor penetration, head clear, deep A squat & clean outer-shoulder hands; mild **A nose/chin touch on B back** + slight upward B wrist pitch |
| `UFDG-QUAD-V00` | 0 | 6.0 | **5.5 / 10** | **-0.5** | Needs Pass 03 (P0 Regression) | Much deeper A frog squat (`hip_z=0.483 m` vs `0.671 m`), clean outer-shoulder hands & quadruped silhouette, **but P0 regression: A's lower face (nose/mouth/chin) penetrates B's upper back**; **B palms hover on thumb-tips** |
| `UFDG-FFRG-V00` | 0 | 5.5 | **6.8 / 10** | **+1.3** | Needs Pass 03 | Pass 01 P0 solved: **zero A-forearm-to-B-knee impaling**, clean 4-foot double-frog silhouette with B knees off floor (`0.420 m`), deep A squat; **B palms hover on thumb-tips**; **A nose/chin clips B upper back** |
| **Overall** | **0** | **4.7** | **6.7 / 10** | **+2.0** | **Run Pass 03** | All Pass 01 P0 structural/collision failures resolved; only 2 targeted fixes left before promotion readiness |

---

## Targeted Fixes for Pass 03 (High-ROI, Low-Risk)

1. **P0 — Eliminate A's face-into-B-back clipping (all 5 poses, critical in `QUAD`):**
   - Lift A's `neck` and `head` pitch (`POSE_LOCAL_REST_AXIS_ROT_X_DEG`) so A looks forward over B's shoulders instead of burying A's face into B's upper back, and back off A's forward torso lean / `pelvic_alignment` shift slightly (`~2–4 cm` in `QUAD`, `~1–2 cm` in the other 4) to relieve the tight A-lower-chest / B-buttock seam while keeping upper torsos close.
2. **P0 — Flatten B's floor palms (all 5 poses):**
   - Inspect exact Rigify hand bone `direction_world` / `normal_world` pitch sign so B's palm pad and all four fingers rest flat along `z ≈ 0.004 m` rather than tilting upward on drooping thumb-tips.
