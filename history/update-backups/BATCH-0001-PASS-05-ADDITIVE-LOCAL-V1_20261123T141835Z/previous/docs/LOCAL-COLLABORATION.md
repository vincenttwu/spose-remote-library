# Local additive calibration — complete agent runbook, v001

## Purpose and control boundary

The user wants a togglable local-agent Blender refinement loop. A normal remote pass has five baseline poses, optionally up to **two additional** guided attempts per pose, and **one** combined feedback ZIP. Baseline Attempt 00 is the remote-authored and tracked revision. Attempts 01 and 02 are scratch-only under `local/`. A local agent uses rendered views and calibrated measurements to suggest and test changes. The remote agent later audits the entire record. All geometry metrics and visual ratings are **advisory**: they never block the next pose or batch.

## 0. Files and lifetimes

`local/`: ephemeral workspace with `ACTIVE.json`, `<batch-pass-run>/<POSE>/attempt-00..02/`. Safe to delete only after `finalize` captures evidence. `snapshots/`: persistent batch run, one `local-refinement-evidence.json` and `local-evidence/` folder with full selected controls, per-attempt changes/results/calibration and compact images; never delete for ordinary workflow. `review/` and `upload/`: disposable flat selected PNG images; `upload/` also has one combined feedback ZIP. `poses/`/SQLite: authoritative and unchanged by local attempts. `tooling/calibration/`: persistent neutral/scene rig measurement data.

## 1. Execute baseline and neutral/persistent measurements

From library root (replace `<BLENDER_EXE>`):

```powershell
python scripts/run_calibrated_batch.py --blender "<BLENDER_EXE>" --plan batches/BATCH-001.json
```

This renders all five baseline packages with saved scenes and invokes `collect_calibration.py` once for the neutral template and per-scene measurements. It creates `local/ACTIVE.json` and each pose's Attempt-00 snapshot with all four reference images. It also creates editable **proposal scaffolds** for Attempt-01 and Attempt-02. It produces an initial feedback ZIP; that baseline file is provisional and will be replaced after final selection in disposable `upload/`. Local agents can use `--local-calibration off` for baseline-only mode, `--max-local-attempts 1` for one refinement limit, or set `local_calibration.enabled=false` in the plan. Default `enabled=true`, maximum two.

## 2. Diagnose current pose problems using geometry and images together

Inspect `review/<POSE>_side.png`, `review/<POSE>_three-quarter.png`, `review/<POSE>_front.png`, and QA view. Read `tooling/calibration/CPL01-v001/runs/<RUN>/neutral-rig.json` and `<POSE>.json`, plus `poses/<POSE>/CPL01/v001/rNNN/validation.json`. Primary reference measurements are hand-pelvis **patch p50 and coverage**, pelvis separation, head forward/elevation, support distances, and whether feet/knees/hands/forearms touch as specified for that silhouette. Beware the minimum surface gap: a tiny nearest-vertex distance is NOT a convincing grip. A head-bone forward vector is an approximation; confirm the actual rendered face direction. FCDN is *intentionally* lower and side-face-down; do not impose raised-head styling on it. Preserve narrow vs wide, standing vs kneeling distinctions.

## 3. Write a focused, bounded hypothesis

Open `local/<RUN>/<POSE>/attempt-01/proposal.json`. Replace `hypothesis` and `expected_effect` and provide one or more explicit `changes`. Example (values are **illustrative**, not valid for every pose):

```json
{
  "schema_version": 1,
  "pose_id": "DOGG-DOGG-V00",
  "attempt": 1,
  "base_attempt": 0,
  "hypothesis": "Left rear palm floats lateral to the receiver hip; the torso already has usable separation",
  "expected_effect": "Reduce left palm patch median distance without increasing penetration or shoulder stretch",
  "changes": [
    {"section": "controls", "actor": "A", "bone": "hand_ik.L", "field": "value", "value": [0.15, 0.08, -0.005]}
  ],
  "visual_review_note": "Pending new render"
}
```

