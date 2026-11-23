# Workspace Visual QA Audit — `UADG` Pass 02

- **Scope:** Experimental backward-roadmap batch #2 (`UADG-FELV-V00`, `UADG-FASS-V00`, `UADG-RELV-V00`, `UADG-DUAL-V00`)
- **Blender build:** Blender `5.2.2 LTS` (`4/4` rendered, exit code `0`, `4` views each, `0` JSON issues across all 4 poses)
- **Audit method:** Fresh-context blind QA auditor inspecting all 16 Pass 02 PNGs strictly before reading `pass-01/AUDIT.md`
- **Batch visual score:** **6.4 / 10** (`+1.9` vs Pass 01's `4.5 / 10`) — **Targeted Pass 03 recommended before promotion**

---

## Summary Table (Pass 01 → Pass 02)

| Pose ID | JSON Issues | Pass 01 | Pass 02 | Delta | Verdict | Visual Findings |
|---|---:|---:|---:|---:|---|---|
| `UADG-FELV-V00` | 0 | 4.0 | **6.0 / 10** | **+2.0** | Needs Pass 03 | **P0 fixed:** B's elevated left knee clears A's left forearm/wrist cleanly. **Remaining:** B.L elevated foot rolls slightly off horizontal in `front`; A fingertip bleed-through on B upper arms; A knees crouched (`133°`); wide torso V-gap |
| `UADG-FASS-V00` | 0 | 3.0 | **5.5 / 10** | **+2.5** | Needs Pass 03 | **P0s fixed:** A's left hand genuinely contacts/cradles underneath B's raised left knee & B.L foot cleanly clears A's legs. **Remaining:** A's left thumb/palm slightly clips B's lateral upper shin with fingers jutting forward past knee; right fingertip bleed-through on B upper arm; A crouch (`130°`); wide torso V-gap |
| `UADG-RELV-V00` | 0 | 6.0 | **7.0 / 10** | **+1.0** | Needs Pass 03 polish | Cleanest stance & balance: B bilateral grounded stance (`142.4°`), flat elevated A.L foot, zero leg/thigh clipping; **remaining:** A fingertip bleed-through on B upper arms; A.R knee `135°`; wide torso V-gap |
| `UADG-DUAL-V00` | 0 | 5.0 | **7.0 / 10** | **+2.0** | Needs Pass 03 polish | **P0s cleanly fixed:** A.L & B.L elevated feet sit dead-level on the exact same horizontal sofa plane (`side`); generous B elbow-to-knee clearance; zero thigh/glute clipping; cleanest shoulder hands. **Remaining:** Grounded knees (`A.R 132°`, `B.R 139°`); wide torso V-gap; mild outward roll on B.L foot |
| **Overall** | **0** | **4.5** | **6.4 / 10** | **+1.9** | **Run Pass 03** | All Pass 01 P0 collisions/misses resolved; localized surgical fixes remain for Pass 03 |

---

## Targeted Surgical Fixes for `UADG` Pass 03

1. **P1 (Systemic) Straighten grounded knees & close torso V-gap:** Raise standing torsos slightly (`A ~1.03 m`, `B ~0.99 m`) so grounded knees straighten to `~150–160°` ("softly flexed"), and pitch A further forward (`~60–62°`, with lifted neck/head/chest) to align upper torsos closely while maintaining clean A head clearance.
2. **P1 (`FELV`, `FASS.R`, `RELV`) Eliminate shoulder-hand fingertip bleed-through:** Shift A's shoulder-hand offset ~1–2 cm outward/upward (`ox=0.118, oz=0.045`) so zero blue fingertips pierce B's upper arms.
3. **P1 (`FASS.L`) Clean up left leg-cradle contact:** Shift A's left hand slightly posterior/downward (`[0.04, 0.09, -0.08]`) to cup smoothly underneath B's popliteal crease / upper calf without clipping the lateral shin or jutting fingers past the knee.
4. **P2 (`FELV`, minor `DUAL`) Level B's elevated left foot sole:** Reduce extreme lateral abduction slightly in `FELV` so the elevated left foot sole reads flat/horizontal on the virtual table plane in `front` view while preserving knee-to-wrist clearance.
