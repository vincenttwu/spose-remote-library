# Pose module and feedback — standalone v2 contract

## Input package

One pose ZIP per actual import: `{POSE_ID}_{UTC_TIMESTAMP}.zip`, flat JSON-only contents:
`manifest.json`, `pose.json`, `rig-targets.json`, `contacts.json`, optional `render-config.json`, `validation-plan.json`. The outer **batch bundle** may contain multiple of these in `pose-packages/`, but `import_pose.py` reads one at a time from library `incoming/`. No code inside input pose ZIPs is executed.

`manifest.json`: schema 1, `spose_pose_module`, source checkpoint and SHA for the exact `specification` string, pair template SHA, rig-map identity, every payload file SHA. Hashes are not digital signatures. `pose.json`: source trace, actor mapping, expected support and notes. `rig-targets.json`: strict engine v2 declarative controls, floor-calibration stages, support assertions and posture assertions; see `docs/GEOMETRY-ENGINE-V2.md`. `contacts.json`: intended anchor pairs, diagnostic bone-head tolerances (not penetrative contact). `render-config.json`: bounded PNG resolution.

The new package validator deliberately rejects old v1 Batch 001 modules. Do not weaken this gate to reuse faulty standing-only files.

## Import commands

```powershell
python scripts/import_pose.py incoming/<POSE_ID>_<timestamp>.zip --dry-run
python scripts/import_pose.py incoming/<POSE_ID>_<timestamp>.zip --blender "C:\path\to\blender.exe" --save-blend
```

Dry-run only verifies identity, dependency hashes, basic declarative controls and required geometry-assertion fields. Blender build applies and measures the actual rig. A completed render is still **draft** if all geometry gates pass, **blocked** if geometry fails, **failed** if Blender could not run. Optional `--save-blend` is useful for the first calibration loop but omitted from normal thousands-of-poses production.

## Feedback and revisions

```powershell
python scripts/export_feedback.py DOGG-DOGG-V00 --revision 2
```

The exporter gathers saved revision data and preview images for a small feedback ZIP; user uploads it for diagnosis. DO NOT rename another pose's feedback or copy its transforms blindly. New revised module ZIP receives a distinct UTC timestamp; importer chooses next rNNN. Do not overwrite existing scenes, trackers, accepted statuses or prior input package. `ROADMAP.md` and `ROADMAP.json` are generated, not hand-maintained.

## Approval

An accepted pose needs both (1) local hard gate pass and evidence and (2) explicit user confirmation after inspecting images and contact. `review_pose.py` enforces the hard gate and failed-job restrictions. Historic local pilots were not approved; they can inform control mechanics only.
