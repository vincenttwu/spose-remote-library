# Batch 0001 Pass 05 — geometry calibration plan

**Origin:** Pass-04 combined feedback `spose-remote-feedback-batch-0001-pass-04_20261123T135002Z.zip`. Pass 04 produced 5 authoritative baseline revisions, 10 local experiments, 40 recorded images; user and remote auditor agreed that the locally selected candidates were better overall but not stable enough to stop refining. **Pass 05 packages are seeded from the exact selected Attempt-02 `rig-targets.json` for each pose**, not from the weaker Pass-04 baseline. The new packages have distinct timestamp identities and will create new tracked baseline revisions.

## Real Pass 04 selected diagnostics

| Pose | Visual score /10 (remote) | Measured evidence | Pass-05 change |
|---|---:|---|---|
| DOGG-DOGG-V00 | 7.0 | Front B hip ~0.456m, B gaze +11°, B palms near floor, hand/hip p50 ~18.7mm | Preserve selected shape; one final floor support recheck after all solvers |
| DOGG-CLSD-V00 | 6.8 | B hip ~0.460m, gaze +11°; retains narrow-knee variant | Same correction without widening knees |
| DOGG-DOWN-V00 | 4.4 | Correct forward gaze restored at -5°, but palms ~0.124m above floor and head ~0.082m ABOVE hip | Conservative halfway torso/fold adjustment and final bounded hand-floor calibration |
| DOGG-FCDN-V00 | 6.7 | Head-side near ~0.024m from floor; forearm mesh min ~-0.011m below floor | Preserve side-facing low head; lift forearm contact target by ~1 cm |
| DOGG-FROG-V00 | 6.1 | Head still angled down -16°, front palms ~0.034m above floor, wide foot stance reduced collision | Optional sampled neck+head aim, then last grounded-palm recheck |

Numbers are from recorded mesh/rig proxies, not ground truth about forces or intentional anatomy. Do not turn tolerance thresholds into blocking conditions.

## Why this can work better than Pass 04

- Pass-04 head search varied only the head bone; the FROG head did not rise, suggesting its neck/rest pose affects the reachability of the required vector. Pass-05 optionally samples BOTH neck and head X rotations on FROG and scores actual measured world forward gaze. DOGG/CLSD retain prior head-only behavior.
- Pass-04 floor checks often ran before later styling/contact changes. DOWN's palms were about 12cm high even when earlier stages had moved the hands near ground. Pass-05 adds a final bounded recalibration of B palm/forearm regions *after* the pelvic/hand solver. If the support is unreachable, record that rather than destroying the silhouette.
- The new baseline uses the demonstrated good local trial controls. This is a seed for a fresh iteration, not an automatic promotion of historical trial objects.

## Pose-specific visual judgment (important for the local agent)

**DOGG / CLSD:** retain +11° forward/up head, established kneeling/knee contact and bilateral hand-on-hip appearance. Check whether A's palms really touch hip *area* (coverage and angle), not merely one closest vertex. B pelvis still reads slightly low but avoid blindly lifting it if knee/palm support breaks. CLSD must remain visibly narrower than DOGG.

**DOWN:** show a standing forward fold with B's head LOWER than B pelvis while B looks forward/slightly upward via neck extension. B's palms must visibly rest on floor; do not increase head height to obtain a forward gaze. Inspect upper-arm reach; moving the IK handle alone may be insufficient. A should remain behind, not separated from B. First local trial should prioritize the *reachability* of B arms/fold; second may polish partner contact if support holds.

**FCDN:** low face-to-side posture, not a raised-head pose. Target forearm support without several centimeters of penetration. If raising forearms lifts head/cheek, do not overfit floor numbers at the expense of the intended fold.

**FROG:** retain the improved wide stance and no foot/knee collision, but the B face must rotate forward/up (not -16° down). Ground palms; knees are not specified as support. Inspect the neck/head in side and three-quarter renders.

## Measurement references (not gates)

- Convincing rear palm-to-hip contact: compare median patch gap, fraction of palm patch within 30mm, wrist/palm orientation and close-up render. `p50 <=0.03m` and `coverage30 >=0.45` are rough references, not universal quality guarantees.
- Head world gaze: for non-FCDN a roughly +8..+18° elevation with a positive -Y forward dot is a target; check actual face in side/3/4 views. FCDN intentionally has negative elevation and side roll.
- DOWN hands: effective B palm region z <=0.03m, head below hip by >=0.045m, and standing (not knee-ground) support.
- FCDN forearms: roughly -0.005..0.035m surface z is a reference; 11mm penetration in Pass04 is worth reducing.
- FROG palms: <=0.03m z, wide feet clear of rear knees; do not force front knees down.

## Local additive workflow

Default is baseline Attempt00 plus *up to* two optional local guided refinements per pose, with all five in same pass. Set `--local-calibration off` to disable, or `--max-local-attempts 1` to limit. Proposals are bounded data-only changes, not arbitrary scripts. The local agent should select independently among attempts 00/01/02 and can select baseline if local trials worsen geometry. One feedback ZIP records all changes, measurements and selected images; no quality gates.

## Audit and reproducibility

Report `new_revision_count` from the baseline batch; it should normally be 5 because the package timestamps are new, but a failed technical import can produce fewer. If an imported pose is unexpectedly reused, identify it explicitly. The final selected trial is preserved with exact `rig-targets.json` and hash in snapshots. Don't silently mark experiments `accepted` or delete evidence. Pass 4 metadata and source hashes are carried in `PASS-05-PROVENANCE.json` in the release. No Blender runtime improvement is claimed until the local agent completes the next run.
