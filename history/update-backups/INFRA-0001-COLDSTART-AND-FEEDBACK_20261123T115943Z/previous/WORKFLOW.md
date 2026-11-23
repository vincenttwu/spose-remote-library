# WORKFLOW.md — pass-based remote workflow

## Standard operating cycle

1. Pick 5 poses.
2. Remote assistant prepares **Pass 1 bundle**.
3. Local agent installs it and runs the full five-pose batch.
4. Local agent returns **one combined feedback ZIP**.
5. Remote assistant calibrates issues across the batch and prepares **Pass 2 bundle**.
6. Local agent runs the full five-pose batch again.
7. If still unsatisfactory, optionally run **Pass 3**.

Target is normally **2 passes**.

## Folder contract

- `snapshots/`: persistent historical pass folders
- `review/`: disposable latest human-readable artifacts
- `upload/`: disposable latest upload-ready artifacts

## Current execution target

Current target is **Batch 0001 / Pass 02** for these five poses:
- `DOGG-DOGG-V00`
- `DOGG-CLSD-V00`
- `DOGG-DOWN-V00`
- `DOGG-FCDN-V00`
- `DOGG-FROG-V00`

All five are attempted every pass. Stability is recorded; it is not a permission check.
