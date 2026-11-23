# GUIDE.md — Local agent guide for Batch 0001 Pass 02

This bundle is for **one 5-pose pass**, not one-pose-at-a-time iteration. The goal is to run all five, refresh the flat workflow folders, and return **one** combined feedback ZIP.

## 1. Verify the installed library

Expected library root is typically `C:\Users\hyper\Documents\GitHub\spose-remote-library`, but verify the actual location yourself. `project.json` must identify `SPOSE-REMOTE-LIBRARY`. The library must contain `pairs/CPL01/v001/template.blend`, `source/dataset.json`, `tracking/progress.sqlite`, and `scripts/`.

## 2. Install this bundle

Extract this ZIP into a temporary folder, not over the live library. Then run:

```powershell
python install-update.py --library "C:\Users\hyper\Documents\GitHub\spose-remote-library"
python install-update.py --library "C:\Users\hyper\Documents\GitHub\spose-remote-library" --apply
```

Dry-run must succeed before apply. Apply mode backs up replaced files and stages five pose ZIPs in `incoming/`.

## 3. Execute the whole batch

From inside the installed library:

```powershell
python scripts/check_remote.py
python scripts/run_pose_batch.py --plan batches/BATCH-001.json --dry-run
python scripts/run_pose_batch.py --plan batches/BATCH-001.json --blender "<BLENDER_EXE>"
```

Use the real Blender executable on the machine. Do **not** stop after the first poor result. All five poses must be attempted.

## 4. Check the flat folders

After the run, verify these top-level folders:

- `snapshots/` contains a new snapshot folder like `batch-0001-pass-02_<timestamp>/`
- `review/` contains flat images for the current pass plus `SUMMARY.md` and `manifest.json`
- `upload/` contains the same flat images plus one ZIP named like `spose-remote-feedback-batch-0001-pass-02_<timestamp>.zip`

`review/` and `upload/` are disposable convenience folders. Clearing them must not affect the authoritative data under `poses/`.

## 5. What to upload back

Upload **one file only by default**:

- `upload/spose-remote-feedback-batch-0001-pass-02_<timestamp>.zip`

If the user wants to discuss a particular result, you may additionally upload one or more individual images from `upload/`. Do not package multiple side ZIPs unless explicitly requested.

## 6. Local work notes for this pass

This pass applies calibration changes learned from pass 01. Local work required:

1. Install the update bundle.
2. Run the batch.
3. Confirm five attempts were recorded.
4. Confirm `review/` and `upload/` were refreshed.
5. Upload the single combined feedback ZIP.

No quality or approval gate should block the batch. Poor results remain usable drafts and may be improved in a later pass.
