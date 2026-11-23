# Workspace Visual QA Audit — `UFDG` Pass 01

- **Scope:** Experimental backward-roadmap Pass 01 (`UFDG-FWCH-V00`, `UFDG-WCHD-V00`, `UFDG-ELBW-V00`, `UFDG-QUAD-V00`, `UFDG-FFRG-V00`)
- **Blender build:** Blender `5.2.2 LTS` (`5/5` rendered, exit code `0`, `4` views each)
- **Audit method:** Independent fresh-context blind QA reviewer (inspected all 20 rendered PNGs against `inputs/pose.json` CSV specs and `blender-result.json`, without seeing authoring rationale)
- **Batch visual benchmark:** **4.7 / 10** — **Pass 02 required** (advisory; no quality gates)

> **Important honesty note:** Diagnostic JSON reported `0` issues on 3 poses (`FWCH`, `QUAD`, `FFRG`) and only `1` issue each on `WCHD` and `ELBW`, yet direct visual inspection revealed two P0 base/penetration failures (`WCHD`, `ELBW`) and a forearm-knee collision in `FFRG`. Metrics remain diagnostic only.

---

## Summary Table

| Pose ID | JSON Issues | Blind Visual Score | Verdict | Primary Visual Findings |
|---|---:|---:|---|---|
| `UFDG-FWCH-V00` | 0 | **5.5 / 10** | Needs Work | Clean hip-width front knees & wide grounded rear feet; B chest too elevated for child-like hinge; B fingers lift off floor; A lower torso clips B buttocks; A squat too shallow & hands stiff/uncupped |
| `UFDG-WCHD-V00` | 1 (`PELVIS_TOO_LOW`) | **3.0 / 10** | Fail (P0) | Wide front knees distinct from FWCH, **but both of A's hands deeply impale B's upper arms**; B face clips into floor (`body_min_z=-0.019 m`); B arms splay sideways instead of long forward; A straight-arm stilts with large torso gap |
| `UFDG-ELBW-V00` | 1 (`BELOW_FLOOR_PENETRATION`) | **3.5 / 10** | Fail (P0) | Good head clearance & grounded knees/rear feet, **but both of B's elbows float ~12–15 cm off the floor** (reads as bent-arm quadruped, not forearm support; `B/forearms` passed on wrist Z alone); B toes/wrists dip `-0.035 m` into floor |
| `UFDG-QUAD-V00` | 0 | **6.0 / 10** | Needs Work | Cleanest collision profile & clear higher-chest quadruped, but B palms hover (`z=0.017 m`) with upturned fingers; A is in a high half-squat (`hip_z=0.671 m`), not a deep frog squat; A fingers float past B shoulders |
| `UFDG-FFRG-V00` | 0 | **5.5 / 10** | Needs Work | Strong dual-frog silhouette with all 4 feet grounded flat and B knees off floor, **but A's forearms/elbows clip into B's raised thighs/knees**; B fingers hover; A squat shallower than B's |
| **Overall** | **2** | **4.7 / 10** | **Pass 02** | Solid first-pass silhouette differentiation (`FWCH`, `QUAD`, `FFRG`), with clear P0/P1 fixes identified for Pass 02 |

---

## Systemic Cross-Batch Findings

1. **Rear frog squat depth (Actor A):** Both rear feet are cleanly flat/grounded (zero rear kneeling), but A's hips sit well above A's knees across all 5 poses (`hip_z` `0.50–0.67 m` vs `knee_z` `0.37–0.42 m`), especially in `QUAD`.
2. **Rear palm turn-in on outer shoulders (V00 baseline):** A's hands behave like flat straight paddles extending forward past B's deltoids (`FWCH`, `ELBW`, `QUAD`, `FFRG`) or impaling B's upper arms (`WCHD`). Needs lateral-outer placement + inward palm rotation toward B's outer deltoids.
3. **Front palm contact (Actor B):** B's wrists pitch upward so only the heel of the palm touches while fingers hover ~2–4 cm off the floor (`FWCH`, `WCHD`, `QUAD`, `FFRG`).
4. **Upper-arm mesh twist shading (`ELBW`, `QUAD`, `FFRG`):** Diagonal skinning crease bands appear on B's upper arms from elbow-pole / shoulder roll alignment.

---

## Prioritized Fixes for `UFDG` Pass 02

1. **P0 — `UFDG-ELBW-V00` true elbow/forearm floor support:** Lower B's chest/shoulders and adjust `hand_ik` + elbow pole targets so **both elbows AND forearms rest flat on `z ≈ 0.004 m`** (verify `DEF-forearm` head Z separately, not just wrist Z), and remove the `-0.035 m` toe/wrist floor dip.
2. **P0 — `UFDG-WCHD-V00` eliminate hand-through-arm clipping & face floor dip:** Raise B's pelvis (`hip_z ≈ 0.28–0.32 m`) and lift B's head/neck clear of the floor; straighten B's arms long forward instead of splayed sideways; route A's hands outside B's lateral deltoids and drop A's torso closer to B.
3. **P0 — `UFDG-FFRG-V00` eliminate forearm-into-knee clipping:** Widen/raise A's elbow pole path cleanly outside B's raised knees before angling A's forearms inward to B's outer shoulders.
4. **P1 — Deepen A's frog squat & close upper-torso gap across all 5 poses:** Lower A's hips closer to knee height (especially `QUAD`), pitch A's torso forward closer to B's back, and back A's pelvis slightly in `FWCH`/`WCHD` to eliminate A-abdomen/B-buttock clipping.
5. **P1 — Fix A's outer-shoulder palm orientation & B's flat floor palms:** Turn A's palms inward around B's lateral deltoids; pitch B's floor hands flat so fingers rest on the floor (`z ≈ 0.004 m`), and lower B's chest further in `FWCH`.
6. **P2 — Reduce B upper-arm twist banding (`ELBW`, `QUAD`, `FFRG`):** Tune B's elbow pole targets to relax upper-arm twist.
