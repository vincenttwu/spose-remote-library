# workspace/AGENTS.md — Experimental Backward-Roadmap Sandbox (Mirrored Library Layout)

> **EXPERIMENTAL SUBPATH ONLY.** Everything under `workspace/` is an isolated local authoring, rendering, and pre-audit sandbox. It mirrors the top-level SPOSE library layout 1:1 while keeping the authoritative top-level library completely untouched. Root `../AGENTS.md` remains supreme for the main library.

## 1. Purpose

`workspace/` allows local agents to author, build in Blender, calibrate, and audit data-only 5-pose batches independently, working **backwards from the bottom of the V00 roadmap** (`UFDG` → `UADG` → `USDG` → `OFEL` → `OCUN` → …) so pose IDs do not collide with the main forward production line (`DOGG` → `GARD` → `MISS` → …).

Work produced here stays cleanly quarantined until explicitly promoted by the user.

---

## 2. Non-Negotiable Non-Pollution Constraints

When operating inside `workspace/`, an agent **MUST NEVER** create, modify, overwrite, or delete any file outside `workspace/` unless the user explicitly initiates a separate **Promotion** step.

### Strictly forbidden writes (top-level library)
- **Tracking & roadmaps:** `../tracking/`, `../ROADMAP.md`, `../ROADMAP.json`, `../CONTINUATION.md`
- **Authoritative assets & revisions:** `../poses/`, `../snapshots/`, `../batches/`, `../incoming/`, `../pairs/`, `../body_profiles/`, `../visual_profiles/`, `../source/`
- **Shared exchange & scratch:** `../review/`, `../upload/`, `../local/`, `../reports/`
- **Core tooling & docs:** `../scripts/`, `../docs/`, `../schemas/`, `../tooling/`, `../project.json`, `../AGENTS.md`

### Permitted read-only top-level dependencies
- Read `../source/SPOSE-FULL-20261122T013728Z.csv` and `../source/dataset.json` (never modify).
- Read `../pairs/CPL01/v001/template.blend`, `../pairs/CPL01/v001/studies/VP001-v001/appearance-study.blend`, and `../tooling/rig-maps/RIG001-v001.json` (never modify or save over them).
- Import/invoke `../scripts/pose_common.py`, `../scripts/blender_build.py`, `../scripts/rigify_floor_engine.py`, and `../scripts/compress_images.py` strictly with output paths enforced inside `workspace/`.
- **No symlinks or directory junctions** anywhere under `workspace/`.
- **No direct edits to `../scripts/`.** Prototype any solver changes inside `workspace/scripts/` (or a separate Git worktree/branch) and document them for formal infrastructure review.

---

## 3. Mirrored Folder Structure

`workspace/` mirrors the exact top-level library architecture so sequential batches of any size (including 20+ pose families split into 5-pose batches), canonical pose revisions, persistent snapshots, and flat disposable exchange folders work identically to the main library:

```text
workspace/
  AGENTS.md                               # This contract
  ROADMAP.md                              # Derived backward V00 checklist (mirrors ../ROADMAP.md)
  ROADMAP.json                            # Derived machine-readable roadmap (mirrors ../ROADMAP.json)
  tracking/
    workspace-tracker.json                # Authoritative workspace registry (batches, passes, snapshots, revisions, audits)
  incoming/
    <POSE_ID>_<YYYYMMDDTHHMMSSZ>.zip      # All authored data-only spose_pose_module ZIPs (mirrors ../incoming/)
  batches/
    BATCH-0001-PASS-01.json               # Sequential 5-pose batch plans (works for 4-pose, 5-pose, and 20-pose families alike)
    BATCH-0001-PASS-02.json
    ...
    BATCH-0004-PASS-01.json               # e.g., OFEL poses 1-5; BATCH-0005 = OFEL poses 6-10, etc.
  poses/
    <POSE_ID>/CPL01/v001/
      r001/                               # Canonical immutable pose revisions (mirrors ../poses/)
        inputs/                           # Unpacked package JSONs
        previews/                         # front.png, side.png, three-quarter.png, qa-regions.png
        scene.blend                       # Saved Blender scene (gitignored)
        blender-result.json
        build-settings.json
        build.log
      r002/
      r003/
  snapshots/
    batch-0001-pass-01_<YYYYMMDDTHHMMSSZ>/ # Persistent per-pass snapshot (mirrors ../snapshots/)
      plan.json
      batch-summary.json
      batch-summary.md
      AUDIT.md
      author.py                           # Authoring script provenance (when applicable)
      spose-workspace-feedback-batch-0001-pass-01_<ts>.zip  # Compact lossless WebP feedback archive (gitignored)
  review/                                 # Disposable flat latest/activated batch PNGs + SUMMARY.md + MANIFEST.json
  upload/                                 # Disposable flat PNGs + single compact feedback ZIP + SUMMARY.md + MANIFEST.json
  scripts/
    ws_common.py                          # Non-pollution boundary guard + read-only catalog/template helpers
    ws_tracker.py                         # Registry + derived workspace/ROADMAP.{md,json}
    ws_run_batch.py                       # Executes a workspace/batches/BATCH-XXXX-PASS-YY.json plan
    ws_activate_batch.py                  # Rebuilds disposable workspace/review/ & workspace/upload/ from any snapshot
```

