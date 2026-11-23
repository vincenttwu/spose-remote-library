> **INFRA 0002: non-linear registry active.** The old Batch 0001 Pass 05 headers below are preserved historical information, not a global work queue. Batch/pass operations now use `scripts/registry.py`, `scripts/run_registered_batch.py`, and `scripts/activate_batch.py`; read `docs/REGISTRY-OPERATIONS.md`.

> **ACTIVE: Batch 0001 Pass 05.** Read release `APPLY.md`, `LOCAL-WORKS.md` and installed `docs/PASS-05-CALIBRATION.md`; five new modules seeded from Pass04 selected local Attempt02 controls. Optional 0–2 guided local refinements per pose. Existing older pass instructions below are historical. All quality metrics are advisory.

# AGENTS.md — rules for all SPOSE local and remote agents

## 1. Who owns the project

The user owns the standalone SPOSE Blender library. The local machine owns `.blend` assets, full source CSV, SQLite progress and all pose revisions. A remote assistant may author *data-only pose packages*, propose geometry changes, inspect feedback and provide **one ZIP update**. The local agent installs verified updates and runs Blender. A portable context/feedback ZIP is a read-only copy, **not** a replacement runnable library.

## 2. Non-negotiable user workflow

- **Five poses in one batch**. All five are attempted every pass; an error in one must not skip the other four.
- **Normally two passes**: author pass 01, receive combined feedback, calibrate *all five together* in pass 02, evaluate. Pass 03 only when the user wants it. Pass numbering is a release label, not evidence of a new revision.
- **One bundle ZIP out and one combined feedback ZIP back.** The ZIP contains relevant context, so no routine second handoff upload. Individually prefixed PNGs may be uploaded for discussion.
- **No quality/approval gates.** A rendered but unstable draft stays usable. Source `REVIEW/EXCLUDE`, geometry warnings, contact-proxy failures and `accepted` do not block anything. Keep integrity checks for safe file operations.
- **State recording rather than guarding.** Track `attempted`, `built`, `accepted`, `needs_work`, individual issues and pass identities separately.
- Ratings are assistant/human visual judgments derived from the actual four views and source specification, **not** fabricated script scores. Present a per-pose rubric and an overall proceed/refine suggestion after feedback.

## 3. Immutable data and identities

Do not mutate or replace the shared pair template `pairs/CPL01/v001/template.blend`, full source catalog, `tracking/progress.sqlite`, existing pose revision folders, or historical review labels when installing updates. Avoid running an incoming installer directly over the library root. Data-only pose ZIPs use source, template, rig-map fingerprints. The importer creates distinct `poses/<POSE_ID>/CPL01/v001/rNNN` revisions. Never claim a new pass built new geometry if its package identity was reused; emit `reused_existing_package` explicitly.

`tracking/progress.sqlite` is the authority for progress; `ROADMAP.json`, `ROADMAP.md`, CSV and `CONTINUATION.md` are derived outputs. A ROADMAP checkbox indicates **built**, not automatically stable or approved. V00-first is the preferred production order for the 28-family, 276-base/3,036-record catalog, not an import permission mechanism.

## 4. Flat exchange and history folders

- `snapshots/`: **persistent**, one timestamped folder per batch/pass run; history does not disappear when temporary folders refresh.
- `review/`: **disposable**, latest batch's 3–4 preview PNGs per pose, prefixed with pose ID, plus batch summary and manifest; no `current/` subfolder.
- `upload/`: **disposable**, same original PNGs **and one combined feedback ZIP** plus summary/manifest. User may send one PNG separately to discuss geometry.
- All files under `review/` and `upload/` must be recreatable from snapshots and authoritative `poses/` via `python scripts/refresh_exchange.py` with no Blender rerender.

## 5. Updating scripts and docs

Tool updates come as a separate `spose-remote-bundle-infra-...zip` with an `updates/` payload, explicit manifest, dry-run/apply and rollback receipt. Install into canonical `scripts/` and documentation locations. Before overwrite, back up previous versions. Preserve all other existing technical docs and custom content not explicitly manifested. A tooling-only update must **not** create a new pose pass, rewrite geometry controls, accept revisions, or change the source catalog.

Use `scripts/check_documentation.py` and a synthetic/fixture feedback run to test reproducibility. After each run generate `CONTINUATION.md` from live state (`scripts/update_continuation.py`) so the next session does not treat a hardcoded note as authoritative.

## 6. Honesty, diagnostics and recovery

