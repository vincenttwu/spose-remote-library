# Rigify floor engine V2 — geometry diagnostics only

The builder uses the shared CPL01 rig, Rigify IK modes, explicit world torso/head/palm/foot targets, floor calibration based on evaluated material-region mesh samples, bounded pelvic adjustment and front/side/three-quarter/QA renders. It records floor supports, knee bend, hip/head levels, sampled floor penetration and contact proxies.

Do **not** equate contact proxies or support closeness with physical correctness. The r002 DOGG feedback demonstrates why: A hip 0.665m, B hip 0.272m, front folded too low despite ten contact supports close to the floor.

`hard_gate_pass` in legacy JSON is retained **only as a compatibility field describing diagnostic scores**. The importer no longer uses that value to block or disallow any usable draft. `geometry_reference_pass` is a clearer equivalent. Warnings show which geometry needs refinement later. We never claim a batch is accurate until its renders have been inspected, but we also never stop the batch or next batch for unreviewed warnings.

Batch 001 contains three silhouettes, not one posture copied five times: standard/closed tabletop kneeling; lower face-down and frog variants; standing forward fold. A shared calibration hypothesis can have class-specific parameters. All five must still render to compare actual geometry.
