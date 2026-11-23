# Batch 001 — five-pose consolidated rerender

This flat-root package upgrades the standalone SPOSE library and replaces the previously restrictive V2 batch workflow. The new default is **run all five** DOGG V00 poses, save all versioned results, create one combined evidence ZIP. No geometry or source quality gate stops the run. A `draft` remains usable even when warnings are present.

The five timestamped ZIPs under `pose-packages/` use the V2 floor/IK engine and incorporate best-effort adjustments based on the measured DOGG r002 over-fold (front hip 0.272m vs rear 0.665m). DOGG/CLSD receive a tabletop-height hypothesis; FROG a lesser correction; FCDN remains low and DOWN remains a standing fold. They are not Blender-verified.

```powershell
python install-update.py --library "<YOUR_FULL_SPOSE_LIBRARY>"
python install-update.py --library "<YOUR_FULL_SPOSE_LIBRARY>" --apply
cd "<YOUR_FULL_SPOSE_LIBRARY>"
python scripts/run_pose_batch.py --plan batches/BATCH-001.json --blender "<BLENDER_EXE>"
```

Output: `reports/BATCH-001-DOGG-V00-FIVEPACK_<timestamp>_combined_feedback.zip`. This includes a five-row summary and feedback for any generated revisions. Hand it back to the assistant; next batches do NOT depend on a clean report.
