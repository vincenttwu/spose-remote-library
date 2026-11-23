# SPOSE — standalone Blender library update bundle

This is **Batch 0001 / Pass 02** for the current five-pose DOGG V00 batch.

Bundle filename pattern:
- `spose-remote-bundle-batch-0001-pass-02_<timestamp>.zip`

Feedback filename pattern generated locally:
- `spose-remote-feedback-batch-0001-pass-02_<timestamp>.zip`

This bundle updates scripts/documentation, stages five timestamped DOGG V00 pose modules, and installs `batches/BATCH-001.json`. The pass-02 goal is to apply the pass-01 feedback calibration across all five poses and evaluate them together.

## Flat workflow folders

The installed library now uses these first-class top-level folders:

- `snapshots/` — persistent batch/pass history
- `review/` — disposable latest images + readable summary
- `upload/` — disposable latest combined feedback ZIP + flat image copies for discussion

`review/` and `upload/` may be cleared any time. They are convenience copies only. Authoritative pose revisions remain under `poses/`.

## Batch rule

Run **all five** poses in one batch. Record unstable or poor results as status only. Do not stop after one pose. Do not require approval to continue.

Read `GUIDE.md` first, then `LOCAL-WORKS.md`.