The change must refer to a real baseline control and stay within allowed bounds: `value` world/control offsets ≤0.09 m per refinement and ≤0.16 m from original baseline; rotation changes ≤20° per refinement and ≤35° cumulative from baseline. The allowed scalars for head and contact policies are similarly bounded. The script refuses arbitrary non-data code, unrecognized controls or impossible proposal structure. This is safety/schema verification, **not a geometry gate**. More independent changes reduce causal interpretability; prefer one high-priority hypothesis per attempt.

## 4. Render Attempt-01 and measure it

```powershell
python scripts/local_refinement.py run --pose DOGG-DOGG-V00 --attempt 1 --blender "<BLENDER_EXE>"
```

The script builds into `local/<RUN>/<POSE>/attempt-01/`, not `poses/`, and saves full local PNG renders, `result.json`, `blender-result.json`, `inputs/rig-targets.json` and a temporary local `scene.blend`. It launches the read-only Blender `calibration_probe_blender.py` on the resulting scene, recording `calibration.json` and logs. It does not add tracker revisions, and it records failures without stopping other poses. Inspect side and three-quarter plus front and QA as needed; record visual evidence in the selection reason.

## 5. Optionally render Attempt-02

If Attempt-01 is insufficient and there is a clear new hypothesis, edit `attempt-02/proposal.json`. `base_attempt=0` compares a new branch from the remote baseline; `base_attempt=1` accumulates on successful Attempt-01. Bounds are validated relative to both parent and baseline. Run with `--attempt 2`. Do not mechanically use both attempts just because they are available; return to Attempt 00 if refinements regress.

## 6. Select the best for each of the five

```powershell
python scripts/local_refinement.py select --pose DOGG-DOGG-V00 --attempt 0 --reason "Baseline best: local trials reduced gap but visibly intersected the hip"
python scripts/local_refinement.py status
```

To select a real local variant use `--attempt 1` or `--attempt 2`. Optional `--score` records a subjective 0..10 local visual rating. Do **not** say a candidate is better without looking at the images and measuring at least the target that was adjusted. Every unattempted pose defaults to baseline, so all five are represented and failure to refine one never blocks the rest. Selected local candidate is **not automatically an approved library revision**.

## 7. Finalize once for all five and upload one ZIP

```powershell
python scripts/run_calibrated_batch.py --phase finalize --plan batches/BATCH-001.json
python scripts/verify_feedback.py "upload/<ACTUAL_FEEDBACK_FILENAME>.zip"
```

Finalization copies trial metadata, compact images, calibrated measurements, proposal deltas and **full selected `rig-targets.json`** into `snapshots/`. It then rebuilds `review/` and `upload/` showing four full PNGs for each selected candidate and creates one compact ZIP containing portable context, baseline and local attempts. The feedback ZIP stores lossless WebP images with exact pixel verification. The local agent may now clear `local/` at any time; full saved Blender scenes stay local and are not uploaded.

## Evidence volume and interpretation

Only the selected candidate gets all four views. Every nonselected attempt gets two diagnostic views (side and three-quarter), including baseline if a local candidate was selected. Maximum is approximately **40 images** for 5 poses with all 3 attempts present, and less if attempts are skipped or the baseline is selected. The ZIP includes JSON measurements/results for attempted candidates and a sha256 inventory; there are no nested per-pose ZIPs or `.blend` payloads. Original flat PNGs can still be uploaded individually from `upload/`. If Pillow/WebP is unavailable, PNG fallback remains lossless but larger.

## Troubleshooting and recovery

A poorly calibrated candidate is a valid experiment, not a failure. If Blender fails, inspect its `result.json` and `build.log`; keep trying other poses and select baseline. An attempt cannot overwrite an already-recorded result: use an unused attempt index or document a new remote pass to avoid falsifying provenance. If `local/` is cleared prematurely, the authoritative baseline still exists; local trial evidence that was not finalized may be lost. After finalization, `scripts/refresh_exchange.py` reconstructs exchange folders from persistent snapshot without Blender. If an installed script or ZIP fails integrity checks, use installer rollback receipt; quality warnings do not require rollback.

**No automatic local AI optimization claim.** The agent must visually inspect and author actual bounded parameter changes; scripts execute/probe/export those declared changes. An uncontrolled optimizer would create misleading confidence.
