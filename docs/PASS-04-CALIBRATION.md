# Batch 0001 Pass 04 — measured geometry experiment

## Why this pass is necessary

Pass 03 created five **new** revisions and introduced surface-based proximity targeting. Images were judged worse overall: head raising was absent, many rear hands remained visibly detached, and pelvis pairing was still weak. The new feedback shows that some palm-to-hip nearest distances were 0.3–2 mm, despite floating hands in the renders. One vertex can make that metric appear successful. FCDN and DOWN could not localize wrist-near palm vertices. A numerical zero-issue report on FROG was not evidence of visual success.

## Changes made in the five new pose modules / builder

1. All five have **fresh package timestamps and payload hashes**. A successful import creates genuinely new revisions.
2. The surface-contact heuristic selects a bounded *palm patch*, aims its centroid toward a lateral pelvis patch, measures distance percentiles and percentage of the patch within 30 mm. A single minimum vertex is diagnostic only, not success.
3. The front head is given an explicit world-forward/elevation target. For DOGG, CLSD and FROG target approximately +13° elevation; for DOWN approximately +7°; for FCDN approximately −60° and preserve its sideways head roll. The engine samples both local-X pitch signs before choosing. These are **provisional targets**, not proven real gaze directions.
4. DOWN starts its front-hand IK targets slightly lower and permits a larger bounded ground recalibration. Floor-contact assertions remain reference notes, never stop points.
5. FCDN keeps the low torso/forearm support and is exempt from the raised-head target. The solver avoids simply lowering its entire torso, since Pass 03 already showed below-floor body penetration.
6. All five are built and rendered together with saved scenes; a read-only calibration process measures neutral rig response and each final scene, then embeds results into the one combined feedback ZIP.

## Interpret numerical results with caution

- p50 hand-to-pelvis distance and the within-30mm fraction are useful but still unsigned, based on material regions and not full physical contact mechanics.
- Head elevation is computed from RIG001's reference -Y forward axis propagated through rest-to-pose head rotation, not actual eye gaze. Check the side view to validate whether the model appears to look ahead/up.
- Pelvis-bone anchors can remain far apart even when hip meshes approach. Do not loosen tolerance just to obtain green status.
- The calibration survey is primarily intended to improve future passes. It does not guarantee Pass 04 will visually exceed Pass 03; only Blender renders will show this.

## User-facing review after feedback

Compare all five side-by-side against Pass 03. Rate each /10 with explicit focus on hand adhesion, pelvis coherence, head/gaze orientation, floor supports, FCDN distinct low side-head profile and variant silhouette. Report changes rather than asserting universal improvement. Leave poor drafts usable and free to move on.
