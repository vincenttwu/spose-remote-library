> **INFRA 0002: non-linear registry active.** The old Batch 0001 Pass 05 headers below are preserved historical information, not a global work queue. Batch/pass operations now use `scripts/registry.py`, `scripts/run_registered_batch.py`, and `scripts/activate_batch.py`; read `docs/REGISTRY-OPERATIONS.md`.

> **ACTIVE: Batch 0001 Pass 05.** Read release `APPLY.md`, `LOCAL-WORKS.md` and installed `docs/PASS-05-CALIBRATION.md`; five new modules seeded from Pass04 selected local Attempt02 controls. Optional 0–2 guided local refinements per pose. Existing older pass instructions below are historical. All quality metrics are advisory.

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


## Pass-03 rig calibration procedure (2026-11-23)
`rigify_floor_engine.py` exposes `palm_to_hip_surface()` and `side_head_clearance()`. Source-specific pose controls may contain `styling_controls`, `post_styling_calibration`, `palm_surface_contact`, and `head_side_floor`. The `POSE_LOCAL_BONE_AXIS_ADD_DEG` declarative space adds a bounded local-axis turn for face-side FCDN; do not use arbitrary pose-executable files. The batch runner is unchanged from infrastructure update 0001 and must attempt every item. When source profile uses `low_wide_hands_feet`, knee height is informational. Read `docs/PASS-03-CALIBRATION.md` for all semantics and limits.


## Active update: Batch 0001 / Pass 04 — measured geometry and calibration

This update supersedes the previous Pass-03 *active-pass instructions* but preserves all prior architecture and safety guidance. The user requested a fourth geometry pass because Pass 03 rendered worse overall despite misleading tiny nearest-vertex contact gaps. Use `APPLY.md` and `LOCAL-WORKS.md` from the incoming Pass-04 release as the exact procedure.

The local agent shall run all five poses and inspect their measured new revisions **without approval gates**, then collect independent neutral-rig and saved-scene measurements using `scripts/run_calibrated_batch.py --blender "<BLENDER_EXE>" --plan batches/BATCH-001.json`. This command builds with `--save-blend`, runs `scripts/collect_calibration.py`, refreshes `review/` and `upload/`, and verifies a **single** compact feedback ZIP containing `calibration/` members.

The head-aim solver measures rotation sign using RIG001 -Y reference. Palm contact uses **distribution/coverage of a bounded patch**; zero minimum distance is not proof of a correct grip. The calibration JSON is versioned under `tooling/calibration/CPL01-v001/` and remains descriptive. Never modify Blender template, catalog or tracker manually. `docs/CALIBRATION-REFERENCE.md` provides schema, confidence limits, recovery and cold-start instructions.


## Local-agent additive calibration procedure (current)

For Pass 04 read `APPLY.md` in the incoming update (or installed `docs/LOCAL-COLLABORATION.md`). Run `scripts/run_calibrated_batch.py --blender <EXE>` to build five Attempt-00 baselines and collect rig/scene probes. The same command prepares `local/ACTIVE.json` and editable pose-specific attempt proposals when `batches/BATCH-001.json.local_calibration.enabled` is true. The local agent inspects at least side and three-quarter images and measurement summaries before writing `proposal.json`; every proposal describes a causal hypothesis and bounded control edits. Run up to two attempts per pose with `scripts/local_refinement.py run`, select a best candidate with `scripts/local_refinement.py select` (Attempt 00 is valid), and finalize once for the whole batch with `scripts/run_calibrated_batch.py --phase finalize`. Inspect `snapshots/` evidence and one compact feedback ZIP. Never infer a valid grip from a single minimum surface distance. For disabling local trials pass `--local-calibration off`. See `docs/LOCAL-COLLABORATION.md` for full command reference and failure recovery.

## Pass 05 — cold start shortcut

1. Verify active plan `batches/BATCH-001.json` says `pass_label=pass-05` and references five new `incoming/` modules.
2. Follow `docs/PASS-05-CALIBRATION.md` and run `scripts/run_calibrated_batch.py` for five baseline renders.
3. If enabled, inspect `local/ACTIVE.json`, author bounded proposals, run at most two local trials per pose and choose best 00/01/02.
4. Finalize once and upload the one ZIP in `upload/`. Run review/feedback verifier; never claim success solely from metrics.


## Infra 0002 cold start — mandatory lookup

1. If inside a local library, run `python scripts/registry.py status` and `python scripts/registry.py next`. When a feedback ZIP is supplied, read `registry/registry.json` together with `manifest.json` and the batch summary.
2. Identify the *requested* batch/pass; do not use the latest snapshot by default. For new work use a unique batch plan with explicit `batch_label`, `pass_label`, and immutable pose package IDs.
3. Use `python scripts/run_registered_batch.py --phase baseline --plan <PLAN> --blender <EXE>`; retain its exact snapshot. For local attempts use `scripts/local_refinement.py --session-snapshot <SNAPSHOT> ...`.
4. Finalize the explicit snapshot, then `activate_batch.py --batch <N> --pass <N>` to populate flat exchange folders for upload.
5. Registered feedback uploads may arrive in arbitrary order. Audit only the named batch/pass, and keep that feedback's portable registry age distinct from local current state. Read `docs/REGISTRY-OPERATIONS.md`.
