# SPOSE pose-agnostic rig calibration reference — v001

## Goals and non-goals

The user wants a measured Blender reference that improves future **first passes**, not an exhaustive database that constrains every pose. The collector maps RIG001 controls to actual evaluated geometry, measures pose-agnostic body anatomy and response probes, and measures each current rendered scene independently. All measurements are **descriptive**. They do not block pose generation, approve results, or automatically overwrite a user's geometry choices.

The current calibration asset `CPL01/v001` contains actor rigs `CPL01_A_RIG`, `CPL01_B_RIG`, body meshes `CPL01_A_BODY`, `CPL01_B_BODY`, and VP001 material roles. Reference hashes bind each measurement run to the actual `template.blend` and `tooling/rig-maps/RIG001-v001.json`.

## Local setup

Use the real Blender 5.2.2, and run the five-pose batch **with saved scenes** so measurements are made on *the actual rendered pose*, not a guessed reconstruction. The preferred one-command workflow is:

```powershell
cd "<LOCAL_LIBRARY>"
python scripts/run_calibrated_batch.py --blender "<BLENDER_EXE>" --plan batches/BATCH-001.json
```

The equivalent explicit steps for troubleshooting are:

```powershell
python scripts/run_pose_batch.py --plan batches/BATCH-001.json --blender "<BLENDER_EXE>" --save-blend
python scripts/collect_calibration.py --blender "<BLENDER_EXE>" --plan batches/BATCH-001.json
python scripts/refresh_exchange.py
python scripts/verify_feedback.py "upload/<ACTUAL_FEEDBACK_ZIP>"
```

`--save-blend` stores each compressed `scene.blend` under its authoritative pose revision. These scenes are local only and are **not** sent in feedback. If some scenes are missing, their measurements are registered as unavailable; the collector does not fall back to an earlier pose revision.

## Measurement sets

### A. Neutral rig and anatomy (once per rig/template version)

`neutral-rig.json` includes:
- All pose bone names, parents, rest and current world-space heads/tails, lengths, rotation modes, constraints, locks, JSON-safe custom properties, and actor ownership.
- Evaluated body mesh material-region point counts, axis-aligned bounds, centroids, region diagonals and limited deterministic point samples, for labels such as hands, pelvis, thighs, forearms and head/neck.
- Finite-difference control-response probes for head, neck, chest, torso, hand IK and foot IK, using ±15° or 25 mm perturbations. The probe restores original transforms in memory after each test.

These are **capabilities and associations**, not correct pose targets. RIG001's `forward_axis=-Y` is the reference used in estimated head-gaze metrics. If a future character uses different axes or materials, build a new versioned calibration dataset.

### B. Each rendered pose scene

`DOGG-<CODE>-V00.json` includes:
- Actual evaluated hip/head heights, joint angles and relative actor hip height.
- Estimated head-forward world vector and elevation from the rig's rest-to-pose rotation.
- Region-ground min-Z for left/right hands, feet, knees, forearms and head-side.
- Palm-patch-to-lateral-pelvis surface distance **distribution** (p10, p25, p50, p75, p90) and contact fractions within 15 mm and 30 mm.
- Localization confidence and readable errors when a patch cannot be identified.

The rig's head rotation proxy is not an eye tracker. An unsigned hand-surface distance does not prove a correct grip, distinguish penetration, or establish weight/force. **Never substitute the minimum distance for quality.** Read the rendered side and three-quarter views alongside p50 and coverage.

### C. Long-term adoption experiment

Before using measured references to drive *other* pose families, compare identical pose specs using (A) baseline generator and (B) reference-assisted generator on several poses, including one not used for calibration. Score silhouette, floor support, head orientation, region contact and visible penetration independently. Adopt only measurements that improve human-rated first-pass quality. Geometry data can degrade visual fidelity when optimized without semantic pose intent.

## Storage and feedback integration

Authoritative calibration outputs are persistent under:

```text
<LIBRARY>/tooling/calibration/CPL01-v001/
  LATEST.json
  runs/
    batch-0001-pass-04_<UTC>/
      CALIBRATION-MANIFEST.json
      neutral-rig.json
      neutral-rig.log
      DOGG-DOGG-V00.json
      DOGG-DOGG-V00.log
      ... other four pose json/log files
```

`LATEST.json` points to the most recent run. Individual JSON files and `CALIBRATION-MANIFEST.json` are included as normal members inside `spose-remote-feedback-*.zip` under `calibration/`, with SHA-256 member inventory. **One feedback ZIP only.** Logs remain local unless needed for troubleshooting. The portable context includes the collector scripts and this guide for cold starts.

The collector's `current_pose_scene()` checks each saved revision's package timestamp against the active batch plan. This prevents old r003/r004 `.blend` scenes from being misreported as measurements of Pass 04.

## Common problems

- `missing_scene_blend`: Run the actual batch with `--save-blend`, not a rerun of an old package; investigate pose-specific import failures first.
- Blender probe failure: Inspect the `*.log` in the persistent calibration run. If a single pose is not measurable, the others still complete.
- No `calibration/` in feedback: Run collector **before** `refresh_exchange.py`, then inspect `tooling/calibration/CPL01-v001/LATEST.json` for matching batch/pass; rerun export.
- Unexpected head vector: Confirm `RIG001` forward axis and orient using rendered faces. The output labels its axis assumption. Do not force sign or increase rotation magnitude just to make the numerical proxy look good.
- Contact fractions worsen despite zero min distance: Trust the distribution and visual contact; correct surface patch localization or wrist orientation, not just the scalar gap.
- Need more measurements: Add a targeted, documented probe with success/failure criteria and versioned schema; do not blindly record every pairwise distance.