### Key Rules
- **Sequential batch numbering (`batch-0001`, `batch-0002`, `batch-0003`, …):** Every batch holds up to 5 poses (or 4 when a family only has 4 poses). Multi-batch families (e.g., `OFEL` with 20 poses) simply span consecutive batches (`batch-0004` through `batch-0007`).
- **Immutable revisions (`workspace/poses/<POSE_ID>/CPL01/v001/rNNN/`):** Every pass creates a distinct `rNNN` revision when a new package SHA-256 is built (or records `reused_existing_package` truthfully if unchanged). Never overwrite an existing `rNNN` folder.
- **Persistent snapshots (`workspace/snapshots/`):** Every pass run gets its own timestamped snapshot folder. History never disappears when `workspace/review/` or `workspace/upload/` refreshes.
- **Disposable flat exchange (`workspace/review/` and `workspace/upload/`):** Always recreatable from `workspace/snapshots/` and `workspace/poses/` via `ws_activate_batch.py` with zero Blender rerenders.

---

## 4. End-to-End Experimental Workflow

### Step 1 — Author & Validate Data-Only Packages
1. Check `python workspace/scripts/ws_tracker.py status` (or `next-batch`) to pick the next 5 unstarted V00 poses in reverse catalog order.
2. Author data-only `spose_pose_module` ZIPs into `workspace/incoming/` containing only allowed JSON members (`manifest.json`, `pose.json`, `rig-targets.json`, `contacts.json`, plus optional `render-config.json` / `validation-plan.json`).
3. Validate every ZIP with `../scripts/pose_common.py::load_package(..., validate_dependencies=True)` against the pinned top-level catalog and pair template hashes.
4. Write the pass plan `workspace/batches/BATCH-XXXX-PASS-YY.json` (`batch_label`: `batch-XXXX`, `pass_label`: `pass-YY`, ordered `poses` list pointing to filenames in `workspace/incoming/`).

### Step 2 — Isolated Blender Build, Revisioning & Snapshot
1. Validate offline first: `python workspace/scripts/ws_run_batch.py --plan workspace/batches/BATCH-XXXX-PASS-YY.json --dry-run`.
2. Render in Blender `5.2.2 LTS`: `python workspace/scripts/ws_run_batch.py --plan workspace/batches/BATCH-XXXX-PASS-YY.json --blender "<BLENDER_EXE>"`.
   - Creates immutable revisions under `workspace/poses/<POSE_ID>/CPL01/v001/rNNN/`.
   - Writes a persistent snapshot under `workspace/snapshots/<batch>-<pass>_<ts>/` with `batch-summary.json`, `batch-summary.md`, `plan.json`, and compact lossless WebP feedback ZIP.
   - Refreshes disposable `workspace/review/` and `workspace/upload/`.
   - Updates `workspace/tracking/workspace-tracker.json` and regenerates `workspace/ROADMAP.md` & `workspace/ROADMAP.json`.

### Step 3 — Independent Blind Visual QA Audit
- **No fabricated scores, no blocking quality gates.** Never trust automated `issue_count: 0` over visual inspection.
- Inspect the rendered PNGs in `workspace/review/` and invoke a fresh-context blind reviewer subagent (given only `pose.json`, `blender-result.json`, and all 4 PNG views per pose) to score independently before comparing with earlier passes.
- Write `AUDIT.md` inside the pass's snapshot folder (`workspace/snapshots/<snapshot>/AUDIT.md`), record the score via `ws_tracker.py mark-audit`, and refresh the feedback ZIP / exchange via `ws_activate_batch.py --batch <batch> --pass <pass> --rebuild-zip`.

---

## 5. Promotion to the Authoritative Library (Explicit User Action Only)

Nothing in `workspace/` is ever automatically promoted into the official library. When the user explicitly approves a workspace batch/pass for official entry:
1. Verify `../scripts/check_remote.py` passes.
2. Copy the approved data-only ZIPs from `workspace/incoming/` into `../incoming/`.
3. Write an official Infra 0002 plan in `../batches/` with the user's chosen official batch ID.
4. Run `../scripts/run_registered_batch.py` so official `../poses/`, `../snapshots/`, and `../tracking/progress.sqlite` records are created through the verified main pipeline.
5. Record promotion provenance via `python workspace/scripts/ws_tracker.py mark-promoted ...`.

---

## 6. Workspace CLI Commands

Run from the repository root:

```powershell
python workspace/scripts/ws_tracker.py status
python workspace/scripts/ws_tracker.py next-batch
python workspace/scripts/ws_tracker.py sync
python workspace/scripts/ws_run_batch.py --plan workspace/batches/BATCH-0004-PASS-01.json --dry-run
python workspace/scripts/ws_run_batch.py --plan workspace/batches/BATCH-0004-PASS-01.json --blender "<BLENDER_EXE>"
python workspace/scripts/ws_activate_batch.py --batch batch-0003 --pass pass-02
python workspace/scripts/ws_tracker.py mark-audit --batch batch-0003 --pass pass-02 --score 6.88 --notes "..."
```

All workspace scripts enforce `ws_common.ensure_in_workspace()` and refuse any write path outside `workspace/`.

---

## 7. Verification & Git Hygiene

- Confirm zero top-level pollution after any run (`python scripts/check_remote.py`, `python scripts/check_documentation.py`, and `git status` showing changes strictly inside `workspace/`).
- Report offline Python/ZIP validation separately from Blender render runs.
- **Data-only Git policy:**
  - Track: `workspace/AGENTS.md`, `workspace/ROADMAP.{md,json}`, `workspace/tracking/workspace-tracker.json`, `workspace/scripts/`, `workspace/incoming/*.zip`, `workspace/batches/*.json`, `workspace/poses/**/inputs/*.json`, `workspace/poses/**/blender-result.json`, `build-settings.json`, `build.log`, and `workspace/snapshots/**` JSON/MD/py files.
  - Ignore: `*.blend`, `*.png`, `*.webp`, `workspace/review/`, `workspace/upload/`, `workspace/local/`, and feedback `*.zip` archives under `workspace/snapshots/`.
