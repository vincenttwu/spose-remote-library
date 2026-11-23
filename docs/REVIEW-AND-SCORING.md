# Human/assistant review rubric — evidence, not approval

The feedback scripts deliberately compute **no visual correctness score**. Mechanical measurements cannot reliably judge whether a pose matches source anatomy/support requirements. After each five-pose feedback ZIP, the assistant should inspect front, side, three-quarter and qa-regions views and the source specification. Report subjective ratings from 0–10 and state uncertainty; compare against the previous pass only if actual new revisions exist.

Suggested evaluation weights (heuristic, not authority):

| Criterion | Suggested share | Questions |
|---|---:|---|
| Source silhouette and identity | 30% | Does standing/kneeling/prone/folded/wide-open configuration match the original pose row? |
| Joint and support geometry | 25% | Are knees, ankles, elbows, arms and hands plausible and intended contacts engaged? |
| Partner alignment and contacts | 20% | Are pelvis, hands and other intentional regions spatially coherent? Are sample proxies misleading? |
| Pose distinction and readability | 15% | Is CLSD distinguishable from DOGG and FROG from the others? Is the intended posture legible in 3/4 view? |
| Technical/render evidence | 10% | Are all views present and are mesh/penetration warnings comprehensible? |

Ratings may be qualitative rather than mathematical; a 0–10 number should be supported by observations. Record at least one strong point and one priority issue per pose. Do not call technical batch success equivalent to visual fidelity.

**Example baseline** from 2026-11-23 previously inspected visuals (not a new Pass 02 result): DOGG-DOGG 6/10, CLSD 5.5/10, DOWN 3/10, FCDN 4.5/10, FROG 6.5/10; unweighted mean 5.1/10. These numbers are historical human judgments and should not be copied into new reports if renders changed.

After review state whether the five poses were newly built vs reused, the actual improvements/regressions, top priorities and a simple user decision: **move to next batch / run another refinement**. No decision is precluded by warnings or low rating. Two passes is a practical target, not a stopping rule; a third pass is optional on user request.
