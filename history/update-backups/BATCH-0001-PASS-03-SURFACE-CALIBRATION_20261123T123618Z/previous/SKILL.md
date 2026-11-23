# SKILL.md — SPOSE remote library operating skill (cold-start)

This is the entrypoint for an agent with **no prior chat history**. Do not infer current batch status from a filename alone. The local library and tracker are authoritative; a portable feedback archive describes an earlier snapshot.

## A. Classify the job

| Request | Use | Must not do |
|---|---|---|
| Install tooling/documentation | Infra bundle `install-update.py` + `UPDATE-MANIFEST.json` | Rebuild/approve any pose |
| Create/refine five poses | New data-only pose modules + batch plan | Accidentally reuse the old package identity |
| Run/render current batch | `scripts/run_pose_batch.py` in local library | Stop after one poor result |
| Review feedback remotely | Single `spose-remote-feedback-...zip` | Assume a pass generated new revisions without checking |
| Recover `review/` and `upload/` | `scripts/refresh_exchange.py` | Rerender geometry unnecessarily |
| Repair documentation | `scripts/check_documentation.py`, inspect receipts | Unilaterally delete source details |

## B. Reconstruct truth

1. Determine whether the input is (a) the installed standalone library, (b) an update ZIP, (c) a pose bundle, or (d) a combined feedback ZIP. **Never extract context-only feedback over the installed library**.
2. From a local root, read `project.json`, `source/dataset.json`, latest `ROADMAP.json`, `tracking/progress.sqlite` through existing scripts and latest `snapshots/*/batch-summary.json`. From a combined ZIP, read `START-HERE.md`, `SUMMARY.md`, `batch-summary.json`, `manifest.json`, then `context/` if present.
3. Confirm source/pair/rig identity (`SRC003`, `CPL01/v001`, `RIG001/v001` in the current checkpoint), plus exact hashes in live manifests; do not assume a later library has the same version.
4. Determine whether each pose has a genuinely new revision. `reused_existing_package` is not improvement; record `new_revision_created` when available. Pass labels and timestamps alone do not prove a new build.
5. Check that five pose results and up to twenty renders are accounted for. Missing previews are **warnings**, not quality gates.

## C. Installed-library commands

Run from the library root with its Python. Use real Blender executable in place of `<BLENDER_EXE>`.

```powershell
python scripts/check_remote.py
python scripts/check_documentation.py
python scripts/run_pose_batch.py --plan batches/BATCH-001.json --dry-run
python scripts/run_pose_batch.py --plan batches/BATCH-001.json --blender "<BLENDER_EXE>"
python scripts/refresh_exchange.py
python scripts/update_continuation.py
python scripts/verify_feedback.py "upload/<FEEDBACK_ZIP>"
```

`--dry-run` checks package contracts; it does not prove a physically correct Blender pose. For new pass modules, use new package metadata and timestamps so the default idempotent runner creates revisions. Avoid `--rerun` unless intentionally generating another revision from the *same* package, and record that decision.

## D. Post-run artifacts

The batch runner attempts every listed pose and creates a persistent timestamped `snapshots/batch-XXXX-pass-YY_<UTC>/`. It regenerates flat `review/` PNGs and `upload/` PNGs + one feedback ZIP. That ZIP contains all five pose results, original input/validation data, losslessly compressed images (when Pillow/WebP available), and a portable read-only source/docs/rig handoff under `context/`.

The local agent should verify the ZIP with `scripts/verify_feedback.py`, look at the 15–20 PNGs in `review/` and upload **one ZIP only**. If compression support is absent, instruct `python -m pip install Pillow` on the Python used for export, then `python scripts/refresh_exchange.py`. Never discard images or switch to lossy JPEG.

## E. Remote evaluation and rating

Inspect all four standard views when available: front, side, three-quarter, qa-regions. Use source silhouette/support requirements, joint coherence, contact, clearance, variant distinction and render completeness. Provide per-pose subjective **/10** ratings and an overall batch rating; state the limitations. Explain highest-priority fixes and ask whether to move on or improve more, **without enforcing a gate**. Read `docs/REVIEW-AND-SCORING.md`.

## F. Batch pass rules

Typical flow: choose five → create Pass 1 ZIP → run all five → return one ZIP → calibrate issues and author **new packages** → Pass 2 ZIP → run all five → review → optionally Pass 3. Tooling/documentation upgrades use a separate infrastructure bundle, never increment a pose pass. Never replace source REVIEW/EXCLUDE with permission logic, require acceptance, or insist all V00s complete before continuing.

## G. Recovery/cold start

- Missing `review/`/`upload/`: run `scripts/refresh_exchange.py`, not Blender.
- Old nested feedback ZIP: preserve it as historical input; new exporter creates a different schema and does not delete history.
- Incorrect installer or stale docs: inspect `updates/installed/` marker and `history/update-backups/.../INSTALL-RECEIPT.json`; use `install-update.py --rollback "<RECEIPT>"` only if no installed targets have been changed since.
- Failed Blender build: keep the attempted row and logs, process all remaining poses.
- Missing optional Pillow: byte-preserving PNG fallback with warning; install Pillow for compact WebP.
- New session cannot reproduce: verify `context/handoff/HANDOFF-MANIFEST.json` checksums and consult source/rig maps; do not invent missing assets or source details.

## H. Additional exact references

`docs/ARCHITECTURE.md` (owners and flow), `docs/SCHEMAS.md` (contracts), `docs/FEEDBACK-CONTRACT.md` (ZIP structure), `docs/MAINTENANCE.md` (installer and scripts), `docs/COLD-START.md` (recovery), plus the preserved original geometry/rig design docs and source row specifications.