- Never equate floor contact proxies with visual/correct posture. Bone-head distance and mesh surface proximity are different diagnostics.
- Report Blender tests separately from offline Python/ZIP tests. If no Blender ran, say so.
- If optional compression is unavailable, retain original PNGs, record a warning and finish the batch; do not silently use lossy conversion.
- If a pose build fails, preserve logs/record and continue; if update integrity/source fingerprint fails, do not install the unsafe update.
- Retain rig definitions and original geometry notes. Do not simplify, delete or relax established rules without documenting the change and obtaining consent for nontrivial policy changes.

## 7. First task for a cold-start agent

Read `README.md`, this document, `SKILL.md`, `WORKFLOW.md`, `GUIDE.md` and **current** `CONTINUATION.md`; inspect `project.json`/`ROADMAP.json`; read the latest batch snapshot and `source/V00-CATALOG.csv` if in portable context. If the user supplies feedback, inspect all five poses, their validation JSON and 3–4 images each, then give ratings and options **before deciding on another geometry pass**. Do not require sequential human approvals.


## Batch 0001 Pass 03 implementation amendment
- Pass 03 is a genuine five-pose rebuild with five **new package identities**, not a reporting-only pass. No pose quality gates.
- The engine now measures hand-to-side-hip evaluated surface gaps, preserving historical wrist-to-bone anchors for reference; the new mesh check is not a physically guaranteed grip.
- FCDN forearm/head-side support diagnostics are approximate mesh regions. Do not claim precise cheek contact or stable neck load.
- Store one combined feedback ZIP in `upload/` while preserving flat individual PNGs in both `review/` and `upload/`.
- Read `docs/PASS-03-CALIBRATION.md` and `LOCAL-WORKS.md` from the delivered bundle before executing the pass.


## Active update: Batch 0001 / Pass 04 — measured geometry and calibration

This update supersedes the previous Pass-03 *active-pass instructions* but preserves all prior architecture and safety guidance. The user requested a fourth geometry pass because Pass 03 rendered worse overall despite misleading tiny nearest-vertex contact gaps. Use `APPLY.md` and `LOCAL-WORKS.md` from the incoming Pass-04 release as the exact procedure.

The local agent shall run all five poses and inspect their measured new revisions **without approval gates**, then collect independent neutral-rig and saved-scene measurements using `scripts/run_calibrated_batch.py --blender "<BLENDER_EXE>" --plan batches/BATCH-001.json`. This command builds with `--save-blend`, runs `scripts/collect_calibration.py`, refreshes `review/` and `upload/`, and verifies a **single** compact feedback ZIP containing `calibration/` members.

The head-aim solver measures rotation sign using RIG001 -Y reference. Palm contact uses **distribution/coverage of a bounded patch**; zero minimum distance is not proof of a correct grip. The calibration JSON is versioned under `tooling/calibration/CPL01-v001/` and remains descriptive. Never modify Blender template, catalog or tracker manually. `docs/CALIBRATION-REFERENCE.md` provides schema, confidence limits, recovery and cold-start instructions.


## Additive local experiments (current policy)

The user may enable or disable `local_calibration` for each batch/pass. When enabled, Attempt 00 is the authoritative remote baseline and at most **two additional local scratch attempts per pose** are allowed. Local agents read images and propose **bounded declarative control-target changes**, test them by rendering, record hypothesis/results, then select the best of attempts 00–02. The current pass is still one remote pass, not three passes. Local trials live under disposable `local/` and must never mutate authoritative `poses/`, source, pair templates or tracker. `scripts/local_refinement.py finalize` persists evidence and selected rig-targets under `snapshots/` before `local/` is cleared. Selection is advisory, not a user approval or promotion. Upload exactly one feedback ZIP, containing local attempts and calibration data.

## Pass 05 audit boundary

Treat Pass04 local selected attempts as measured input provenance, not a new accepted template. The current Pass05 five-pack contains distinct timestamped modules seeded from those controls. Never substitute prior Pass04 baseline previews for Pass05 results. Record new/reused revisions truthfully. Never allow local experiments to edit source, tracker, Blender template, or existing `poses/` revisions.


## Infra 0002 authority rule — independent batches

The source of truth for batch/pass metadata is the *existing* `tracking/progress.sqlite` registry tables; portable exports are snapshots. Never infer one global active batch from `CONTINUATION.md` or a filename. Every local trial, baseline run, calibration probe, and feedback ZIP must identify its own batch, pass, and persistent snapshot path. Use explicit `--session-snapshot` to avoid the legacy global `local/ACTIVE.json`. Only a user-requested `activate_batch.py` operation rewrites flat disposable `review/` and `upload/`. Quality status never acts as a gate.
