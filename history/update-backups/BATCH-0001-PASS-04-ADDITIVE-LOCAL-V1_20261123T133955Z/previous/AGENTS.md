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
